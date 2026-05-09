"""Row synthesis and filtering for semantic validator handoff clearance resolution plan read-plane."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_clearance_resolution_plan_common import (
    _PHASE_RANK,
    _PRIORITY_RANK,
    _SCHEMA_VERSION,
    _SEVERITY_RANK,
    _STEP_STATE_RANK,
    _as_list,
    _authority,
    _contains,
    _digest,
    _norm,
    _s,
)


def _phase(action_state: str) -> str:
    return {
        "BLOCKED_ACTION": "BLOCKER_TRIAGE",
        "WAITING_EXTERNAL_ARTIFACT": "EXTERNAL_ARTIFACT_COLLECTION",
        "HUMAN_REVIEW_REQUIRED": "HUMAN_OPERATOR_REVIEW",
        "REFRESH_REQUIRED": "UPSTREAM_EVIDENCE_REFRESH",
        "INVESTIGATION_REQUIRED": "UNKNOWN_STATE_INVESTIGATION",
        "READY_REVIEW_CANDIDATE": "AUTHORIZED_CLEARANCE_REVIEW",
    }.get(action_state, "UNKNOWN_STATE_INVESTIGATION")


def _step_state(phase: str) -> str:
    return {
        "BLOCKER_TRIAGE": "BLOCKED_UNTIL_SOURCE_RECLASSIFIED",
        "EXTERNAL_ARTIFACT_COLLECTION": "WAITING_ON_EXTERNAL_ARTIFACT",
        "HUMAN_OPERATOR_REVIEW": "WAITING_ON_HUMAN_REVIEW",
        "UPSTREAM_EVIDENCE_REFRESH": "WAITING_ON_UPSTREAM_REFRESH",
        "UNKNOWN_STATE_INVESTIGATION": "WAITING_ON_INVESTIGATION",
        "AUTHORIZED_CLEARANCE_REVIEW": "READY_FOR_AUTHORIZED_CLEARANCE_REVIEW",
    }.get(phase, "WAITING_ON_INVESTIGATION")


def _safe_instruction(phase: str, lane: str) -> str:
    if phase == "BLOCKER_TRIAGE":
        return f"Triage {lane} blocker evidence in the source clearance surfaces; this plan does not acknowledge, override, approve, sign off, submit, or execute."
    if phase == "EXTERNAL_ARTIFACT_COLLECTION":
        return f"Create or attach the required {lane} external artifact outside this read-plane, then refresh the clearance evidence matrix and action register."
    if phase == "HUMAN_OPERATOR_REVIEW":
        return f"Review {lane} through the checklist, dossier, and source rows; do not treat this plan as operator approval or clearance."
    if phase == "UPSTREAM_EVIDENCE_REFRESH":
        return f"Refresh upstream semantic-validator handoff evidence for {lane}, then rebuild coverage, operations, action, and resolution projections."
    if phase == "AUTHORIZED_CLEARANCE_REVIEW":
        return f"Use the authorized clearance/signoff path to review {lane}; this projection only indicates that source coverage is visible."
    return f"Investigate {lane} source lineage because the action register could not map it to a known deterministic clearance resolution phase."


def _completion_gate(phase: str) -> str:
    return {
        "BLOCKER_TRIAGE": "blocking_action_no_longer_present_in_clearance_action_register",
        "EXTERNAL_ARTIFACT_COLLECTION": "external_artifact_action_no_longer_present_in_clearance_action_register",
        "HUMAN_OPERATOR_REVIEW": "human_review_action_no_longer_present_or_reclassified_in_clearance_action_register",
        "UPSTREAM_EVIDENCE_REFRESH": "refresh_required_action_no_longer_present_in_clearance_action_register",
        "UNKNOWN_STATE_INVESTIGATION": "unknown_action_state_reclassified_to_known_clearance_phase",
        "AUTHORIZED_CLEARANCE_REVIEW": "authorized_clearance_path_completed_outside_this_projection",
    }.get(phase, "source_clearance_action_resolved_or_reclassified")


def _verification_hint(phase: str) -> str:
    return {
        "BLOCKER_TRIAGE": "Rebuild the clearance action register; BLOCKED_ACTION rows for the same lane must disappear or be reclassified before this step can close.",
        "EXTERNAL_ARTIFACT_COLLECTION": "Rebuild the evidence matrix and action register; the external artifact requirement must no longer be visible for the lane.",
        "HUMAN_OPERATOR_REVIEW": "Refresh checklist and dossier evidence, then rebuild the action register to confirm human-review demand changed state.",
        "UPSTREAM_EVIDENCE_REFRESH": "Re-run upstream handoff projections and confirm visible evidence rows support coverage before any clearance review.",
        "AUTHORIZED_CLEARANCE_REVIEW": "This plan cannot clear or sign off; verify the authorized clearance/signoff surface records the real decision.",
    }.get(phase, "Inspect action row lineage, source operation card, and source coverage card before continuing.")


def _resolution_step(action: dict[str, Any], ordinal: int, source_payload: dict[str, Any]) -> dict[str, Any]:
    lane = _s(action.get("evidence_lane")) or "UNKNOWN"
    action_state = _s(action.get("action_state")) or "INVESTIGATION_REQUIRED"
    phase = _phase(action_state)
    step_state = _step_state(phase)
    step_id = "semantic-validator-handoff-clearance-resolution-step-" + _digest(
        {
            "schema_version": _SCHEMA_VERSION,
            "source_action_id": action.get("action_id"),
            "phase": phase,
            "lane": lane,
            "source_schema_version": source_payload.get("schema_version"),
        }
    )[:20]
    blocks_clearance = phase in {
        "BLOCKER_TRIAGE",
        "EXTERNAL_ARTIFACT_COLLECTION",
        "UPSTREAM_EVIDENCE_REFRESH",
        "UNKNOWN_STATE_INVESTIGATION",
    } or bool(action.get("blocked"))
    return {
        "resolution_step_id": step_id,
        "schema_version": _SCHEMA_VERSION,
        "ordinal": ordinal,
        "phase": phase,
        "phase_rank": _PHASE_RANK.get(phase, 99),
        "step_state": step_state,
        "step_state_rank": _STEP_STATE_RANK.get(step_state, 99),
        "evidence_lane": lane,
        "action_state": action_state,
        "action_type": _s(action.get("action_type")) or "UNKNOWN",
        "operation_state": _s(action.get("operation_state")) or "UNKNOWN",
        "action_group": _s(action.get("action_group")) or "UNKNOWN",
        "coverage_status": _s(action.get("coverage_status")) or "UNKNOWN",
        "coverage_percent": int(action.get("coverage_percent") or 0),
        "source_action_id": action.get("action_id"),
        "source_operation_card_id": action.get("source_operation_card_id"),
        "source_coverage_card_id": action.get("source_coverage_card_id"),
        "row_count": int(action.get("row_count") or 0),
        "priority": _s(action.get("priority")) or "P3",
        "severity": _s(action.get("severity")) or "INFO",
        "trust_banner": _s(action.get("trust_banner")) or "TRUSTED",
        "owner_hint": _s(action.get("owner_hint")) or "human_operator_clearance_owner",
        "owner_hints": _as_list(action.get("owner_hints")),
        "check_ids": _as_list(action.get("check_ids")),
        "issue_codes": _as_list(action.get("issue_codes")),
        "issue_count": int(action.get("issue_count") or len(_as_list(action.get("issue_codes")))),
        "phase_set": _as_list(action.get("phase_set")),
        "experiment_ids": _as_list(action.get("experiment_ids")),
        "continuity_ids": _as_list(action.get("continuity_ids")),
        "audit_packet_ids": _as_list(action.get("audit_packet_ids")),
        "blocks_handoff_clearance": blocks_clearance,
        "requires_external_artifact": bool(action.get("requires_external_artifact")),
        "requires_human_review": bool(action.get("requires_human_review")),
        "ready_for_operator_clearance_review": bool(action.get("ready_for_operator_clearance_review")),
        "operator_action": _s(action.get("operator_action")) or _safe_instruction(phase, lane),
        "safe_instruction": _safe_instruction(phase, lane),
        "completion_gate": _completion_gate(phase),
        "verification_hint": _verification_hint(phase),
        "source_matrix_route": action.get("source_matrix_route") or "/ui/semantic-validator-handoff/clearance-evidence-matrix",
        "coverage_board_route": action.get("coverage_board_route") or "/ui/semantic-validator-handoff/clearance-coverage-board",
        "operations_board_route": action.get("operations_board_route") or "/ui/semantic-validator-handoff/clearance-operations-board",
        "action_register_route": action.get("action_register_route") or "/ui/semantic-validator-handoff/clearance-action-register",
        "resolution_plan_route": "/ui/semantic-validator-handoff/clearance-resolution-plan",
        "source_routes": _as_list(action.get("source_routes")),
        "authority": _authority(),
        "plan_materialization_authority": "none_read_plane",
        "step_acknowledgment_authority": "none_read_plane",
        "repair_execution_authority": "none_read_plane",
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
        "source_action_row": action,
        "summary_line": f"{ordinal}. {lane} · {phase} · {step_state} · priority={_s(action.get('priority')) or 'P3'} · ack=false repair=false approve=false signoff=false submit=false execute=false",
    }


def _sort_step(step: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(step.get("phase_rank") if step.get("phase_rank") is not None else 99),
        int(step.get("step_state_rank") if step.get("step_state_rank") is not None else 99),
        _PRIORITY_RANK.get(_norm(step.get("priority")), 9),
        _SEVERITY_RANK.get(_norm(step.get("severity")), 9),
        _s(step.get("evidence_lane")),
    )


def _haystack(step: dict[str, Any]) -> str:
    keys = (
        "resolution_step_id",
        "source_action_id",
        "phase",
        "step_state",
        "action_state",
        "action_type",
        "evidence_lane",
        "operation_state",
        "action_group",
        "coverage_status",
        "priority",
        "severity",
        "trust_banner",
        "owner_hint",
        "operator_action",
        "safe_instruction",
        "completion_gate",
        "verification_hint",
        "summary_line",
    )
    return "\n".join(
        [_s(step.get(k)) for k in keys]
        + _as_list(step.get("issue_codes"))
        + _as_list(step.get("check_ids"))
        + _as_list(step.get("phase_set"))
        + _as_list(step.get("experiment_ids"))
        + _as_list(step.get("continuity_ids"))
        + _as_list(step.get("audit_packet_ids"))
    )


def _matches(
    step: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    evidence_lane: set[str],
    phase: set[str],
    step_state: set[str],
    action_state: set[str],
    action_type: set[str],
    priority: set[str],
    severity: set[str],
    trust_banner: set[str],
    owner_hint: set[str],
    blocks_handoff_clearance: bool | None,
    requires_external_artifact: bool | None,
    requires_human_review: bool | None,
    ready_for_operator_clearance_review: bool | None,
) -> bool:
    owner_values = {_norm(value) for value in _as_list(step.get("owner_hints"))}
    return (
        _contains("\n".join(_as_list(step.get("experiment_ids"))), experiment_id_contains)
        and _contains(_haystack(step), issue_contains)
        and (not evidence_lane or _norm(step.get("evidence_lane")) in evidence_lane)
        and (not phase or _norm(step.get("phase")) in phase)
        and (not step_state or _norm(step.get("step_state")) in step_state)
        and (not action_state or _norm(step.get("action_state")) in action_state)
        and (not action_type or _norm(step.get("action_type")) in action_type)
        and (not priority or _norm(step.get("priority")) in priority)
        and (not severity or _norm(step.get("severity")) in severity)
        and (not trust_banner or _norm(step.get("trust_banner")) in trust_banner)
        and (not owner_hint or bool(owner_values & owner_hint) or _norm(step.get("owner_hint")) in owner_hint)
        and (blocks_handoff_clearance is None or bool(step.get("blocks_handoff_clearance")) is blocks_handoff_clearance)
        and (requires_external_artifact is None or bool(step.get("requires_external_artifact")) is requires_external_artifact)
        and (requires_human_review is None or bool(step.get("requires_human_review")) is requires_human_review)
        and (ready_for_operator_clearance_review is None or bool(step.get("ready_for_operator_clearance_review")) is ready_for_operator_clearance_review)
    )


def _degraded(source_payload: dict[str, Any], steps: list[dict[str, Any]]) -> list[str]:
    degraded = [f"SOURCE_CLEARANCE_ACTION_REGISTER::{item}" for item in _as_list(source_payload.get("degraded"))]
    if any(step.get("phase") == "BLOCKER_TRIAGE" for step in steps):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RESOLUTION_PLAN_BLOCKER_TRIAGE_PRESENT")
    if any(step.get("phase") == "EXTERNAL_ARTIFACT_COLLECTION" for step in steps):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RESOLUTION_PLAN_EXTERNAL_ARTIFACT_PRESENT")
    if any(step.get("phase") == "UPSTREAM_EVIDENCE_REFRESH" for step in steps):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RESOLUTION_PLAN_REFRESH_REQUIRED")
    if any(step.get("phase") == "UNKNOWN_STATE_INVESTIGATION" for step in steps):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RESOLUTION_PLAN_INVESTIGATION_REQUIRED")
    return sorted(set(degraded))
