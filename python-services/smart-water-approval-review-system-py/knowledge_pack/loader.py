"""Load the static SmartWater MVP regulation knowledge pack."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class KnowledgePackError(ValueError):
    """Raised when a knowledge pack file is missing or structurally invalid."""


REQUIRED_SECTIONS = (
    "version",
    "materialChecklist",
    "applicationFieldRules",
    "reviewBasis",
    "promptSnippets",
    "manualReviewRules",
)


def _default_pack_path() -> Path:
    return Path(__file__).with_name("water_permit_mvp.json")


def load_knowledge_pack(path: str | Path | None = None) -> dict[str, Any]:
    """Load and minimally validate the SmartWater MVP knowledge pack.

    The Worker can pass the returned dict directly into prompt assembly, while
    stricter schema validation can be added when the review pipeline is built.
    """

    pack_path = Path(path) if path is not None else _default_pack_path()
    try:
        data = json.loads(pack_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise KnowledgePackError(f"Knowledge pack not found: {pack_path}") from exc
    except json.JSONDecodeError as exc:
        raise KnowledgePackError(f"Knowledge pack is not valid JSON: {pack_path}") from exc

    missing = [section for section in REQUIRED_SECTIONS if section not in data]
    if missing:
        raise KnowledgePackError(f"Knowledge pack missing section(s): {', '.join(missing)}")

    _validate_basis_refs(data)
    return data


def normalize_knowledge_fragments(pack: dict[str, Any]) -> list[dict[str, str]]:
    """Return adapter-ready fragments with the PR5 snake_case internal shape.

    The PR6 knowledge pack is structured by domain section and uses camelCase
    fields. The review adapter expects flat fragments with stable IDs that the
    model may cite through ``basisRefs``.
    """

    fragments: list[dict[str, str]] = []

    for item in pack.get("reviewBasis", []):
        if not isinstance(item, dict):
            continue
        source_id = str(item.get("id") or "").strip()
        source_title = str(item.get("sourceTitle") or item.get("sourceId") or source_id).strip()
        content = str(item.get("summary") or "").strip()
        if source_id and source_title and content:
            fragments.append({
                "source_id": source_id,
                "source_title": source_title,
                "content": content,
            })

    for item in pack.get("promptSnippets", []):
        if not isinstance(item, dict):
            continue
        source_id = str(item.get("id") or "").strip()
        source_title = str(item.get("kind") or "prompt").strip()
        content = str(item.get("text") or "").strip()
        if source_id and content:
            fragments.append({
                "source_id": source_id,
                "source_title": f"prompt snippet: {source_title}",
                "content": content,
            })

    return fragments


def _validate_basis_refs(pack: dict[str, Any]) -> None:
    basis_ids = {
        item.get("id")
        for item in pack.get("reviewBasis", [])
        if isinstance(item, dict) and item.get("id")
    }

    for section in ("materialChecklist", "applicationFieldRules", "promptSnippets", "manualReviewRules"):
        for item in pack.get(section, []):
            if not isinstance(item, dict):
                continue
            refs = item.get("basisRefs", [])
            if not isinstance(refs, list):
                raise KnowledgePackError(f"Knowledge pack section {section} has non-list basisRefs")
            undefined = sorted(set(refs) - basis_ids)
            if undefined:
                item_id = item.get("id", "<unknown>")
                raise KnowledgePackError(
                    f"Knowledge pack section {section} item {item_id} has undefined basisRefs: {', '.join(undefined)}"
                )
