"""Shared helpers for semantic validator handoff continuity read-plane."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable

_SCHEMA_VERSION = "ui_semantic_validator_handoff_continuity/v1"
_LIMIT_MAX = 1000
_STAGES: tuple[tuple[str, str, str], ...] = (
    ("decision", "Decision packet", "/ui/semantic-validator-handoff/decision"),
    ("signoff", "Operator signoff", "/ui/semantic-validator-handoff/signoff"),
    ("custody", "Custody seal", "/ui/semantic-validator-handoff/custody"),
    ("archive", "Archive manifest", "/ui/semantic-validator-handoff/archive"),
    ("closure", "Closure attestation", "/ui/semantic-validator-handoff/closure"),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _s(value: object) -> str:
    return str(value or "").strip()


def _norm(value: object) -> str:
    return _s(value).upper()


def _norm_set(values: tuple[str, ...] | list[str] | None) -> set[str]:
    return {_norm(value) for value in values or () if _s(value)}


def _as_list(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return []


def _counts(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter[_s(row.get(field)) or "UNKNOWN"] += 1
    return dict(sorted(counter.items()))


def _contains(value: object, needle: str | None) -> bool:
    return True if not needle else needle.strip().lower() in str(value or "").lower()


def _authority() -> dict[str, Any]:
    return {
        "mutation_allowed": False,
        "artifact_mutation_allowed": False,
        "validator_submission_allowed": False,
        "adjudication_allowed": False,
        "promotion_allowed": False,
        "execution_allowed": False,
        "authority_boundary": "read_plane_only_no_mutation_no_submission_no_execution",
    }
