from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from src.services.knowledge_tools import SmartWaterKnowledgeTools


def build_mcp_server(tools: SmartWaterKnowledgeTools | None = None) -> FastMCP:
    knowledge_tools = tools or SmartWaterKnowledgeTools()

    server = FastMCP(
        name="smartwater-mcp-tools",
        instructions="SmartWater MVP knowledge tools: knowledge_search and check_completeness.",
    )

    @server.tool(
        name="knowledge_search",
        description="Search SmartWater MVP knowledge pack and return structured matches.",
    )
    def knowledge_search(query: str, top_k: int | str = 5) -> dict:
        return knowledge_tools.knowledge_search(query=query, top_k=top_k)

    @server.tool(
        name="check_completeness",
        description="Check submitted materials against SmartWater MVP checklist.",
    )
    def check_completeness(materials: list | dict | str | None = None) -> dict:
        return knowledge_tools.check_completeness(materials=materials)

    return server
