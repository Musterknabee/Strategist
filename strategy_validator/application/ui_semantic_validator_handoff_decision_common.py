"""Shared helpers for semantic validator handoff decision read-plane."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable

_SCHEMA_VERSION = "ui_semantic_validator_handoff_decision/v1"
_READY_STATUS = "READY_FOR_OPERATOR_DECISION_DRAFT"
_BLOCKED_REMEDIATION_STATUS = "BLOCKED_REMEDIATION_REQUIRED"
_BLOCKED_EVIDENCE_STATUS = "BLOCKED_EVIDENCE_REPAIR_REQUIRED"
_BLOCKED_LINEAGE_STATUS = "BLOCKED_LINEAGE_RECONSTRUCTION_REQUIRED"
_BLOCKED_UNTRUSTED_STATUS = "BLOCKED_UNTRUSTED_EVIDENCE"
_LIMIT_MAX = 1000

_DECISION_PRECONDITIONS: tuple[dict[str, str], ...] = (
    {
        "precondition_id": "review_gate_ready",
        "label": "Review gate is ready",
        "requirement": "source review_status must be READY_FOR_OPERATOR_REVIEW",
    },
    {
        "precondition_id": "trust_banner_trusted",
        "label": "Trust banner is trusted",
        "requirement": "source trust_banner must be TRUSTED",
    },
    {
        "precondition_id": "review_checklist_passed",
        "label": "All review checklist items passed",
        "requirement": "review_pass_count must equal review_check_count and review_block_count must be zero",
    },
    {
        "precondition_id": "no_remediation_steps",
        "label": "No remediation steps remain",
        "requirement": "remediation_step_count must be zero",
    },
    {
        "precondition_id": "authority_boundary_intact",
        "label": "Read-plane authority boundary is intact",
        "requirement": "validator submission, promotion, and execution must all remain false from this surface",
    },
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _s(value: object) -> str:
    return str(value or "").strip()


def _as_list(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return []


def _norm_set(values: tuple[str, ...] | list[str] | None) -> set[str]:
    return {_s(value).upper() for value in values or () if _s(value)}


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


def _authority() -> dict[str, object]:
    return {
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "adjudication_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
    }
