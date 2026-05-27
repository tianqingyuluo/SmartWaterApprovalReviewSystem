from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters, stdio_client

from src.config import config
from src.models import ToolCallTrace

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class McpToolCallResult:
    tool_name: str
    input_summary: str
    output_summary: str
    structured_content: dict[str, Any] | None
    content_text: str
    trace: ToolCallTrace


class SmartWaterMcpClient:
    def __init__(
        self,
        command: str | None = None,
        args: list[str] | None = None,
        cwd: str | Path | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self._command = command or config.MCP_SERVER_COMMAND
        self._args = args or config.MCP_SERVER_ARGS
        self._cwd = cwd or config.MCP_SERVER_CWD or config.PROJECT_ROOT
        self._env = env or config.MCP_SERVER_ENV
        self._tool_cache: list[dict[str, Any]] | None = None
        self._traces: list[ToolCallTrace] = []

    async def list_tools(self) -> list[dict[str, Any]]:
        if self._tool_cache is not None:
            return list(self._tool_cache)

        started = time.monotonic()
        try:
            result = await self._call_session(lambda session: session.list_tools())
        except Exception as exc:
            self._record_trace(
                tool_name="list_tools",
                input_summary="discover MCP tools",
                output_summary="",
                status="ERROR",
                started=started,
                error=exc.__class__.__name__,
            )
            raise

        tools = result.tools
        discovered = [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
                "outputSchema": getattr(tool, "outputSchema", None),
            }
            for tool in tools
        ]
        self._tool_cache = discovered
        self._record_trace(
            tool_name="list_tools",
            input_summary="discover MCP tools",
            output_summary=", ".join(tool["name"] for tool in discovered),
            status="SUCCESS",
            started=started,
        )
        return list(discovered)

    async def knowledge_search(self, query: str, top_k: int | str = 5) -> dict[str, Any]:
        return await self._call_tool("knowledge_search", {"query": query, "top_k": top_k})

    async def check_completeness(self, materials: Any) -> dict[str, Any]:
        return await self._call_tool("check_completeness", {"materials": materials})

    async def _call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        await self._ensure_tool_available(name)
        started = time.monotonic()
        input_summary = _summarize_tool_input(arguments)
        try:
            call = await self._call_session(lambda session: session.call_tool(name, arguments))
        except Exception as exc:
            self._record_trace(
                tool_name=name,
                input_summary=input_summary,
                output_summary="",
                status="ERROR",
                started=started,
                error=exc.__class__.__name__,
            )
            raise

        if getattr(call, "isError", False):
            self._record_trace(
                tool_name=name,
                input_summary=input_summary,
                output_summary="MCP tool returned isError=true",
                status="ERROR",
                started=started,
                error="MCP_TOOL_ERROR",
            )
            raise RuntimeError(f"MCP tool {name} returned error")

        structured = getattr(call, "structuredContent", None)
        if isinstance(structured, dict):
            self._record_trace(
                tool_name=name,
                input_summary=input_summary,
                output_summary=_summarize_tool_output(name, structured),
                source_refs=_source_refs(structured),
                status="SUCCESS",
                started=started,
            )
            return structured

        content_text = self._content_text(call)
        if not content_text.strip():
            self._record_trace(
                tool_name=name,
                input_summary=input_summary,
                output_summary="empty MCP content",
                status="ERROR",
                started=started,
                error="EMPTY_CONTENT",
            )
            raise RuntimeError(f"MCP tool {name} returned empty content")

        try:
            parsed = json.loads(content_text)
        except json.JSONDecodeError as exc:
            self._record_trace(
                tool_name=name,
                input_summary=input_summary,
                output_summary="non-JSON MCP content",
                status="ERROR",
                started=started,
                error="NON_JSON_CONTENT",
            )
            raise RuntimeError(f"MCP tool {name} returned non-JSON content") from exc

        if not isinstance(parsed, dict):
            self._record_trace(
                tool_name=name,
                input_summary=input_summary,
                output_summary="unexpected MCP content shape",
                status="ERROR",
                started=started,
                error="UNEXPECTED_CONTENT_SHAPE",
            )
            raise RuntimeError(f"MCP tool {name} returned unexpected content shape")

        self._record_trace(
            tool_name=name,
            input_summary=input_summary,
            output_summary=_summarize_tool_output(name, parsed),
            source_refs=_source_refs(parsed),
            status="SUCCESS",
            started=started,
        )
        return parsed

    async def _ensure_tool_available(self, name: str) -> None:
        tools = await self.list_tools()
        names = {str(tool.get("name") or "") for tool in tools}
        if name not in names:
            raise RuntimeError(f"MCP tool {name} is not available; discovered={sorted(names)}")

    async def _call_session(self, action: Callable[[ClientSession], Coroutine[Any, Any, Any]]) -> Any:
        params = StdioServerParameters(
            command=self._command,
            args=self._args,
            cwd=str(self._cwd),
            env=self._env,
        )
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                return await action(session)

    def list_tools_sync(self) -> list[dict[str, Any]]:
        return _run_sync(self.list_tools())

    def knowledge_search_sync(self, query: str, top_k: int | str = 5) -> dict[str, Any]:
        return _run_sync(self.knowledge_search(query, top_k=top_k))

    def check_completeness_sync(self, materials: Any) -> dict[str, Any]:
        return _run_sync(self.check_completeness(materials))

    def consume_traces(self) -> list[ToolCallTrace]:
        traces = list(self._traces)
        self._traces.clear()
        return traces

    def traces_snapshot(self) -> list[ToolCallTrace]:
        return list(self._traces)

    def _record_trace(
        self,
        tool_name: str,
        input_summary: str,
        output_summary: str,
        status: str,
        started: float,
        source_refs: list[str] | None = None,
        error: str | None = None,
    ) -> None:
        latency_ms = max(0, int((time.monotonic() - started) * 1000))
        trace = ToolCallTrace(
            tool_name=tool_name,
            input_summary=input_summary[:500],
            output_summary=output_summary[:800],
            source_refs=source_refs or [],
            status=status,
            latency_ms=latency_ms,
            error=error,
        )
        self._traces.append(trace)
        if status == "SUCCESS":
            logger.info(
                "MCP tool call succeeded: tool=%s latencyMs=%d summary=%s",
                tool_name,
                latency_ms,
                trace.output_summary,
            )
        else:
            logger.warning(
                "MCP tool call failed: tool=%s latencyMs=%d error=%s",
                tool_name,
                latency_ms,
                error,
            )

    @staticmethod
    def _content_text(call_result: Any) -> str:
        content = getattr(call_result, "content", []) or []
        parts: list[str] = []
        for item in content:
            text = getattr(item, "text", None)
            if text:
                parts.append(str(text))
        return "\n".join(parts)


