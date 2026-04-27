import json
import logging
import time
from openai import OpenAI
from src.config import config
from src.adapters import ReviewAdapter
from src.models import (
    ExtractedField,
    ReviewResult,
    Issue,
    RiskHint,
    MaterialCompleteness,
    ModelMetadata,
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

_SYSTEM_PROMPT = (
    "你是一个取水许可材料审核辅助工具。你的职责是帮助审批人员检查材料完整性、"
    "识别字段问题、发现一致性风险并提供审核意见草稿。"
    "你不能给出最终的批准或驳回判定。"
    "必须严格按照要求的JSON格式输出结果。"
)


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
    "required": ["summary", "issues", "risk_hints", "draft_opinion", "material_completeness", "basis_refs", "manual_review_notice"],
}


class ReviewReasoningAdapter(ReviewAdapter):
    def review(
        self,
        task_id: str,
        extracted_fields: list[ExtractedField],
        material_types: list[str],
        missing_materials: list[str],
        knowledge_fragments: list,
    ) -> ReviewResult:
        client = self._build_client()
        user_prompt = self._build_user_prompt(
            extracted_fields, material_types, missing_materials, knowledge_fragments
        )

        payload = {
            "model": config.REVIEW_LLM_MODEL,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
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

        for attempt in range(config.WORKER_MAX_RETRIES):
            try:
                logger.info("Review attempt %d/%d for task %s", attempt + 1, config.WORKER_MAX_RETRIES, task_id)
                resp = client.chat.completions.create(**payload)
                content = resp.choices[0].message.content
                finish = resp.choices[0].finish_reason

                parsed = self._parse_and_validate(content, task_id)
                if parsed is not None:
                    parsed.model_metadata = ModelMetadata(
                        provider=config.REVIEW_LLM_PROVIDER,
                        model=config.REVIEW_LLM_MODEL,
                        request_id=resp.id,
                        finish_reason=finish,
                        token_usage=_safe_token_usage(resp),
                    )
                    return parsed

                if attempt >= config.WORKER_MAX_RETRIES - 1:
                    return self._schema_mismatch_result(task_id)

            except Exception as e:
                logger.error("Review API error for task %s: %s", task_id, e)
                if attempt < config.WORKER_MAX_RETRIES - 1:
                    time.sleep(2**attempt)
                else:
                    return self._error_result(task_id, str(e))

        return self._error_result(task_id, "max retries exhausted")

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
            parts.append(
                f"- {f.field_key}: {f.field_value} (置信度: {f.confidence:.2f})"
            )

        if knowledge:
            parts.append("\n## 法规依据")
            for k in knowledge:
                if hasattr(k, "source_title"):
                    parts.append(
                        f"- [{k.source_id}] {k.source_title}: {k.content}"
                    )
                elif isinstance(k, dict):
                    parts.append(
                        f"- [{k.get('source_id', '')}] {k.get('source_title', '')}: {k.get('content', '')}"
                    )

        parts.append("\n## 审核要求")
        parts.append("请根据以上信息生成审核结果，包括：材料完整性、字段问题、一致性风险、审核意见草稿。")
        parts.append("注意：你只能引用上述法规依据中列出的条目，不能编造法规条文。")

        return "\n".join(parts)

    def _parse_and_validate(self, content: str, task_id: str) -> ReviewResult | None:
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning("Invalid JSON from review for task %s: %s", task_id, e)
            return None

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
                for i in data.get("issues", [])
            ]

            risk_hints = [
                RiskHint(
                    risk_level=r.get("risk_level", "LOW"),
                    description=r.get("description", ""),
                    basis_refs=r.get("basis_refs", []),
                    requires_manual_review=r.get("requires_manual_review", False),
                )
                for r in data.get("risk_hints", [])
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
            )
        except Exception as e:
            logger.warning("Schema validation failed for task %s: %s", task_id, e)
            return None

    def _schema_mismatch_result(self, task_id: str) -> ReviewResult:
        return ReviewResult(
            summary="AI审核输出格式校验失败",
            issues=[
                Issue(
                    code="SYSTEM_ERROR",
                    severity="BLOCKER",
                    message="审核推理输出格式不符合预期，需要人工复核。",
                    applicant_visible=False,
                )
            ],
            manual_review_notice="AI审核输出格式校验失败，请人工审核所有材料。",
        )

    def _error_result(self, task_id: str, error: str) -> ReviewResult:
        return ReviewResult(
            summary=f"审核推理失败: {error}",
            issues=[
                Issue(
                    code="SYSTEM_ERROR",
                    severity="BLOCKER",
                    message=f"审核推理调用失败: {error}",
                    applicant_visible=False,
                )
            ],
            manual_review_notice="AI审核服务暂时不可用，请稍后重试或人工审核。",
        )


def _safe_token_usage(resp) -> dict:
    try:
        return {
            "prompt_tokens": resp.usage.prompt_tokens,
            "completion_tokens": resp.usage.completion_tokens,
            "total_tokens": resp.usage.total_tokens,
        }
    except Exception:
        return {}
