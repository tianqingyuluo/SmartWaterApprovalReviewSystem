import base64
import logging
import re
from typing import Any

import httpx

from src.adapters import OcrAdapter
from src.config import config
from src.models import ExtractedField

logger = logging.getLogger(__name__)

_GLM_OCR_MODEL = "glm-ocr"
_GLM_OCR_PATH = "layout_parsing"
_OCR_MARKDOWN_FIELD_KEY = "ocr_markdown"
_DEFAULT_OCR_CONFIDENCE = 1.0
_SUPPORTED_EXTENSIONS = {"jpg", "jpeg", "png", "pdf"}
_ERROR_SUMMARY_MAX_LENGTH = 240
_DATA_URI_MIME_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "pdf": "application/pdf",
}


def _encode_file_payload(file_bytes: bytes, extension: str) -> str:
    mime_type = _DATA_URI_MIME_TYPES.get(extension)
    if not mime_type:
        raise ValueError(f"Unsupported OCR file type: {extension}")

    encoded = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def _safe_key_fragment(value: Any) -> str:
    text = str(value or "text").strip().lower()
    text = re.sub(r"[^a-z0-9_]+", "_", text)
    return text.strip("_") or "text"


def _sanitize_error_text(text: str) -> str:
    sanitized = re.sub(r"data:[^;,\s]+;base64,[A-Za-z0-9+/=_-]+", "data:[REDACTED]", text)
    sanitized = re.sub(r"Bearer\s+[A-Za-z0-9._\-]+", "Bearer [REDACTED]", sanitized)
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    if len(sanitized) > _ERROR_SUMMARY_MAX_LENGTH:
        sanitized = f"{sanitized[:_ERROR_SUMMARY_MAX_LENGTH - 3]}..."
    return sanitized


def _extract_error_message(data: Any) -> str | None:
    if isinstance(data, dict):
        for key in ("message", "detail"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        error = data.get("error")
        if isinstance(error, dict):
            return _extract_error_message(error)
        if isinstance(error, str) and error.strip():
            return error.strip()

    if isinstance(data, list):
        for item in data:
            message = _extract_error_message(item)
            if message:
                return message

    return None


def _summarize_exception(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        response = exc.response
        message: str | None = None
        try:
            message = _extract_error_message(response.json())
        except ValueError:
            body = response.text.strip()
            if body:
                message = body

        if message:
            return _sanitize_error_text(f"HTTP {response.status_code}: {message}")
        return f"HTTP {response.status_code}: {response.reason_phrase}"

    sanitized = _sanitize_error_text(str(exc))
    return sanitized or exc.__class__.__name__


def clean_ocr_markdown(text: str | None) -> str:
    """
    清洗 OCR 返回的 Markdown 格式文本，移除：
    1. HTML 标签（<div>, <center> 等）
    2. Markdown 图片标记（![](...)）
    3. bbox 坐标信息
    4. 多余的空白行

    Args:
        text: OCR 返回的原始 Markdown 文本

    Returns:
        清洗后的纯文本
    """
    if not text:
        return ""

    # 移除 Markdown 图片标记和 bbox 坐标
    # 例如: ![](page=0,bbox=[79, 111, 183, 224])
    cleaned = re.sub(r'!\[\]\(page=\d+,bbox=\[[^\]]+\]\)', '', text)

    # 移除 HTML 标签
    # 例如: <div align="center">, </div>, <center>, </center>
    cleaned = re.sub(r'<[^>]+>', '', cleaned)

    # 移除多余的空白行（保留单个换行）
    cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)

    # 移除行首行尾空白
    lines = [line.strip() for line in cleaned.split('\n')]
    cleaned = '\n'.join(line for line in lines if line)

    return cleaned.strip()


def _coerce_markdown_results(md_results: Any) -> str:
    if isinstance(md_results, str):
        return md_results.strip()

    if isinstance(md_results, list):
        parts: list[str] = []
        for item in md_results:
            if isinstance(item, str):
                text = item.strip()
                if text:
                    parts.append(text)
            elif isinstance(item, dict):
                for key in ("content", "text", "markdown", "md"):
                    value = item.get(key)
                    if isinstance(value, str) and value.strip():
                        parts.append(value.strip())
                        break
        return "\n\n".join(parts)

    return ""


def _layout_details_to_fields(layout_details: Any) -> list[ExtractedField]:
    if not isinstance(layout_details, list):
        return []

    fields: list[ExtractedField] = []
    for page_index, page in enumerate(layout_details, start=1):
        page_items = page if isinstance(page, list) else [page]

        for item_index, item in enumerate(page_items, start=1):
            if not isinstance(item, dict):
                continue

            content = item.get("content")
            if not isinstance(content, str):
                continue

            text = content.strip()
            if not text:
                continue

            label = _safe_key_fragment(item.get("label"))
            item_id = item.get("index")
            if not isinstance(item_id, int):
                item_id = item_index

            fields.append(
                ExtractedField(
                    field_key=f"ocr_{label}_p{page_index}_{item_id}",
                    field_value=text,
                    confidence=_DEFAULT_OCR_CONFIDENCE,
                )
            )

    return fields


def _parse_ocr_response(data: dict[str, Any]) -> list[ExtractedField]:
    markdown = _coerce_markdown_results(data.get("md_results"))
    if markdown:
        # 清洗 OCR 返回的 Markdown，移除 HTML 标签和图片标记
        cleaned_markdown = clean_ocr_markdown(markdown)
        return [
            ExtractedField(
                field_key=_OCR_MARKDOWN_FIELD_KEY,
                field_value=cleaned_markdown,
                confidence=_DEFAULT_OCR_CONFIDENCE,
            )
        ]

    return _layout_details_to_fields(data.get("layout_details"))


class GlmOcrAdapter(OcrAdapter):
    def extract_fields(self, file_bytes: bytes, material_type: str, file_name: str) -> list[ExtractedField]:
        ext = file_name.split(".")[-1].lower() if "." in file_name else ""

        if ext not in _SUPPORTED_EXTENSIONS:
            logger.warning("Unsupported OCR file type: %s", ext)
            return []

        return self._extract_document(file_bytes, ext)

    def _extract_document(self, file_bytes: bytes, extension: str) -> list[ExtractedField]:
        payload = {
            "model": _GLM_OCR_MODEL,
            "file": _encode_file_payload(file_bytes, extension),
        }
        return self._call_api(payload)

    def _call_api(self, payload: dict[str, Any]) -> list[ExtractedField]:
        headers = {
            "Authorization": f"Bearer {config.OCR_GLM_API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            url = f"{config.OCR_GLM_BASE_URL.rstrip('/')}/{_GLM_OCR_PATH}"
            with httpx.Client(timeout=120) as client:
                resp = client.post(url, json=payload, headers=headers)
                resp.raise_for_status()

                data = resp.json()
                if not isinstance(data, dict):
                    raise ValueError("GLM OCR response is not a JSON object")

                return _parse_ocr_response(data)

        except Exception as exc:
            summary = _summarize_exception(exc)
            logger.error("GLM OCR API call failed: %s", summary)
            return [
                ExtractedField(
                    field_key="ocr_error",
                    field_value=summary,
                    confidence=0.0,
                )
            ]
