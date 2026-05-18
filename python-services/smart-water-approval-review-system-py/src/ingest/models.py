from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class DocumentBlock(BaseModel):
    source_file: str
    source_title: str
    content: str
    doc_type: str = ""
    chapter: str = ""
    page_num: int | None = None
    block_index: int = 0


class ChunkResult(BaseModel):
    content: str
    metadata: dict[str, Any]
    embedding: list[float] | None = None


class IngestStats(BaseModel):
    doc_count: int = 0
    block_count: int = 0
    chunk_count: int = 0
    vector_count: int = 0
    sources: list[str] = []
    errors: list[str] = []
