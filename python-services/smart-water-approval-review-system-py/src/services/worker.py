import logging
import os
import signal
import time

from knowledge_pack import KnowledgePackError, load_knowledge_pack, normalize_knowledge_fragments
from src.adapters.review_adapter import ReviewReasoningAdapter
from src.config import config
from src.models import (
    ExtractedField,
    Issue,
    MaterialCompleteness,
    MaterialSlot,
    ProcessingResult,
    ReviewResult,
)
from src.services.field_extractor import FieldExtractor
from src.services.result_writer import ResultWriter

logger = logging.getLogger(__name__)


class SmartWaterWorker:
    def __init__(self):
        self.extractor = FieldExtractor()
        self.reviewer = ReviewReasoningAdapter()
        self.writer = ResultWriter()
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

        materials = [
            MaterialSlot(
                material_type=m.get("materialType", ""),
                original_file_name=m.get("originalFileName"),
                storage_key=m.get("storageKey"),
                file_extension=m.get("fileExtension"),
                uploaded=m.get("uploaded", False),
            )
            for m in task_data.get("materials", [])
        ]

        uploaded = [m for m in materials if m.uploaded]
        material_types = [m.material_type for m in uploaded]
        missing = [m.material_type for m in materials if not m.uploaded]

        self.writer.update_status(task_id, "PROCESSING")

        extracted_fields: list[ExtractedField] = []
        partial_failures: list[str] = []

        for material in uploaded:
            fields = self.extractor.extract(material)
            extracted_fields.extend(fields)

            has_error = any(f.field_key in ("ocr_error", "extraction_error", "download_error") for f in fields)
            if has_error:
                partial_failures.append(material.material_type)

        review_result: ReviewResult | None = None
        review_error: str | None = None

        if extracted_fields:
            try:
                review_result = self.reviewer.review(
                    task_id=task_id,
                    session_id=str(task_data.get("sessionId", "")),
                    extracted_fields=extracted_fields,
                    material_types=material_types,
                    missing_materials=missing,
                    knowledge_fragments=self._knowledge_cache,
                )
            except Exception as e:
                logger.error("Review failed for task %s: %s", task_id, e)
                review_error = str(e)
        else:
            review_result = self._no_fields_result(missing)

        if not review_result:
            review_result = ReviewResult(
                summary="审核推理失败",
                issues=[
                    Issue(
                        code="SYSTEM_ERROR",
                        severity="BLOCKER",
                        message=f"审核推理调用失败: {review_error}",
                        applicant_visible=False,
                    )
                ],
                manual_review_notice="AI审核服务暂时不可用，请稍后重试或人工审核。",
            )

        processing_result = self._build_processing_result(task_id, review_result, partial_failures, missing)

        success = self.writer.write_results(task_id, processing_result)
        if not success:
            logger.error("Failed to write results for task %s, marking as FAILED", task_id)
            self.writer.update_status(task_id, "FAILED")

    def _build_processing_result(
        self,
        task_id: str,
        review_result: ReviewResult,
        partial_failures: list[str],
        missing_materials: list[str],
    ) -> ProcessingResult:
        if partial_failures or missing_materials:
            status = "PARTIAL_SUCCESS"
        else:
            status = "COMPLETED"

        result_summary = (
            (f"{review_result.summary} (已处理材料{3 - len(missing_materials)}/3, 部分失败: {len(partial_failures)})")
            if partial_failures
            else review_result.summary
        )

        applicant_result = ReviewResult(
            summary=review_result.summary,
            issues=[i for i in review_result.issues if i.applicant_visible],
            material_completeness=review_result.material_completeness,
            manual_review_notice=review_result.manual_review_notice,
        )

        return ProcessingResult(
            task_id=task_id,
            status=status,
            result_summary=result_summary,
            applicant_result=applicant_result,
            reviewer_result=review_result,
            knowledge_pack_version=self._knowledge_pack_version,
        )

    def _no_fields_result(self, missing: list[str]) -> ReviewResult:
        issues = [
            Issue(
                code="MISSING_MATERIAL",
                severity="WARNING",
                message=f"缺失材料: {m}",
                material_type=m,
                applicant_visible=True,
            )
            for m in missing
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
