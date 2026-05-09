"""Shared helpers/constants for semantic validator handoff closure read-planes."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

_SCHEMA_VERSION = "ui_semantic_validator_handoff_closure/v1"
_CLOSURE_SCHEMA_VERSION = "semantic_validator_handoff_closure_attestation/v1"
_VERIFIED_ARCHIVE_STATUS = "ARCHIVE_MANIFEST_VERIFIED"
_RECORDED_STATUS = "CLOSURE_ATTESTATION_RECORDED"
_READY_STATUS = "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION"
_INVALID_STATUS = "CLOSURE_ATTESTATION_INVALID"
_DIGEST_MISMATCH_STATUS = "CLOSURE_ATTESTATION_DIGEST_MISMATCH"
_BLOCKED_STATUS = "BLOCKED_ARCHIVE_NOT_VERIFIED"
_PLACEHOLDER_MARKERS = ("<REQUIRED", "<PENDING", "PLACEHOLDER", "TBD", "TODO")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _s(value: object) -> str:
    return str(value or "").strip()

def _norm(value: object) -> str:
    return _s(value).upper()

def _as_list(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return []

def _norm_set(values: tuple[str, ...] | list[str] | None) -> set[str]:
    return {_norm(value) for value in values or () if _s(value)}

def _contains(value: object, needle: str | None) -> bool:
    if not needle:
        return True
    return needle.strip().lower() in str(value or "").lower()

def _counts(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter[_s(row.get(field)) or "UNKNOWN"] += 1
    return dict(sorted(counter.items()))

def _digest(parts: Iterable[object]) -> str:
    payload = json.dumps([part for part in parts], sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None

def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None

def _placeholder(value: object) -> bool:
    text = _norm(value)
    if not text:
        return True
    return any(marker in text for marker in _PLACEHOLDER_MARKERS)

def _authority_assertion_true(raw: dict[str, Any], key: str) -> bool:
    direct = raw.get(key)
    if isinstance(direct, bool):
        return direct
    assertions = raw.get("authority_assertions")
    if isinstance(assertions, dict) and isinstance(assertions.get(key), bool):
        return bool(assertions.get(key))
    return False

def _closure_value(raw: dict[str, Any], *names: str) -> str:
    for name in names:
        value = _s(raw.get(name))
        if value:
            return value
    return ""


__all__ = [
    "_SCHEMA_VERSION",
    "_CLOSURE_SCHEMA_VERSION",
    "_VERIFIED_ARCHIVE_STATUS",
    "_RECORDED_STATUS",
    "_READY_STATUS",
    "_INVALID_STATUS",
    "_DIGEST_MISMATCH_STATUS",
    "_BLOCKED_STATUS",
    "_utc_now",
    "_s",
    "_norm",
    "_as_list",
    "_norm_set",
    "_contains",
    "_counts",
    "_digest",
    "_sha256",
    "_read_json",
    "_placeholder",
    "_authority_assertion_true",
    "_closure_value",
]
