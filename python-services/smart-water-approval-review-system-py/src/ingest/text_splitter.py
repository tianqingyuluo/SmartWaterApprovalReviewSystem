from __future__ import annotations

import logging
import re
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.ingest.models import ChunkResult, DocumentBlock

logger = logging.getLogger(__name__)

STRUCTURE_HEADING_PATTERN = re.compile(
    r"^(第[一二三四五六七八九十百千]+[章节条款]|"
    r"[一二三四五六七八九十]、|"
    r"\d+[.、]|"
    r"【.*?】|"
    r"[A-Z]+[.、])\s*",
    re.MULTILINE,
)


def split_blocks(
    blocks: list[DocumentBlock],
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> list[ChunkResult]:
    chunks: list[ChunkResult] = []

    for block in blocks:
        if block.doc_type == "image":
            continue

        block_chunks = _split_single_block(block, chunk_size, chunk_overlap)
        chunks.extend(block_chunks)

    logger.info("Split %d blocks into %d chunks", len(blocks), len(chunks))
    return chunks


def _split_single_block(
    block: DocumentBlock,
    chunk_size: int,
    chunk_overlap: int,
) -> list[ChunkResult]:
    content = block.content
    if not content.strip():
        return []

    structure_sections = STRUCTURE_HEADING_PATTERN.split(content)
    if len(structure_sections) == 1:
        return _fixed_length_split(block, content, chunk_size, chunk_overlap)

    chunks: list[ChunkResult] = []
    current_segment: str = structure_sections[0] if structure_sections[0] else ""
    current_title: str = ""

    for i in range(1, len(structure_sections), 2):
        heading = structure_sections[i]
        after = structure_sections[i + 1] if i + 1 < len(structure_sections) else ""

        if current_segment.strip():
            sub_chunks = _fixed_length_split(
                block, current_segment.strip(), chunk_size, chunk_overlap, heading=current_title
            )
            chunks.extend(sub_chunks)

        current_title = heading.strip()
        current_segment = heading + after

    if current_segment.strip():
        sub_chunks = _fixed_length_split(
            block, current_segment.strip(), chunk_size, chunk_overlap, heading=current_title
        )
        chunks.extend(sub_chunks)

    return chunks


def _fixed_length_split(
    block: DocumentBlock,
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    heading: str = "",
) -> list[ChunkResult]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "；", "，", " ", ""],
        length_function=len,
    )
    texts = splitter.split_text(text)

    results: list[ChunkResult] = []
    for i, chunk_text in enumerate(texts):
        metadata: dict[str, Any] = {
            "source_file": block.source_file,
            "source_title": block.source_title,
            "doc_type": block.doc_type,
            "chapter": block.chapter or heading,
            "page_num": block.page_num,
            "block_index": block.block_index,
            "chunk_index": i,
        }
        results.append(ChunkResult(content=chunk_text, metadata=metadata))

    return results
