"""Shared helpers for generated single-tenant bundle verification."""
from __future__ import annotations

import re
from pathlib import Path

def _is_safe_bundle_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    candidate = Path(value)
    if candidate.is_absolute():
        return False
    return ".." not in candidate.parts

def _manifest_generated_file_entries(manifest: dict[str, object]) -> dict[str, dict[str, object]]:
    raw_entries = manifest.get("generated_files", [])
    if not isinstance(raw_entries, list):
        return {}
    entries: dict[str, dict[str, object]] = {}
    for item in raw_entries:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        if _is_safe_bundle_relative_path(path):
            entries[str(path)] = item
    return entries

def _is_valid_sha256(value: object) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value))
