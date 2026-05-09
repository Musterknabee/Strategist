"""Common helpers for paper execution cockpit execution-state projections."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _strings(v: Any) -> list[str]:
    if isinstance(v, list):
        return [str(x) for x in v if x not in (None, "")]
    if v in (None, ""):
        return []
    return [str(v)]


def _as_dict(v: Any) -> dict[str, Any]:
    return v if isinstance(v, dict) else {}


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


__all__ = ["_as_dict", "_mtime", "_safe_read_json", "_strings"]
