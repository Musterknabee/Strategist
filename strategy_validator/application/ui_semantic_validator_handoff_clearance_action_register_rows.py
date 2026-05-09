"""Row synthesis and filtering for clearance action register payloads."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_clearance_action_register_common import (
    _ACTION_STATE_RANK,
    _ACTION_TYPE_RANK,
    _LIMIT_MAX,
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


def _action_state(operation_state: str) -> str:
    return {
        "BLOCKED_CLEARANCE_OPERATION": "BLOCKED_ACTION",
        "EXTERNAL_ARTIFACT_OPERATION": "WAITING_EXTERNAL_ARTIFACT",
        "OPERATOR_REVIEW_OPERATION": "HUMAN_REVIEW_REQUIRED",
        "NO_CLEARANCE_EVIDENCE": "REFRESH_REQUIRED",
        "UNKNOWN_CLEARANCE_OPERATION": "INVESTIGATION_REQUIRED",
        "COVERAGE_OBSERVED_READY": "READY_REVIEW_CANDIDATE",
    }.get(operation_state, "INVESTIGATION_REQUIRED")


def _action_type(action_state: str) -> str:
    return {
        "BLOCKED_ACTION": "TRIAGE_CLEARANCE_BLOCKER",
        "WAITING_EXTERNAL_ARTIFACT": "COLLECT_EXTERNAL_ARTIFACT",
        "HUMAN_REVIEW_REQUIRED": "PERFORM_OPERATOR_REVIEW",
        "REFRESH_REQUIRED": "REFRESH_UPSTREAM_EVIDENCE",
        "INVESTIGATION_REQUIRED": "INVESTIGATE_UNKNOWN_STATE",
        "READY_REVIEW_CANDIDATE": "REVIEW_READY_COVERAGE",
    }.get(action_state, "INVESTIGATE_UNKNOWN_STATE")


def _operator_action(action_state: str, lane: str) -> str:
    if action_state == "BLOCKED_ACTION":
        return f"Triage the blocking clearance evidence for {lane} in the upstream clearance sources."
    if action_state == "WAITING_EXTERNAL_ARTIFACT":
        return f"Collect or attach the missing external artifact for {lane} outside this read-plane, then refresh the clearance evidence matrix."
    if action_state == "HUMAN_REVIEW_REQUIRED":
        return f"Perform human operator review for {lane} using the clearance checklist, dossier, and source rows."
    if action_state == "REFRESH_REQUIRED":
        return f"Refresh the upstream semantic-validator handoff evidence for {lane}; no visible coverage rows support review yet."
    if action_state == "READY_REVIEW_CANDIDATE":
        return f"Review ready coverage for {lane} through the real clearance authority path; this register does not approve or sign off."
    return f"Investigate {lane} because the operation state could not be mapped to a deterministic clearance action."


def _completion_gate(action_state: str) -> str:
    if action_state == "BLOCKED_ACTION":
        return "blocking_source_issue_removed_or_reclassified_by_upstream_clearance_surface"
    if action_state == "WAITING_EXTERNAL_ARTIFACT":
        return "required_external_artifact_visible_in_clearance_evidence_matrix"
    if action_state == "HUMAN_REVIEW_REQUIRED":
        return "human_review_evidence_visible_in_checklist_or_dossier"
    if action_state == "REFRESH_REQUIRED":
        return "upstream_clearance_evidence_rows_visible"
    if action_state == "READY_REVIEW_CANDIDATE":
        return "operator_review_completed_through_authorized_clearance_path"
    return "unknown_state_resolved_to_known_clearance_action"


def _verification_hint(action_state: str) -> str:
    if action_state == "BLOCKED_ACTION":
        return "Rebuild clearance coverage and operations board; blocked count must fall before this action can leave blocked state."
    if action_state == "WAITING_EXTERNAL_ARTIFACT":
        return "Rebuild evidence matrix; external artifact requirement must no longer be visible for the lane."
    if action_state == "HUMAN_REVIEW_REQUIRED":
        return "Inspect source checklist and dossier rows; review evidence must be present before clearance authority evaluates it."
    if action_state == "REFRESH_REQUIRED":
        return "Re-run upstream handoff projections and confirm at least one source evidence row exists."
    if action_state == "READY_REVIEW_CANDIDATE":
        return "Do not treat this as clearance; use the authorized clearance/signoff path for any real decision."
    return "Inspect operation card lineage and source coverage rows before continuing."


def _register_action(card: dict[str, Any], ordinal: int, source_payload: dict[str, Any]) -> dict[str, Any]:
    lane = _s(card.get("evidence_lane")) or "UNKNOWN"
    operation_state = _s(card.get("operation_state")) or "UNKNOWN_CLEARANCE_OPERATION"
    action_state = _action_state(operation_state)
    action_type = _action_type(action_state)
    action_id = "semantic-validator-handoff-clearance-action-" + _digest(
        {
            "schema_version": _SCHEMA_VERSION,
            "source_operation_card_id": card.get("operation_card_id"),
            "lane": lane,
            "operation_state": operation_state,
            "action_state": action_state,
            "source_schema_version": source_payload.get("schema_version"),
        }
    )[:20]
    blocked = action_state == "BLOCKED_ACTION" or bool(card.get("handoff_clearance_blocked"))
    external = action_state == "WAITING_EXTERNAL_ARTIFACT" or bool(card.get("requires_external_artifact"))
    review = action_state in {"HUMAN_REVIEW_REQUIRED", "READY_REVIEW_CANDIDATE"} or bool(card.get("operator_attention_required"))
    return {
        "action_id": action_id,
        "schema_version": _SCHEMA_VERSION,
        "ordinal": ordinal,
        "action_state": action_state,
        "action_state_rank": _ACTION_STATE_RANK.get(action_state, 99),
        "action_type": action_type,
        "action_type_rank": _ACTION_TYPE_RANK.get(action_type, 99),
        "evidence_lane": lane,
        "operation_state": operation_state,
        "action_group": _s(card.get("action_group")) or "UNKNOWN",
        "coverage_status": _s(card.get("coverage_status")) or "UNKNOWN",
        "coverage_percent": int(card.get("coverage_percent") or 0),
        "source_operation_card_id": card.get("operation_card_id"),
        "source_coverage_card_id": card.get("source_coverage_card_id"),
        "row_count": int(card.get("row_count") or 0),
        "priority": _s(card.get("highest_priority")) or "P3",
        "severity": _s(card.get("highest_severity")) or "INFO",
        "trust_banner": _s(card.get("trust_banner")) or "TRUSTED",
        "owner_hint": _s(card.get("owner_hint")) or "human_operator_clearance_owner",
        "owner_hints": _as_list(card.get("owner_hints")),
        "check_ids": _as_list(card.get("check_ids")),
        "issue_codes": _as_list(card.get("issue_codes")),
        "issue_count": int(card.get("issue_count") or len(_as_list(card.get("issue_codes")))),
        "phase_set": _as_list(card.get("phase_set")),
        "experiment_ids": _as_list(card.get("experiment_ids")),
        "continuity_ids": _as_list(card.get("continuity_ids")),
        "audit_packet_ids": _as_list(card.get("audit_packet_ids")),
        "blocked": blocked,
        "requires_external_artifact": external,
        "requires_human_review": review,
        "operator_attention_required": bool(card.get("operator_attention_required")),
        "ready_for_operator_clearance_review": bool(card.get("ready_for_operator_clearance_review")),
        "operator_action": _operator_action(action_state, lane),
        "safe_next_step": _s(card.get("next_safe_action")) or _operator_action(action_state, lane),
        "completion_gate": _completion_gate(action_state),
        "verification_hint": _verification_hint(action_state),
        "source_matrix_route": card.get("source_matrix_route") or "/ui/semantic-validator-handoff/clearance-evidence-matrix",
        "coverage_board_route": card.get("coverage_board_route") or "/ui/semantic-validator-handoff/clearance-coverage-board",
        "operations_board_route": card.get("operations_board_route") or "/ui/semantic-validator-handoff/clearance-operations-board",
        "action_register_route": "/ui/semantic-validator-handoff/clearance-action-register",
        "source_routes": _as_list(card.get("source_routes")),
        "authority": _authority(),
        "action_acknowledgment_authority": "none_read_plane",
        "action_execution_authority": "none_read_plane",
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
        "source_operation_card": card,
        "summary_line": f"{ordinal}. {lane} · {action_state} · {action_type} · priority={_s(card.get('highest_priority')) or 'P3'} · ack=false execute=false approve=false signoff=false submit=false",
    }


def _sort_action(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(row.get("action_state_rank") if row.get("action_state_rank") is not None else 99),
        int(row.get("action_type_rank") if row.get("action_type_rank") is not None else 99),
        _PRIORITY_RANK.get(_norm(row.get("priority")), 9),
        _SEVERITY_RANK.get(_norm(row.get("severity")), 9),
        _s(row.get("evidence_lane")),
    )


def _haystack(row: dict[str, Any]) -> str:
    return "\n".join(
        [
            _s(row.get("action_id")),
            _s(row.get("source_operation_card_id")),
            _s(row.get("action_state")),
            _s(row.get("action_type")),
            _s(row.get("evidence_lane")),
            _s(row.get("operation_state")),
            _s(row.get("action_group")),
            _s(row.get("coverage_status")),
            _s(row.get("priority")),
            _s(row.get("severity")),
            _s(row.get("trust_banner")),
            _s(row.get("owner_hint")),
            _s(row.get("operator_action")),
            _s(row.get("safe_next_step")),
            _s(row.get("completion_gate")),
            _s(row.get("verification_hint")),
            _s(row.get("summary_line")),
        ]
        + _as_list(row.get("issue_codes"))
        + _as_list(row.get("check_ids"))
        + _as_list(row.get("phase_set"))
        + _as_list(row.get("experiment_ids"))
        + _as_list(row.get("continuity_ids"))
        + _as_list(row.get("audit_packet_ids"))
    )


def _matches(
    row: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    evidence_lane: set[str],
    action_state: set[str],
    action_type: set[str],
    operation_state: set[str],
    action_group: set[str],
    priority: set[str],
    severity: set[str],
    trust_banner: set[str],
    owner_hint: set[str],
    blocked: bool | None,
    requires_external_artifact: bool | None,
    requires_human_review: bool | None,
    ready_for_operator_clearance_review: bool | None,
) -> bool:
    haystack = _haystack(row)
    owner_values = {_norm(v) for v in _as_list(row.get("owner_hints"))}
    return (
        _contains("\n".join(_as_list(row.get("experiment_ids"))), experiment_id_contains)
        and _contains(haystack, issue_contains)
        and (not evidence_lane or _norm(row.get("evidence_lane")) in evidence_lane)
        and (not action_state or _norm(row.get("action_state")) in action_state)
        and (not action_type or _norm(row.get("action_type")) in action_type)
        and (not operation_state or _norm(row.get("operation_state")) in operation_state)
        and (not action_group or _norm(row.get("action_group")) in action_group)
        and (not priority or _norm(row.get("priority")) in priority)
        and (not severity or _norm(row.get("severity")) in severity)
        and (not trust_banner or _norm(row.get("trust_banner")) in trust_banner)
        and (not owner_hint or bool(owner_values & owner_hint) or _norm(row.get("owner_hint")) in owner_hint)
        and (blocked is None or bool(row.get("blocked")) is blocked)
        and (requires_external_artifact is None or bool(row.get("requires_external_artifact")) is requires_external_artifact)
        and (requires_human_review is None or bool(row.get("requires_human_review")) is requires_human_review)
        and (ready_for_operator_clearance_review is None or bool(row.get("ready_for_operator_clearance_review")) is ready_for_operator_clearance_review)
    )


def _degraded(source_payload: dict[str, Any], actions: list[dict[str, Any]]) -> list[str]:
    degraded = [f"SOURCE_CLEARANCE_OPERATIONS_BOARD::{item}" for item in _as_list(source_payload.get("degraded"))]
    if any(row.get("action_state") == "BLOCKED_ACTION" for row in actions):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_ACTION_REGISTER_BLOCKED")
    if any(row.get("action_state") == "WAITING_EXTERNAL_ARTIFACT" for row in actions):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_ACTION_REGISTER_WAITING_EXTERNAL_ARTIFACT")
    if any(row.get("action_state") == "REFRESH_REQUIRED" for row in actions):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_ACTION_REGISTER_REFRESH_REQUIRED")
    if any(row.get("action_state") == "INVESTIGATION_REQUIRED" for row in actions):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_ACTION_REGISTER_INVESTIGATION_REQUIRED")
    return sorted(set(degraded))
