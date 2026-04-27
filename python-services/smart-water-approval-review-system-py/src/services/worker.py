import logging
import time
import signal
import sys
from typing import Optional
from src.config import config
from src.models import (
    MaterialSlot,
    ExtractedField,
    ReviewResult,
    ProcessingResult,
    Issue,
    RiskHint,
    MaterialCompleteness,
)
from src.services.field_extractor import FieldExtractor
from src.services.result_writer import ResultWriter
from src.adapters.review_adapter import ReviewReasoningAdapter

logger = logging.getLogger(__name__)


class SmartWaterWorker:
    def __init__(self):
        self.extractor = FieldExtractor()
        self.reviewer = ReviewReasoningAdapter()
        self.writer = ResultWriter()
        self._running = False
        self._knowledge_cache: list = []

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
                        task_id = str(task_data.get("task_id", ""))
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
        task_id = str(task_data.get("task_id", ""))

        materials = [
            MaterialSlot(
                material_type=m.get("material_type", ""),
                original_file_name=m.get("original_file_name"),
                storage_key=m.get("storage_key"),
                file_extension=m.get("file_extension"),
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

            has_error = any(
                f.field_key in ("ocr_error", "extraction_error", "download_error")
                for f in fields
            )
            if has_error:
                partial_failures.append(material.material_type)

        review_result: ReviewResult | None = None
        review_error: str | None = None

        if extracted_fields:
            try:
                review_result = self.reviewer.review(
                    task_id=task_id,
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

        processing_result = self._build_processing_result(
            task_id, review_result, partial_failures, missing
        )

        self.writer.write_results(task_id, processing_result)

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
            f"{review_result.summary} (已处理材料{3 - len(missing_materials)}/3, "
            f"部分失败: {len(partial_failures)})"
        ) if partial_failures else review_result.summary

        applicant_result = ReviewResult(
            summary=review_result.summary,
            issues=[
                i for i in review_result.issues if i.applicant_visible
            ],
            material_completeness=review_result.material_completeness,
            manual_review_notice=review_result.manual_review_notice,
        )

        return ProcessingResult(
            task_id=task_id,
            status=status,
            result_summary=result_summary,
            applicant_result=applicant_result,
            reviewer_result=review_result,
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
            import os
            import json

            pack_dir = config.KNOWLEDGE_PACK_DIR
            if not os.path.isdir(pack_dir):
                logger.warning("Knowledge pack directory not found: %s", pack_dir)
                return

            for fname in os.listdir(pack_dir):
                if fname.endswith(".json"):
                    path = os.path.join(pack_dir, fname)
                    with open(path, encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self._knowledge_cache.extend(data)
                        else:
                            self._knowledge_cache.append(data)

            logger.info("Loaded %d knowledge fragments", len(self._knowledge_cache))
        except Exception as e:
            logger.warning("Failed to load knowledge pack: %s", e)
