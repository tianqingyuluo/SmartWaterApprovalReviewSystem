"""CP2 答辩证据生成脚本：ingest、ChromaDB 验证、MCP 工具演示。"""

from __future__ import annotations

import argparse
import sys

from src.config import config
from src.ingest.chroma_store import ChromaStore
from src.ingest.embedding_client import EmbeddingClient
from src.ingest.ingest_pipeline import IngestPipeline
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

    if stats.errors:
        print(f"\n错误数: {len(stats.errors)}")
        for err in stats.errors:
            print(f"  - {err}")


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


def run_tool_demos() -> None:
    _sep("3. MCP 工具演示")
    tools = SmartWaterKnowledgeTools()
    print(f"知识库版本: {tools.knowledge_pack_version}")

    queries = [
        ("取水许可 办理流程", 3),
        ("填报说明 行业分类", 3),
        ("申请材料", 5),
    ]
    for q, k in queries:
        result = tools.knowledge_search(query=q, top_k=k)
        print(f"\nknowledge_search('{q}', top_k={k})")
        print(f"  匹配数: {result['total']}, topK: {result['topK']}")
        for r in result["results"][:2]:
            print(f"  [{r['section']}] {r['title']} (score={r['score']})")

    materials_cases = [
        ("仅营业执照", ["BUSINESS_LICENSE"]),
        ("仅身份证", ["ID_CARD"]),
        ("全部材料", ["APPLICATION_FORM", "BUSINESS_LICENSE", "ID_CARD"]),
    ]
    for label, mats in materials_cases:
        result = tools.check_completeness(materials=mats)
        print(f"\ncheck_completeness('{label}')")
        print(f"  已提交: {result['submitted']}")
        print(f"  必需:   {result['required']}")
        print(f"  缺失:   {result['missing']}")
        print(f"  完整:   {result['complete']}")


def run_full_evidence(rebuild: bool = True) -> None:
    print("=" * 60)
    print("  SmartWater V1 CP2 知识库答辩证据")
    print("=" * 60)

    _check_config()
    run_ingest(rebuild=rebuild)
    verify_chromadb()
    run_tool_demos()

    _sep("证据生成完成")
    print("以上输出可用于 CP2 答辩材料（截图或复制）。")
    print(f"ChromaDB 持久化目录: {config.CHROMA_PERSIST_DIR}")
    print("可使用以下命令重新运行: python -m src.cp2_evidence")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CP2 答辩证据生成")
    parser.add_argument("--no-rebuild", action="store_true", help="增量 ingest（不清空）")
    args = parser.parse_args(argv)

    run_full_evidence(rebuild=not args.no_rebuild)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
