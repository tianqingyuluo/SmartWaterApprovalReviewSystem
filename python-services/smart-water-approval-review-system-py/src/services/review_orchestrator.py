from __future__ import annotations

import logging
from typing import Any

from src.adapters.review_adapter import ReviewReasoningAdapter
from src.models import (
    ExtractedField,
    Issue,
    MaterialCompleteness,
    MaterialSlot,
    ProcessingResult,
    ReviewResult,
    RiskHint,
)
from src.services.field_extractor import FieldExtractor
from src.services.knowledge_tools import SmartWaterKnowledgeTools

logger = logging.getLogger(__name__)

_TOTAL_MVP_SLOTS = 3
_AGENT_FAILURE_CODES = {
    "AUTH_ERROR",
    "RATE_LIMIT",
    "TIMEOUT",
    "UPSTREAM_5XX",
    "INVALID_JSON",
    "SCHEMA_MISMATCH",
    "CONTENT_FILTERED",
    "UNSUPPORTED_CAPABILITY",
}
_ERROR_FIELD_KEYS = {"ocr_error", "extraction_error", "download_error"}


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _dedupe_issues(issues: list[Issue]) -> list[Issue]:
    seen: set[tuple[str, str, str, str, str]] = set()
    result: list[Issue] = []
    for issue in issues:
        key = (
            issue.code,
            issue.severity,
            issue.message,
            issue.material_type or "",
            issue.field_key or "",
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(issue)
    return result


class ReviewTaskOrchestrator:
    def __init__(
        self,
        extractor: FieldExtractor | None = None,
        reviewer: ReviewReasoningAdapter | None = None,
        knowledge_tools: SmartWaterKnowledgeTools | None = None,
        knowledge_fragments: list[dict[str, str]] | None = None,
        knowledge_pack_version: str | None = None,
    ) -> None:
        self._extractor = extractor or FieldExtractor()
        self._reviewer = reviewer or ReviewReasoningAdapter()
        self._knowledge_tools = knowledge_tools
        self._knowledge_fragments = knowledge_fragments or []
        self._knowledge_pack_version = knowledge_pack_version

    def process_task(self, task_data: dict[str, Any]) -> ProcessingResult:
        task_id = str(task_data.get("taskId") or "").strip()
        session_id = str(task_data.get("sessionId") or "").strip()
        materials = self._to_material_slots(task_data)
        uploaded = [material for material in materials if material.uploaded]
        material_types = [material.material_type for material in uploaded]

        completeness = self._check_completeness(material_types)
        missing_materials = completeness.get("missing", [])
        required_materials = completeness.get("required", [])
        rule_issues = self._build_rule_issues(completeness)

        extracted_fields: list[ExtractedField] = []
        partial_failures: list[str] = []
        for material in uploaded:
            fields = self._extractor.extract(material)
            extracted_fields.extend(fields)
            if any(field.field_key in _ERROR_FIELD_KEYS for field in fields):
                partial_failures.append(material.material_type)

        rule_issues.extend(self._build_extraction_issues(extracted_fields))
        rule_issues = _dedupe_issues(rule_issues)

        reviewer_result, agent_failed = self._review_with_fallback(
            task_id=task_id,
            session_id=session_id,
            extracted_fields=extracted_fields,
            material_types=material_types,
            missing_materials=missing_materials,
            rule_issues=rule_issues,
        )

        reviewer_result.material_completeness = self._merge_material_completeness(
            reviewer_result.material_completeness,
            material_types,
            missing_materials,
            completeness.get("unrecognized", []),
        )
        reviewer_result.extracted_fields = extracted_fields

        total_required = len(required_materials) or _TOTAL_MVP_SLOTS
        status = (
            "PARTIAL_SUCCESS"
            if agent_failed or partial_failures or missing_materials
            else "COMPLETED"
        )
        result_summary = reviewer_result.summary
        if partial_failures:
            processed_count = len(material_types)
            failure_count = len(partial_failures)
            result_summary = (
                f"{result_summary} (已处理材料{processed_count}/{total_required}, 部分失败: {failure_count})"
            )
        elif agent_failed:
            result_summary = f"{result_summary} (已降级为规则结果，建议人工复核)"

        applicant_result = ReviewResult(
            summary=reviewer_result.summary,
            issues=[issue for issue in reviewer_result.issues if issue.applicant_visible],
            material_completeness=reviewer_result.material_completeness,
            manual_review_notice=reviewer_result.manual_review_notice,
        )

        return ProcessingResult(
            task_id=task_id,
            status=status,
            result_summary=result_summary,
            applicant_result=applicant_result,
            reviewer_result=reviewer_result,
            knowledge_pack_version=self._knowledge_pack_version,
        )

    def _to_material_slots(self, task_data: dict[str, Any]) -> list[MaterialSlot]:
        slots: list[MaterialSlot] = []
        for item in task_data.get("materials", []):
            if not isinstance(item, dict):
                continue
            slots.append(
                MaterialSlot(
                    material_type=str(item.get("materialType") or ""),
                    original_file_name=item.get("originalFileName"),
                    storage_key=item.get("storageKey"),
                    file_extension=item.get("fileExtension"),
                    uploaded=bool(item.get("uploaded", False)),
                )
            )
        return slots

    def _check_completeness(self, material_types: list[str]) -> dict[str, Any]:
        if not self._knowledge_tools:
            missing = [
                material_type
                for material_type in ("APPLICATION_FORM", "BUSINESS_LICENSE", "ID_CARD")
                if material_type not in material_types
            ]
            return {
                "submitted": _dedupe(material_types),
                "required": ["APPLICATION_FORM", "BUSINESS_LICENSE", "ID_CARD"],
                "missing": missing,
                "unrecognized": [],
                "findings": [],
            }
        return self._knowledge_tools.check_completeness(material_types)

    def _build_rule_issues(self, completeness: dict[str, Any]) -> list[Issue]:
        issues: list[Issue] = []
        for finding in completeness.get("findings", []):
            if not isinstance(finding, dict):
                continue
            issues.append(
                Issue(
                    code=str(finding.get("code") or "MISSING_MATERIAL"),
                    severity=str(finding.get("severity") or "WARNING"),
                    message=str(finding.get("message") or "缺少必需材料。"),
                    material_type=str(finding.get("materialType") or "") or None,
                    basis_refs=[str(ref) for ref in finding.get("basisRefs", [])],
                    applicant_visible=True,
                )
            )
        return issues

    def _build_extraction_issues(self, extracted_fields: list[ExtractedField]) -> list[Issue]:
        issues: list[Issue] = []
        for field in extracted_fields:
            if field.field_key == "download_error":
                issues.append(
                    Issue(
                        code="SYSTEM_ERROR",
                        severity="BLOCKER",
                        message=f"{field.source_material or '材料'}下载失败，需人工补充处理。",
                        material_type=field.source_material,
                        applicant_visible=False,
                    )
                )
            elif field.field_key == "extraction_error":
                issues.append(
                    Issue(
                        code="SYSTEM_ERROR",
                        severity="BLOCKER",
                        message=f"{field.source_material or '材料'}解析失败，需人工复核。",
                        material_type=field.source_material,
                        applicant_visible=False,
                    )
                )
            elif field.field_key == "ocr_error":
                issues.append(
                    Issue(
                        code="OCR_LOW_CONFIDENCE",
                        severity="WARNING",
                        message=f"{field.source_material or '材料'}OCR失败或置信度不足，请人工核对。",
                        material_type=field.source_material,
                        applicant_visible=False,
                    )
                )
            elif 0.0 < field.confidence < 0.6:
                issues.append(
                    Issue(
                        code="OCR_LOW_CONFIDENCE",
                        severity="WARNING",
                        message=f"字段 {field.field_key} 置信度较低，建议人工核对。",
                        material_type=field.source_material,
                        field_key=field.field_key,
                        applicant_visible=False,
                    )
                )
        return issues

    def _review_with_fallback(
        self,
        task_id: str,
        session_id: str,
        extracted_fields: list[ExtractedField],
        material_types: list[str],
        missing_materials: list[str],
        rule_issues: list[Issue],
    ) -> tuple[ReviewResult, bool]:
        usable_fields = [field for field in extracted_fields if field.field_key not in _ERROR_FIELD_KEYS]
        if not usable_fields:
            return self._build_fallback_result(rule_issues, material_types, missing_materials, "NO_USABLE_FIELDS"), True

        knowledge_fragments = self._build_rag_fragments(material_types, usable_fields)
        try:
            review_result = self._reviewer.review(
                task_id=task_id,
                session_id=session_id,
                extracted_fields=usable_fields,
                material_types=material_types,
                missing_materials=missing_materials,
                knowledge_fragments=knowledge_fragments,
            )
        except Exception as exc:  # pragma: no cover - defensive, adapter already maps most failures.
            logger.error("Agent review failed for task %s: %s", task_id, exc)
            return self._build_fallback_result(rule_issues, material_types, missing_materials, str(exc)), True

        if any(issue.code in _AGENT_FAILURE_CODES for issue in review_result.issues):
            return self._build_fallback_result(rule_issues, material_types, missing_materials, "AGENT_FAILURE"), True

        merged = review_result.model_copy(deep=True)
        merged.issues = _dedupe_issues(rule_issues + list(review_result.issues))
        merged.basis_refs = _dedupe(
            list(review_result.basis_refs)
            + [ref for issue in rule_issues for ref in issue.basis_refs]
        )
        if not merged.manual_review_notice:
            merged.manual_review_notice = "AI审核结果为辅助建议，不构成最终审批意见。"
        return merged, False

    def _build_rag_fragments(
        self,
        material_types: list[str],
        extracted_fields: list[ExtractedField],
    ) -> list[dict[str, str]]:
        if not self._knowledge_tools:
            return list(self._knowledge_fragments)

        query_parts = list(material_types)
        query_parts.extend(field.field_key for field in extracted_fields[:8])
        query = " ".join(query_parts).strip() or "取水许可 材料审核 规则"
        search_result = self._knowledge_tools.knowledge_search(query, top_k=8)

        fragments: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in search_result.get("results", []):
            if not isinstance(item, dict):
                continue
            source_id = str(item.get("id") or "").strip()
            if not source_id or source_id in seen:
                continue
            title = str(item.get("title") or source_id).strip()
            content = str(item.get("excerpt") or "").strip()
            if not content:
                continue
            fragments.append({"source_id": source_id, "source_title": title, "content": content})
            seen.add(source_id)

        for base in self._knowledge_fragments:
            source_id = str(base.get("source_id") or "").strip()
            if not source_id or source_id in seen:
                continue
            if not source_id.startswith("PROMPT_"):
                continue
            title = str(base.get("source_title") or source_id).strip()
            content = str(base.get("content") or "").strip()
            if not content:
                continue
            fragments.append({"source_id": source_id, "source_title": title, "content": content})
            seen.add(source_id)

        return fragments or list(self._knowledge_fragments)

    def _build_fallback_result(
        self,
        rule_issues: list[Issue],
        material_types: list[str],
        missing_materials: list[str],
        reason: str,
    ) -> ReviewResult:
        issues = _dedupe_issues(
            rule_issues
            + [
                Issue(
                    code="MODEL_UNCERTAIN",
                    severity="WARNING",
                    message=f"Agent汇总失败({reason})，已降级为规则检查结论。",
                    applicant_visible=False,
                )
            ]
        )
        basis_refs = _dedupe([ref for issue in issues for ref in issue.basis_refs])
        return ReviewResult(
            summary="规则检查完成，Agent汇总不可用，已降级为规则结果",
            issues=issues,
            risk_hints=[
                RiskHint(
                    risk_level="HIGH",
                    description="Agent汇总失败，当前结果仅供辅助参考，需人工复核全部结论。",
                    requires_manual_review=True,
                )
            ],
            draft_opinion="建议人工复核后再形成审批意见。",
            material_completeness=MaterialCompleteness(
                received=_dedupe(material_types),
                missing=_dedupe(missing_materials),
                unrecognized=[],
            ),
            basis_refs=basis_refs,
            manual_review_notice="AI审核服务不可用或输出异常，已回退为规则检查结果，请人工复核。",
        )

    def _merge_material_completeness(
        self,
        existing: MaterialCompleteness,
        received: list[str],
        missing: list[str],
        unrecognized: list[str],
    ) -> MaterialCompleteness:
        merged = existing.model_copy(deep=True)
        merged.received = _dedupe(list(existing.received) + list(received))
        merged.missing = _dedupe(list(existing.missing) + list(missing))
        merged.unrecognized = _dedupe(list(existing.unrecognized) + list(unrecognized))
        return merged
