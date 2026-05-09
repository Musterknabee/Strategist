"""Row synthesis for semantic validator handoff clearance signoff packet."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_clearance_signoff_packet_common import (
    _PRIORITY_RANK,
    _SCHEMA_VERSION,
    _SEVERITY_RANK,
    _SIGNOFF_READINESS_RANK,
    _SIGNOFF_STATUS_RANK,
    _as_list,
    _authority,
    _contains,
    _digest,
    _norm,
    _s,
)

def _signoff_status(row: dict[str, Any]) -> str:
    status = _s(row.get("docket_status"))
    readiness = _s(row.get("docket_readiness"))
    if readiness == "FAIL_CLOSED" or status == "CLEARANCE_REVIEW_DOCKET_BLOCKED" or row.get("blocked"):
        return "CLEARANCE_SIGNOFF_PACKET_BLOCKED"
    if status == "CLEARANCE_REVIEW_DOCKET_WAITING_EXTERNAL_ARTIFACT":
        return "CLEARANCE_SIGNOFF_PACKET_WAITING_EXTERNAL_ARTIFACT"
    if status == "CLEARANCE_REVIEW_DOCKET_WAITING_REFRESH":
        return "CLEARANCE_SIGNOFF_PACKET_WAITING_REFRESH"
    if status == "CLEARANCE_REVIEW_DOCKET_WAITING_HUMAN_REVIEW":
        return "CLEARANCE_SIGNOFF_PACKET_WAITING_AUTHORIZED_REVIEW"
    if status == "CLEARANCE_REVIEW_DOCKET_READY_FOR_AUTHORIZED_REVIEW" or row.get("ready_for_authorized_review"):
        return "CLEARANCE_SIGNOFF_PACKET_READY_FOR_HUMAN_SIGNOFF_OBSERVATION"
    return "CLEARANCE_SIGNOFF_PACKET_INVESTIGATION_REQUIRED"


def _signoff_readiness(status: str) -> str:
    if status == "CLEARANCE_SIGNOFF_PACKET_BLOCKED":
        return "FAIL_CLOSED"
    if status == "CLEARANCE_SIGNOFF_PACKET_READY_FOR_HUMAN_SIGNOFF_OBSERVATION":
        return "SIGNOFF_READY_OBSERVATION"
    return "WAITING"


def _signoff_gate(status: str) -> str:
    return {
        "CLEARANCE_SIGNOFF_PACKET_BLOCKED": "source_review_docket_stops_clearance_signoff_packet_routing",
        "CLEARANCE_SIGNOFF_PACKET_WAITING_EXTERNAL_ARTIFACT": "external_artifacts_present_before_signoff_packet_review",
        "CLEARANCE_SIGNOFF_PACKET_WAITING_REFRESH": "upstream_clearance_chain_refreshed_before_signoff_packet_review",
        "CLEARANCE_SIGNOFF_PACKET_WAITING_AUTHORIZED_REVIEW": "authorized_review_completed_outside_this_read_plane_before_signoff",
        "CLEARANCE_SIGNOFF_PACKET_INVESTIGATION_REQUIRED": "review_docket_status_reclassified_to_known_signoff_terminal_state",
        "CLEARANCE_SIGNOFF_PACKET_READY_FOR_HUMAN_SIGNOFF_OBSERVATION": "authorized_human_signoff_may_review_source_evidence_outside_this_read_plane",
    }.get(status, "source_review_docket_resolved_or_reclassified")


def _signoff_instruction(status: str, lane: str) -> str:
    if status == "CLEARANCE_SIGNOFF_PACKET_BLOCKED":
        return f"{lane} remains fail-closed in the review docket; do not prepare or assert clearance signoff until upstream blockers are resolved."
    if status == "CLEARANCE_SIGNOFF_PACKET_WAITING_EXTERNAL_ARTIFACT":
        return f"{lane} is waiting on external artifacts; governed artifact evidence must arrive before signoff review."
    if status == "CLEARANCE_SIGNOFF_PACKET_WAITING_REFRESH":
        return f"{lane} needs an upstream clearance refresh before any signoff packet can be trusted."
    if status == "CLEARANCE_SIGNOFF_PACKET_WAITING_AUTHORIZED_REVIEW":
        return f"{lane} still requires authorized human review before human signoff can be considered."
    if status == "CLEARANCE_SIGNOFF_PACKET_READY_FOR_HUMAN_SIGNOFF_OBSERVATION":
        return f"{lane} is only observed as ready for human signoff review; this read-plane writes no signoff packet, approval, decision, or record."
    return f"{lane} requires investigation because the review docket is not classified enough for signoff packet routing."


def _packet_from_docket(row: dict[str, Any], ordinal: int, source_payload: dict[str, Any]) -> dict[str, Any]:
    status = _signoff_status(row)
    readiness = _signoff_readiness(status)
    lane = _s(row.get("evidence_lane")) or "UNKNOWN"
    packet_id = "semantic-validator-handoff-clearance-signoff-packet-" + _digest(
        {
            "schema_version": _SCHEMA_VERSION,
            "source_schema_version": source_payload.get("schema_version"),
            "source_review_docket_id": row.get("review_docket_id"),
            "lane": lane,
            "status": status,
        }
    )[:20]
    return {
        "signoff_packet_id": packet_id,
        "schema_version": _SCHEMA_VERSION,
        "ordinal": ordinal,
        "evidence_lane": lane,
        "signoff_status": status,
        "signoff_status_rank": _SIGNOFF_STATUS_RANK.get(status, 99),
        "signoff_readiness": readiness,
        "signoff_readiness_rank": _SIGNOFF_READINESS_RANK.get(readiness, 99),
        "ready_for_human_signoff_observation": status == "CLEARANCE_SIGNOFF_PACKET_READY_FOR_HUMAN_SIGNOFF_OBSERVATION",
        "blocked": readiness == "FAIL_CLOSED",
        "waiting": readiness == "WAITING",
        "requires_authorized_review": status == "CLEARANCE_SIGNOFF_PACKET_WAITING_AUTHORIZED_REVIEW",
        "requires_external_artifact": status == "CLEARANCE_SIGNOFF_PACKET_WAITING_EXTERNAL_ARTIFACT",
        "source_review_docket_id": row.get("review_docket_id"),
        "source_docket_status": row.get("docket_status"),
        "source_docket_readiness": row.get("docket_readiness"),
        "source_review_gate": row.get("review_gate"),
        "source_review_instruction": row.get("review_instruction"),
        "source_closeout_card_id": row.get("source_closeout_card_id"),
        "source_closeout_status": row.get("source_closeout_status"),
        "source_closeout_readiness": row.get("source_closeout_readiness"),
        "source_closeout_gate": row.get("source_closeout_gate"),
        "source_verification_card_ids": _as_list(row.get("source_verification_card_ids")),
        "source_resolution_step_ids": _as_list(row.get("source_resolution_step_ids")),
        "source_action_ids": _as_list(row.get("source_action_ids")),
        "source_operation_card_ids": _as_list(row.get("source_operation_card_ids")),
        "source_coverage_card_ids": _as_list(row.get("source_coverage_card_ids")),
        "verification_card_count": int(row.get("verification_card_count") or 0),
        "verification_statuses": _as_list(row.get("verification_statuses")),
        "verification_results": _as_list(row.get("verification_results")),
        "phases": _as_list(row.get("phases")),
        "priority": _s(row.get("priority")) or "P3",
        "severity": _s(row.get("severity")) or "INFO",
        "trust_banner": "TRUST_RESTRICTED" if readiness != "SIGNOFF_READY_OBSERVATION" else _s(row.get("trust_banner")) or "TRUSTED",
        "owner_hint": _s(row.get("owner_hint")) or "human_operator_clearance_owner",
        "owner_hints": _as_list(row.get("owner_hints")) or [_s(row.get("owner_hint")) or "human_operator_clearance_owner"],
        "check_ids": _as_list(row.get("check_ids")),
        "issue_codes": _as_list(row.get("issue_codes")),
        "issue_count": len(_as_list(row.get("issue_codes"))),
        "experiment_ids": _as_list(row.get("experiment_ids")),
        "continuity_ids": _as_list(row.get("continuity_ids")),
        "audit_packet_ids": _as_list(row.get("audit_packet_ids")),
        "blocks_handoff_clearance_count": int(row.get("blocks_handoff_clearance_count") or 0),
        "requires_external_artifact_count": int(row.get("requires_external_artifact_count") or 0),
        "requires_human_review_count": int(row.get("requires_human_review_count") or 0),
        "verification_passed_count": int(row.get("verification_passed_count") or 0),
        "signoff_gate": _signoff_gate(status),
        "signoff_instruction": _signoff_instruction(status, lane),
        "recommended_operator_path": "governed_human_signoff_path_only" if readiness == "SIGNOFF_READY_OBSERVATION" else "return_to_clearance_review_docket_before_signoff_packet_review",
        "clearance_signoff_packet_route": "/ui/semantic-validator-handoff/clearance-signoff-packet",
        "clearance_review_docket_route": "/ui/semantic-validator-handoff/clearance-review-docket",
        "clearance_closeout_board_route": "/ui/semantic-validator-handoff/clearance-closeout-board",
        "verification_board_route": "/ui/semantic-validator-handoff/clearance-verification-board",
        "resolution_plan_route": "/ui/semantic-validator-handoff/clearance-resolution-plan",
        "action_register_route": "/ui/semantic-validator-handoff/clearance-action-register",
        "operations_board_route": "/ui/semantic-validator-handoff/clearance-operations-board",
        "coverage_board_route": "/ui/semantic-validator-handoff/clearance-coverage-board",
        "evidence_matrix_route": "/ui/semantic-validator-handoff/clearance-evidence-matrix",
        "authority": _authority(),
        "signoff_packet_write_authority": "none_read_plane",
        "signoff_record_write_authority": "none_read_plane",
        "signoff_assertion_authority": "none_read_plane",
        "operator_signoff_authority": "none_read_plane",
        "operator_approval_authority": "none_read_plane",
        "review_record_write_authority": "none_read_plane",
        "review_assertion_authority": "none_read_plane",
        "review_authorization_authority": "none_read_plane",
        "closeout_write_authority": "none_read_plane",
        "closeout_assertion_authority": "none_read_plane",
        "clearance_decision_authority": "none_read_plane",
        "verification_write_authority": "none_read_plane",
        "verification_assertion_authority": "none_read_plane",
        "completion_assertion_authority": "none_read_plane",
        "repair_execution_authority": "none_read_plane",
        "action_execution_authority": "none_read_plane",
        "external_artifact_write_authority": "none_read_plane",
        "artifact_mutation_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "adjudication_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
        "source_review_docket": row,
        "summary_line": f"{ordinal}. {lane} · {status} · {readiness} · packet_write=false signoff=false approve=false decide=false submit=false execute=false",
    }


def _sort_packet(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(row.get("signoff_status_rank") if row.get("signoff_status_rank") is not None else 99),
        int(row.get("signoff_readiness_rank") if row.get("signoff_readiness_rank") is not None else 99),
        _PRIORITY_RANK.get(_norm(row.get("priority")), 9),
        _SEVERITY_RANK.get(_norm(row.get("severity")), 9),
        _s(row.get("evidence_lane")),
    )


def _haystack(row: dict[str, Any]) -> str:
    keys = (
        "signoff_packet_id",
        "evidence_lane",
        "signoff_status",
        "signoff_readiness",
        "source_docket_status",
        "source_docket_readiness",
        "source_closeout_status",
        "priority",
        "severity",
        "trust_banner",
        "owner_hint",
        "signoff_gate",
        "signoff_instruction",
        "recommended_operator_path",
        "summary_line",
    )
    return "\n".join(
        [_s(row.get(key)) for key in keys]
        + _as_list(row.get("issue_codes"))
        + _as_list(row.get("check_ids"))
        + _as_list(row.get("experiment_ids"))
        + _as_list(row.get("verification_statuses"))
        + _as_list(row.get("verification_results"))
        + _as_list(row.get("phases"))
    )


def _matches(
    row: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    evidence_lane: set[str],
    signoff_status: set[str],
    signoff_readiness: set[str],
    docket_status: set[str],
    docket_readiness: set[str],
    closeout_status: set[str],
    priority: set[str],
    severity: set[str],
    trust_banner: set[str],
    owner_hint: set[str],
    ready_for_human_signoff_observation: bool | None,
    blocked: bool | None,
    waiting: bool | None,
    requires_authorized_review: bool | None,
    requires_external_artifact: bool | None,
) -> bool:
    owner_values = {_norm(value) for value in _as_list(row.get("owner_hints"))}
    return (
        _contains("\n".join(_as_list(row.get("experiment_ids"))), experiment_id_contains)
        and _contains(_haystack(row), issue_contains)
        and (not evidence_lane or _norm(row.get("evidence_lane")) in evidence_lane)
        and (not signoff_status or _norm(row.get("signoff_status")) in signoff_status)
        and (not signoff_readiness or _norm(row.get("signoff_readiness")) in signoff_readiness)
        and (not docket_status or _norm(row.get("source_docket_status")) in docket_status)
        and (not docket_readiness or _norm(row.get("source_docket_readiness")) in docket_readiness)
        and (not closeout_status or _norm(row.get("source_closeout_status")) in closeout_status)
        and (not priority or _norm(row.get("priority")) in priority)
        and (not severity or _norm(row.get("severity")) in severity)
        and (not trust_banner or _norm(row.get("trust_banner")) in trust_banner)
        and (not owner_hint or bool(owner_values & owner_hint) or _norm(row.get("owner_hint")) in owner_hint)
        and (ready_for_human_signoff_observation is None or bool(row.get("ready_for_human_signoff_observation")) is ready_for_human_signoff_observation)
        and (blocked is None or bool(row.get("blocked")) is blocked)
        and (waiting is None or bool(row.get("waiting")) is waiting)
        and (requires_authorized_review is None or bool(row.get("requires_authorized_review")) is requires_authorized_review)
        and (requires_external_artifact is None or bool(row.get("requires_external_artifact")) is requires_external_artifact)
    )


def _degraded(source_payload: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    degraded = [f"SOURCE_CLEARANCE_REVIEW_DOCKET::{item}" for item in _as_list(source_payload.get("degraded"))]
    if any(row.get("signoff_readiness") == "FAIL_CLOSED" for row in rows):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_SIGNOFF_PACKET_FAIL_CLOSED_PRESENT")
    if any(row.get("signoff_status") == "CLEARANCE_SIGNOFF_PACKET_WAITING_EXTERNAL_ARTIFACT" for row in rows):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_SIGNOFF_PACKET_EXTERNAL_ARTIFACT_WAITING")
    if any(row.get("signoff_status") == "CLEARANCE_SIGNOFF_PACKET_WAITING_REFRESH" for row in rows):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_SIGNOFF_PACKET_UPSTREAM_REFRESH_WAITING")
    if any(row.get("signoff_status") == "CLEARANCE_SIGNOFF_PACKET_INVESTIGATION_REQUIRED" for row in rows):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_SIGNOFF_PACKET_INVESTIGATION_REQUIRED")
    return sorted(set(degraded))
