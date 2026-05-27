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

_TOP_LEVEL_ALIASES = {
    "摘要": "summary",
    "总结": "summary",
    "审核摘要": "summary",
    "riskHints": "risk_hints",
    "一致性风险": "risk_hints",
    "风险提示": "risk_hints",
    "draftOpinion": "draft_opinion",
    "审核意见草稿": "draft_opinion",
    "意见草稿": "draft_opinion",
    "materialCompleteness": "material_completeness",
    "材料完整性": "material_completeness",
    "basisRefs": "basis_refs",
    "依据引用": "basis_refs",
    "引用依据": "basis_refs",
    "manualReviewNotice": "manual_review_notice",
    "人工复核说明": "manual_review_notice",
    "人工审核提示": "manual_review_notice",
    "字段问题": "issues",
    "问题列表": "issues",
    "合规问题": "issues",
}

_ISSUE_ALIASES = {
    "问题编码": "code",
    "问题类型": "code",
    "类型": "code",
    "严重级别": "severity",
    "级别": "severity",
    "问题描述": "message",
    "描述": "message",
    "说明": "message",
    "materialType": "material_type",
    "材料类型": "material_type",
    "fieldKey": "field_key",
    "字段": "field_key",
    "字段键": "field_key",
    "basisRefs": "basis_refs",
    "依据": "basis_refs",
    "依据引用": "basis_refs",
    "applicantVisible": "applicant_visible",
    "是否申请人可见": "applicant_visible",
}

_RISK_HINT_ALIASES = {
    "riskLevel": "risk_level",
    "风险等级": "risk_level",
    "等级": "risk_level",
    "风险描述": "description",
    "描述": "description",
    "basisRefs": "basis_refs",
    "依据": "basis_refs",
    "依据引用": "basis_refs",
    "requiresManualReview": "requires_manual_review",
    "是否需要人工复核": "requires_manual_review",
    "需要人工复核": "requires_manual_review",
}

_MATERIAL_COMPLETENESS_ALIASES = {
    "已接收材料": "received",
    "接收材料": "received",
    "已上传材料": "received",
    "缺失材料": "missing",
    "未识别材料": "unrecognized",
    "无法识别材料": "unrecognized",
}

