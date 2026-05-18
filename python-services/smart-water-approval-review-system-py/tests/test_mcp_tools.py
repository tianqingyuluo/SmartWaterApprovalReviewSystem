import unittest

from src.services.knowledge_tools import SmartWaterKnowledgeTools


class SmartWaterKnowledgeToolsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tools = SmartWaterKnowledgeTools()

    def test_knowledge_search_returns_structured_matches(self) -> None:
        result = self.tools.knowledge_search(query="营业执照", top_k=3)

        self.assertEqual("营业执照", result["query"])
        self.assertEqual(3, result["topK"])
        self.assertTrue(result["knowledgePackVersion"])
        self.assertGreaterEqual(result["total"], 1)

        first = result["results"][0]
        self.assertIn("section", first)
        self.assertIn("id", first)
        self.assertIn("title", first)
        self.assertIn("excerpt", first)
        self.assertIn("rank", first)
        self.assertIn("score", first)
        self.assertIn("sourceIds", first)
        self.assertIn("sourceRefs", first)
        self.assertIn("basisRefs", first)
        self.assertTrue(first["sourceIds"])

    def test_knowledge_search_includes_direct_review_basis_source_id(self) -> None:
        result = self.tools.knowledge_search(query="BASIS_WATER_LAW_PERMIT_REQUIREMENT", top_k=1)

        review_basis_results = [
            item for item in result["results"] if item["section"] == "reviewBasis"
        ]
        self.assertTrue(review_basis_results)
        self.assertIn("SRC_PROCESS_DOC", review_basis_results[0]["sourceIds"])

    def test_can_inject_empty_knowledge_pack_without_loading_default_pack(self) -> None:
        tools = SmartWaterKnowledgeTools(
            {
                "version": "empty-test-pack",
                "materialChecklist": [],
                "applicationFieldRules": [],
                "reviewBasis": [],
                "promptSnippets": [],
                "manualReviewRules": [],
            }
        )

        search = tools.knowledge_search(query="", top_k=5)
        completeness = tools.check_completeness(materials=[])

        self.assertEqual("empty-test-pack", search["knowledgePackVersion"])
        self.assertEqual([], search["results"])
        self.assertEqual([], completeness["required"])

    def test_knowledge_search_clamps_top_k(self) -> None:
        result = self.tools.knowledge_search(query="取水", top_k=-3)

        self.assertEqual(-3, result["requestedTopK"])
        self.assertEqual(1, result["topK"])
        self.assertEqual(1, len(result["results"]))

    def test_knowledge_search_invalid_top_k_falls_back_to_default(self) -> None:
        result = self.tools.knowledge_search(query="取水", top_k="abc")

        self.assertEqual("abc", result["requestedTopK"])
        self.assertEqual(5, result["topK"])

    def test_knowledge_search_empty_query_returns_ranked_slice(self) -> None:
        result = self.tools.knowledge_search(query="", top_k=4)

        self.assertEqual("", result["query"])
        self.assertEqual(4, result["topK"])
        self.assertEqual(4, len(result["results"]))
        self.assertEqual([1, 2, 3, 4], [item["rank"] for item in result["results"]])

    def test_check_completeness_from_simple_list(self) -> None:
        result = self.tools.check_completeness(["APPLICATION_FORM", "BUSINESS_LICENSE"])

        self.assertEqual(["APPLICATION_FORM", "BUSINESS_LICENSE"], result["submitted"])
        self.assertEqual(["APPLICATION_FORM", "BUSINESS_LICENSE", "ID_CARD"], result["required"])
        self.assertEqual(["ID_CARD"], result["missing"])
        self.assertFalse(result["complete"])
        self.assertEqual(1, len(result["findings"]))
        finding = result["findings"][0]
        self.assertEqual("MISSING_MATERIAL", finding["code"])
        self.assertEqual("ID_CARD", finding["materialType"])
        self.assertTrue(finding["basisRefs"])

    def test_check_completeness_accepts_object_inputs_and_deduplicates(self) -> None:
        materials = {
            "materials": [
                {"materialType": "application_form"},
                {"material_type": "BUSINESS_LICENSE"},
                {"type": "ID_CARD"},
                {"materialType": "ID_CARD"},
            ]
        }

        result = self.tools.check_completeness(materials)

        self.assertEqual(["APPLICATION_FORM", "BUSINESS_LICENSE", "ID_CARD"], result["submitted"])
        self.assertEqual([], result["missing"])
        self.assertTrue(result["complete"])
        self.assertEqual([], result["findings"])

    def test_check_completeness_ignores_unrecognized_values(self) -> None:
        result = self.tools.check_completeness(["UNRELATED", {"foo": "bar"}, None, ""])

        self.assertEqual([], result["submitted"])
        self.assertEqual(["APPLICATION_FORM", "BUSINESS_LICENSE", "ID_CARD"], result["missing"])
        self.assertFalse(result["complete"])


if __name__ == "__main__":
    unittest.main()
