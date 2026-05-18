from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any, cast

from src.mcp_server.server import build_mcp_server
from src.services.knowledge_tools import SmartWaterKnowledgeTools


def _tool_to_dict(item: Any) -> dict[str, Any]:
    if hasattr(item, "model_dump"):
        return cast(dict[str, Any], item.model_dump())
    if isinstance(item, dict):
        return item
    return {
        "name": getattr(item, "name", None),
        "title": getattr(item, "title", None),
        "description": getattr(item, "description", None),
        "inputSchema": getattr(item, "inputSchema", None),
    }


async def list_tools_data() -> list[dict[str, Any]]:
    server = build_mcp_server()
    tools = await server.list_tools()
    return [_tool_to_dict(item) for item in tools]


def run_sample_calls(
    query: str = "取水许可 材料",
    top_k: int = 5,
    sample_materials: Any | None = None,
) -> dict[str, Any]:
    tools = SmartWaterKnowledgeTools()
    materials = sample_materials
    if materials is None:
        materials = ["APPLICATION_FORM", "BUSINESS_LICENSE"]

    search_result = tools.knowledge_search(query=query, top_k=top_k)
    completeness_result = tools.check_completeness(materials=materials)

    return {
        "knowledge_search": search_result,
        "check_completeness": completeness_result,
    }


def run_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SmartWater MCP tools demo")
    parser.add_argument("--list-tools", action="store_true", help="List MCP tools")
    parser.add_argument("--run-samples", action="store_true", help="Run local sample calls")
    parser.add_argument("--query", default="取水许可 材料", help="Sample query for knowledge_search")
    parser.add_argument("--top-k", type=int, default=5, help="Sample top_k for knowledge_search")
    parser.add_argument(
        "--materials-json",
        default="",
        help="JSON value for sample materials (list or dict), e.g. '[\"APPLICATION_FORM\"]'",
    )

    args = parser.parse_args(argv)

    if not args.list_tools and not args.run_samples:
        parser.error("Specify at least one of --list-tools or --run-samples")

    if args.list_tools:
        tools_data = asyncio.run(list_tools_data())
        print(json.dumps({"tools": tools_data}, ensure_ascii=False, indent=2))

    if args.run_samples:
        materials = None
        if args.materials_json:
            materials = json.loads(args.materials_json)
        sample_data = run_sample_calls(query=args.query, top_k=args.top_k, sample_materials=materials)
        print(json.dumps(sample_data, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
