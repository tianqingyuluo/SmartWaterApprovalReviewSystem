import json
import logging
import re
import time
from typing import Any

from openai import OpenAI

from src.adapters import ReviewAdapter
from src.config import config
from src.models import (
    ExtractedField,
    FindingType,
    Issue,
    MaterialCompleteness,
    ModelMetadata,
    ReviewResult,
    RiskHint,
)

logger = logging.getLogger(__name__)

FAILURE_CATEGORIES = [
    "AUTH_ERROR",
    "RATE_LIMIT",
    "TIMEOUT",
    "UPSTREAM_5XX",
    "INVALID_JSON",
    "SCHEMA_MISMATCH",
    "CONTENT_FILTERED",
    "UNSUPPORTED_CAPABILITY",
]

RETRYABLE_FAILURES = {"TIMEOUT", "RATE_LIMIT", "UPSTREAM_5XX"}

_FINDING_CODES = ", ".join(sorted(FindingType.ALL))

_SYSTEM_PROMPT = (
    "你是一个取水许可材料审核辅助工具。你的职责是帮助审批人员检查材料完整性、"
    "识别字段问题、发现一致性风险并提供审核意见草稿。"
    "你不能给出最终的批准或驳回判定。"
    "必须严格按照要求的JSON格式输出结果。"
    f"issue.code 必须使用以下枚举值之一: {_FINDING_CODES}"
)

_REVIEW_MODE = "ASSISTIVE_REVIEW"
_OUTPUT_LANGUAGE = "zh-CN"

_SCHEMA_REQUIRED_TOP = {
    "summary",
    "issues",
    "risk_hints",
    "draft_opinion",
    "material_completeness",
    "basis_refs",
    "manual_review_notice",
}

_SCHEMA_REQUIRED_ISSUE = {"code", "severity", "message"}


_REVIEW_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "severity": {"type": "string", "enum": ["INFO", "WARNING", "BLOCKER"]},
                    "message": {"type": "string"},
                    "material_type": {"type": "string"},
                    "field_key": {"type": "string"},
                    "basis_refs": {"type": "array", "items": {"type": "string"}},
                    "applicant_visible": {"type": "boolean"},
                },
                "required": ["code", "severity", "message"],
            },
        },
        "risk_hints": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
                    "description": {"type": "string"},
                    "basis_refs": {"type": "array", "items": {"type": "string"}},
                    "requires_manual_review": {"type": "boolean"},
                },
                "required": ["risk_level", "description"],
            },
        },
        "draft_opinion": {"type": "string"},
        "material_completeness": {
            "type": "object",
            "properties": {
                "received": {"type": "array", "items": {"type": "string"}},
                "missing": {"type": "array", "items": {"type": "string"}},
                "unrecognized": {"type": "array", "items": {"type": "string"}},
            },
        },
        "basis_refs": {"type": "array", "items": {"type": "string"}},
        "manual_review_notice": {"type": "string"},
    },
    "required": [
        "summary",
        "issues",
        "risk_hints",
        "draft_opinion",
        "material_completeness",
        "basis_refs",
        "manual_review_notice",
    ],
}