_WRAPPER_KEYS = (
    "review_result",
    "reviewResult",
    "result",
    "data",
    "output",
    "response",
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
        basis_ref_aliases = _knowledge_fragment_aliases(knowledge_fragments)
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
                    "Review attempt %d/%d for task %s",
                    attempt + 1,
                    config.WORKER_MAX_RETRIES,
                    task_id,
                )
                start_time = time.time()
                resp = client.chat.completions.create(**payload)
                elapsed = time.time() - start_time
                content = resp.choices[0].message.content or ""
                finish = resp.choices[0].finish_reason

                parsed, failure = self._parse_and_validate(content, task_id, allowed_basis_refs, basis_ref_aliases)
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
                category = _classify_error(e)
                logger.error(
                    "Review API error for task %s: category=%s errorType=%s latency=%.1fs",
                    task_id,
                    category,
                    e.__class__.__name__,
                    elapsed,
                )
                if attempt < config.WORKER_MAX_RETRIES - 1 and category in RETRYABLE_FAILURES:
                    time.sleep(2**attempt)
                    continue
                return self._error_result(task_id, category)

        return self._error_result(task_id, classification or "UNKNOWN")

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
        parts.append("注意：你只能引用上述法规依据中列出的 source_id，不能编造法规条文或来源 ID。")
        parts.append("必须只输出一个 JSON object，不要 Markdown，不要解释文字。")
        parts.append(
            "JSON 顶层字段名必须使用英文 snake_case，且必须包含: "
            "summary, issues, risk_hints, draft_opinion, material_completeness, basis_refs, manual_review_notice。"
        )
        parts.append(
            "issues[] 字段名必须使用: "
            "code, severity, message, material_type, field_key, basis_refs, applicant_visible。"
        )
        parts.append(
            "risk_hints[] 字段名必须使用: risk_level, description, basis_refs, requires_manual_review。"
        )

        return "\n".join(parts)

    def _parse_and_validate(
        self,
        content: str,
        task_id: str,
        allowed_basis_refs: set[str] | None = None,
        basis_ref_aliases: dict[str, str] | None = None,
    ) -> tuple[ReviewResult | None, str | None]:
        if not content or not content.strip():
            logger.warning("Empty content from review for task %s", task_id)
            return None, "INVALID_JSON"

        json_text = _extract_json_object(content)
        if not json_text:
            logger.warning("No JSON object found in review content for task %s", task_id)
            return None, "INVALID_JSON"

        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.warning("Invalid JSON from review for task %s: %s", task_id, e)
            return None, "INVALID_JSON"

        if not isinstance(data, dict):
            logger.warning("Review output is not a JSON object for task %s", task_id)
            return None, "SCHEMA_MISMATCH"
        data = _normalize_review_payload(data)
        if basis_ref_aliases:
            data = _canonicalize_basis_refs_in_payload(data, basis_ref_aliases, allowed_basis_refs or set())

        missing_top = _SCHEMA_REQUIRED_TOP - set(data.keys())
        if missing_top:
            logger.warning(
                "Schema mismatch for task %s: keys=%s missing top-level keys %s",
                task_id,
                sorted(str(key) for key in data.keys())[:20],
                missing_top,
            )
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

    def _error_result(self, task_id: str, category: str = "UPSTREAM_5XX") -> ReviewResult:
        return ReviewResult(
            summary=f"审核推理失败: {category}",
            issues=[
                Issue(
                    code=category,
                    severity="BLOCKER",
                    message=f"审核推理调用失败，失败类型: {category}，需要人工复核。",
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


def _extract_json_object(content: str) -> str | None:
    text = content.strip()
    if not text:
        return None

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()

    if text.startswith("{") and text.endswith("}"):
        return text

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def _normalize_review_payload(data: dict[str, Any]) -> dict[str, Any]:
    unwrapped = _unwrap_review_payload(data)
    normalized = _normalize_aliases(unwrapped, _TOP_LEVEL_ALIASES)

    issues = normalized.get("issues")
    if isinstance(issues, list):
        normalized["issues"] = [
            _normalize_issue(issue) if isinstance(issue, dict) else issue for issue in issues
        ]

    risk_hints = normalized.get("risk_hints")
    if isinstance(risk_hints, list):
        normalized["risk_hints"] = [
            _normalize_risk_hint(hint) if isinstance(hint, dict) else hint for hint in risk_hints
        ]

    material_completeness = normalized.get("material_completeness")
    if isinstance(material_completeness, dict):
        normalized["material_completeness"] = _normalize_material_completeness(material_completeness)

    normalized = _apply_review_defaults(normalized)
    return normalized


def _normalize_issue(issue: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_aliases(issue, _ISSUE_ALIASES)
    normalized["code"] = _normalize_issue_code(normalized.get("code"))
    normalized["severity"] = _normalize_severity(normalized.get("severity"))
    normalized["message"] = str(normalized.get("message") or normalized.get("code") or "模型返回问题项未提供描述。")
    normalized["basis_refs"] = _normalize_basis_refs(normalized.get("basis_refs"))
    normalized["applicant_visible"] = _normalize_bool(normalized.get("applicant_visible"), default=True)
    if normalized.get("material_type") is not None:
        normalized["material_type"] = str(normalized.get("material_type"))
    if normalized.get("field_key") is not None:
        normalized["field_key"] = str(normalized.get("field_key"))
    return normalized


def _normalize_risk_hint(hint: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_aliases(hint, _RISK_HINT_ALIASES)
    normalized["risk_level"] = _normalize_risk_level(normalized.get("risk_level"))
    normalized["description"] = str(normalized.get("description") or "模型返回风险项未提供描述。")
    normalized["basis_refs"] = _normalize_basis_refs(normalized.get("basis_refs"))
    normalized["requires_manual_review"] = _normalize_bool(normalized.get("requires_manual_review"), default=False)
    return normalized


def _normalize_material_completeness(value: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_aliases(value, _MATERIAL_COMPLETENESS_ALIASES)
    return {
        "received": _normalize_string_list(normalized.get("received")),
        "missing": _normalize_string_list(normalized.get("missing")),
        "unrecognized": _normalize_string_list(normalized.get("unrecognized")),
    }


def _apply_review_defaults(data: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(data)
    if "summary" not in normalized:
        normalized["summary"] = "AI已根据材料抽取结果和知识库依据生成辅助初审结果。"
    if "risk_hints" not in normalized:
        normalized["risk_hints"] = []
    if "basis_refs" not in normalized:
        refs: list[str] = []
        for issue in normalized.get("issues", []):
            if isinstance(issue, dict):
                refs.extend(_normalize_basis_refs(issue.get("basis_refs")))
        for hint in normalized.get("risk_hints", []):
            if isinstance(hint, dict):
                refs.extend(_normalize_basis_refs(hint.get("basis_refs")))
        normalized["basis_refs"] = _dedupe_strings(refs)
    else:
        normalized["basis_refs"] = _normalize_basis_refs(normalized.get("basis_refs"))
    if "manual_review_notice" not in normalized:
        normalized["manual_review_notice"] = "AI审核结果为辅助建议，不构成最终审批意见。"
    return normalized


def _unwrap_review_payload(data: dict[str, Any]) -> dict[str, Any]:
    if _looks_like_review_payload(data):
        return data

    for key in _WRAPPER_KEYS:
        value = data.get(key)
        if isinstance(value, dict) and _looks_like_review_payload(value):
            return value

    for value in data.values():
        if isinstance(value, dict) and _looks_like_review_payload(value):
            return value

    return data


def _looks_like_review_payload(data: dict[str, Any]) -> bool:
    normalized_keys = set(data.keys())
    for alias, canonical in _TOP_LEVEL_ALIASES.items():
        if alias in normalized_keys:
            normalized_keys.add(canonical)
    return bool(_SCHEMA_REQUIRED_TOP & normalized_keys)


def _normalize_aliases(data: dict[str, Any], aliases: dict[str, str]) -> dict[str, Any]:
    normalized = dict(data)
    for alias, canonical in aliases.items():
        if canonical not in normalized and alias in normalized:
            normalized[canonical] = normalized[alias]
    return normalized


def _normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return _dedupe_strings(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, str):
        parts = re.split(r"[、,，;；\\s]+", value.strip())
        return _dedupe_strings(part for part in parts if part)
    return [str(value)]


def _normalize_basis_refs(value: Any) -> list[str]:
    return _dedupe_strings(_strip_basis_ref_wrapper(item) for item in _normalize_string_list(value))


def _canonicalize_basis_refs_in_payload(
    data: dict[str, Any],
    aliases: dict[str, str],
    allowed_basis_refs: set[str],
) -> dict[str, Any]:
    normalized = dict(data)
    normalized["basis_refs"] = [
        _canonicalize_basis_ref(ref, aliases, allowed_basis_refs)
        for ref in _normalize_basis_refs(normalized.get("basis_refs"))
    ]

    issues = normalized.get("issues")
    if isinstance(issues, list):
        normalized["issues"] = [
            _canonicalize_basis_refs_in_item(item, aliases, allowed_basis_refs) if isinstance(item, dict) else item
            for item in issues
        ]

    risk_hints = normalized.get("risk_hints")
    if isinstance(risk_hints, list):
        normalized["risk_hints"] = [
            _canonicalize_basis_refs_in_item(item, aliases, allowed_basis_refs) if isinstance(item, dict) else item
            for item in risk_hints
        ]

    return normalized


def _canonicalize_basis_refs_in_item(
    item: dict[str, Any],
    aliases: dict[str, str],
    allowed_basis_refs: set[str],
) -> dict[str, Any]:
    normalized = dict(item)
    normalized["basis_refs"] = [
        _canonicalize_basis_ref(ref, aliases, allowed_basis_refs)
        for ref in _normalize_basis_refs(normalized.get("basis_refs"))
    ]
    return normalized


def _canonicalize_basis_ref(value: str, aliases: dict[str, str], allowed_basis_refs: set[str]) -> str:
    text = _strip_basis_ref_wrapper(value)
    if text in aliases:
        return aliases[text]

    prefix = re.split(r"[:：]", text, maxsplit=1)[0].strip()
    if prefix in aliases:
        return aliases[prefix]

    for allowed in allowed_basis_refs:
        if allowed and allowed in text:
            return allowed

    return text


def _strip_basis_ref_wrapper(value: str) -> str:
    text = str(value).strip()
    while len(text) >= 2 and (
        (text[0] == "[" and text[-1] == "]")
        or (text[0] == "【" and text[-1] == "】")
        or (text[0] == "(" and text[-1] == ")")
        or (text[0] == "（" and text[-1] == "）")
    ):
        text = text[1:-1].strip()
    return text


def _dedupe_strings(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _normalize_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "yes", "y", "1", "是", "需要", "可见"}:
            return True
        if text in {"false", "no", "n", "0", "否", "不需要", "不可见"}:
            return False
    if isinstance(value, int | float):
        return bool(value)
    return default


def _normalize_severity(value: Any) -> str:
    text = str(value or "").strip().upper()
    if text in {"INFO", "WARNING", "BLOCKER"}:
        return text
    if any(token in text for token in ("阻断", "严重", "高", "HIGH")):
        return "BLOCKER"
    if any(token in text for token in ("警告", "中", "MEDIUM", "WARN")):
        return "WARNING"
    return "INFO"


def _normalize_risk_level(value: Any) -> str:
    text = str(value or "").strip().upper()
    if text in {"LOW", "MEDIUM", "HIGH"}:
        return text
    if any(token in text for token in ("高", "严重", "HIGH")):
        return "HIGH"
    if any(token in text for token in ("中", "MEDIUM")):
        return "MEDIUM"
    return "LOW"


def _normalize_issue_code(value: Any) -> str:
    text = str(value or "").strip()
    upper = text.upper()
    if upper in FindingType.ALL:
        return upper

    mappings = (
        ("缺失材料", FindingType.MISSING_MATERIAL),
        ("材料缺失", FindingType.MISSING_MATERIAL),
        ("字段缺失", FindingType.MISSING_FIELD),
        ("缺少字段", FindingType.MISSING_FIELD),
        ("格式", FindingType.INVALID_FORMAT),
        ("身份", FindingType.INCONSISTENT_IDENTITY),
        ("证照", FindingType.INCONSISTENT_CREDENTIAL),
        ("取水量", FindingType.WATER_AMOUNT_REVIEW_REQUIRED),
        ("取水用途", FindingType.PERMIT_REQUIREMENT_REVIEW_REQUIRED),
        ("公示", FindingType.PUBLIC_NOTICE_REVIEW_REQUIRED),
        ("水资源论证", FindingType.WATER_RESOURCE_ASSESSMENT_REVIEW_REQUIRED),
    )
    for token, code in mappings:
        if token in text:
            return code
    return FindingType.MODEL_UNCERTAIN


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


def _knowledge_fragment_aliases(knowledge_fragments: list) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for fragment in knowledge_fragments:
        if hasattr(fragment, "source_id"):
            source_id = getattr(fragment, "source_id", None)
            source_title = getattr(fragment, "source_title", None)
        elif isinstance(fragment, dict):
            source_id = fragment.get("source_id") or fragment.get("sourceId") or fragment.get("id")
            source_title = fragment.get("source_title") or fragment.get("sourceTitle") or fragment.get("title")
        else:
            source_id = None
            source_title = None

        if not source_id:
            continue
        canonical = str(source_id).strip()
        if not canonical:
            continue
        aliases[canonical] = canonical
        for alias in _basis_ref_alias_candidates(canonical, source_title):
            aliases.setdefault(alias, canonical)
    return aliases


def _basis_ref_alias_candidates(source_id: str, source_title: Any) -> list[str]:
    candidates = [source_id]
    if source_title:
        title = str(source_title).strip()
        if title:
            candidates.append(title)
            candidates.append(re.sub(r"\.(docx?|pdf|jpe?g|png)$", "", title, flags=re.IGNORECASE))
    source_prefix = re.split(r"[_#]", source_id, maxsplit=1)[0].strip()
    if source_prefix:
        candidates.append(source_prefix)
        candidates.append(re.sub(r"\.(docx?|pdf|jpe?g|png)$", "", source_prefix, flags=re.IGNORECASE))
    return _dedupe_strings(candidates)


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
