"""Shared helpers for semantic validator handoff review read-plane."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable

_SCHEMA_VERSION = "ui_semantic_validator_handoff_review/v1"
_READY_ACTION = "CONDUCT_OPERATOR_REVIEW_OF_READY_SEMANTIC_VALIDATOR_HANDOFF"
_BLOCKED_ACTION = "COMPLETE_SEMANTIC_VALIDATOR_HANDOFF_REMEDIATION_BEFORE_REVIEW"
_LIMIT_MAX = 1000

_COMPONENT_LABELS = {
    "decision_ledger": "terminal semantic decision ledger",
    "handoff_certificate": "release handoff certificate",
    "validator_packet": "portable validator handoff packet",
    "ingress_certificate": "validator-ingress certificate",
}

_STACKED_CHECKS: tuple[dict[str, str], ...] = (
    {
        "check_id": "component_chain_complete",
        "label": "All four handoff components are present",
        "requirement": "decision ledger, handoff certificate, validator packet, and ingress certificate must all be discoverable",
    },
    {
        "check_id": "lineage_integrity_clear",
        "label": "Artifact IDs and payload checksums form a continuous chain",
        "requirement": "downstream references must match upstream IDs and payload checksums",
    },
    {
        "check_id": "component_verification_clear",
        "label": "Component self-verification has no issues or blockers",
        "requirement": "source component verifiers must not report issue or blocker codes",
    },
    {
        "check_id": "handoff_allowed_clear",
        "label": "Every present component allows handoff",
        "requirement": "component summaries must explicitly keep the handoff path allowed",
    },
    {
        "check_id": "validator_ingress_ready",
        "label": "Ingress certificate marks validator ingress ready",
        "requirement": "ready_for_validator_ingress must be true on the ingress certificate",
    },
    {
        "check_id": "remediation_clear",
        "label": "No remediation action remains before review",
        "requirement": "remediation status must be READY_NO_ACTION with zero repair steps",
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
    payload = json.dumps([str(part or "") for part in parts], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _authority() -> dict[str, str | bool]:
    return {
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "adjudication_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
    }
