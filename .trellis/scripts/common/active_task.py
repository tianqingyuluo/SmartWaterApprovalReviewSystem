#!/usr/bin/env python3
"""Active task resolution shared by Trellis hooks and CLI helpers."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .paths import (
    DIR_WORKFLOW,
    get_current_task,
    normalize_task_ref,
    resolve_task_ref,
)


@dataclass(frozen=True)
class ActiveTask:
    """Resolved active task pointer plus its provenance."""

    task_path: str | None
    source: str
    source_type: str
    stale: bool = False


_CONTEXT_KEY_FIELDS = (
    "session_id",
    "sessionId",
    "conversation_id",
    "conversationId",
    "thread_id",
    "threadId",
    "chat_id",
    "chatId",
    "run_id",
    "runId",
)

_TASK_REF_FIELDS = (
    "trellis_task",
    "trellisTask",
    "active_task",
    "activeTask",
    "current_task",
    "currentTask",
    "task_path",
    "taskPath",
    "task_dir",
    "taskDir",
)


def _string_value(value: Any) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return None


def _nested_value(data: dict[str, Any], fields: tuple[str, ...]) -> str | None:
    for key in fields:
        value = _string_value(data.get(key))
        if value:
            return value

    for container_key in ("session", "conversation", "thread", "chat", "metadata"):
        container = data.get(container_key)
        if isinstance(container, dict):
            value = _nested_value(container, fields)
            if value:
                return value

    return None


def _sanitize_context_key(raw: str, platform: str | None) -> str | None:
    text = re.sub(r"[^A-Za-z0-9_.-]+", "-", raw.strip()).strip("-._")
    if not text:
        return None
    text = text[:120]
    if platform and not text.startswith(f"{platform}-"):
        return f"{platform}-{text}"
    return text


def resolve_context_key(hook_input: dict[str, Any] | None, platform: str | None = None) -> str | None:
    """Return a stable session key from hook input or environment, if available."""

    env_key = _string_value(os.environ.get("TRELLIS_CONTEXT_ID"))
    if env_key:
        return _sanitize_context_key(env_key, platform)

    data = hook_input if isinstance(hook_input, dict) else {}
    raw = _nested_value(data, _CONTEXT_KEY_FIELDS)
    if raw:
        return _sanitize_context_key(raw, platform)

    for env_name in (
        "CODEX_SESSION_ID",
        "CLAUDE_SESSION_ID",
        "CURSOR_SESSION_ID",
        "GEMINI_SESSION_ID",
        "QODER_SESSION_ID",
    ):
        raw = _string_value(os.environ.get(env_name))
        if raw:
            return _sanitize_context_key(raw, platform)

    return None


def _extract_task_ref(value: Any) -> str | None:
    direct = _string_value(value)
    if direct:
        return direct

    if not isinstance(value, dict):
        return None

    for key in (*_TASK_REF_FIELDS, "path", "task", "taskRef"):
        nested = _extract_task_ref(value.get(key))
        if nested:
            return nested

    return None


def _looks_like_task_ref(task_ref: str, repo_root: Path) -> bool:
    normalized = normalize_task_ref(task_ref)
    if not normalized:
        return False

    normalized_posix = normalized.replace("\\", "/")
    if normalized_posix.startswith(f"{DIR_WORKFLOW}/") or normalized_posix.startswith("tasks/"):
        return True
    if Path(normalized).is_absolute():
        return True

    resolved = resolve_task_ref(normalized, repo_root)
    return bool(resolved and (resolved / "task.json").is_file())


def _task_ref_from_input(data: dict[str, Any], repo_root: Path) -> str | None:
    for key in _TASK_REF_FIELDS:
        task_ref = _extract_task_ref(data.get(key))
        if task_ref and _looks_like_task_ref(task_ref, repo_root):
            return task_ref

    for container_key in ("trellis", "session", "metadata"):
        container = data.get(container_key)
        if isinstance(container, dict):
            task_ref = _task_ref_from_input(container, repo_root)
            if task_ref:
                return task_ref

    return None


def _runtime_session_file(repo_root: Path, context_key: str) -> Path:
    return repo_root / DIR_WORKFLOW / ".runtime" / "sessions" / f"{context_key}.json"


def _task_ref_from_session(repo_root: Path, context_key: str | None) -> str | None:
    if not context_key:
        return None

    session_file = _runtime_session_file(repo_root, context_key)
    if not session_file.is_file():
        return None

    try:
        data = json.loads(session_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    if not isinstance(data, dict):
        return None
    return _task_ref_from_input(data, repo_root)


def _to_repo_relative_task_path(task_ref: str, repo_root: Path) -> str:
    normalized = normalize_task_ref(task_ref)
    resolved = resolve_task_ref(normalized, repo_root)
    if resolved is not None:
        try:
            return resolved.relative_to(repo_root).as_posix()
        except ValueError:
            return str(resolved)
    return normalized


def _active_from_ref(
    task_ref: str,
    repo_root: Path,
    source: str,
    source_type: str,
) -> ActiveTask:
    task_path = _to_repo_relative_task_path(task_ref, repo_root)
    resolved = resolve_task_ref(task_path, repo_root)
    stale = resolved is None or not resolved.is_dir()
    return ActiveTask(
        task_path=task_path,
        source=source,
        source_type=source_type,
        stale=stale,
    )


def resolve_active_task(
    repo_root: Path,
    hook_input: dict[str, Any] | None = None,
    platform: str | None = None,
) -> ActiveTask:
    """Resolve the active Trellis task from hook/session state.

    Priority:
    1. Explicit task pointer in hook input.
    2. Session-scoped runtime state keyed by hook/session id.
    3. Local ``.trellis/.current-task`` pointer.
    """

    repo_root = repo_root.resolve()
    data = hook_input if isinstance(hook_input, dict) else {}

    input_ref = _task_ref_from_input(data, repo_root)
    if input_ref:
        return _active_from_ref(input_ref, repo_root, "hook input", "input")

    context_key = resolve_context_key(data, platform)
    session_ref = _task_ref_from_session(repo_root, context_key)
    if session_ref:
        return _active_from_ref(
            session_ref,
            repo_root,
            f".trellis/.runtime/sessions/{context_key}.json",
            "session",
        )

    current_ref = get_current_task(repo_root)
    if current_ref:
        return _active_from_ref(
            current_ref,
            repo_root,
            ".trellis/.current-task",
            "file",
        )

    return ActiveTask(task_path=None, source="none", source_type="none", stale=False)
