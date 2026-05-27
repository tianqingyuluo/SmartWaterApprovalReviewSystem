import unittest
from unittest.mock import patch

import httpx

from src.models import ExtractedField, ProcessingResult, ReviewResult, ToolCallTrace
from src.services.result_writer import ResultWriter, _parse_backend_response, _result_to_dict


class ResultWriterResponseTest(unittest.TestCase):
    def test_should_return_payload_when_business_code_is_200(self) -> None:
        response = httpx.Response(
            200,
            json={"code": 200, "message": "success", "data": [{"taskId": "task-1"}]},
            request=httpx.Request("GET", "http://localhost/api/task/pending"),
        )

        payload = _parse_backend_response(response)

        self.assertEqual(200, payload["code"])
        self.assertEqual([{"taskId": "task-1"}], payload["data"])

    def test_should_raise_when_business_code_is_not_200(self) -> None:
        response = httpx.Response(
            200,
            json={"code": 403, "message": "Invalid worker token", "data": None},
            request=httpx.Request("PUT", "http://localhost/api/task/task-1/status"),
        )

        with self.assertRaises(RuntimeError) as context:
            _parse_backend_response(response)

        self.assertIn("code=403", str(context.exception))

    def test_should_raise_when_response_is_not_json(self) -> None:
        response = httpx.Response(
            200,
            text="ok",
            request=httpx.Request("GET", "http://localhost/api/task/pending"),
        )

        with self.assertRaises(RuntimeError):
            _parse_backend_response(response)

    @patch("src.services.result_writer.httpx.Client")
    def test_update_status_should_fail_when_backend_business_code_is_not_200(self, client_cls) -> None:
        response = httpx.Response(
            200,
            json={"code": 409, "message": "不允许的状态流转: SUBMITTED -> COMPLETED", "data": None},
            request=httpx.Request("PUT", "http://localhost/api/task/task-1/status"),
        )
        client = client_cls.return_value.__enter__.return_value
        client.put.return_value = response

        writer = ResultWriter()

        success = writer.update_status("task-1", "COMPLETED", retries=1)

        self.assertFalse(success)

    @patch("src.services.result_writer.httpx.Client")
    def test_write_results_should_fail_when_backend_business_code_is_not_200(self, client_cls) -> None:
        response = httpx.Response(
            200,
            json={"code": 403, "message": "Invalid worker token", "data": None},
            request=httpx.Request("PUT", "http://localhost/api/task/task-1/result"),
        )
        client = client_cls.return_value.__enter__.return_value
        client.put.return_value = response

        writer = ResultWriter()
        result = ProcessingResult(task_id="task-1", status="COMPLETED", result_summary="done")

        success = writer.write_results("task-1", result, retries=1)

        self.assertFalse(success)

    @patch("src.services.result_writer.httpx.Client")
    def test_write_results_should_send_knowledge_pack_version(self, client_cls) -> None:
        response = httpx.Response(
            200,
            json={"code": 200, "message": "success", "data": None},
            request=httpx.Request("PUT", "http://localhost/api/task/task-1/result"),
        )
        client = client_cls.return_value.__enter__.return_value
        client.put.return_value = response

        writer = ResultWriter()
        result = ProcessingResult(
            task_id="task-1",
            status="COMPLETED",
            result_summary="done",
            knowledge_pack_version="water-permit-mvp-2026-04-27",
        )

        success = writer.write_results("task-1", result, retries=1)

        self.assertTrue(success)
        payload = client.put.call_args.kwargs["json"]
        self.assertEqual("water-permit-mvp-2026-04-27", payload["knowledgePackVersion"])

    def test_result_to_dict_should_serialize_extracted_field_snapshot(self) -> None:
        result = ReviewResult(
            summary="done",
            extracted_fields=[
                ExtractedField(
                    field_key="applicant.name",
                    field_value="某某科技有限公司",
                    confidence=0.93,
                    source_material="APPLICATION_FORM",
                    evidence="申请人：某某科技有限公司",
                )
            ],
        )

        payload = _result_to_dict(result)

        self.assertIsNotNone(payload)
        self.assertEqual(
            [
                {
                    "fieldKey": "applicant.name",
                    "fieldValue": "某某科技有限公司",
                    "confidence": 0.93,
                    "sourceMaterial": "APPLICATION_FORM",
                    "evidence": "申请人：某某科技有限公司",
                }
            ],
            payload["extractedFields"],
        )

    def test_result_to_dict_should_serialize_tool_call_traces(self) -> None:
        result = ReviewResult(
            summary="done",
            tool_call_traces=[
                ToolCallTrace(
                    tool_name="knowledge_search",
                    input_summary="query='营业执照', top_k=8",
                    output_summary="total=3",
                    source_refs=["BASIS_MATERIAL_INITIAL_LIST"],
                    latency_ms=42,
                )
            ],
        )

        payload = _result_to_dict(result)

        self.assertIsNotNone(payload)
        self.assertEqual(
            [
                {
                    "toolName": "knowledge_search",
                    "inputSummary": "query='营业执照', top_k=8",
                    "outputSummary": "total=3",
                    "sourceRefs": ["BASIS_MATERIAL_INITIAL_LIST"],
                    "status": "SUCCESS",
                    "latencyMs": 42,
                    "error": None,
                }
            ],
            payload["toolCallTraces"],
        )


if __name__ == "__main__":
    unittest.main()
