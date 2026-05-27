import unittest

from src.mcp_server.demo import list_tools_data, run_sample_calls


class McpDemoTests(unittest.IsolatedAsyncioTestCase):
    async def test_list_tools_data_contains_required_tools(self) -> None:
        tools = await list_tools_data()

        names = {tool.get("name") for tool in tools}
        self.assertEqual({"knowledge_search", "check_completeness"}, names)

        for tool in tools:
            self.assertIn("description", tool)
            self.assertIn("inputSchema", tool)

    async def test_run_sample_calls_outputs_both_surfaces(self) -> None:
        output = run_sample_calls(
            query="身份证",
            top_k=2,
            sample_materials=["APPLICATION_FORM", "BUSINESS_LICENSE"],
        )

        self.assertIn("knowledge_search", output)
        self.assertIn("check_completeness", output)

        search = output["knowledge_search"]
        completeness = output["check_completeness"]

        self.assertEqual("身份证", search["query"])
        self.assertEqual(2, search["topK"])
        self.assertTrue(search["knowledgePackVersion"])
        self.assertEqual(["ID_CARD"], completeness["missing"])
        self.assertTrue(completeness["knowledgePackVersion"])


if __name__ == "__main__":
    unittest.main()
