from __future__ import annotations

import argparse

from src.mcp_server.server import build_mcp_server


def run_server(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SmartWater MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport mode",
    )
    args = parser.parse_args(argv)

    server = build_mcp_server()
    server.run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_server())
