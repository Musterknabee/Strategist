"""Artifact discovery for semantic validator handoff read-plane."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from strategy_validator.application.ui_semantic_validator_handoff_common import _KNOWN_SCHEMAS, _read_json
from strategy_validator.application.ui_semantic_validator_handoff_entries import _artifact_entry


def _discover(root: Path, *, include_raw: bool) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    if not root.exists():
        return [], [{"path": str(root.as_posix()), "reason": "search_root_missing"}]
    if not root.is_dir():
        return [], [{"path": str(root.as_posix()), "reason": "search_root_not_directory"}]
    entries: list[dict[str, Any]] = []
    invalid: list[dict[str, str]] = []
    for path in sorted(root.rglob("*.json")):
        raw = _read_json(path)
        if raw is None:
            if "handoff" in path.name.lower() or "validator" in path.name.lower() or "semantic" in path.name.lower():
                invalid.append({"path": str(path.as_posix()), "reason": "invalid_json_or_not_object"})
            continue
        schema = str(raw.get("schema_version") or "")
        if schema not in _KNOWN_SCHEMAS:
            continue
        try:
            entries.append(_artifact_entry(path, raw, include_raw=include_raw))
        except (ValidationError, ValueError) as exc:
            invalid.append({"path": str(path.as_posix()), "reason": f"invalid_semantic_validator_handoff_artifact:{exc.__class__.__name__}"})
    entries.sort(key=lambda item: (str(item.get("experiment_id") or ""), str(item.get("artifact_kind") or ""), str(item.get("artifact_id") or "")), reverse=True)
    return entries, invalid
