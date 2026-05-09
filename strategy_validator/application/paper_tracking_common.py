"""Shared paper-tracking persistence helpers."""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


def _paper_tracking_root(repo_root: Path | None = None) -> Path:
    from strategy_validator.application.research_os_paths import paper_tracking_root_directory

    return paper_tracking_root_directory(repo_root)


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=_json_dt) + "\n", encoding="utf-8")


def _json_dt(o: Any) -> str:
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    raise TypeError(type(o))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


