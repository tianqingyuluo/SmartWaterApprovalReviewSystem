from __future__ import annotations

import unittest
from pathlib import Path

from src.services.mcp_client import SmartWaterMcpClient


class SmartWaterMcpClientTests(unittest.TestCase):
    def _client(self) -> SmartWaterMcpClient:
        root = Path(__file__).resolve().parents[1]
        python = root / ".venv" / "bin" / "python"
        command = str(python if python.exists() else "python")
        return SmartWaterMcpClient(
            command=command,
            args=["-m", "src.mcp_server.app", "--transport", "stdio"],
            cwd=root,
            env={"KNOWLEDGE_PACK_DIR": str(root / "knowledge_pack")},
        )

    def test_stdio_client_discovers_tools_and_calls_knowledge_search(self) -> None:
        client = self._client()

        tools = client.list_tools_sync()
        names = {tool["name"] for tool in tools}
        self.assertIn("knowledge_search", names)
        self.assertIn("check_completeness", names)

        result = client.knowledge_search_sync("营业执照", top_k=2)

        self.assertIn("results", result)
        self.assertGreaterEqual(len(result["results"]), 1)
        traces = client.traces_snapshot()
        self.assertTrue(any(trace.tool_name == "list_tools" for trace in traces))
        self.assertTrue(any(trace.tool_name == "knowledge_search" for trace in traces))

    def test_stdio_client_calls_check_completeness(self) -> None:
        client = self._client()

        result = client.check_completeness_sync(["APPLICATION_FORM", "BUSINESS_LICENSE"])

        self.assertEqual(["ID_CARD"], result["missing"])
        self.assertFalse(result["complete"])
        self.assertTrue(any(trace.tool_name == "check_completeness" for trace in client.traces_snapshot()))


if __name__ == "__main__":
    unittest.main()
