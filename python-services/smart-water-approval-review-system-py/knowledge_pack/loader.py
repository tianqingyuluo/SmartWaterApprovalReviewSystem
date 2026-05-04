"""Load the static SmartWater MVP regulation knowledge pack."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class KnowledgePackError(ValueError):
    """Raised when a knowledge pack file is missing or structurally invalid."""


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

    required_sections = (
        "version",
        "materialChecklist",
        "applicationFieldRules",
        "reviewBasis",
        "promptSnippets",
        "manualReviewRules",
    )
    missing = [section for section in required_sections if section not in data]
    if missing:
        raise KnowledgePackError(f"Knowledge pack missing section(s): {', '.join(missing)}")

    return data
