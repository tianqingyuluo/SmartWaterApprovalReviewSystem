# MCP Python SDK Design Notes

## Decision

Implement the CP2-C MCP server inside `python-services/smart-water-approval-review-system-py` and use the official `mcp` Python SDK `FastMCP` API.

Rationale:

- The service is Python-owned in the V1 checkpoint plan.
- The existing Python service already owns the static SmartWater knowledge pack loader.
- `FastMCP` provides a concise decorator-based server and supports stdio and HTTP transports for local demos.

## MCP Surface

Deliver two tools:

- `knowledge_search(query, top_k=5)`: search the local SmartWater MVP knowledge pack and return structured matches with source IDs, basis refs, section names, and excerpts.
- `check_completeness(materials)`: evaluate submitted material presence against `materialChecklist` and return missing material findings with applicant/reviewer messages and basis refs.

Both tools must return JSON-serializable dictionaries, not free-form text only, so Java/frontend/agent callers can rely on stable fields.

## Project Integration

- Reuse `knowledge_pack.load_knowledge_pack` and existing knowledge pack JSON.
- Keep implementation dependency-injectable and unit-testable without starting a real MCP process.
- Add CLI/demo entry points that can list tools and call the two tool implementations without requiring an MCP client.
- Do not call external OCR, LLM, Java backend, object storage, or network services for CP2-C.

## Verification

Required checks:

- `python -m compileall src main.py knowledge_pack`
- `python -m pytest`
- A local demo command that lists the two tools and prints sample structured results.

