import unittest

from src.models import ExtractedField, Issue, MaterialCompleteness, ReviewResult
from src.services.review_orchestrator import ReviewTaskOrchestrator


class _StubExtractor:
    def extract(self, material):
        return [
            ExtractedField(
                field_key="applicant.name",
                field_value="某某科技有限公司",
                confidence=0.95,
                source_material=material.material_type,
                evidence="申请人：某某科技有限公司",
            )
        ]


class _StubKnowledgeTools:
    def check_completeness(self, materials):
        return {
            "submitted": materials,
            "required": ["APPLICATION_FORM", "BUSINESS_LICENSE", "ID_CARD"],
            "missing": ["ID_CARD"],
            "unrecognized": [],
            "findings": [
                {
                    "code": "MISSING_MATERIAL",
                    "severity": "WARNING",
                    "materialType": "ID_CARD",
                    "message": "缺少法定代表人身份证，法定代表人与身份证姓名一致性需要人工补充核对。",
                    "basisRefs": ["BASIS_MATERIAL_INITIAL_LIST"],
                }
            ],
        }

    def knowledge_search(self, query, top_k=8):
        return {
            "results": [
                {
                    "id": "BASIS_MATERIAL_INITIAL_LIST",
                    "title": "材料清单要求",
                    "excerpt": "申请材料需包含申请书、营业执照和身份证。",
                }
            ]
        }


class ReviewTaskOrchestratorTests(unittest.TestCase):
    def _task_payload(self):
        return {
            "taskId": "task-1",
            "sessionId": "session-1",
            "materials": [
                {
                    "materialType": "APPLICATION_FORM",
                    "originalFileName": "app.pdf",
                    "storageKey": "k1",
                    "fileExtension": "pdf",
                    "uploaded": True,
                },
                {
                    "materialType": "BUSINESS_LICENSE",
                    "originalFileName": "license.jpg",
                    "storageKey": "k2",
                    "fileExtension": "jpg",
                    "uploaded": True,
                },
                {
                    "materialType": "ID_CARD",
                    "originalFileName": None,
                    "storageKey": None,
                    "fileExtension": None,
                    "uploaded": False,
                },
            ],
        }

    def test_fallback_to_rules_when_agent_returns_failure_issue(self):
        reviewer = type(
            "ReviewerStub",
            (),
            {
                "review": lambda *args, **kwargs: ReviewResult(
                    summary="agent failed",
                    issues=[Issue(code="UPSTREAM_5XX", severity="BLOCKER", message="error", applicant_visible=False)],
                )
            },
        )()
        orchestrator = ReviewTaskOrchestrator(
            extractor=_StubExtractor(),
            reviewer=reviewer,
            knowledge_tools=_StubKnowledgeTools(),
            knowledge_fragments=[{"source_id": "PROMPT_BASIS_LIMIT", "source_title": "prompt", "content": "限制依据"}],
            knowledge_pack_version="water-permit-mvp-2026-04-27",
        )

        result = orchestrator.process_task(self._task_payload())

        self.assertEqual("PARTIAL_SUCCESS", result.status)
        self.assertIn("降级为规则", result.result_summary)
        self.assertTrue(any(issue.code == "MODEL_UNCERTAIN" for issue in result.reviewer_result.issues))
        self.assertTrue(any(issue.code == "MISSING_MATERIAL" for issue in result.reviewer_result.issues))
        self.assertEqual([], result.applicant_result.extracted_fields)
        self.assertGreater(len(result.reviewer_result.extracted_fields), 0)

    def test_merge_rules_with_agent_success(self):
        reviewer = type(
            "ReviewerStub",
            (),
            {
                "review": lambda *args, **kwargs: ReviewResult(
                    summary="review done",
                    issues=[Issue(code="WATER_AMOUNT_REVIEW_REQUIRED", severity="WARNING", message="需核对取水量")],
                    material_completeness=MaterialCompleteness(received=["APPLICATION_FORM"], missing=[]),
                )
            },
        )()
        orchestrator = ReviewTaskOrchestrator(
            extractor=_StubExtractor(),
            reviewer=reviewer,
            knowledge_tools=_StubKnowledgeTools(),
            knowledge_fragments=[],
            knowledge_pack_version="water-permit-mvp-2026-04-27",
        )

        result = orchestrator.process_task(self._task_payload())

        self.assertEqual("PARTIAL_SUCCESS", result.status)
        codes = {issue.code for issue in result.reviewer_result.issues}
        self.assertIn("MISSING_MATERIAL", codes)
        self.assertIn("WATER_AMOUNT_REVIEW_REQUIRED", codes)
        self.assertEqual("water-permit-mvp-2026-04-27", result.knowledge_pack_version)


if __name__ == "__main__":
    unittest.main()
