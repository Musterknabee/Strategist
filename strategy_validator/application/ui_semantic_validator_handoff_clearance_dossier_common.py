"""Shared helpers for semantic validator handoff clearance dossier read-plane."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable

_SCHEMA_VERSION = "ui_semantic_validator_handoff_clearance_dossier/v1"
_LIMIT_MAX = 1000
_POSTURE_RANK = {
    "CLEARANCE_BLOCKED": 0,
    "WAITING_EXTERNAL_ARTIFACT": 1,
    "OPERATOR_REVIEW_OBSERVATION": 2,
    "MONITORING_OBSERVATION": 3,
    "OBSERVED_CLEAR_NO_ESCALATIONS": 4,
}
_PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
_SEVERITY_RANK = {"CRITICAL": 0, "HIGH": 1, "BLOCKED": 1, "WARN": 2, "MEDIUM": 2, "LOW": 3, "INFO": 4}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _s(value: Any) -> str:
    return str(value or "").strip()


def _norm(value: Any) -> str:
    return _s(value).upper()


def _as_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return []


def _norm_set(values: Iterable[str] | None) -> set[str]:
    return {_norm(value) for value in (values or ()) if _s(value)}


def _contains(value: Any, needle: str | None) -> bool:
    if not needle:
        return True
    return needle.strip().lower() in str(value or "").lower()


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def _counts(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    counts = Counter(_s(row.get(field)) or "UNKNOWN" for row in rows)
    return dict(sorted(counts.items()))


def _authority() -> dict[str, Any]:
    return {
        "read_plane_only": True,
        "dossier_materialization_allowed": False,
        "clearance_decision_allowed": False,
        "operator_approval_allowed": False,
        "signoff_allowed": False,
        "resolution_step_acknowledgment_allowed": False,
        "repair_execution_allowed": False,
        "external_artifact_write_allowed": False,
        "artifact_mutation_allowed": False,
        "validator_submission_allowed": False,
        "adjudication_allowed": False,
        "promotion_allowed": False,
        "execution_allowed": False,
        "authority_boundary": "read_plane_only_clearance_dossier_visibility_no_approval_no_signoff_no_ack_no_write_no_submit_no_execute",
    }
