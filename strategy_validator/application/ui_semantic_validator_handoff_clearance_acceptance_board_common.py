"""Shared helpers for semantic validator handoff clearance acceptance board."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable

_SCHEMA_VERSION = "ui_semantic_validator_handoff_clearance_acceptance_board/v1"
_LIMIT_MAX = 1000
_ACCEPTANCE_STATUS_RANK = {"CLEARANCE_ACCEPTANCE_BLOCKED": 0, "CLEARANCE_ACCEPTANCE_WAITING_EXTERNAL_ARTIFACT": 1, "CLEARANCE_ACCEPTANCE_WAITING_REFRESH": 2, "CLEARANCE_ACCEPTANCE_WAITING_AUTHORIZED_REVIEW": 3, "CLEARANCE_ACCEPTANCE_INVESTIGATION_REQUIRED": 4, "CLEARANCE_ACCEPTANCE_READY_FOR_OBSERVATION": 5}
_ACCEPTANCE_READINESS_RANK = {"FAIL_CLOSED": 0, "WAITING": 1, "ACCEPTANCE_READY_OBSERVATION": 2}
_PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
_SEVERITY_RANK = {"CRITICAL": 0, "HIGH": 1, "BLOCKED": 1, "WARN": 2, "MEDIUM": 2, "LOW": 3, "INFO": 4}

def _utc_now() -> str: return datetime.now(timezone.utc).isoformat()
def _s(value: Any) -> str: return str(value or "").strip()
def _norm(value: Any) -> str: return _s(value).upper()
def _as_list(value: Any) -> list[str]: return [str(item) for item in value if str(item).strip()] if isinstance(value, (list, tuple, set)) else []
def _norm_set(values: Iterable[str] | None) -> set[str]: return {_norm(value) for value in values or () if _s(value)}
def _contains(value: Any, needle: str | None) -> bool: return True if not needle else needle.strip().lower() in str(value or "").lower()
def _digest(value: Any) -> str: return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
def _counts(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]: return dict(sorted(Counter(_s(row.get(field)) or "UNKNOWN" for row in rows).items()))
def _authority() -> dict[str, Any]:
    return {"read_plane_only": True, "acceptance_record_write_allowed": False, "acceptance_assertion_allowed": False, "acceptance_authorization_allowed": False, "signoff_packet_write_allowed": False, "signoff_record_write_allowed": False, "signoff_assertion_allowed": False, "operator_signoff_allowed": False, "operator_approval_allowed": False, "clearance_decision_allowed": False, "artifact_mutation_allowed": False, "validator_submission_allowed": False, "adjudication_allowed": False, "promotion_allowed": False, "execution_allowed": False, "authority_boundary": "read_plane_only_clearance_acceptance_visibility_no_acceptance_write_no_signoff_no_approval_no_decision_no_submit_no_execute"}
