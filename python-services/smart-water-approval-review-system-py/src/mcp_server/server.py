from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from src.services.knowledge_tools import SmartWaterKnowledgeTools

_logger = logging.getLogger(__name__)


def build_mcp_server(
    tools: SmartWaterKnowledgeTools | None = None,
    *,
    enable_vector_search: bool = True,
    precompute_json_embeddings: bool = False,
) -> FastMCP:
    if tools is None:
        chroma_store = None
        embedding_client = None
        if enable_vector_search:
            try:
                from src.ingest.chroma_store import ChromaStore

                chroma_store = ChromaStore()
            except Exception as e:
                _logger.info("ChromaStore not available, vector search disabled: %s", e)

            try:
                from src.ingest.embedding_client import EmbeddingClient

                embedding_client = EmbeddingClient()
            except Exception as e:
                _logger.info("EmbeddingClient not available, vector search disabled: %s", e)

        tools = SmartWaterKnowledgeTools(
            chroma_store=chroma_store,
            embedding_client=embedding_client,
            precompute_json_embeddings=precompute_json_embeddings,
        )

    knowledge_tools = tools

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
