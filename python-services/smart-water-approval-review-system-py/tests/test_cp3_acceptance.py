import unittest
from unittest.mock import patch

from src.api.app import get_review_task_status, runtime
from src.models import ExtractedField, Issue, ProcessingResult, ReviewResult
from src.services.review_orchestrator import ReviewTaskOrchestrator


class _DeterministicExtractor:
    def extract(self, material):
        return [
            ExtractedField(
                field_key="applicant.name",
                field_value="某某科技有限公司",
                confidence=0.91,
                source_material=material.material_type,
                evidence="申请人：某某科技有限公司",
            )
        ]


class _VariableNarrativeReviewer:
    def __init__(self):
        self._count = 0

    def review(self, *args, **kwargs):
        self._count += 1
        return ReviewResult(
            summary=f"第{self._count}次运行文本说明（允许差异）",
            issues=[
                Issue(
                    code="INCONSISTENT_IDENTITY",
                    severity="BLOCKER",
                    message="申请人名称与证照信息需要人工核对。",
                    material_type="APPLICATION_FORM",
                    field_key="applicant.name",
                    applicant_visible=False,
                )
            ],
            draft_opinion="建议人工复核后再形成正式结论。",
            manual_review_notice="AI初审仅供辅助，请人工复核。",
        )


class _McpClient:
    def list_tools_sync(self):
        return [{"name": "knowledge_search"}, {"name": "check_completeness"}]

    def check_completeness_sync(self, materials):
        return {
            "submitted": materials,
            "required": ["APPLICATION_FORM", "BUSINESS_LICENSE", "ID_CARD"],
            "missing": ["ID_CARD"],
            "unrecognized": [],
            "findings": [
                {
                    "code": "MISSING_MATERIAL",
                    "severity": "WARNING",
                    "materialType": "ID_CARD",
                    "message": "缺少身份证材料。",
                    "basisRefs": ["BASIS_MATERIAL_INITIAL_LIST"],
                }
            ],
        }

    def knowledge_search_sync(self, query, top_k=8):
        return {
            "results": [
                {
                    "id": "BASIS_MATERIAL_INITIAL_LIST",
                    "title": "材料清单要求",
                    "excerpt": "申请材料需包含申请书、营业执照和身份证。",
                }
            ]
        }

    def consume_traces(self):
        return []


class CP3AcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        runtime.store = runtime.store.__class__()
        runtime.knowledge_pack_version = None
        runtime._knowledge_fragments = []
        runtime._knowledge_loaded = False

    @staticmethod
    def _task_payload(task_id: str) -> dict:
        return {
            "taskId": task_id,
            "sessionId": "session-cp3-acceptance",
            "materials": [
                {
                    "materialType": "APPLICATION_FORM",
                    "originalFileName": "application.pdf",
                    "storageKey": "k1",
                    "fileExtension": "pdf",
                    "uploaded": True,
                },
                {
                    "materialType": "BUSINESS_LICENSE",
                    "originalFileName": "license.jpg",
                    "storageKey": "k2",
                    "fileExtension": "jpg",
                    "uploaded": True,
                },
                {
                    "materialType": "ID_CARD",
                    "originalFileName": None,
                    "storageKey": None,
                    "fileExtension": None,
                    "uploaded": False,
                },
            ],
        }

    @staticmethod
    def _stable_signature(result: ProcessingResult) -> tuple:
        issues = result.reviewer_result.issues if result.reviewer_result else []
        return tuple(
            sorted(
                (
                    issue.code,
                    issue.severity,
                    issue.material_type or "",
                    issue.field_key or "",
                )
                for issue in issues
            )
        )

    def test_repeated_runs_keep_structured_fields_stable(self):
        orchestrator = ReviewTaskOrchestrator(
            extractor=_DeterministicExtractor(),
            reviewer=_VariableNarrativeReviewer(),
            mcp_client=_McpClient(),
            knowledge_fragments=[],
            knowledge_pack_version="water-permit-mvp-2026-04-27",
        )

        payload = self._task_payload("task-cp3-stability")
        results = [orchestrator.process_task(payload) for _ in range(3)]

        statuses = {result.status for result in results}
        self.assertEqual({"PARTIAL_SUCCESS"}, statuses)

        stable_signatures = {self._stable_signature(result) for result in results}
        self.assertEqual(1, len(stable_signatures))

        signature = stable_signatures.pop()
        self.assertIn(("MISSING_MATERIAL", "WARNING", "ID_CARD", ""), signature)
        self.assertIn(("INCONSISTENT_IDENTITY", "BLOCKER", "APPLICATION_FORM", "applicant.name"), signature)

    def test_callback_failure_records_failed_status_for_query_fallback(self):
        task_id = "task-cp3-callback-fail"
        payload = self._task_payload(task_id)
        runtime.store.create(task_id, payload)

        fake_result = ProcessingResult(
            task_id=task_id,
            status="COMPLETED",
            result_summary="AI初审完成",
            applicant_result=ReviewResult(summary="申请人结果"),
            reviewer_result=ReviewResult(summary="审批结果"),
            knowledge_pack_version="water-permit-mvp-2026-04-27",
        )

        with (
            patch.object(runtime, "ensure_knowledge_loaded"),
            patch("src.api.app.ReviewTaskOrchestrator") as orchestrator_cls,
            patch.object(runtime.writer, "write_results", return_value=False),
            patch.object(runtime.writer, "update_status", return_value=True) as update_status_mock,
        ):
            orchestrator_cls.return_value.process_task.return_value = fake_result
            runtime.process_task(payload)

            update_status_mock.assert_any_call(task_id, "PROCESSING")
            update_status_mock.assert_any_call(task_id, "FAILED")

        status_payload = get_review_task_status(task_id, _auth=None)
        self.assertEqual("FAILED", status_payload.status)
        self.assertEqual("result callback failed after retries", status_payload.error_message)


if __name__ == "__main__":
    unittest.main()
