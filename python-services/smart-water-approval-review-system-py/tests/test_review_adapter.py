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

    def test_parse_accepts_bracketed_basis_refs_from_qwen(self) -> None:
        adapter = ReviewReasoningAdapter()
        payload = {
            "summary": "完成",
            "issues": [
                {
                    "code": "INCONSISTENT_IDENTITY",
                    "severity": "BLOCKER",
                    "message": "申请人身份信息需要核对。",
                    "basis_refs": ["[BASIS_FIELD_APPLICANT_IDENTITY]"],
                }
            ],
            "risk_hints": [
                {
                    "risk_level": "HIGH",
                    "description": "证照字段存在一致性风险。",
                    "basis_refs": ["【BASIS_FIELD_APPLICANT_IDENTITY】"],
                    "requires_manual_review": True,
                }
            ],
            "draft_opinion": "建议人工复核。",
            "material_completeness": {
                "received": ["APPLICATION_FORM", "BUSINESS_LICENSE", "ID_CARD"],
                "missing": [],
                "unrecognized": [],
            },
            "basis_refs": ["[BASIS_FIELD_APPLICANT_IDENTITY]"],
            "manual_review_notice": "AI审核结果为辅助建议。",
        }

        parsed, failure = adapter._parse_and_validate(
            json.dumps(payload, ensure_ascii=False),
            task_id="task-bracketed-basis",
            allowed_basis_refs={"BASIS_FIELD_APPLICANT_IDENTITY"},
        )

        self.assertIsNone(failure)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(["BASIS_FIELD_APPLICANT_IDENTITY"], parsed.basis_refs)
        self.assertEqual(["BASIS_FIELD_APPLICANT_IDENTITY"], parsed.issues[0].basis_refs)
        self.assertEqual(["BASIS_FIELD_APPLICANT_IDENTITY"], parsed.risk_hints[0].basis_refs)

    def test_parse_canonicalizes_basis_ref_title_aliases(self) -> None:
        adapter = ReviewReasoningAdapter()
        payload = {
            "summary": "完成",
            "issues": [
                {
                    "code": "MISSING_FIELD",
                    "severity": "WARNING",
                    "message": "申请书字段需要补充。",
                    "basis_refs": ["申请书: 申请人基本情况 | 联系人 | 联系人手机号码"],
                }
            ],
            "risk_hints": [],
            "draft_opinion": "建议人工复核。",
            "material_completeness": {
                "received": ["APPLICATION_FORM", "BUSINESS_LICENSE", "ID_CARD"],
                "missing": [],
                "unrecognized": [],
            },
            "basis_refs": ["取水许可申请书.docx: 申请人基本情况 | 法定代表人"],
            "manual_review_notice": "AI审核结果为辅助建议。",
        }

        parsed, failure = adapter._parse_and_validate(
            json.dumps(payload, ensure_ascii=False),
            task_id="task-title-alias-basis",
            allowed_basis_refs={"申请书.docx_4_0", "取水许可申请书.docx_53_0"},
            basis_ref_aliases={
                "申请书": "申请书.docx_4_0",
                "申请书.docx": "申请书.docx_4_0",
                "取水许可申请书": "取水许可申请书.docx_53_0",
                "取水许可申请书.docx": "取水许可申请书.docx_53_0",
            },
        )

        self.assertIsNone(failure)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(["取水许可申请书.docx_53_0"], parsed.basis_refs)
        self.assertEqual(["申请书.docx_4_0"], parsed.issues[0].basis_refs)

    def test_parse_accepts_fenced_json_and_camel_case_keys(self) -> None:
        adapter = ReviewReasoningAdapter()
        payload = {
            "summary": "完成",
            "issues": [
                {
                    "code": "MISSING_MATERIAL",
                    "severity": "WARNING",
                    "message": "缺少营业执照",
                    "materialType": "BUSINESS_LICENSE",
                    "fieldKey": "businessLicense.name",
                    "basisRefs": ["BASIS_MATERIAL_INITIAL_LIST"],
                    "applicantVisible": True,
                }
            ],
            "riskHints": [
                {
                    "riskLevel": "MEDIUM",
                    "description": "材料不完整",
                    "basisRefs": ["BASIS_MATERIAL_INITIAL_LIST"],
                    "requiresManualReview": True,
                }
            ],
            "draftOpinion": "建议人工复核。",
            "materialCompleteness": {
                "received": ["APPLICATION_FORM"],
                "missing": ["BUSINESS_LICENSE"],
                "unrecognized": [],
            },
            "basisRefs": ["BASIS_MATERIAL_INITIAL_LIST"],
            "manualReviewNotice": "AI审核结果为辅助建议。",
        }

        content = "```json\n" + json.dumps(payload, ensure_ascii=False) + "\n```"
        parsed, failure = adapter._parse_and_validate(
            content,
            task_id="task-2",
            allowed_basis_refs={"BASIS_MATERIAL_INITIAL_LIST"},
        )

        self.assertIsNone(failure)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual("BUSINESS_LICENSE", parsed.issues[0].material_type)
        self.assertEqual("businessLicense.name", parsed.issues[0].field_key)
        self.assertEqual("MEDIUM", parsed.risk_hints[0].risk_level)
        self.assertTrue(parsed.risk_hints[0].requires_manual_review)

    def test_parse_accepts_wrapped_review_result_payload(self) -> None:
        adapter = ReviewReasoningAdapter()
        payload = {
            "review_result": {
                "summary": "完成",
                "issues": [],
                "risk_hints": [],
                "draft_opinion": "建议人工复核。",
                "material_completeness": {
                    "received": ["APPLICATION_FORM"],
                    "missing": [],
                    "unrecognized": [],
                },
                "basis_refs": ["BASIS_MATERIAL_INITIAL_LIST"],
                "manual_review_notice": "AI审核结果为辅助建议。",
            }
        }

        parsed, failure = adapter._parse_and_validate(
            json.dumps(payload, ensure_ascii=False),
            task_id="task-3",
            allowed_basis_refs={"BASIS_MATERIAL_INITIAL_LIST"},
        )

        self.assertIsNone(failure)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual("完成", parsed.summary)
        self.assertEqual(["BASIS_MATERIAL_INITIAL_LIST"], parsed.basis_refs)

    def test_parse_accepts_qwen_chinese_key_payload(self) -> None:
        adapter = ReviewReasoningAdapter()
        payload = {
            "材料完整性": {
                "已接收材料": ["APPLICATION_FORM", "BUSINESS_LICENSE"],
                "缺失材料": ["ID_CARD"],
                "未识别材料": [],
            },
            "字段问题": [
                {
                    "问题类型": "缺失材料",
                    "严重级别": "警告",
                    "问题描述": "缺少身份证材料。",
                    "材料类型": "ID_CARD",
                    "依据": ["BASIS_MATERIAL_INITIAL_LIST"],
                    "是否申请人可见": "是",
                }
            ],
            "一致性风险": [
                {
                    "风险等级": "中",
                    "风险描述": "申请人与证照信息需要人工核对。",
                    "依据": "BASIS_MATERIAL_INITIAL_LIST",
                    "需要人工复核": "是",
                }
            ],
            "审核意见草稿": "建议补充身份证材料后人工复核。",
        }

        parsed, failure = adapter._parse_and_validate(
            json.dumps(payload, ensure_ascii=False),
            task_id="task-4",
            allowed_basis_refs={"BASIS_MATERIAL_INITIAL_LIST"},
        )

        self.assertIsNone(failure)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual("MISSING_MATERIAL", parsed.issues[0].code)
        self.assertEqual("WARNING", parsed.issues[0].severity)
        self.assertEqual("ID_CARD", parsed.issues[0].material_type)
        self.assertEqual("MEDIUM", parsed.risk_hints[0].risk_level)
        self.assertTrue(parsed.risk_hints[0].requires_manual_review)
        self.assertEqual(["ID_CARD"], parsed.material_completeness.missing)
        self.assertEqual(["BASIS_MATERIAL_INITIAL_LIST"], parsed.basis_refs)
        self.assertIn("辅助建议", parsed.manual_review_notice)


if __name__ == "__main__":
    unittest.main()
