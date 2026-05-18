from __future__ import annotations

import logging
from pathlib import Path

from src.config import config
from src.ingest.chroma_store import ChromaStore
from src.ingest.document_parser import list_source_files, parse_file
from src.ingest.embedding_client import EmbeddingClient
from src.ingest.models import ChunkResult, IngestStats
from src.ingest.text_splitter import split_blocks

logger = logging.getLogger(__name__)


class IngestPipeline:
    def __init__(
        self,
        source_dir: str | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        rebuild: bool = False,
    ) -> None:
        self._source_dir = source_dir or config.KNOWLEDGE_SOURCE_DIR
        self._chunk_size = chunk_size or config.CHUNK_SIZE
        self._chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP
        self._rebuild = rebuild

        self._embedder = EmbeddingClient()
        self._store = ChromaStore()

    def run(self) -> IngestStats:
        stats = IngestStats()

        if not self._source_dir:
            stats.errors.append("KNOWLEDGE_SOURCE_DIR not configured")
            logger.error("KNOWLEDGE_SOURCE_DIR not set - cannot run ingest")
            return stats

        source_path = Path(self._source_dir)
        if not source_path.is_dir():
            stats.errors.append(f"Source directory not found: {self._source_dir}")
            logger.error("Source directory not found: %s", self._source_dir)
            return stats

        logger.info("Starting ingest from: %s", self._source_dir)

        if self._rebuild:
            self._store.rebuild()
            logger.info("Rebuild mode: ChromaDB cleared")

        source_files = list_source_files(source_path)
        stats.doc_count = len(source_files)
        stats.sources = [f.name for f in source_files]

        if not source_files:
            logger.warning("No source files found in: %s", self._source_dir)
            return stats

        all_chunks: list[ChunkResult] = []

        for file_path in source_files:
            try:
                blocks = parse_file(file_path)
                stats.block_count += len(blocks)

                chunks = split_blocks(
                    blocks,
                    chunk_size=self._chunk_size,
                    chunk_overlap=self._chunk_overlap,
                )
                all_chunks.extend(chunks)
            except Exception as e:
                error_msg = f"Failed to process {file_path.name}: {e}"
                logger.error(error_msg)
                stats.errors.append(error_msg)

        stats.chunk_count = len(all_chunks)

        if not all_chunks:
            logger.warning("No chunks generated - nothing to embed or store")
            return stats

        chunk_texts = [c.content for c in all_chunks]
        batch_size = 16
        all_embeddings: list[list[float]] = []

        for i in range(0, len(chunk_texts), batch_size):
            batch = chunk_texts[i : i + batch_size]
            try:
                batch_embeddings = self._embedder.embed(batch)
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                error_msg = f"Embedding failed at batch {i // batch_size}: {e}"
                logger.error(error_msg)
                stats.errors.append(error_msg)
                continue

        if not all_embeddings:
            logger.warning("No embeddings generated")
            return stats

        stored = self._store.store_chunks(all_chunks[: len(all_embeddings)], all_embeddings)
        stats.vector_count = stored

        logger.info(
            "Ingest complete: %d docs, %d blocks, %d chunks, %d vectors",
            stats.doc_count,
            stats.block_count,
            stats.chunk_count,
            stats.vector_count,
        )

        return stats
