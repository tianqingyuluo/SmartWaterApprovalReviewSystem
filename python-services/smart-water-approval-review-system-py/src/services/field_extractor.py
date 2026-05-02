import logging
import io
import httpx
from src.config import config
from src.adapters.ocr_adapter import GlmOcrAdapter
from src.models import ExtractedField, MaterialSlot

logger = logging.getLogger(__name__)


class FieldExtractor:
    def __init__(self):
        self.ocr = GlmOcrAdapter()
        self._headers = {}
        token = getattr(config, "WORKER_TOKEN", None) or getattr(config, "BACKEND_WORKER_TOKEN", None)
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
            fields = self.ocr.extract_fields(
                file_bytes, material.material_type, name
            )

            for f in fields:
                f.source_material = material.material_type
                f.evidence = f"OCR extracted from {material.material_type}"

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
