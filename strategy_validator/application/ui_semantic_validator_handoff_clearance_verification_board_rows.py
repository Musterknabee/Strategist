"""Row synthesis for semantic validator handoff clearance verification board."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_clearance_verification_board_common import (
    _PRIORITY_RANK,
    _RESULT_RANK,
    _SCHEMA_VERSION,
    _SEVERITY_RANK,
    _STATUS_RANK,
    _as_list,
    _authority,
    _contains,
    _digest,
    _norm,
    _s,
)


def _verification_status(step: dict[str, Any]) -> str:
    phase = _s(step.get("phase"))
    if phase == "BLOCKER_TRIAGE" or bool(step.get("blocks_handoff_clearance")):
        return "BLOCKING_SOURCE_ACTION_VISIBLE"
    if phase == "EXTERNAL_ARTIFACT_COLLECTION" or bool(step.get("requires_external_artifact")):
        return "EXTERNAL_ARTIFACT_STILL_REQUIRED"
    if phase == "UPSTREAM_EVIDENCE_REFRESH":
        return "UPSTREAM_REFRESH_STILL_REQUIRED"
    if phase == "AUTHORIZED_CLEARANCE_REVIEW" or bool(step.get("ready_for_operator_clearance_review")):
        return "READY_FOR_AUTHORIZED_REVIEW_OBSERVED"
    if phase == "HUMAN_OPERATOR_REVIEW" or bool(step.get("requires_human_review")):
        return "HUMAN_REVIEW_STILL_REQUIRED"
    return "INVESTIGATION_STILL_REQUIRED"


def _verification_result(status: str) -> str:
    if status == "BLOCKING_SOURCE_ACTION_VISIBLE":
        return "FAIL_CLOSED"
    if status in {
        "EXTERNAL_ARTIFACT_STILL_REQUIRED",
        "UPSTREAM_REFRESH_STILL_REQUIRED",
        "HUMAN_REVIEW_STILL_REQUIRED",
        "INVESTIGATION_STILL_REQUIRED",
    }:
        return "WAITING"
    return "REVIEW_OBSERVATION"


def _verification_note(status: str, lane: str) -> str:
    if status == "BLOCKING_SOURCE_ACTION_VISIBLE":
        return f"{lane} still has source blocker evidence visible; keep clearance fail-closed until the resolution plan no longer emits this step."
    if status == "EXTERNAL_ARTIFACT_STILL_REQUIRED":
        return f"{lane} still needs an external artifact collected outside this read-plane; refresh the evidence matrix and resolution plan afterward."
    if status == "UPSTREAM_REFRESH_STILL_REQUIRED":
        return f"{lane} still needs upstream evidence refresh outside this projection before any clearance review can rely on it."
    if status == "HUMAN_REVIEW_STILL_REQUIRED":
        return f"{lane} still requires human review via the authorized checklist/dossier path; this board cannot approve or sign off."
    if status == "READY_FOR_AUTHORIZED_REVIEW_OBSERVED":
        return f"{lane} is only observed as ready for authorized review; use the governed clearance/signoff path for any real decision."
    return f"{lane} needs investigation because the resolution plan could not be verified into a known clearance state."


def _verification_gate(status: str) -> str:
    return {
        "BLOCKING_SOURCE_ACTION_VISIBLE": "source_blocker_resolution_step_removed_or_reclassified",
        "EXTERNAL_ARTIFACT_STILL_REQUIRED": "external_artifact_resolution_step_removed_or_reclassified",
        "UPSTREAM_REFRESH_STILL_REQUIRED": "upstream_refresh_resolution_step_removed_or_reclassified",
        "HUMAN_REVIEW_STILL_REQUIRED": "human_review_resolution_step_removed_or_handled_by_authorized_review_path",
        "INVESTIGATION_STILL_REQUIRED": "unknown_resolution_step_reclassified_to_known_clearance_status",
        "READY_FOR_AUTHORIZED_REVIEW_OBSERVED": "authorized_clearance_review_completed_outside_this_read_plane",
    }.get(status, "source_resolution_step_resolved_or_reclassified")


def _card(step: dict[str, Any], ordinal: int, source_payload: dict[str, Any]) -> dict[str, Any]:
    lane = _s(step.get("evidence_lane")) or "UNKNOWN"
    status = _verification_status(step)
    result = _verification_result(status)
    card_id = "semantic-validator-handoff-clearance-verification-card-" + _digest(
        {
            "schema_version": _SCHEMA_VERSION,
            "source_resolution_step_id": step.get("resolution_step_id"),
            "status": status,
            "lane": lane,
            "source_schema_version": source_payload.get("schema_version"),
        }
    )[:20]
    return {
        "verification_card_id": card_id,
        "schema_version": _SCHEMA_VERSION,
        "ordinal": ordinal,
        "verification_status": status,
        "verification_status_rank": _STATUS_RANK.get(status, 99),
        "verification_result": result,
        "verification_result_rank": _RESULT_RANK.get(result, 99),
        "verification_passed": result == "REVIEW_OBSERVATION",
        "evidence_lane": lane,
        "phase": _s(step.get("phase")) or "UNKNOWN",
        "step_state": _s(step.get("step_state")) or "UNKNOWN",
        "action_state": _s(step.get("action_state")) or "UNKNOWN",
        "action_type": _s(step.get("action_type")) or "UNKNOWN",
        "operation_state": _s(step.get("operation_state")) or "UNKNOWN",
        "action_group": _s(step.get("action_group")) or "UNKNOWN",
        "coverage_status": _s(step.get("coverage_status")) or "UNKNOWN",
        "coverage_percent": int(step.get("coverage_percent") or 0),
        "source_resolution_step_id": step.get("resolution_step_id"),
        "source_action_id": step.get("source_action_id"),
        "source_operation_card_id": step.get("source_operation_card_id"),
        "source_coverage_card_id": step.get("source_coverage_card_id"),
        "priority": _s(step.get("priority")) or "P3",
        "severity": _s(step.get("severity")) or "INFO",
        "trust_banner": _s(step.get("trust_banner")) or "TRUSTED",
        "owner_hint": _s(step.get("owner_hint")) or "human_operator_clearance_owner",
        "owner_hints": _as_list(step.get("owner_hints")),
        "check_ids": _as_list(step.get("check_ids")),
        "issue_codes": _as_list(step.get("issue_codes")),
        "issue_count": int(step.get("issue_count") or len(_as_list(step.get("issue_codes")))),
        "phase_set": _as_list(step.get("phase_set")),
        "experiment_ids": _as_list(step.get("experiment_ids")),
        "continuity_ids": _as_list(step.get("continuity_ids")),
        "audit_packet_ids": _as_list(step.get("audit_packet_ids")),
        "blocks_handoff_clearance": bool(step.get("blocks_handoff_clearance")),
        "requires_external_artifact": bool(step.get("requires_external_artifact")),
        "requires_human_review": bool(step.get("requires_human_review")),
        "ready_for_operator_clearance_review": bool(step.get("ready_for_operator_clearance_review")),
        "verification_note": _verification_note(status, lane),
        "verification_gate": _verification_gate(status),
        "source_completion_gate": _s(step.get("completion_gate")),
        "source_verification_hint": _s(step.get("verification_hint")),
        "operator_action": _s(step.get("operator_action")),
        "safe_instruction": _s(step.get("safe_instruction")),
        "source_matrix_route": step.get("source_matrix_route") or "/ui/semantic-validator-handoff/clearance-evidence-matrix",
        "coverage_board_route": step.get("coverage_board_route") or "/ui/semantic-validator-handoff/clearance-coverage-board",
        "operations_board_route": step.get("operations_board_route") or "/ui/semantic-validator-handoff/clearance-operations-board",
        "action_register_route": step.get("action_register_route") or "/ui/semantic-validator-handoff/clearance-action-register",
        "resolution_plan_route": step.get("resolution_plan_route") or "/ui/semantic-validator-handoff/clearance-resolution-plan",
        "verification_board_route": "/ui/semantic-validator-handoff/clearance-verification-board",
        "source_routes": _as_list(step.get("source_routes")),
        "authority": _authority(),
        "verification_write_authority": "none_read_plane",
        "verification_assertion_authority": "none_read_plane",
        "completion_assertion_authority": "none_read_plane",
        "resolution_step_acknowledgment_authority": "none_read_plane",
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
        "source_resolution_step": step,
        "summary_line": f"{ordinal}. {lane} · {status} · {result} · priority={_s(step.get('priority')) or 'P3'} · verify_write=false completion_assert=false approve=false signoff=false submit=false execute=false",
    }


def _sort_card(card: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(card.get("verification_status_rank") if card.get("verification_status_rank") is not None else 99),
        int(card.get("verification_result_rank") if card.get("verification_result_rank") is not None else 99),
        _PRIORITY_RANK.get(_norm(card.get("priority")), 9),
        _SEVERITY_RANK.get(_norm(card.get("severity")), 9),
        _s(card.get("evidence_lane")),
    )


def _haystack(card: dict[str, Any]) -> str:
    keys = (
        "verification_card_id",
        "source_resolution_step_id",
        "verification_status",
        "verification_result",
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
        "verification_note",
        "verification_gate",
        "source_completion_gate",
        "source_verification_hint",
        "summary_line",
    )
    return "\n".join(
        [_s(card.get(k)) for k in keys]
        + _as_list(card.get("issue_codes"))
        + _as_list(card.get("check_ids"))
        + _as_list(card.get("phase_set"))
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
    verification_status: set[str],
    verification_result: set[str],
    phase: set[str],
    step_state: set[str],
    action_state: set[str],
    priority: set[str],
    severity: set[str],
    trust_banner: set[str],
    owner_hint: set[str],
    blocks_handoff_clearance: bool | None,
    requires_external_artifact: bool | None,
    requires_human_review: bool | None,
    ready_for_operator_clearance_review: bool | None,
    verification_passed: bool | None,
) -> bool:
    owner_values = {_norm(value) for value in _as_list(card.get("owner_hints"))}
    return (
        _contains("\n".join(_as_list(card.get("experiment_ids"))), experiment_id_contains)
        and _contains(_haystack(card), issue_contains)
        and (not evidence_lane or _norm(card.get("evidence_lane")) in evidence_lane)
        and (not verification_status or _norm(card.get("verification_status")) in verification_status)
        and (not verification_result or _norm(card.get("verification_result")) in verification_result)
        and (not phase or _norm(card.get("phase")) in phase)
        and (not step_state or _norm(card.get("step_state")) in step_state)
        and (not action_state or _norm(card.get("action_state")) in action_state)
        and (not priority or _norm(card.get("priority")) in priority)
        and (not severity or _norm(card.get("severity")) in severity)
        and (not trust_banner or _norm(card.get("trust_banner")) in trust_banner)
        and (not owner_hint or bool(owner_values & owner_hint) or _norm(card.get("owner_hint")) in owner_hint)
        and (blocks_handoff_clearance is None or bool(card.get("blocks_handoff_clearance")) is blocks_handoff_clearance)
        and (requires_external_artifact is None or bool(card.get("requires_external_artifact")) is requires_external_artifact)
        and (requires_human_review is None or bool(card.get("requires_human_review")) is requires_human_review)
        and (
            ready_for_operator_clearance_review is None
            or bool(card.get("ready_for_operator_clearance_review")) is ready_for_operator_clearance_review
        )
        and (verification_passed is None or bool(card.get("verification_passed")) is verification_passed)
    )


def _degraded(source_payload: dict[str, Any], cards: list[dict[str, Any]]) -> list[str]:
    degraded = [f"SOURCE_CLEARANCE_RESOLUTION_PLAN::{item}" for item in _as_list(source_payload.get("degraded"))]
    if any(card.get("verification_result") == "FAIL_CLOSED" for card in cards):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_VERIFICATION_FAIL_CLOSED_PRESENT")
    if any(card.get("verification_status") == "EXTERNAL_ARTIFACT_STILL_REQUIRED" for card in cards):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_VERIFICATION_EXTERNAL_ARTIFACT_STILL_REQUIRED")
    if any(card.get("verification_status") == "UPSTREAM_REFRESH_STILL_REQUIRED" for card in cards):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_VERIFICATION_UPSTREAM_REFRESH_STILL_REQUIRED")
    if any(card.get("verification_status") == "INVESTIGATION_STILL_REQUIRED" for card in cards):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_VERIFICATION_INVESTIGATION_STILL_REQUIRED")
    return sorted(set(degraded))
