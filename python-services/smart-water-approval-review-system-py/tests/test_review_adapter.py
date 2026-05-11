import json
import unittest

from src.adapters.review_adapter import ReviewReasoningAdapter


class ReviewReasoningAdapterValidationTests(unittest.TestCase):
    def test_parse_rejects_invented_basis_refs(self) -> None:
        adapter = ReviewReasoningAdapter()
        payload = {
            "summary": "完成",
            "issues": [
                {
                    "code": "MISSING_MATERIAL",
                    "severity": "WARNING",
                    "message": "缺少营业执照",
                    "basis_refs": ["BASIS_INVENTED"],
                }
            ],
            "risk_hints": [],
            "draft_opinion": "建议人工复核。",
            "material_completeness": {
                "received": ["APPLICATION_FORM"],
                "missing": ["BUSINESS_LICENSE"],
                "unrecognized": [],
            },
            "basis_refs": ["BASIS_MATERIAL_INITIAL_LIST"],
            "manual_review_notice": "AI审核结果为辅助建议。",
        }

        parsed, failure = adapter._parse_and_validate(
            json.dumps(payload, ensure_ascii=False),
            task_id="task-1",
            allowed_basis_refs={"BASIS_MATERIAL_INITIAL_LIST"},
        )

        self.assertIsNone(parsed)
        self.assertEqual("SCHEMA_MISMATCH", failure)

    def test_parse_accepts_allowed_basis_refs(self) -> None:
        adapter = ReviewReasoningAdapter()
        payload = {
            "summary": "完成",
            "issues": [
                {
                    "code": "MISSING_MATERIAL",
                    "severity": "WARNING",
                    "message": "缺少营业执照",
                    "basis_refs": ["BASIS_MATERIAL_INITIAL_LIST"],
                }
            ],
            "risk_hints": [
                {
                    "risk_level": "MEDIUM",
                    "description": "材料不完整",
                    "basis_refs": ["BASIS_MATERIAL_INITIAL_LIST"],
                    "requires_manual_review": True,
                }
            ],
            "draft_opinion": "建议人工复核。",
            "material_completeness": {
                "received": ["APPLICATION_FORM"],
                "missing": ["BUSINESS_LICENSE"],
                "unrecognized": [],
            },
            "basis_refs": ["BASIS_MATERIAL_INITIAL_LIST"],
            "manual_review_notice": "AI审核结果为辅助建议。",
        }

        parsed, failure = adapter._parse_and_validate(
            json.dumps(payload, ensure_ascii=False),
            task_id="task-1",
            allowed_basis_refs={"BASIS_MATERIAL_INITIAL_LIST"},
        )

        self.assertIsNone(failure)
        self.assertIsNotNone(parsed)


if __name__ == "__main__":
    unittest.main()
