from __future__ import annotations

import logging
import re
from contextlib import redirect_stderr, redirect_stdout
from io import BytesIO, StringIO
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
            for table_text in _table_to_text_blocks(rows):
                result.content_blocks.append(
                    DocumentContentBlock(
                        text=table_text,
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
                block_index = _extract_pdf_tables(result, page, page_index + 1, block_index)

            if total_text >= _PDF_MIN_TEXT_LENGTH_BEFORE_OCR or _has_parsed_content(result):
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
            result.extracted_fields.extend(fields)
            return result

        result.extracted_fields.extend(fields)
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
    return "\n".join(_table_to_text_blocks(rows)).strip()


def _table_to_text_blocks(rows: list[list[str]]) -> list[str]:
    blocks: list[str] = []
    for row in rows:
        text = _table_row_to_text(row)
        if text:
            blocks.append(text)
    return blocks


def _table_row_to_text(row: list[str]) -> str:
    field = _extract_key_value_from_row(row, "")
    if field is not None:
        key, value = field
        if value == "-":
            return ""
        return f"{key} | {value}"

    cells = _dedupe_cells(row)
    if _is_template_row(cells):
        return ""
    text = " | ".join(cells)
    if text in {"...", "…"}:
        return ""
    return text


# 选项引导标记：空白框为"未选中"，其余符号一律视为"选中"
# 设计依据：OCR 对手写勾的识别极不稳定（可能是 ✓ √ X 乃至乱码），
# 唯一可靠的"未选中"信号是干净的空白框 □/☐。
_CHECKBOX_UNCHECKED_MARKS = "□☐"
_CHECKBOX_CHECKED_MARKS = "☑✓✔√☒■✗xX×"
_CHECKBOX_ALL_MARKS = _CHECKBOX_UNCHECKED_MARKS + _CHECKBOX_CHECKED_MARKS
_CHECKBOX_STRUCTURAL_MARKS = _CHECKBOX_UNCHECKED_MARKS + _CHECKBOX_CHECKED_MARKS.replace("x", "").replace("X", "")


def _parse_checkbox_field(text: str) -> str:
    """
    解析勾选框字段，只返回被选中的选项

    判断规则：以 □/☐（空白框）为唯一的"未选中"标记，任何其他引导标记
    （☑ ✓ ✔ √ ☒ ■ ✗ x X × 等）都视为"选中"。每个选项由一个标记符号引导，
    例如 "□新建 ☑改建、扩建 □其他"。

    Args:
        text: 包含勾选框的文本，例如 "□新建 ☑改建、扩建 □其他"

    Returns:
        选中的选项，多个用逗号分隔，如 "改建、扩建"
        如果没有选中任何选项，返回 "-"
    """
    if not text:
        return "-"

    checked_options: list[str] = []
    current_label: list[str] = []
    current_is_checked = False
    seen_mark = False

    def flush() -> None:
        if seen_mark and current_is_checked:
            label = "".join(current_label).strip()
            if label:
                checked_options.append(label)

    for char in text:
        if char in _CHECKBOX_ALL_MARKS:
            # 遇到新标记，先保存上一个选项
            flush()
            current_label = []
            # 只有空白框是"未选中"，其余一律视为"选中"
            current_is_checked = char not in _CHECKBOX_UNCHECKED_MARKS
            seen_mark = True
        elif char in ("\n", "\t"):
            # 换行/制表符作为选项分隔
            flush()
            current_label = []
            seen_mark = False
        else:
            if seen_mark and current_is_checked:
                current_label.append(char)

    # 保存最后一个选项
    flush()

    if checked_options:
        return ", ".join(checked_options)
    return "-"


def _looks_like_checkbox_value(text: str) -> bool:
    return any(mark in text for mark in _CHECKBOX_STRUCTURAL_MARKS)


_TEMPLATE_VALUE_LABELS = {
    "%",
    "份额",
    "法定代表人",
    "邮 编",
    "邮编",
    "用水管理部门",
    "联系人",
    "联系人手机号码",
    "单位名称（个人姓名）",
    "统一社会信用代码 （身份证号码）",
    "期限",
    "（同上）",
}


def _dedupe_cells(row: list[str]) -> list[str]:
    cells: list[str] = []
    previous = ""
    for cell in row:
        normalized = re.sub(r"\s+", " ", str(cell or "")).strip()
        if not normalized or normalized == previous:
            continue
        cells.append(normalized)
        previous = normalized
    return cells


def _extract_key_value_from_row(row: list[str], material_type: str) -> tuple[str, str] | None:
    if len(row) < 2:
        return None

    if len(row) >= 3 and row[1].strip() and row[1].strip() == row[2].strip():
        key = re.sub(r"\s+", " ", row[1]).strip()
        values = [re.sub(r"\s+", " ", cell).strip() for cell in row[2:] if cell.strip()]

        if len(values) > 1:
            value_counts: dict[str, int] = {}
            for value in values:
                value_counts[value] = value_counts.get(value, 0) + 1

            repeated_noise = [
                value
                for value, count in value_counts.items()
                if count >= 3 and not _looks_like_checkbox_value(value)
            ]
            if repeated_noise and not all(_is_template_value(value) for value in repeated_noise):
                return None

        value = _coerce_table_field_value(key, values)
        if value is None:
            return None
    else:
        key = re.sub(r"\s+", " ", row[0]).strip()
        value = re.sub(r"\s+", " ", row[1]).strip()

    if not key:
        return None
    if value == key:
        return None
    if not value:
        value = "-"
    elif _looks_like_checkbox_value(value):
        value = _parse_checkbox_field(value)
    elif _is_template_value(value):
        value = "-"

    return _normalize_field_key(key), value


def _coerce_table_field_value(key: str, values: list[str]) -> str | None:
    actual_values = _dedupe_cells([value for value in values if value != key])
    if not actual_values:
        return "-"
    if any(_looks_like_checkbox_value(value) for value in actual_values):
        return _parse_checkbox_field(" ".join(actual_values))
    if _looks_like_secondary_field_titles(actual_values):
        return None
    if all(_is_template_value(value) for value in actual_values):
        return "-"
    return ", ".join(actual_values)


def _looks_like_secondary_field_titles(values: list[str]) -> bool:
    return bool(values) and all(_is_template_value(value) and _looks_like_field_label(value) for value in values)


def _is_template_value(value: str) -> bool:
    normalized = re.sub(r"\s+", " ", value or "").strip()
    if not normalized or normalized in _TEMPLATE_VALUE_LABELS:
        return True
    if normalized in {"...", "…"}:
        return True
    if _looks_like_checkbox_value(normalized) and _parse_checkbox_field(normalized) == "-":
        return True
    if _looks_like_field_label(normalized):
        return True
    if normalized.endswith(("：", ":")):
        return True
    if re.fullmatch(r"[从至年月日 ]+", normalized):
        return True
    if "省（自治区、直辖市）" in normalized and not re.search(r"\d", normalized):
        return True
    if "可不按年取水量填写" in normalized:
        return True
    if "我单位（本人）承诺" in normalized:
        return True
    return False


def _looks_like_field_label(value: str) -> bool:
    normalized = re.sub(r"\s+", " ", value or "").strip()
    if not normalized or len(normalized) > 40:
        return False
    if normalized in {"住所（住址）", "邮 编", "邮编", "份额"}:
        return True
    label = re.sub(r"[（(].*?[）)]", "", normalized).strip()
    if re.fullmatch(r"(水源\d+|水源n|共同申请人\d+|共同申请人n)", normalized):
        return True
    return label.endswith(
        (
            "情况",
            "代码",
            "号码",
            "代表人",
            "地址",
            "类别",
            "部门",
            "联系人",
            "名称",
            "姓名",
            "份额",
            "概况",
            "性质",
            "类型",
            "地点",
            "位置",
            "取水量",
            "用水量",
            "方式",
            "用途",
            "事由",
            "时间",
        )
    )


def _is_template_row(cells: list[str]) -> bool:
    if not cells:
        return True
    if len(cells) == 1:
        return _is_template_value(cells[0])
    value_cells = cells[1:]
    return all(_is_template_value(cell) for cell in value_cells)


def _extract_key_value_fields(rows: list[list[str]], material_type: str) -> list[ExtractedField]:
    """
    从表格行中提取键值对字段

    处理两种表格格式：
    1. 简单键值对：[字段名, 值]
    2. 申请表格式：[分类, 字段名, 字段名重复, 值1, 值2, ...]
    """
    fields: list[ExtractedField] = []

    for row in rows:
        field = _extract_key_value_from_row(row, material_type)
        if field is None:
            continue
        key, value = field

        fields.append(
            ExtractedField(
                field_key=key,
                field_value=value,
                confidence=1.0,
                source_material=material_type,
                evidence="Extracted from document table",
            )
        )

    return fields


def _extract_pdf_tables(
    result: MaterialDocumentParseResult,
    page: fitz.Page,
    page_number: int,
    block_index: int,
) -> int:
    try:
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            table_finder = page.find_tables()
    except Exception as exc:
        logger.warning("Failed to extract PDF tables from %s page %d: %s", result.source_file_name, page_number, exc)
        return block_index

    for table_index, table in enumerate(table_finder.tables):
        rows = _normalize_table_rows(table.extract())
        if not rows:
            continue

        result.tables.append(
            DocumentTable(
                rows=rows,
                pageNumber=page_number,
                tableIndex=table_index,
            )
        )
        for table_text in _table_to_text_blocks(rows):
            result.content_blocks.append(
                DocumentContentBlock(
                    text=table_text,
                    blockType="pdf_table",
                    pageNumber=page_number,
                    blockIndex=block_index,
                )
            )
            block_index += 1
        result.extracted_fields.extend(_extract_key_value_fields(rows, result.material_type))

    return block_index


def _has_parsed_content(result: MaterialDocumentParseResult) -> bool:
    return bool(result.content_blocks or result.tables or result.extracted_fields)


def _normalize_table_rows(rows: Any) -> list[list[str]]:
    if not isinstance(rows, list):
        return []

    normalized: list[list[str]] = []
    for row in rows:
        if not isinstance(row, list):
            continue
        cells = [_normalize_table_cell(cell) for cell in row]
        if any(cells):
            normalized.append(cells)
    return normalized


def _normalize_table_cell(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" _", "_").replace("_ ", "_")
    return text


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