class ReviewReasoningAdapter(ReviewAdapter):
    def review(
        self,
        task_id: str,
        session_id: str,
        extracted_fields: list[ExtractedField],
        material_types: list[str],
        missing_materials: list[str],
        knowledge_fragments: list,
    ) -> ReviewResult:
        client = self._build_client()
        allowed_basis_refs = _knowledge_fragment_ids(knowledge_fragments)
        user_prompt = self._build_user_prompt(extracted_fields, material_types, missing_materials, knowledge_fragments)

        messages: list[dict[str, str]] = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        payload: dict[str, Any] = {
            "model": config.REVIEW_LLM_MODEL,
            "messages": messages,
            "max_tokens": 4000,
            "temperature": 0.1,
        }

        if config.REVIEW_LLM_PROVIDER == "dashscope":
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "review_result",
                    "strict": True,
                    "schema": _REVIEW_JSON_SCHEMA,
                },
            }
        else:
            payload["response_format"] = {"type": "json_object"}

        classification: str | None = None
        repair_attempted = False

        for attempt in range(config.WORKER_MAX_RETRIES):
            try:
                logger.info(
                    "Review attempt %d/%d for task %s session %s",
                    attempt + 1,
                    config.WORKER_MAX_RETRIES,
                    task_id,
                    session_id[:8] + "..." if len(session_id) > 8 else session_id,
                )
                start_time = time.time()
                resp = client.chat.completions.create(**payload)
                elapsed = time.time() - start_time
                content = resp.choices[0].message.content or ""
                finish = resp.choices[0].finish_reason

                parsed, failure = self._parse_and_validate(content, task_id, allowed_basis_refs)
                if parsed is not None:
                    parsed.model_metadata = ModelMetadata(
                        provider=config.REVIEW_LLM_PROVIDER,
                        model=config.REVIEW_LLM_MODEL,
                        request_id=resp.id,
                        finish_reason=finish,
                        token_usage=_safe_token_usage(resp),
                    )
                    logger.info(
                        "Review done for task %s: model=%s latency=%.1fs tokens=%s",
                        task_id,
                        config.REVIEW_LLM_MODEL,
                        elapsed,
                        _safe_token_usage(resp),
                    )
                    return parsed

                failure_type = failure or "SCHEMA_MISMATCH"
                classification = failure_type
                logger.warning(
                    "Review validation failed for task %s: %s latency=%.1fs attempt=%d",
                    task_id,
                    failure_type,
                    elapsed,
                    attempt + 1,
                )

                if repair_attempted or attempt >= config.WORKER_MAX_RETRIES - 1:
                    return self._schema_mismatch_result(task_id, failure_type)

                repair_attempted = True
                messages.append({"role": "user", "content": _repair_prompt(failure_type)})

            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    "Review API error for task %s: %s latency=%.1fs",
                    task_id,
                    e,
                    elapsed,
                )
                category = _classify_error(e)
                if attempt < config.WORKER_MAX_RETRIES - 1 and category in RETRYABLE_FAILURES:
                    time.sleep(2**attempt)
                    continue
                return self._error_result(task_id, str(e), category)

        return self._error_result(task_id, "max retries exhausted", classification or "UNKNOWN")

    def _build_client(self) -> OpenAI:
        return OpenAI(
            api_key=config.REVIEW_LLM_API_KEY,
            base_url=config.REVIEW_LLM_BASE_URL,
            timeout=120,
        )

    def _build_user_prompt(
        self,
        fields: list[ExtractedField],
        material_types: list[str],
        missing: list[str],
        knowledge: list,
    ) -> str:
        parts: list[str] = []

        parts.append("## 材料状态")
        parts.append(f"已上传材料: {', '.join(material_types) if material_types else '无'}")
        if missing:
            parts.append(f"缺失材料: {', '.join(missing)}")

        parts.append("\n## 抽取字段")
        for f in fields:
            parts.append(f"- {f.field_key}: {f.field_value} (置信度: {f.confidence:.2f})")

        if knowledge:
            parts.append("\n## 法规依据")
            for k in knowledge:
                if hasattr(k, "source_title"):
                    parts.append(f"- [{k.source_id}] {k.source_title}: {k.content}")
                elif isinstance(k, dict):
                    parts.append(f"- [{k.get('source_id', '')}] {k.get('source_title', '')}: {k.get('content', '')}")

        parts.append(f"审核模式: {_REVIEW_MODE}, 输出语言: {_OUTPUT_LANGUAGE}")

        parts.append("\n## 审核要求")
        parts.append("请根据以上信息生成审核结果，包括：材料完整性、字段问题、一致性风险、审核意见草稿。")
        parts.append("注意：你只能引用上述法规依据中列出的条目，不能编造法规条文。")

        return "\n".join(parts)

    def _parse_and_validate(
        self,
        content: str,
        task_id: str,
        allowed_basis_refs: set[str] | None = None,
    ) -> tuple[ReviewResult | None, str | None]:
        if not content or not content.strip():
            logger.warning("Empty content from review for task %s", task_id)
            return None, "INVALID_JSON"

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning("Invalid JSON from review for task %s: %s", task_id, e)
            return None, "INVALID_JSON"

        if not isinstance(data, dict):
            logger.warning("Review output is not a JSON object for task %s", task_id)
            return None, "SCHEMA_MISMATCH"

        missing_top = _SCHEMA_REQUIRED_TOP - set(data.keys())
        if missing_top:
            logger.warning("Schema mismatch for task %s: missing top-level keys %s", task_id, missing_top)
            return None, "SCHEMA_MISMATCH"

        issues_raw = data.get("issues", [])
        if not isinstance(issues_raw, list):
            return None, "SCHEMA_MISMATCH"

        for idx, i in enumerate(issues_raw):
            if not isinstance(i, dict):
                return None, "SCHEMA_MISMATCH"
            missing_issue = _SCHEMA_REQUIRED_ISSUE - set(i.keys())
            if missing_issue:
                logger.warning("Schema mismatch for task %s: issue[%d] missing keys %s", task_id, idx, missing_issue)
                return None, "SCHEMA_MISMATCH"

        risk_hints_raw = data.get("risk_hints", [])
        if not isinstance(risk_hints_raw, list):
            return None, "SCHEMA_MISMATCH"

        invalid_refs = _invalid_basis_refs(data, allowed_basis_refs)
        if invalid_refs:
            logger.warning(
                "Schema mismatch for task %s: invented basisRefs %s",
                task_id,
                sorted(invalid_refs),
            )
            return None, "SCHEMA_MISMATCH"

        try:
            issues = [
                Issue(
                    code=i.get("code", ""),
                    severity=i.get("severity", "INFO"),
                    message=i.get("message", ""),
                    material_type=i.get("material_type"),
                    field_key=i.get("field_key"),
                    basis_refs=i.get("basis_refs", []),
                    applicant_visible=i.get("applicant_visible", True),
                )
                for i in issues_raw
            ]

            risk_hints = [
                RiskHint(
                    risk_level=r.get("risk_level", "LOW"),
                    description=r.get("description", ""),
                    basis_refs=r.get("basis_refs", []),
                    requires_manual_review=r.get("requires_manual_review", False),
                )
                for r in risk_hints_raw
            ]

            mc = data.get("material_completeness", {})
            material_completeness = MaterialCompleteness(
                received=mc.get("received", []),
                missing=mc.get("missing", []),
                unrecognized=mc.get("unrecognized", []),
            )

            return ReviewResult(
                summary=data.get("summary", ""),
                issues=issues,
                risk_hints=risk_hints,
                draft_opinion=data.get("draft_opinion", ""),
                material_completeness=material_completeness,
                basis_refs=data.get("basis_refs", []),
                manual_review_notice=data.get(
                    "manual_review_notice",
                    "AI审核结果为辅助建议，不构成最终审批意见。",
                ),
            ), None
        except Exception as e:
            logger.warning("Schema validation failed for task %s: %s", task_id, e)
            return None, "SCHEMA_MISMATCH"

    def _schema_mismatch_result(self, task_id: str, category: str = "SCHEMA_MISMATCH") -> ReviewResult:
        return ReviewResult(
            summary="AI审核输出格式校验失败",
            issues=[
                Issue(
                    code=category,
                    severity="BLOCKER",
                    message="审核推理输出格式不符合预期，需要人工复核。",
                    applicant_visible=False,
                )
            ],
            manual_review_notice="AI审核输出格式校验失败，请人工审核所有材料。",
        )

    def _error_result(self, task_id: str, error: str, category: str = "UPSTREAM_5XX") -> ReviewResult:
        return ReviewResult(
            summary=f"审核推理失败: {error}",
            issues=[
                Issue(
                    code=category,
                    severity="BLOCKER",
                    message=f"审核推理调用失败: {error}",
                    applicant_visible=False,
                )
            ],
            manual_review_notice="AI审核服务暂时不可用，请稍后重试或人工审核。",
        )


