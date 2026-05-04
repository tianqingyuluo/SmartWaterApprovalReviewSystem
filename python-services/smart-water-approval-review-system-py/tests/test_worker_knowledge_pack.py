import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models import MaterialCompleteness, ReviewResult
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
        )

        self.assertEqual("water-permit-mvp-2026-04-27", result.knowledge_pack_version)

    @patch("src.services.worker.config.KNOWLEDGE_PACK_DIR", "/path/not-found")
    def test_missing_knowledge_pack_dir_leaves_empty_cache(self) -> None:
        worker = SmartWaterWorker()

        worker._load_knowledge_pack()

        self.assertIsNone(worker._knowledge_pack_version)
        self.assertEqual([], worker._knowledge_cache)


if __name__ == "__main__":
    unittest.main()
