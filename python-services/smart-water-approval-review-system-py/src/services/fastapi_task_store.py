from __future__ import annotations

import threading
from datetime import UTC, datetime
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(UTC)


class InMemoryTaskStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tasks: dict[str, dict[str, Any]] = {}

    def create(self, task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        now = _utc_now()
        record = {
            "aiTaskId": task_id,
            "status": "QUEUED",
            "createdAt": now,
            "updatedAt": now,
            "payload": payload,
            "result": None,
            "errorMessage": None,
        }
        with self._lock:
            self._tasks[task_id] = record
        return self._public(record)

    def mark_processing(self, task_id: str) -> None:
        with self._lock:
            record = self._tasks.get(task_id)
            if not record:
                return
            record["status"] = "PROCESSING"
            record["updatedAt"] = _utc_now()

    def mark_result(self, task_id: str, result: dict[str, Any]) -> None:
        with self._lock:
            record = self._tasks.get(task_id)
            if not record:
                return
            record["status"] = str(result.get("status") or "FAILED")
            record["result"] = result
            record["updatedAt"] = _utc_now()

    def mark_failed(self, task_id: str, error_message: str) -> None:
        with self._lock:
            record = self._tasks.get(task_id)
            if not record:
                return
            record["status"] = "FAILED"
            record["errorMessage"] = error_message
            record["updatedAt"] = _utc_now()

    def get(self, task_id: str) -> dict[str, Any] | None:
        with self._lock:
            record = self._tasks.get(task_id)
            return self._public(record) if record else None

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = [self._public(row) for row in self._tasks.values()]
        rows.sort(key=lambda row: row["createdAt"], reverse=True)
        return rows

    def _public(self, record: dict[str, Any]) -> dict[str, Any]:
        return {
            "aiTaskId": record["aiTaskId"],
            "status": record["status"],
            "createdAt": record["createdAt"],
            "updatedAt": record["updatedAt"],
            "result": record["result"],
            "errorMessage": record["errorMessage"],
        }