def _repair_prompt(failure_type: str) -> str:
    if failure_type == "INVALID_JSON":
        return "你上一次的输出不是有效的JSON格式。请严格按照JSON格式重新输出，确保所有字段都存在且符合指定的schema。"
    else:
        return (
            "你上一次的输出缺少必要的字段或字段类型不正确。"
            "请严格按照以下schema补全所有required字段后重新输出完整的审核结果JSON。"
        )


def _classify_error(e: Exception) -> str:
    msg = str(e).lower()
    if "401" in msg or "unauthorized" in msg or "auth" in msg:
        return "AUTH_ERROR"
    if "429" in msg or "rate" in msg:
        return "RATE_LIMIT"
    if "timeout" in msg:
        return "TIMEOUT"
    if "content" in msg and ("filter" in msg or "policy" in msg or "safety" in msg):
        return "CONTENT_FILTERED"
    if re.search(r"(500|502|503|504)", msg):
        return "UPSTREAM_5XX"
    return "UPSTREAM_5XX"


def _safe_token_usage(resp) -> dict:
    try:
        return {
            "prompt_tokens": resp.usage.prompt_tokens,
            "completion_tokens": resp.usage.completion_tokens,
            "total_tokens": resp.usage.total_tokens,
        }
    except Exception:
        return {}


def _knowledge_fragment_ids(knowledge_fragments: list) -> set[str]:
    ids: set[str] = set()
    for fragment in knowledge_fragments:
        if hasattr(fragment, "source_id"):
            source_id = getattr(fragment, "source_id", None)
        elif isinstance(fragment, dict):
            source_id = fragment.get("source_id") or fragment.get("sourceId") or fragment.get("id")
        else:
            source_id = None

        if source_id:
            ids.add(str(source_id))
    return ids


def _invalid_basis_refs(data: dict, allowed_basis_refs: set[str] | None) -> set[str]:
    if allowed_basis_refs is None:
        return set()

    observed: set[str] = set()
    for ref in data.get("basis_refs", []):
        observed.add(str(ref))

    for issue in data.get("issues", []):
        if isinstance(issue, dict):
            for ref in issue.get("basis_refs", []):
                observed.add(str(ref))

    for hint in data.get("risk_hints", []):
        if isinstance(hint, dict):
            for ref in hint.get("basis_refs", []):
                observed.add(str(ref))

    return observed - allowed_basis_refs
