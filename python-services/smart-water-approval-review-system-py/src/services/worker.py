import logging
import os
import signal
import time

from knowledge_pack import KnowledgePackError, load_knowledge_pack, normalize_knowledge_fragments
from src.config import config
from src.models import ExtractedField, Issue, MaterialCompleteness, ProcessingResult, ReviewResult
from src.services.mcp_client import SmartWaterMcpClient
from src.services.result_writer import ResultWriter
from src.services.review_orchestrator import ReviewTaskOrchestrator

logger = logging.getLogger(__name__)


class SmartWaterWorker:
    def __init__(self):
        self.writer = ResultWriter()
        self._orchestrator: ReviewTaskOrchestrator | None = None
        self._running = False
        self._knowledge_cache: list = []
        self._knowledge_pack_version: str | None = None

    def start(self):
        logger.info("SmartWater Worker starting...")
        self._load_knowledge_pack()
        self._running = True

        signal.signal(signal.SIGINT, lambda *_: self.stop())
        signal.signal(signal.SIGTERM, lambda *_: self.stop())

        while self._running:
            try:
                tasks = self.writer.fetch_pending_tasks()
                if not tasks:
                    time.sleep(config.WORKER_POLL_INTERVAL)
                    continue

                for task_data in tasks:
                    if not self._running:
                        break
                    try:
                        task_id = str(task_data.get("taskId", ""))
                        logger.info("Processing task: %s", task_id)
                        self._process_task(task_data)
                    except Exception as e:
                        logger.error("Unhandled error processing task: %s", e)

            except Exception as e:
                logger.error("Worker loop error: %s", e)
                time.sleep(config.WORKER_POLL_INTERVAL)

        logger.info("SmartWater Worker stopped.")

    def stop(self):
        self._running = False

    def _process_task(self, task_data: dict):
        task_id = str(task_data.get("taskId", ""))
        self.writer.update_status(task_id, "PROCESSING")

        try:
            if not self._orchestrator:
                self._orchestrator = ReviewTaskOrchestrator(
                    mcp_client=SmartWaterMcpClient(),
                    knowledge_fragments=self._knowledge_cache,
                    knowledge_pack_version=self._knowledge_pack_version,
                )
            processing_result = self._orchestrator.process_task(task_data)
        except Exception as exc:
            logger.error("Task processing failed for %s: %s", task_id, exc)
            self.writer.update_status(task_id, "FAILED")
            return

        success = self.writer.write_results(task_id, processing_result)
        if not success:
            logger.error("Failed to write results for task %s, marking as FAILED", task_id)
            self.writer.update_status(task_id, "FAILED")

    # Kept for backward-compatible unit tests that verify reviewer/applicant projection semantics.
    def _build_processing_result(
        self,
        task_id: str,
        review_result: ReviewResult,
        partial_failures: list[str],
        missing_materials: list[str],
        extracted_fields: list[ExtractedField] | None = None,
    ) -> ProcessingResult:
        status = "PARTIAL_SUCCESS" if partial_failures or missing_materials else "COMPLETED"
        result_summary = (
            f"{review_result.summary} (已处理材料{3 - len(missing_materials)}/3, 部分失败: {len(partial_failures)})"
            if partial_failures
            else review_result.summary
        )
        applicant_result = ReviewResult(
            summary=review_result.summary,
            issues=[issue for issue in review_result.issues if issue.applicant_visible],
            material_completeness=review_result.material_completeness,
            manual_review_notice=review_result.manual_review_notice,
        )
        reviewer_result = review_result.model_copy(deep=True)
        reviewer_result.extracted_fields = extracted_fields or []
        return ProcessingResult(
            task_id=task_id,
            status=status,
            result_summary=result_summary,
            applicant_result=applicant_result,
            reviewer_result=reviewer_result,
            knowledge_pack_version=self._knowledge_pack_version,
        )

    def _no_fields_result(self, missing: list[str]) -> ReviewResult:
        issues = [
            Issue(
                code="MISSING_MATERIAL",
                severity="WARNING",
                message=f"缺失材料: {material_type}",
                material_type=material_type,
                applicant_visible=True,
            )
            for material_type in missing
        ]
        return ReviewResult(
            summary="无材料可处理，所有材料均为缺失状态",
            issues=issues,
            material_completeness=MaterialCompleteness(missing=missing),
            manual_review_notice="请补充缺失材料后重新提交。",
        )

    def _load_knowledge_pack(self):
        try:
            pack_dir = config.KNOWLEDGE_PACK_DIR
            if not os.path.isdir(pack_dir):
                logger.warning("Knowledge pack directory not found: %s", pack_dir)
                return

            preferred_pack = os.path.join(pack_dir, "water_permit_mvp.json")
            if os.path.isfile(preferred_pack):
                pack = load_knowledge_pack(preferred_pack)
                self._knowledge_pack_version = str(pack.get("version") or "")
                self._knowledge_cache = normalize_knowledge_fragments(pack)
                logger.info(
                    "Loaded knowledge pack version=%s fragments=%d",
                    self._knowledge_pack_version,
                    len(self._knowledge_cache),
                )
                return

            for fname in os.listdir(pack_dir):
                if fname.endswith(".json"):
                    path = os.path.join(pack_dir, fname)
                    pack = load_knowledge_pack(path)
                    self._knowledge_pack_version = str(pack.get("version") or "")
                    self._knowledge_cache.extend(normalize_knowledge_fragments(pack))

            logger.info("Loaded %d knowledge fragments", len(self._knowledge_cache))
        except (KnowledgePackError, OSError) as e:
            logger.warning("Failed to load knowledge pack: %s", e)
