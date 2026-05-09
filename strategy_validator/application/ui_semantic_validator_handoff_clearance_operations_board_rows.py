"""Operation-card synthesis and filtering for the clearance operations board read-plane."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_clearance_operations_board_common import (
    _ACTION_GROUP_RANK,
    _LIMIT_MAX,
    _OPERATION_STATE_RANK,
    _PRIORITY_RANK,
    _SCHEMA_VERSION,
    _SEVERITY_RANK,
    _as_list,
    _authority,
    _contains,
    _digest,
    _norm,
    _s,
)

def _operation_state(coverage_status: str) -> str:
    if coverage_status == "BLOCKED_BY_EVIDENCE_GAP":
        return "BLOCKED_CLEARANCE_OPERATION"
    if coverage_status == "WAITING_EXTERNAL_ARTIFACT":
        return "EXTERNAL_ARTIFACT_OPERATION"
    if coverage_status == "NEEDS_OPERATOR_REVIEW":
        return "OPERATOR_REVIEW_OPERATION"
    if coverage_status == "OBSERVED_COVERED":
        return "COVERAGE_OBSERVED_READY"
    if coverage_status == "NO_EVIDENCE_ROWS":
        return "NO_CLEARANCE_EVIDENCE"
    return "UNKNOWN_CLEARANCE_OPERATION"


def _action_group(operation_state: str) -> str:
    return {
        "BLOCKED_CLEARANCE_OPERATION": "TRIAGE_BLOCKERS",
        "EXTERNAL_ARTIFACT_OPERATION": "COLLECT_EXTERNAL_ARTIFACTS",
        "OPERATOR_REVIEW_OPERATION": "OPERATOR_REVIEW",
        "COVERAGE_OBSERVED_READY": "READINESS_REVIEW",
        "NO_CLEARANCE_EVIDENCE": "REFRESH_UPSTREAM_EVIDENCE",
        "UNKNOWN_CLEARANCE_OPERATION": "INVESTIGATE_UNKNOWN",
    }.get(operation_state, "INVESTIGATE_UNKNOWN")


def _next_safe_action(operation_state: str, lane: str) -> str:
    if operation_state == "BLOCKED_CLEARANCE_OPERATION":
        return f"Triage blocker evidence for {lane} in the source clearance surfaces; this operations board cannot resolve, override, approve, sign off, submit, or execute."
    if operation_state == "EXTERNAL_ARTIFACT_OPERATION":
        return f"Collect missing external artifacts for {lane} outside this read-plane, then refresh the clearance evidence matrix and coverage board."
    if operation_state == "OPERATOR_REVIEW_OPERATION":
        return f"Review {lane} attention items through the source checklist and dossier; no acknowledgment or clearance authority exists here."
    if operation_state == "COVERAGE_OBSERVED_READY":
        return f"{lane} is observed covered and can be reviewed through the real clearance authority path; this projection is not approval or signoff."
    if operation_state == "NO_CLEARANCE_EVIDENCE":
        return f"Refresh upstream clearance surfaces for {lane}; no visible evidence rows are available to support an operator review."
    return f"Inspect {lane} source rows and route lineage; this projection could not derive a deterministic clearance operation state."


def _source_row_values(card: dict[str, Any], field: str) -> list[str]:
    rows = card.get("source_evidence_rows")
    if not isinstance(rows, list):
        return []
    return sorted({_s(row.get(field)) for row in rows if isinstance(row, dict) and _s(row.get(field))})


def _operation_card(card: dict[str, Any], ordinal: int, source_payload: dict[str, Any]) -> dict[str, Any]:
    lane = _s(card.get("evidence_lane")) or "UNKNOWN"
    coverage_status = _s(card.get("coverage_status")) or "UNKNOWN"
    state = _operation_state(coverage_status)
    action_group = _action_group(state)
    experiment_ids = _source_row_values(card, "experiment_id")
    continuity_ids = _source_row_values(card, "continuity_id")
    audit_packet_ids = _source_row_values(card, "audit_packet_id")
    operation_card_id = "semantic-validator-handoff-clearance-operation-" + _digest(
        {
            "schema_version": _SCHEMA_VERSION,
            "coverage_card_id": card.get("coverage_card_id"),
            "evidence_lane": lane,
            "coverage_status": coverage_status,
            "operation_state": state,
            "source_schema_version": source_payload.get("schema_version"),
        }
    )[:20]
    attention_required = state != "COVERAGE_OBSERVED_READY"
    blocked = state == "BLOCKED_CLEARANCE_OPERATION"
    requires_external = state == "EXTERNAL_ARTIFACT_OPERATION" or bool(card.get("requires_external_artifact"))
    ready_for_review = state == "COVERAGE_OBSERVED_READY" and not blocked and not requires_external
    return {
        "operation_card_id": operation_card_id,
        "schema_version": _SCHEMA_VERSION,
        "ordinal": ordinal,
        "operation_state": state,
        "operation_state_rank": _OPERATION_STATE_RANK.get(state, 99),
        "action_group": action_group,
        "action_group_rank": _ACTION_GROUP_RANK.get(action_group, 99),
        "evidence_lane": lane,
        "coverage_status": coverage_status,
        "coverage_percent": int(card.get("coverage_percent") or 0),
        "source_coverage_card_id": card.get("coverage_card_id"),
        "row_count": int(card.get("row_count") or 0),
        "attention_required_count": int(card.get("attention_required_count") or 0),
        "blocks_clearance_count": int(card.get("blocks_clearance_count") or 0),
        "requires_external_artifact_count": int(card.get("requires_external_artifact_count") or 0),
        "verified_observation_count": int(card.get("verified_observation_count") or 0),
        "unknown_evidence_count": int(card.get("unknown_evidence_count") or 0),
        "highest_priority": _s(card.get("highest_priority")) or "P3",
        "highest_severity": _s(card.get("highest_severity")) or "INFO",
        "trust_banner": _s(card.get("trust_banner")) or "TRUSTED",
        "owner_hints": _as_list(card.get("owner_hints")),
        "owner_hint": ",".join(_as_list(card.get("owner_hints"))) or "human_operator_clearance_owner",
        "check_ids": _as_list(card.get("check_ids")),
        "issue_codes": _as_list(card.get("issue_codes")),
        "issue_count": int(card.get("issue_count") or len(_as_list(card.get("issue_codes")))),
        "phase_set": _as_list(card.get("phase_set")),
        "source_routes": _as_list(card.get("source_routes")),
        "experiment_ids": experiment_ids,
        "continuity_ids": continuity_ids,
        "audit_packet_ids": audit_packet_ids,
        "operator_attention_required": attention_required,
        "handoff_clearance_blocked": blocked,
        "requires_external_artifact": requires_external,
        "ready_for_operator_clearance_review": ready_for_review,
        "source_matrix_route": card.get("source_matrix_route") or "/ui/semantic-validator-handoff/clearance-evidence-matrix",
        "coverage_board_route": card.get("coverage_board_route") or "/ui/semantic-validator-handoff/clearance-coverage-board",
        "operations_board_route": "/ui/semantic-validator-handoff/clearance-operations-board",
        "next_safe_action": _next_safe_action(state, lane),
        "authority": _authority(),
        "operation_acknowledgment_authority": "none_read_plane",
        "coverage_assertion_authority": "none_read_plane",
        "evidence_attestation_authority": "none_read_plane",
        "evidence_override_authority": "none_read_plane",
        "check_acknowledgment_authority": "none_read_plane",
        "check_override_authority": "none_read_plane",
        "clearance_decision_authority": "none_read_plane",
        "operator_approval_authority": "none_read_plane",
        "signoff_authority": "none_read_plane",
        "external_artifact_write_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "adjudication_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
        "source_coverage_card": card,
        "summary_line": f"{ordinal}. {lane} · {state} · coverage={int(card.get('coverage_percent') or 0)}% · rows={int(card.get('row_count') or 0)} · ack=false approve=false signoff=false submit=false execute=false",
    }


def _sort_card(card: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(card.get("operation_state_rank") if card.get("operation_state_rank") is not None else 99),
        int(card.get("action_group_rank") if card.get("action_group_rank") is not None else 99),
        _PRIORITY_RANK.get(_norm(card.get("highest_priority")), 9),
        _SEVERITY_RANK.get(_norm(card.get("highest_severity")), 9),
        _s(card.get("evidence_lane")),
    )


def _haystack(card: dict[str, Any]) -> str:
    return "\n".join(
        [
            _s(card.get("operation_card_id")),
            _s(card.get("source_coverage_card_id")),
            _s(card.get("operation_state")),
            _s(card.get("action_group")),
            _s(card.get("evidence_lane")),
            _s(card.get("coverage_status")),
            _s(card.get("highest_priority")),
            _s(card.get("highest_severity")),
            _s(card.get("trust_banner")),
            _s(card.get("owner_hint")),
            _s(card.get("next_safe_action")),
            _s(card.get("summary_line")),
        ]
        + _as_list(card.get("check_ids"))
        + _as_list(card.get("issue_codes"))
        + _as_list(card.get("phase_set"))
        + _as_list(card.get("owner_hints"))
        + _as_list(card.get("source_routes"))
        + _as_list(card.get("experiment_ids"))
        + _as_list(card.get("continuity_ids"))
        + _as_list(card.get("audit_packet_ids"))
    )


def _matches(
    card: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    evidence_lane: set[str],
    coverage_status: set[str],
    operation_state: set[str],
    action_group: set[str],
    priority: set[str],
    severity: set[str],
    trust_banner: set[str],
    owner_hint: set[str],
    operator_attention_required: bool | None,
    handoff_clearance_blocked: bool | None,
    requires_external_artifact: bool | None,
    ready_for_operator_clearance_review: bool | None,
) -> bool:
    haystack = _haystack(card)
    owner_values = {_norm(v) for v in _as_list(card.get("owner_hints"))}
    return (
        _contains("\n".join(_as_list(card.get("experiment_ids"))), experiment_id_contains)
        and _contains(haystack, issue_contains)
        and (not evidence_lane or _norm(card.get("evidence_lane")) in evidence_lane)
        and (not coverage_status or _norm(card.get("coverage_status")) in coverage_status)
        and (not operation_state or _norm(card.get("operation_state")) in operation_state)
        and (not action_group or _norm(card.get("action_group")) in action_group)
        and (not priority or _norm(card.get("highest_priority")) in priority)
        and (not severity or _norm(card.get("highest_severity")) in severity)
        and (not trust_banner or _norm(card.get("trust_banner")) in trust_banner)
        and (not owner_hint or bool(owner_values & owner_hint) or _norm(card.get("owner_hint")) in owner_hint)
        and (operator_attention_required is None or bool(card.get("operator_attention_required")) is operator_attention_required)
        and (handoff_clearance_blocked is None or bool(card.get("handoff_clearance_blocked")) is handoff_clearance_blocked)
        and (requires_external_artifact is None or bool(card.get("requires_external_artifact")) is requires_external_artifact)
        and (ready_for_operator_clearance_review is None or bool(card.get("ready_for_operator_clearance_review")) is ready_for_operator_clearance_review)
    )


def _degraded(source_payload: dict[str, Any], cards: list[dict[str, Any]]) -> list[str]:
    degraded = [f"SOURCE_COVERAGE_BOARD::{item}" for item in _as_list(source_payload.get("degraded"))]
    if any(card.get("handoff_clearance_blocked") for card in cards):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_OPERATIONS_BLOCKED")
    if any(card.get("requires_external_artifact") for card in cards):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_OPERATIONS_WAITING_EXTERNAL_ARTIFACT")
    if any(card.get("operation_state") == "NO_CLEARANCE_EVIDENCE" for card in cards):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_OPERATIONS_NO_VISIBLE_EVIDENCE")
    if any(card.get("operation_state") == "UNKNOWN_CLEARANCE_OPERATION" for card in cards):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_OPERATIONS_UNKNOWN_STATE")
    return sorted(set(degraded))

