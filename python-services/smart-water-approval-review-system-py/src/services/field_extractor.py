import logging

import httpx

from src.adapters.ocr_adapter import GlmOcrAdapter
from src.config import config
from src.models import ExtractedField, MaterialSlot
from src.services.document_ocr_pipeline import DocumentOcrPipeline, MaterialDocumentParseResult

logger = logging.getLogger(__name__)


class FieldExtractor:
    def __init__(self) -> None:
        self.ocr: GlmOcrAdapter = GlmOcrAdapter()
        self._document_pipeline = DocumentOcrPipeline(ocr_adapter=self.ocr)
        self._headers: dict[str, str] = {}
        token = getattr(config, "WORKER_TOKEN", None)
        if token:
            self._headers["X-Worker-Token"] = token

    def extract(self, material: MaterialSlot) -> list[ExtractedField]:
        if not material.storage_key:
            logger.warning("No storage key for material type %s", material.material_type)
            return []

        try:
            file_bytes = self._download_material(material.storage_key)
            if not file_bytes:
                return self._download_error_result(material.material_type)

            name = material.original_file_name or f"unknown.{material.file_extension or 'pdf'}"
            parse_result = self._document_pipeline.parse_material(
                material_type=material.material_type,
                source_file_name=name,
                file_bytes=file_bytes,
            )
            fields = self._parse_result_to_fields(parse_result)

            for f in fields:
                f.source_material = material.material_type
                if not f.evidence:
                    f.evidence = f"Extracted from {name}"

            return fields

        except Exception as e:
            logger.error("Field extraction failed for %s: %s", material.material_type, e)
            return [
                ExtractedField(
                    field_key="extraction_error",
                    field_value=str(e),
                    confidence=0.0,
                    source_material=material.material_type,
                )
            ]

    def _download_material(self, storage_key: str) -> bytes | None:
        url = f"{config.BACKEND_API_BASE}/material/download?key={storage_key}"
        try:
            with httpx.Client(timeout=60) as client:
                resp = client.get(url, headers=self._headers)
                resp.raise_for_status()
                return resp.content
        except Exception as e:
            logger.error("Failed to download material %s: %s", storage_key, e)
            return None

    def _download_error_result(self, material_type: str) -> list[ExtractedField]:
        return [
            ExtractedField(
                field_key="download_error",
                field_value="Failed to download material file",
                confidence=0.0,
                source_material=material_type,
            )
        ]

    def _parse_result_to_fields(self, result: MaterialDocumentParseResult) -> list[ExtractedField]:
        fields = list(result.extracted_fields)

        for index, block in enumerate(result.content_blocks, start=1):
            text = block.text.strip()
            if not text:
                continue
            fields.append(
                ExtractedField(
                    field_key=f"content_block_{index}",
                    field_value=text,
                    confidence=1.0,
                    source_material=result.material_type,
                    evidence=f"Parsed from {result.source_file_name}",
                )
            )

        for error in result.errors:
            field_key = "ocr_error" if error.code.startswith("OCR") else "extraction_error"
            if any(field.field_key == field_key for field in fields):
                continue
            fields.append(
                ExtractedField(
                    field_key=field_key,
                    field_value=f"{error.code}: {error.message}",
                    confidence=0.0,
                    source_material=result.material_type,
                    evidence=f"Failed to parse {result.source_file_name}",
                )
            )

        return fields
