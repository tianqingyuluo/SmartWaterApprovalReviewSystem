import unittest
from unittest.mock import patch

from fastapi import BackgroundTasks, HTTPException

from src.api.app import (
    _check_internal_token,
    create_review_task,
    get_review_task_status,
    health,
    runtime,
)
from src.api.models import CreateReviewTaskRequest
from src.config import config


class FastapiAppTests(unittest.TestCase):
    def setUp(self) -> None:
        runtime.store = runtime.store.__class__()
        runtime.knowledge_pack_version = None
        runtime._knowledge_fragments = []
        runtime._knowledge_loaded = False
        config.INTERNAL_API_TOKEN = ""

    @patch("src.api.app.runtime.ensure_knowledge_loaded")
    def test_health_returns_ok(self, _ensure) -> None:
        runtime.knowledge_pack_version = "water-permit-mvp-2026-04-27"
        payload = health()
        self.assertEqual("ok", payload.status)
        self.assertEqual("water-permit-mvp-2026-04-27", payload.knowledge_pack_version)

    @patch("src.api.app.runtime.process_task")
    def test_create_task_accepts_and_queues_background_processing(self, _process_task) -> None:
        req = CreateReviewTaskRequest(
            taskId="java-task-1",
            sessionId="session-1",
            materials=[
                {
                    "materialType": "APPLICATION_FORM",
                    "originalFileName": "app.pdf",
                    "storageKey": "k1",
                    "fileExtension": "pdf",
                    "uploaded": True,
                }
            ],
        )
        background_tasks = BackgroundTasks()

        resp = create_review_task(req, background_tasks, _auth=None)

        self.assertEqual("java-task-1", resp.ai_task_id)
        self.assertEqual("QUEUED", resp.status)
        self.assertEqual(1, len(background_tasks.tasks))
        task = background_tasks.tasks[0]
        self.assertIs(task.func, _process_task)
        self.assertEqual("java-task-1", task.args[0]["taskId"])

        status_resp = get_review_task_status("java-task-1", _auth=None)
        self.assertEqual("java-task-1", status_resp.ai_task_id)

    def test_task_api_rejects_invalid_internal_token(self) -> None:
        config.INTERNAL_API_TOKEN = "expected-token"
        with self.assertRaises(HTTPException) as exc:
            _check_internal_token("wrong-token")
        self.assertEqual(403, exc.exception.status_code)

    def test_task_api_allows_valid_internal_token(self) -> None:
        config.INTERNAL_API_TOKEN = "expected-token"
        _check_internal_token("expected-token")
        req = CreateReviewTaskRequest(taskId="java-task-3", sessionId="session-3", materials=[])
        with patch("src.api.app.runtime.process_task"):
            resp = create_review_task(req, BackgroundTasks(), _auth=None)
        self.assertEqual("java-task-3", resp.ai_task_id)

    def test_status_contract_enforces_internal_token_and_returns_camel_case_aliases(self) -> None:
        config.INTERNAL_API_TOKEN = "expected-token"
        runtime.store.create("java-task-http-1", {"taskId": "java-task-http-1", "sessionId": "session-http-1"})

        with self.assertRaises(HTTPException) as exc:
            _check_internal_token("wrong-token")
        self.assertEqual(403, exc.exception.status_code)

        _check_internal_token("expected-token")
        status_resp = get_review_task_status("java-task-http-1", _auth=None)
        payload = status_resp.model_dump(by_alias=True)
        self.assertEqual("java-task-http-1", payload["aiTaskId"])
        self.assertEqual("QUEUED", payload["status"])
        self.assertIn("createdAt", payload)
        self.assertIn("updatedAt", payload)

    def test_http_status_contract_returns_404_for_unknown_task(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            get_review_task_status("missing-task", _auth=None)
        self.assertEqual(404, exc.exception.status_code)


if __name__ == "__main__":
    unittest.main()
