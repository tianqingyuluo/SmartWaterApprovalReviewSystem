from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from src.config import config
from src.ingest.models import ChunkResult

logger = logging.getLogger(__name__)


class ChromaStore:
    def __init__(self) -> None:
        self._client = self._create_client()
        self._collection_name = config.CHROMA_COLLECTION_NAME

    def store_chunks(
        self,
        chunks: list[ChunkResult],
        embeddings: list[list[float]],
    ) -> int:
        if not chunks or not embeddings:
            logger.warning("No chunks or embeddings to store")
            return 0

        if len(chunks) != len(embeddings):
            raise ValueError(f"Chunk count ({len(chunks)}) != embedding count ({len(embeddings)})")

        collection = self._get_or_create_collection()

        ids: list[str] = []
        metadatas: list[dict[str, Any]] = []
        documents: list[str] = []
        embedding_list: list[list[float]] = []

        for _i, (chunk, emb) in enumerate(zip(chunks, embeddings, strict=True)):
            chunk_id = (
                f"{chunk.metadata.get('source_file', 'unknown')}_"
                f"{chunk.metadata.get('block_index', 0)}_"
                f"{chunk.metadata.get('chunk_index', 0)}"
            )

            meta: dict[str, Any] = {}
            for key in ("source_file", "source_title", "doc_type", "chapter", "page_num", "block_index", "chunk_index"):
                val = chunk.metadata.get(key)
                if val is not None:
                    meta[key] = val

            ids.append(chunk_id)
            metadatas.append(meta)
            documents.append(chunk.content)
            embedding_list.append(emb)

        collection.upsert(
            ids=ids,
            embeddings=embedding_list,
            metadatas=metadatas,
            documents=documents,
        )

        logger.info("Stored %d vectors in collection '%s'", len(ids), self._collection_name)
        return len(ids)

    def query(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        collection = self._get_or_create_collection()

        where = filters or {}

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where or None,
        )

        hits: list[dict[str, Any]] = []
        if results["ids"] and results["documents"]:
            for i in range(len(results["ids"][0])):
                hit = {
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                }
                hits.append(hit)

        return hits

    def count(self) -> int:
        collection = self._get_or_create_collection()
        return int(collection.count())

    def rebuild(self) -> None:
        self.clear_persist_dir()
        self._client = self._create_client()
        logger.info("Rebuilt ChromaDB at: %s", config.CHROMA_PERSIST_DIR)

    @staticmethod
    def clear_persist_dir() -> None:
        persist_dir = Path(config.CHROMA_PERSIST_DIR)
        if persist_dir.exists():
            shutil.rmtree(persist_dir)
            logger.info("Cleared ChromaDB persist directory: %s", persist_dir)

        persist_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _create_client():
        persist_dir = Path(config.CHROMA_PERSIST_DIR)
        persist_dir.mkdir(parents=True, exist_ok=True)
        return chromadb.PersistentClient(
            path=str(persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )

    def _get_or_create_collection(self):
        return self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
