# SmartWater Python FastAPI + Worker + MCP Tools

## Install

```bash
uv sync
```

## Start Worker

```bash
uv run python main.py
```

## Start FastAPI Review Service

```bash
uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

FastAPI exposes:

- `GET /health`
- `POST /api/review/tasks`
- `GET /api/review/tasks/{aiTaskId}`

If `INTERNAL_API_TOKEN` is configured, the review-task APIs require header `X-Internal-Token: <token>`.

## Start MCP Server

Use official `mcp` Python SDK `FastMCP` with stdio transport:

```bash
uv run python -m src.mcp_server.app --transport stdio
```

Optional transports:

```bash
uv run python -m src.mcp_server.app --transport sse
uv run python -m src.mcp_server.app --transport streamable-http
```

## MCP Tools Demo (No MCP client required)

List registered tools:

```bash
uv run python -m src.mcp_server.demo --list-tools
```

Run sample calls for both tools:

```bash
uv run python -m src.mcp_server.demo --run-samples
```

Run sample calls with custom inputs:

```bash
uv run python -m src.mcp_server.demo --run-samples --query "营业执照" --top-k 3 --materials-json '["APPLICATION_FORM","BUSINESS_LICENSE"]'
```

## Verify

```bash
uv run python -m compileall src main.py knowledge_pack
uv run python -m pytest
```
