"""Shared helpers for semantic validator handoff evidence-gap read-plane payloads."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable

_SCHEMA_VERSION = "ui_semantic_validator_handoff_evidence_gaps/v1"
_LIMIT_MAX = 1000
_STAGE_RANK: dict[str, int] = {"decision": 1, "signoff": 2, "custody": 3, "archive": 4, "closure": 5}
_PRIORITY_RANK: dict[str, int] = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}


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


def _counts(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter[_s(row.get(field)) or "UNKNOWN"] += 1
    return dict(sorted(counter.items()))


def _contains(value: object, needle: str | None) -> bool:
    return True if not needle else needle.strip().lower() in str(value or "").lower()


def _authority() -> dict[str, Any]:
    return {
        "read_plane_only": True,
        "mutation_allowed": False,
        "external_artifact_write_allowed": False,
        "artifact_mutation_allowed": False,
        "validator_submission_allowed": False,
        "adjudication_allowed": False,
        "promotion_allowed": False,
        "execution_allowed": False,
        "authority_boundary": "read_plane_only_evidence_gap_visibility_no_writes_no_submission_no_execution",
    }


__all__ = [
    "_SCHEMA_VERSION",
    "_LIMIT_MAX",
    "_STAGE_RANK",
    "_PRIORITY_RANK",
    "_utc_now",
    "_s",
    "_norm",
    "_as_list",
    "_norm_set",
    "_counts",
    "_contains",
    "_authority",
]
