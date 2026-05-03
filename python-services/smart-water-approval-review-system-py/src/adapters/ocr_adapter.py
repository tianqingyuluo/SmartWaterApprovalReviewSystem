import json
import logging
import base64
from typing import Any
import httpx
from src.config import config
from src.adapters import OcrAdapter
from src.models import ExtractedField

logger = logging.getLogger(__name__)

_STANDARD_PROMPT = (
    "请从以下取水许可申请材料图片中提取关键字段。"
    "返回严格的JSON格式："
    '{"fields":[{"field_key":"字段名","field_value":"值","confidence":0.0-1.0}]}'
    "只返回JSON，不要有其他文字。"
)


def _build_field_hash(fields: list[dict]) -> list[ExtractedField]:
    result: list[ExtractedField] = []
    for f in fields:
        result.append(
            ExtractedField(
                field_key=f.get("field_key", ""),
                field_value=f.get("field_value"),
                confidence=f.get("confidence", 0.0),
            )
        )
    return result


class GlmOcrAdapter(OcrAdapter):
    def extract_fields(self, file_bytes: bytes, material_type: str, file_name: str) -> list[ExtractedField]:
        ext = file_name.split(".")[-1].lower() if "." in file_name else ""

        if ext in ("jpg", "jpeg", "png"):
            return self._extract_image(file_bytes)
        elif ext == "pdf":
            return self._extract_pdf(file_bytes)
        else:
            logger.warning("Unsupported OCR file type: %s", ext)
            return []

    def _extract_image(self, file_bytes: bytes) -> list[ExtractedField]:
        image_b64 = base64.b64encode(file_bytes).decode("utf-8")

        payload = {
            "model": "glm-4v",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _STANDARD_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                    ],
                }
            ],
            "max_tokens": 2000,
        }

        return self._call_api(payload)

    def _extract_pdf(self, file_bytes: bytes) -> list[ExtractedField]:
        image_b64 = base64.b64encode(file_bytes).decode("utf-8")
        payload = {
            "model": "glm-4v",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _STANDARD_PROMPT},
                        {"type": "file_url", "file_url": {"url": f"data:application/pdf;base64,{image_b64}"}},
                    ],
                }
            ],
            "max_tokens": 2000,
        }

        return self._call_api(payload)

    def _call_api(self, payload: dict[str, Any]) -> list[ExtractedField]:
        headers = {
            "Authorization": f"Bearer {config.OCR_GLM_API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=120) as client:
                resp = client.post(
                    f"{config.OCR_GLM_BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]

                start = content.find("{")
                end = content.rfind("}")
                if start != -1 and end != -1:
                    parsed = json.loads(content[start : end + 1])
                else:
                    parsed = json.loads(content)

                return _build_field_hash(parsed.get("fields", []))

        except Exception as e:
            logger.error("GLM OCR API call failed")
            return [
                ExtractedField(
                    field_key="ocr_error",
                    field_value=str(e),
                    confidence=0.0,
                )
            ]
