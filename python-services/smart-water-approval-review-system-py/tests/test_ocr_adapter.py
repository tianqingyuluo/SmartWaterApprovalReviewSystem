import base64
import unittest
from unittest.mock import patch

import httpx

from src.adapters.ocr_adapter import GlmOcrAdapter


class GlmOcrAdapterTests(unittest.TestCase):
    @patch("src.adapters.ocr_adapter.config.OCR_GLM_API_KEY", "test-glm-key")
    @patch("src.adapters.ocr_adapter.config.OCR_GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
    @patch("src.adapters.ocr_adapter.httpx.Client")
    def test_extract_fields_posts_data_uri_payload_for_supported_extensions(self, client_cls) -> None:
        cases = [
            ("form.png", "data:image/png;base64,"),
            ("license.jpg", "data:image/jpeg;base64,"),
            ("license.jpeg", "data:image/jpeg;base64,"),
            ("form.pdf", "data:application/pdf;base64,"),
        ]

        for file_name, expected_prefix in cases:
            with self.subTest(file_name=file_name):
                client = client_cls.return_value.__enter__.return_value
                client.post.reset_mock()
                response = httpx.Response(
                    200,
                    json={
                        "id": "task-ocr-1",
                        "model": "GLM-OCR",
                        "md_results": "# OCR Result\n申请人：张三",
                    },
                    request=httpx.Request("POST", "https://open.bigmodel.cn/api/paas/v4/layout_parsing"),
                )
                client.post.return_value = response

                adapter = GlmOcrAdapter()
                fields = adapter.extract_fields(b"binary-image", "APPLICATION_FORM", file_name)

                self.assertEqual(1, len(fields))
                self.assertEqual("ocr_markdown", fields[0].field_key)
                self.assertEqual("# OCR Result\n申请人：张三", fields[0].field_value)
                self.assertEqual(1.0, fields[0].confidence)

                client.post.assert_called_once()
                url = client.post.call_args.args[0]
                payload = client.post.call_args.kwargs["json"]
                headers = client.post.call_args.kwargs["headers"]

                self.assertEqual("https://open.bigmodel.cn/api/paas/v4/layout_parsing", url)
                self.assertEqual("glm-ocr", payload["model"])
                self.assertTrue(payload["file"].startswith(expected_prefix))
                self.assertEqual(
                    f"{expected_prefix}{base64.b64encode(b'binary-image').decode('utf-8')}",
                    payload["file"],
                )
                self.assertEqual("Bearer test-glm-key", headers["Authorization"])
                self.assertEqual("application/json", headers["Content-Type"])
                self.assertNotIn("messages", payload)
                self.assertNotIn("max_tokens", payload)

    @patch("src.adapters.ocr_adapter.config.OCR_GLM_API_KEY", "test-glm-key")
    @patch("src.adapters.ocr_adapter.config.OCR_GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
    @patch("src.adapters.ocr_adapter.httpx.Client")
    def test_extract_fields_parses_layout_details_when_markdown_is_missing(self, client_cls) -> None:
        client = client_cls.return_value.__enter__.return_value
        response = httpx.Response(
            200,
            json={
                "id": "task-ocr-2",
                "model": "GLM-OCR",
                "layout_details": [
                    [
                        {"index": 1, "label": "text", "content": "申请人：张三"},
                        {"index": 2, "label": "table", "content": "统一社会信用代码：1234567890"},
                    ]
                ],
            },
            request=httpx.Request("POST", "https://open.bigmodel.cn/api/paas/v4/layout_parsing"),
        )
        client.post.return_value = response

        adapter = GlmOcrAdapter()
        fields = adapter.extract_fields(b"binary-pdf", "APPLICATION_FORM", "form.pdf")

        payload = client.post.call_args.kwargs["json"]
        self.assertEqual(
            ["ocr_text_p1_1", "ocr_table_p1_2"],
            [field.field_key for field in fields],
        )
        self.assertEqual(
            ["申请人：张三", "统一社会信用代码：1234567890"],
            [field.field_value for field in fields],
        )
        self.assertTrue(all(field.confidence == 1.0 for field in fields))
        self.assertEqual(
            f"data:application/pdf;base64,{base64.b64encode(b'binary-pdf').decode('utf-8')}",
            payload["file"],
        )

    @patch("src.adapters.ocr_adapter.httpx.Client")
    def test_extract_fields_rejects_unsupported_extension_without_calling_api(self, client_cls) -> None:
        adapter = GlmOcrAdapter()
        fields = adapter.extract_fields(b"binary", "APPLICATION_FORM", "form.docx")

        self.assertEqual([], fields)
        client_cls.return_value.__enter__.return_value.post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
