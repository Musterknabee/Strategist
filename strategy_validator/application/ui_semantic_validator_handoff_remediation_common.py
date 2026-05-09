"""Shared helpers for semantic validator handoff remediation read-plane."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable

_SCHEMA_VERSION = "ui_semantic_validator_handoff_remediation/v1"
_READY_ACTION = "REVIEW_READY_SEMANTIC_VALIDATOR_HANDOFF_LINEAGE"
_REMEDIATE_ACTION = "EXECUTE_SEMANTIC_VALIDATOR_HANDOFF_REMEDIATION_BEFORE_REVIEW"
_LIMIT_MAX = 1000

_SEVERITY_RANK = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

_COMPONENT_LABELS = {
    "DECISION_LEDGER": "terminal semantic decision ledger",
    "HANDOFF_CERTIFICATE": "release handoff certificate",
    "VALIDATOR_PACKET": "portable validator handoff packet",
    "INGRESS_CERTIFICATE": "validator-ingress certificate",
}

_COMPONENT_FIELDS = {
    "DECISION_LEDGER": "decision_ledger",
    "HANDOFF_CERTIFICATE": "handoff_certificate",
    "VALIDATOR_PACKET": "validator_packet",
    "INGRESS_CERTIFICATE": "ingress_certificate",
}

_STEP_LIBRARY: dict[str, dict[str, str]] = {
    "MISSING_DECISION_LEDGER": {
        "severity": "CRITICAL",
        "target_component": "decision_ledger",
        "operator_action": "RESTORE_TERMINAL_DECISION_LEDGER",
        "repair_hint": "Restore the terminal semantic adjudication release decision ledger for this experiment, or rerun the governed semantic release decision ledger builder from accepted release records.",
        "rationale": "The downstream certificate cannot be trusted without the ledger it claims to certify.",
    },
    "MISSING_HANDOFF_CERTIFICATE": {
        "severity": "CRITICAL",
        "target_component": "handoff_certificate",
        "operator_action": "RESTORE_OR_REGENERATE_RELEASE_HANDOFF_CERTIFICATE",
        "repair_hint": "Regenerate the release handoff certificate from the terminal decision ledger and its accepted records; do not synthesize certificate IDs or checksums by hand.",
        "rationale": "The validator packet must derive from a certified terminal release handoff.",
    },
    "MISSING_VALIDATOR_PACKET": {
        "severity": "HIGH",
        "target_component": "validator_packet",
        "operator_action": "RESTORE_OR_REGENERATE_VALIDATOR_HANDOFF_PACKET",
        "repair_hint": "Regenerate the validator handoff packet from the certificate evidence payload, then re-run packet verification before ingress review.",
        "rationale": "Validator review needs the portable packet, not only the upstream release certificate.",
    },
    "MISSING_INGRESS_CERTIFICATE": {
        "severity": "HIGH",
        "target_component": "ingress_certificate",
        "operator_action": "RESTORE_OR_REGENERATE_INGRESS_CERTIFICATE",
        "repair_hint": "Regenerate the ingress certificate from the verified validator packet with the same ingress policy flags intended for review.",
        "rationale": "Operator review should see explicit ingress readiness instead of inferring it from packet presence.",
    },
    "COMPONENT_BLOCKERS_PRESENT": {
        "severity": "HIGH",
        "target_component": "component_set",
        "operator_action": "RESOLVE_COMPONENT_BLOCKERS",
        "repair_hint": "Open the blocking component summaries and repair the underlying release, packet, or ingress blocker before re-running lineage review.",
        "rationale": "A complete chain is not review-ready when any component advertises blockers.",
    },
    "COMPONENT_SELF_VERIFICATION_ISSUES_PRESENT": {
        "severity": "HIGH",
        "target_component": "component_set",
        "operator_action": "REVERIFY_AND_REGENERATE_FAILED_COMPONENTS",
        "repair_hint": "Inspect component issue codes, regenerate the affected artifact from its canonical upstream input, and verify it before trusting the lineage chain.",
        "rationale": "Lineage continuity cannot override failed component-level verification.",
    },
    "UNVERIFIED_COMPONENTS_PRESENT": {
        "severity": "HIGH",
        "target_component": "component_set",
        "operator_action": "VERIFY_OR_REBUILD_UNVERIFIED_COMPONENTS",
        "repair_hint": "Run the artifact-specific verifier for every unverified component; rebuild components that cannot validate against their checksum payload.",
        "rationale": "A chain with unverified components cannot be handed to an operator as ready evidence.",
    },
    "HANDOFF_NOT_ALLOWED_FOR_ALL_PRESENT_COMPONENTS": {
        "severity": "HIGH",
        "target_component": "component_set",
        "operator_action": "RESTORE_ALLOWED_HANDOFF_STATE",
        "repair_hint": "Review the component summaries and upstream decision state; only regenerate downstream handoff artifacts from components that explicitly allow handoff.",
        "rationale": "The handoff path must remain blocked until every present component allows handoff.",
    },
    "INGRESS_CERTIFICATE_NOT_READY_FOR_VALIDATOR_INGRESS": {
        "severity": "HIGH",
        "target_component": "ingress_certificate",
        "operator_action": "REPAIR_PACKET_INGRESS_PRECONDITIONS",
        "repair_hint": "Inspect ingress certificate blockers, repair packet evidence or policy preconditions, then rebuild the ingress certificate.",
        "rationale": "Validator ingress readiness must be explicitly certified, not inferred.",
    },
}

_LINK_STEP_TEMPLATES: tuple[tuple[str, dict[str, str]], ...] = (
    (
        "ID_LINK_BROKEN",
        {
            "severity": "CRITICAL",
            "target_component": "lineage_link",
            "operator_action": "RESELECT_MATCHING_UPSTREAM_DOWNSTREAM_ARTIFACTS",
            "repair_hint": "Find the artifact whose declared upstream ID matches the downstream reference, or regenerate the downstream artifact from the intended upstream artifact.",
            "rationale": "A downstream artifact points to a different upstream artifact than the one present in the chain.",
        },
    ),
    (
        "PAYLOAD_CHECKSUM_MISMATCH",
        {
            "severity": "CRITICAL",
            "target_component": "lineage_link",
            "operator_action": "REGENERATE_DOWNSTREAM_ARTIFACT_FROM_CANONICAL_UPSTREAM",
            "repair_hint": "Do not edit checksum fields manually. Regenerate the downstream artifact from the canonical upstream payload so the embedded payload checksum is recalculated.",
            "rationale": "The linked artifact ID may match, but the downstream checksum does not bind to the upstream payload currently present.",
        },
    ),
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


def _link_digest(parts: Iterable[object]) -> str:
    payload = json.dumps([str(part or "") for part in parts], sort_keys=True, separators=(",", ":"))
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
