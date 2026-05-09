"""Shared helpers for the semantic validator handoff action queue read-plane."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable

_SCHEMA_VERSION = "ui_semantic_validator_handoff_action_queue/v1"
_LIMIT_MAX = 1000


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _s(value: Any) -> str:
    return str(value or "").strip()


def _norm(value: Any) -> str:
    return _s(value).upper()


def _as_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    return [str(item) for item in value if str(item).strip()]


def _norm_set(value: Iterable[Any] | None) -> set[str]:
    return {_norm(item) for item in (value or ()) if _s(item)}


def _contains(value: Any, needle: str | None) -> bool:
    return True if not needle else needle.strip().lower() in str(value or "").lower()


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def _counts(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    counter = Counter(_s(row.get(field)) or "UNKNOWN" for row in rows)
    return dict(sorted(counter.items()))


def _authority() -> dict[str, bool | str]:
    return {
        "read_plane_only": True,
        "action_execution_allowed": False,
        "external_artifact_write_allowed": False,
        "artifact_mutation_allowed": False,
        "validator_submission_allowed": False,
        "adjudication_allowed": False,
        "promotion_allowed": False,
        "execution_allowed": False,
        "authority_boundary": "read_plane_only_action_queue_visibility_no_write_no_submit_no_execute",
    }
