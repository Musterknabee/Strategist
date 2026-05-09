"""Shared helpers for semantic validator handoff clearance signoff packet read-plane."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable

_SCHEMA_VERSION = "ui_semantic_validator_handoff_clearance_signoff_packet/v1"
_LIMIT_MAX = 1000
_SIGNOFF_STATUS_RANK = {
    "CLEARANCE_SIGNOFF_PACKET_BLOCKED": 0,
    "CLEARANCE_SIGNOFF_PACKET_WAITING_EXTERNAL_ARTIFACT": 1,
    "CLEARANCE_SIGNOFF_PACKET_WAITING_REFRESH": 2,
    "CLEARANCE_SIGNOFF_PACKET_WAITING_AUTHORIZED_REVIEW": 3,
    "CLEARANCE_SIGNOFF_PACKET_INVESTIGATION_REQUIRED": 4,
    "CLEARANCE_SIGNOFF_PACKET_READY_FOR_HUMAN_SIGNOFF_OBSERVATION": 5,
}
_SIGNOFF_READINESS_RANK = {"FAIL_CLOSED": 0, "WAITING": 1, "SIGNOFF_READY_OBSERVATION": 2}
_PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
_SEVERITY_RANK = {"CRITICAL": 0, "HIGH": 1, "BLOCKED": 1, "WARN": 2, "MEDIUM": 2, "LOW": 3, "INFO": 4}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _s(value: Any) -> str:
    return str(value or "").strip()


def _norm(value: Any) -> str:
    return _s(value).upper()


def _as_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, (list, tuple, set)) else []


def _uniq(values: Iterable[Any]) -> list[str]:
    seen: dict[str, None] = {}
    for value in values:
        text = _s(value)
        if text:
            seen.setdefault(text, None)
    return list(seen)


def _norm_set(values: Iterable[str] | None) -> set[str]:
    return {_norm(value) for value in values or () if _s(value)}


def _contains(value: Any, needle: str | None) -> bool:
    return True if not needle else needle.strip().lower() in str(value or "").lower()


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _counts(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(_s(row.get(field)) or "UNKNOWN" for row in rows).items()))


def _authority() -> dict[str, Any]:
    return {
        "read_plane_only": True,
        "signoff_packet_write_allowed": False,
        "signoff_record_write_allowed": False,
        "signoff_assertion_allowed": False,
        "operator_signoff_allowed": False,
        "operator_approval_allowed": False,
        "review_record_write_allowed": False,
        "review_assertion_allowed": False,
        "review_authorization_allowed": False,
        "closeout_write_allowed": False,
        "closeout_assertion_allowed": False,
        "clearance_decision_allowed": False,
        "verification_write_allowed": False,
        "verification_assertion_allowed": False,
        "completion_assertion_allowed": False,
        "resolution_step_acknowledgment_allowed": False,
        "repair_execution_allowed": False,
        "action_execution_allowed": False,
        "operation_acknowledgment_allowed": False,
        "coverage_assertion_allowed": False,
        "evidence_attestation_allowed": False,
        "evidence_override_allowed": False,
        "external_artifact_write_allowed": False,
        "artifact_mutation_allowed": False,
        "validator_submission_allowed": False,
        "adjudication_allowed": False,
        "promotion_allowed": False,
        "execution_allowed": False,
        "authority_boundary": "read_plane_only_clearance_signoff_packet_visibility_no_packet_write_no_signoff_record_no_operator_signoff_no_approval_no_decision_no_submit_no_execute",
    }
