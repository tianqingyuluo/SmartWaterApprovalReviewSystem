import json
import logging
import httpx
from src.config import config
from src.models import ProcessingResult, ReviewResult

logger = logging.getLogger(__name__)


class ResultWriter:
    def write_results(self, task_id: str, result: ProcessingResult) -> bool:
        url = f"{config.BACKEND_API_BASE}/task/{task_id}/result"
            payload = {
                "status": result.status,
                "resultSummary": result.result_summary,
                "applicantResult": _result_to_dict(result.applicant_result),
                "reviewerResult": _result_to_dict(result.reviewer_result),
                "errorMessage": result.error_message,
            }

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.put(url, json=payload)
                resp.raise_for_status()
                logger.info("Result written for task %s, status=%s", task_id, result.status)
                return True
        except Exception as e:
            logger.error("Failed to write result for task %s: %s", task_id, e)
            return False

    def update_status(self, task_id: str, status: str) -> bool:
        url = f"{config.BACKEND_API_BASE}/task/{task_id}/status"
        payload = {"status": status}

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.put(url, json=payload)
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error("Failed to update status for task %s: %s", task_id, e)
            return False

    def fetch_pending_tasks(self) -> list[dict]:
        url = f"{config.BACKEND_API_BASE}/task/pending"
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(url)
                resp.raise_for_status()
                data = resp.json()
                return data.get("data", []) if isinstance(data, dict) else []
        except Exception as e:
            logger.error("Failed to fetch pending tasks: %s", e)
            return []


def _result_to_dict(result: ReviewResult | None) -> dict | None:
    if result is None:
        return None
    return json.loads(result.model_dump_json())
