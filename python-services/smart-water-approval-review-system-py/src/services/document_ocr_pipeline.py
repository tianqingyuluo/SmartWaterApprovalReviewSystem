from __future__ import annotations

import logging
import re
from io import BytesIO
from pathlib import Path
from typing import Any

import fitz  # type: ignore[import-untyped]
from docx import Document
from pydantic import BaseModel, ConfigDict, Field

from src.adapters.ocr_adapter import GlmOcrAdapter
from src.models import ExtractedField

logger = logging.getLogger(__name__)

_SUPPORTED_EXTENSIONS = {"pdf", "docx", "jpg", "jpeg", "png"}
_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
_PDF_MIN_TEXT_LENGTH_BEFORE_OCR = 20
_OCR_ERROR_KEYS = {"ocr_error"}


class DocumentContentBlock(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    text: str
    block_type: str = Field(default="text", alias="blockType")
    page_number: int | None = Field(default=None, alias="pageNumber")
    block_index: int = Field(default=0, alias="blockIndex")


class DocumentTable(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    rows: list[list[str]] = Field(default_factory=list)
    page_number: int | None = Field(default=None, alias="pageNumber")
    table_index: int = Field(default=0, alias="tableIndex")


class OcrMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    used: bool = False
    provider: str | None = None
    field_count: int = Field(default=0, alias="fieldCount")
    source: str | None = None


class DocumentParseError(BaseModel):
    code: str
    message: str
    retryable: bool = False


class MaterialDocumentParseResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    material_type: str = Field(alias="materialType")
    source_file_name: str = Field(alias="sourceFileName")
    content_blocks: list[DocumentContentBlock] = Field(default_factory=list, alias="contentBlocks")
    tables: list[DocumentTable] = Field(default_factory=list)
    extracted_fields: list[ExtractedField] = Field(default_factory=list, alias="extractedFields")
    ocr_metadata: OcrMetadata = Field(default_factory=OcrMetadata, alias="ocrMetadata")
    errors: list[DocumentParseError] = Field(default_factory=list)

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        data = super().model_dump(*args, **kwargs)
        by_alias = bool(kwargs.get("by_alias", False))
        if by_alias:
            data["extractedFields"] = [_extracted_field_to_alias_dict(field) for field in self.extracted_fields]
        return data


class DocumentOcrPipeline:
    def __init__(self, ocr_adapter: GlmOcrAdapter | None = None) -> None:
        self._ocr = ocr_adapter or GlmOcrAdapter()

    def parse_material(
        self,
        *,
        material_type: str,
        source_file_name: str,
        file_bytes: bytes,
    ) -> MaterialDocumentParseResult:
        ext = _extension(source_file_name)
        result = MaterialDocumentParseResult(materialType=material_type, sourceFileName=source_file_name)

        if ext not in _SUPPORTED_EXTENSIONS:
            result.errors.append(
                DocumentParseError(
                    code="UNSUPPORTED_FILE_TYPE",
                    message=f"Unsupported material file type: {ext or '<missing>'}",
                    retryable=False,
                )
            )
            return result

        if not file_bytes:
            result.errors.append(
                DocumentParseError(
                    code="EMPTY_FILE",
                    message="Material file is empty",
                    retryable=False,
                )
            )
            return result

        if ext == "docx":
            return self._parse_docx(result, file_bytes)
        if ext == "pdf":
            return self._parse_pdf(result, file_bytes)
        if ext in _IMAGE_EXTENSIONS:
            return self._apply_ocr(result, file_bytes, material_type, source_file_name, source="image")

        return result

    def process_material(
        self,
        *,
        material_type: str,
        source_file_name: str,
        file_bytes: bytes,
    ) -> MaterialDocumentParseResult:
        return self.parse_material(
            material_type=material_type,
            source_file_name=source_file_name,
            file_bytes=file_bytes,
        )

    def parse(
        self,
        *,
        material_type: str,
        source_file_name: str,
        file_bytes: bytes,
    ) -> MaterialDocumentParseResult:
        return self.parse_material(
            material_type=material_type,
            source_file_name=source_file_name,
            file_bytes=file_bytes,
        )

    def _parse_docx(
        self,
        result: MaterialDocumentParseResult,
        file_bytes: bytes,
    ) -> MaterialDocumentParseResult:
        try:
            doc = Document(BytesIO(file_bytes))
        except Exception as exc:
            logger.warning("Failed to parse DOCX material %s: %s", result.source_file_name, exc)
            result.errors.append(
                DocumentParseError(
                    code="PARSE_ERROR",
                    message=f"Failed to parse DOCX material: {_safe_error(exc)}",
                    retryable=False,
                )
            )
            return result

        block_index = 0
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            result.content_blocks.append(
                DocumentContentBlock(
                    text=text,
                    blockType="paragraph",
                    blockIndex=block_index,
                )
            )
            block_index += 1

        for table_index, table in enumerate(doc.tables):
            rows: list[list[str]] = []
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                if any(cells):
                    rows.append(cells)

            if not rows:
                continue

            result.tables.append(DocumentTable(rows=rows, tableIndex=table_index))
            result.content_blocks.append(
                DocumentContentBlock(
                    text=_table_to_text(rows),
                    blockType="table",
                    blockIndex=block_index,
                )
            )
            block_index += 1
            result.extracted_fields.extend(_extract_key_value_fields(rows, result.material_type))

        if not result.content_blocks and not result.tables and not result.extracted_fields:
            result.errors.append(
                DocumentParseError(
                    code="NO_EXTRACTABLE_CONTENT",
                    message="DOCX material contains no extractable text or tables",
                    retryable=False,
                )
            )

        return result

    def _parse_pdf(
        self,
        result: MaterialDocumentParseResult,
        file_bytes: bytes,
    ) -> MaterialDocumentParseResult:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as exc:
            logger.warning("Failed to parse PDF material %s: %s", result.source_file_name, exc)
            result.errors.append(
                DocumentParseError(
                    code="PARSE_ERROR",
                    message=f"Failed to parse PDF material: {_safe_error(exc)}",
                    retryable=False,
                )
            )
            return result

        try:
            block_index = 0
            total_text = 0
            for page_index in range(len(doc)):
                page = doc[page_index]
                text = page.get_text().strip()
                if not text:
                    continue
                total_text += len(text)
                result.content_blocks.append(
                    DocumentContentBlock(
                        text=text,
                        blockType="pdf_text",
                        pageNumber=page_index + 1,
                        blockIndex=block_index,
                    )
                )
                block_index += 1

            if total_text >= _PDF_MIN_TEXT_LENGTH_BEFORE_OCR:
                return result
        finally:
            doc.close()

        return self._apply_ocr(
            result,
            file_bytes,
            result.material_type,
            result.source_file_name,
            source="scanned_pdf",
        )

    def _apply_ocr(
        self,
        result: MaterialDocumentParseResult,
        file_bytes: bytes,
        material_type: str,
        source_file_name: str,
        *,
        source: str,
    ) -> MaterialDocumentParseResult:
        fields = self._ocr.extract_fields(file_bytes, material_type, source_file_name)
        result.ocr_metadata = OcrMetadata(
            used=True,
            provider="glm-ocr",
            fieldCount=len(fields),
            source=source,
        )

        if any(field.field_key in _OCR_ERROR_KEYS for field in fields):
            for field in fields:
                if field.field_key in _OCR_ERROR_KEYS:
                    result.errors.append(
                        DocumentParseError(
                            code="OCR_ERROR",
                            message=str(field.field_value or "OCR failed"),
                            retryable=True,
                        )
                    )
            result.extracted_fields = fields
            return result

        result.extracted_fields = fields
        text = _fields_to_text(fields)
        if text:
            result.content_blocks.append(
                DocumentContentBlock(
                    text=text,
                    blockType="ocr_text",
                    blockIndex=0,
                )
            )
        else:
            result.errors.append(
                DocumentParseError(
                    code="OCR_EMPTY_RESULT",
                    message="OCR completed but returned no extractable text",
                    retryable=True,
                )
            )

        return result


def _extension(source_file_name: str) -> str:
    suffix = Path(source_file_name or "").suffix.lower().lstrip(".")
    return suffix


def _table_to_text(rows: list[list[str]]) -> str:
    return "\n".join(" | ".join(cell for cell in row if cell) for row in rows).strip()


def _extract_key_value_fields(rows: list[list[str]], material_type: str) -> list[ExtractedField]:
    fields: list[ExtractedField] = []
    for row in rows:
        if len(row) < 2:
            continue

        key = row[0].strip()
        value = row[1].strip()
        if not key or not value:
            continue

        fields.append(
            ExtractedField(
                field_key=_normalize_field_key(key),
                field_value=value,
                confidence=1.0,
                source_material=material_type,
                evidence="Extracted from document table",
            )
        )
    return fields


def _normalize_field_key(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9_\u4e00-\u9fff]+", "_", text)
    return text.strip("_") or "field"


def _fields_to_text(fields: list[ExtractedField]) -> str:
    parts: list[str] = []
    for field in fields:
        value: Any = field.field_value
        if value is None:
            continue
        text = str(value).strip()
        if text:
            parts.append(text)
    return "\n".join(parts)


def _extracted_field_to_alias_dict(field: ExtractedField) -> dict[str, Any]:
    return {
        "fieldKey": field.field_key,
        "fieldValue": field.field_value,
        "confidence": field.confidence,
        "sourceMaterial": field.source_material,
        "evidence": field.evidence,
    }


def _safe_error(exc: Exception) -> str:
    text = re.sub(r"\s+", " ", str(exc)).strip()
    return text[:240] if text else exc.__class__.__name__
