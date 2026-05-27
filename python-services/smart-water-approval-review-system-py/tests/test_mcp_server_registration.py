import unittest

from src.mcp_server.server import build_mcp_server


class McpServerRegistrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_server_registers_required_tools(self) -> None:
        server = build_mcp_server()

        tools = await server.list_tools()
        names = {tool.name for tool in tools}

        self.assertEqual({"knowledge_search", "check_completeness"}, names)


if __name__ == "__main__":
    unittest.main()
