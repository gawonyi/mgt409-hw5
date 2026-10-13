"""Append-only audit trail: output/audit_trail.json holds one JSON array that only grows."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from config import AUDIT_PATH, MAX_TOOL_RESULT_CHARS
from models import AuditEvent

_LOCK = threading.Lock()
_SEQ = 0  # in-memory sequence so the board can ask "events after N"
# In-memory feed for the /events route (Problem 7); the file is the permanent record.
RECENT_EVENTS: list[dict[str, Any]] = []
_listeners: list[Callable[[dict[str, Any]], None]] = []


def clip(value: Any, limit: int = 2_000) -> Any:
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    return value if len(text) <= limit else text[:limit] + f"... [truncated {len(text) - limit} chars]"


def add_listener(fn: Callable[[dict[str, Any]], None]) -> None:
    _listeners.append(fn)


def _read_all(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        # Never silently wipe history: refuse instead.
        raise RuntimeError(f"{path} is not a JSON array; fix it by hand, it will not be overwritten.")
    return data


def log(path: Path | None = None, **fields: Any) -> dict[str, Any]:
    """Validate one event and append it. Existing entries are always preserved."""
    fields.setdefault("ts", datetime.now(timezone.utc).isoformat(timespec="milliseconds"))
    event = AuditEvent(**fields).model_dump()
    target = path or AUDIT_PATH
    with _LOCK:
        target.parent.mkdir(parents=True, exist_ok=True)
        entries = _read_all(target)
        entries.append(event)
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(entries, indent=2, default=str), encoding="utf-8")
        os.replace(tmp, target)  # atomic: a crash mid-write cannot lose old entries
        global _SEQ
        _SEQ += 1
        event = {"seq": _SEQ, **event}
        RECENT_EVENTS.append(event)
        del RECENT_EVENTS[:-500]
    for fn in list(_listeners):
        try:
            fn(event)
        except Exception:
            pass
    return event


def truncate_tool_result(content: Any) -> Any:
    return clip(content, MAX_TOOL_RESULT_CHARS)
