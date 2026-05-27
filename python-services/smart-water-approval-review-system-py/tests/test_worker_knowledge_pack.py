import unittest
from unittest.mock import patch

from src.models import ExtractedField, MaterialCompleteness, ReviewResult
from src.services.worker import SmartWaterWorker


class WorkerKnowledgePackTests(unittest.TestCase):
    def test_load_knowledge_pack_sets_version_and_normalized_fragments(self) -> None:
        worker = SmartWaterWorker()

        worker._load_knowledge_pack()

        self.assertEqual("water-permit-mvp-2026-04-27", worker._knowledge_pack_version)
        self.assertIn(
            "BASIS_MATERIAL_INITIAL_LIST",
            {fragment["source_id"] for fragment in worker._knowledge_cache},
        )

    def test_processing_result_carries_knowledge_pack_version(self) -> None:
        worker = SmartWaterWorker()
        worker._knowledge_pack_version = "water-permit-mvp-2026-04-27"

        result = worker._build_processing_result(
            task_id="task-1",
            review_result=ReviewResult(
                summary="done",
                material_completeness=MaterialCompleteness(received=["APPLICATION_FORM"]),
            ),
            partial_failures=[],
            missing_materials=[],
            extracted_fields=[],
        )

        self.assertEqual("water-permit-mvp-2026-04-27", result.knowledge_pack_version)

    def test_processing_result_carries_extracted_field_snapshot_to_reviewer_only(self) -> None:
        worker = SmartWaterWorker()
        fields = [
            ExtractedField(
                field_key="applicant.name",
                field_value="某某科技有限公司",
                confidence=0.93,
                source_material="APPLICATION_FORM",
            )
        ]

        result = worker._build_processing_result(
            task_id="task-1",
            review_result=ReviewResult(summary="done"),
            partial_failures=[],
            missing_materials=[],
            extracted_fields=fields,
        )

        self.assertEqual([], result.applicant_result.extracted_fields)
        self.assertEqual(fields, result.reviewer_result.extracted_fields)

    @patch("src.services.worker.config.KNOWLEDGE_PACK_DIR", "/path/not-found")
    def test_missing_knowledge_pack_dir_leaves_empty_cache(self) -> None:
        worker = SmartWaterWorker()

        worker._load_knowledge_pack()

        self.assertIsNone(worker._knowledge_pack_version)
        self.assertEqual([], worker._knowledge_cache)

    def test_process_task_marks_failed_when_orchestrator_fails(self) -> None:
        worker = SmartWaterWorker()
        worker.writer = type(
            "WriterStub",
            (),
            {
                "__init__": lambda self: setattr(self, "statuses", []),
                "update_status": lambda self, task_id, status: self.statuses.append((task_id, status)) or True,
                "write_results": lambda self, task_id, result: True,
            },
        )()
        worker._orchestrator = type(
            "BrokenOrchestrator",
            (),
            {"process_task": lambda self, task_data: (_ for _ in ()).throw(RuntimeError("MCP unavailable"))},
        )()

        worker._process_task({"taskId": "task-mcp-down"})

        self.assertEqual(
            [("task-mcp-down", "PROCESSING"), ("task-mcp-down", "FAILED")],
            worker.writer.statuses,
        )


if __name__ == "__main__":
    unittest.main()