def _run_sync(coro: Coroutine[Any, Any, Any]) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    coro.close()
    raise RuntimeError("SmartWaterMcpClient synchronous methods cannot run inside an active event loop")


def _summarize_tool_input(arguments: dict[str, Any]) -> str:
    if "query" in arguments:
        query = str(arguments.get("query") or "").strip()
        top_k = arguments.get("top_k")
        return f"query={query[:180]!r}, top_k={top_k}"

    if "materials" in arguments:
        materials = arguments.get("materials")
        if isinstance(materials, list):
            return "materials=" + ",".join(str(item) for item in materials[:20])
        return f"materials={str(materials)[:180]}"

    return json.dumps(arguments, ensure_ascii=False, default=str)[:200]


def _summarize_tool_output(tool_name: str, payload: dict[str, Any]) -> str:
    if tool_name == "knowledge_search":
        ids = [
            str(item.get("id") or item.get("sourceId") or "")
            for item in payload.get("results", [])
            if isinstance(item, dict)
        ]
        ids = [item for item in ids if item]
        return f"total={payload.get('total', len(ids))}, ids={ids[:8]}"

    if tool_name == "check_completeness":
        return (
            f"complete={payload.get('complete')}, "
            f"submitted={payload.get('submitted', [])}, missing={payload.get('missing', [])}"
        )

    if tool_name == "list_tools":
        return json.dumps(payload, ensure_ascii=False, default=str)[:300]

    return json.dumps(payload, ensure_ascii=False, default=str)[:500]


def _source_refs(payload: dict[str, Any]) -> list[str]:
    refs: list[str] = []

    for key in ("basisRefs", "sourceRefs", "sourceIds"):
        value = payload.get(key)
        if isinstance(value, list):
            refs.extend(str(item) for item in value if item)

    results = payload.get("results")
    if isinstance(results, list):
        for item in results:
            if not isinstance(item, dict):
                continue
            for key in ("id", "basisRefs", "sourceRefs", "sourceIds"):
                value = item.get(key)
                if isinstance(value, list):
                    refs.extend(str(ref) for ref in value if ref)
                elif value:
                    refs.append(str(value))

    findings = payload.get("findings")
    if isinstance(findings, list):
        for item in findings:
            if not isinstance(item, dict):
                continue
            for key in ("basisRefs", "sourceRefs"):
                value = item.get(key)
                if isinstance(value, list):
                    refs.extend(str(ref) for ref in value if ref)

    seen: set[str] = set()
    deduped: list[str] = []
    for ref in refs:
        if ref in seen:
            continue
        seen.add(ref)
        deduped.append(ref)
    return deduped[:30]
