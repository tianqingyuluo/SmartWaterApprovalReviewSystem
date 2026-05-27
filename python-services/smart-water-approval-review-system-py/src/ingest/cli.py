from __future__ import annotations

import argparse
import logging
import sys

from src.ingest.ingest_pipeline import IngestPipeline

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="SmartWater knowledge base ingest")
    parser.add_argument(
        "--source-dir",
        default="",
        help="Path to source documents directory (default: KNOWLEDGE_SOURCE_DIR env)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=512,
        help="Max characters per chunk (default: 512)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=64,
        help="Overlap between chunks (default: 64)",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Clear ChromaDB and re-ingest from scratch",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    pipeline = IngestPipeline(
        source_dir=args.source_dir or None,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        rebuild=args.rebuild,
    )

    stats = pipeline.run()

    print("\n=== Ingest Statistics ===")
    print(f"  Documents found: {stats.doc_count}")
    print(f"  Text blocks:     {stats.block_count}")
    print(f"  Chunks created:  {stats.chunk_count}")
    print(f"  Vectors stored:  {stats.vector_count}")
    print(f"  Sources:         {', '.join(stats.sources) if stats.sources else 'none'}")
    if stats.errors:
        print(f"  Errors:          {len(stats.errors)}")
        for err in stats.errors:
            print(f"    - {err}")

    if stats.errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
