import logging
import time

import httpx

from src.config import config
from src.models import ProcessingResult, ReviewResult

logger = logging.getLogger(__name__)


def _result_to_dict(result: ReviewResult | None) -> dict | None:
    if result is None:
        return None

    d: dict = {}
    if result.summary:
        d["summary"] = result.summary
    if result.issues:
        d["issues"] = [
            {
                "code": i.code,
                "severity": i.severity,
                "message": i.message,
                "materialType": i.material_type,
                "fieldKey": i.field_key,
                "basisRefs": i.basis_refs,
                "applicantVisible": i.applicant_visible,
            }
            for i in result.issues
        ]
    if result.risk_hints:
        d["riskHints"] = [
            {
                "riskLevel": r.risk_level,
                "description": r.description,
                "basisRefs": r.basis_refs,
                "requiresManualReview": r.requires_manual_review,
            }
            for r in result.risk_hints
        ]
    if result.draft_opinion:
        d["draftOpinion"] = result.draft_opinion
    if result.material_completeness:
        d["materialCompleteness"] = {
            "received": result.material_completeness.received,
            "missing": result.material_completeness.missing,
            "unrecognized": result.material_completeness.unrecognized,
        }
    if result.extracted_fields:
        d["extractedFields"] = [
            {
                "fieldKey": field.field_key,
                "fieldValue": field.field_value,
                "confidence": field.confidence,
                "sourceMaterial": field.source_material,
                "evidence": field.evidence,
            }
            for field in result.extracted_fields
        ]
    if result.basis_refs:
        d["basisRefs"] = result.basis_refs
    if result.manual_review_notice:
        d["manualReviewNotice"] = result.manual_review_notice
    if result.model_metadata:
        d["modelMetadata"] = {
            "provider": result.model_metadata.provider,
            "model": result.model_metadata.model,
            "requestId": result.model_metadata.request_id,
            "finishReason": result.model_metadata.finish_reason,
            "tokenUsage": result.model_metadata.token_usage,
        }
    if result.tool_call_traces:
        d["toolCallTraces"] = [
            {
                "toolName": trace.tool_name,
                "inputSummary": trace.input_summary,
                "outputSummary": trace.output_summary,
                "sourceRefs": trace.source_refs,
                "status": trace.status,
                "latencyMs": trace.latency_ms,
                "error": trace.error,
            }
            for trace in result.tool_call_traces
        ]
    return d


def _parse_backend_response(resp: httpx.Response) -> dict:
    resp.raise_for_status()

    try:
        payload = resp.json()
    except ValueError as exc:
        raise RuntimeError("Backend returned non-JSON response") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("Backend returned unexpected response shape")

    code = payload.get("code")
    message = payload.get("message", "Unknown backend error")
    if code != 200:
        raise RuntimeError(f"Backend business error code={code}: {message}")

    return payload


class ResultWriter:
    def __init__(self):
        self._headers = {}
        token = getattr(config, "WORKER_TOKEN", None)
        if token:
            self._headers["X-Worker-Token"] = token

    def write_results(self, task_id: str, result: ProcessingResult, retries: int = 3) -> bool:
        url = f"{config.BACKEND_API_BASE}/task/{task_id}/result"
        payload = {
            "status": result.status,
            "resultSummary": result.result_summary,
            "applicantResult": _result_to_dict(result.applicant_result),
            "reviewerResult": _result_to_dict(result.reviewer_result),
            "errorMessage": result.error_message,
            "knowledgePackVersion": result.knowledge_pack_version,
        }

        last_error = None
        for attempt in range(retries):
            try:
                with httpx.Client(timeout=30) as client:
                    resp = client.put(url, json=payload, headers=self._headers)
                    _parse_backend_response(resp)
                    logger.info("Result written for task %s, status=%s", task_id, result.status)
                    return True
            except Exception as e:
                last_error = e
                logger.error("Failed to write result for task %s (attempt %d/%d): %s", task_id, attempt + 1, retries, e)
                if attempt < retries - 1:
                    time.sleep(2**attempt)

        logger.error("Giving up writing result for task %s after %d retries: %s", task_id, retries, last_error)
        return False

    def update_status(self, task_id: str, status: str, retries: int = 3) -> bool:
        url = f"{config.BACKEND_API_BASE}/task/{task_id}/status"
        payload = {"status": status}
        last_error = None

        for attempt in range(retries):
            try:
                with httpx.Client(timeout=30) as client:
                    resp = client.put(url, json=payload, headers=self._headers)
                    _parse_backend_response(resp)
                    return True
            except Exception as e:
                last_error = e
                logger.error(
                    "Failed to update status for task %s (attempt %d/%d): %s", task_id, attempt + 1, retries, e
                )
                if attempt < retries - 1:
                    time.sleep(2**attempt)

        logger.error(
            "Giving up updating status for task %s after %d retries: %s",
            task_id,
            retries,
            last_error,
        )
        return False

    def fetch_pending_tasks(self) -> list[dict]:
        url = f"{config.BACKEND_API_BASE}/task/pending"
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(url, headers=self._headers)
                data = _parse_backend_response(resp)
                result = data.get("data", [])
                return result if isinstance(result, list) else []
        except Exception as e:
            logger.error("Failed to fetch pending tasks: %s", e)
            return []
