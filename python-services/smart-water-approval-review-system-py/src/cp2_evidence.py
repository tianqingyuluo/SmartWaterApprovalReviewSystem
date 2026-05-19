"""CP2 答辩证据生成脚本：ingest、ChromaDB 验证、MCP 工具演示。"""

from __future__ import annotations

import argparse
import asyncio
import sys

from src.config import config
from src.ingest.chroma_store import ChromaStore
from src.ingest.embedding_client import EmbeddingClient
from src.ingest.ingest_pipeline import IngestPipeline
from src.mcp_server.server import build_mcp_server
from src.services.knowledge_tools import SmartWaterKnowledgeTools


def _sep(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def _check_config() -> None:
    issues = []
    if not config.KNOWLEDGE_SOURCE_DIR:
        issues.append("KNOWLEDGE_SOURCE_DIR")
    if not config.EMBEDDING_API_KEY:
        issues.append("EMBEDDING_API_KEY")
    if issues:
        print(f"ERROR: 缺少配置: {', '.join(issues)}")
        print("请在 .env 中设置相关环境变量后重试。")
        sys.exit(1)


class IngestError(Exception):
    pass


def run_ingest(rebuild: bool = True) -> None:
    _sep("1. Ingest 知识库构建")
    source_dir = config.KNOWLEDGE_SOURCE_DIR
    print(f"源目录: {source_dir}")
    print(f"ChromaDB 持久化目录: {config.CHROMA_PERSIST_DIR}")
    print(f"Embedding 模型: {config.EMBEDDING_MODEL}")
    print(f"重建模式: {'是' if rebuild else '否'}")

    pipeline = IngestPipeline(
        source_dir=source_dir,
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        rebuild=rebuild,
    )
    stats = pipeline.run()

    print(f"\n文档数:      {stats.doc_count}")
    print(f"文本块数:    {stats.block_count}")
    print(f"Chunk 数:    {stats.chunk_count}")
    print(f"向量条目数:  {stats.vector_count}")
    print(f"文件列表:    {', '.join(stats.sources) if stats.sources else '(无)'}")

    errors = stats.errors
    if errors:
        print(f"\n错误数: {len(errors)}")
        for err in errors:
            print(f"  - {err}")

    if errors or stats.chunk_count == 0 or stats.vector_count == 0:
        raise IngestError(
            f"ingest 未完成 — errors={len(errors)}, chunks={stats.chunk_count}, vectors={stats.vector_count}"
        )


def verify_chromadb() -> None:
    _sep("2. ChromaDB 存储验证")
    store = ChromaStore()
    count = store.count()
    print(f"Collection: {config.CHROMA_COLLECTION_NAME}")
    print(f"向量总数:   {count}")

    if count == 0:
        print("WARNING: ChromaDB 为空，请先运行 ingest。")
        return

    embedder = EmbeddingClient()
    test_queries = ["取水许可", "营业执照", "填报说明", "行业分类"]
    for q in test_queries:
        try:
            emb = embedder.embed([q])[0]
            hits = store.query(emb, top_k=2)
            print(f"\n检索: '{q}'")
            for h in hits:
                doc = h.get("document", "")[:80]
                source = h.get("metadata", {}).get("source_file", "?")
                print(f"  [{source}] {doc}...")
        except Exception as e:
            print(f"检索失败: {e}")


def _list_mcp_tools() -> list[str]:
    server = build_mcp_server()
    tools = asyncio.run(server.list_tools())
    names = []
    for t in tools:
        names.append(getattr(t, "name", str(t)))
    return names


def _call_mcp_tool(name: str, arguments: dict) -> dict:
    async def _call() -> dict:
        server = build_mcp_server()
        result = await server.call_tool(name, arguments)
        content = getattr(result, "content", result)
        if isinstance(content, list):
            for item in content:
                text = getattr(item, "text", None)
                if text:
                    import json

                    return json.loads(text)
        return result

    return asyncio.run(_call())


def run_tool_demos() -> None:
    _sep("3. MCP 工具演示")

    print("MCP Server 工具注册:")
    tool_names = _list_mcp_tools()
    for name in sorted(tool_names):
        print(f"  - {name}")

    tools = SmartWaterKnowledgeTools()
    print(f"\n知识库版本: {tools.knowledge_pack_version}")

    print("\n--- knowledge_search (MCP call_tool) ---")
    queries = {
        "取水许可 办理流程": 3,
        "填报说明 行业分类": 3,
    }
    for q, k in queries.items():
        result = _call_mcp_tool("knowledge_search", {"query": q, "top_k": k})
        print(f"\nknowledge_search('{q}', top_k={k})")
        print(f"  匹配数: {result.get('total', 0)}, topK: {result.get('topK', '?')}")
        for r in result.get("results", [])[:2]:
            print(f"  [{r.get('section', '?')}] {r.get('title', '?')} (score={r.get('score', '?')})")

    print("\n--- check_completeness (MCP call_tool) ---")
    materials_cases = [
        ("仅营业执照", ["BUSINESS_LICENSE"]),
        ("仅身份证", ["ID_CARD"]),
        ("全部材料", ["APPLICATION_FORM", "BUSINESS_LICENSE", "ID_CARD"]),
        ("嵌套 dict-bool", {"APPLICATION_FORM": True, "BUSINESS_LICENSE": True}),
    ]
    for label, mats in materials_cases:
        result = _call_mcp_tool("check_completeness", {"materials": mats})
        print(f"\ncheck_completeness('{label}')")
        print(f"  已提交: {result.get('submitted', '?')}")
        print(f"  必需:   {result.get('required', '?')}")
        print(f"  缺失:   {result.get('missing', '?')}")
        print(f"  完整:   {result.get('complete', '?')}")


def run_full_evidence(rebuild: bool = True) -> int:
    print("=" * 60)
    print("  SmartWater V1 CP2 知识库答辩证据")
    print("=" * 60)

    _check_config()

    try:
        run_ingest(rebuild=rebuild)
    except IngestError as e:
        print(f"\nABORTED: {e}")
        return 1

    verify_chromadb()
    run_tool_demos()

    _sep("证据生成完成")
    print("以上输出可用于 CP2 答辩材料（截图或复制）。")
    print(f"ChromaDB 持久化目录: {config.CHROMA_PERSIST_DIR}")
    print("可使用以下命令重新运行: python -m src.cp2_evidence")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CP2 答辩证据生成")
    parser.add_argument("--no-rebuild", action="store_true", help="增量 ingest（不清空）")
    args = parser.parse_args(argv)

    return run_full_evidence(rebuild=not args.no_rebuild)


if __name__ == "__main__":
    raise SystemExit(main())
