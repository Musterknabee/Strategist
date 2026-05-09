"""Row synthesis and filtering for semantic validator handoff clearance review docket."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_clearance_review_docket_common import (
    _DOCKET_READINESS_RANK,
    _DOCKET_STATUS_RANK,
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

def _docket_status(card: dict[str, Any]) -> str:
    closeout_status = _s(card.get("closeout_status"))
    readiness = _s(card.get("closeout_readiness"))
    if readiness == "FAIL_CLOSED" or closeout_status == "CLEARANCE_CLOSEOUT_BLOCKED" or card.get("blocked"):
        return "CLEARANCE_REVIEW_DOCKET_BLOCKED"
    if closeout_status == "CLEARANCE_CLOSEOUT_WAITING_EXTERNAL_ARTIFACT":
        return "CLEARANCE_REVIEW_DOCKET_WAITING_EXTERNAL_ARTIFACT"
    if closeout_status == "CLEARANCE_CLOSEOUT_WAITING_REFRESH":
        return "CLEARANCE_REVIEW_DOCKET_WAITING_REFRESH"
    if closeout_status == "CLEARANCE_CLOSEOUT_WAITING_HUMAN_REVIEW":
        return "CLEARANCE_REVIEW_DOCKET_WAITING_HUMAN_REVIEW"
    if closeout_status == "CLEARANCE_CLOSEOUT_READY_FOR_AUTHORIZED_REVIEW" or card.get("ready_for_authorized_clearance_review"):
        return "CLEARANCE_REVIEW_DOCKET_READY_FOR_AUTHORIZED_REVIEW"
    return "CLEARANCE_REVIEW_DOCKET_INVESTIGATION_REQUIRED"


def _docket_readiness(status: str) -> str:
    if status == "CLEARANCE_REVIEW_DOCKET_BLOCKED":
        return "FAIL_CLOSED"
    if status == "CLEARANCE_REVIEW_DOCKET_READY_FOR_AUTHORIZED_REVIEW":
        return "AUTHORIZED_REVIEW_OBSERVATION"
    return "WAITING"


def _review_gate(status: str) -> str:
    return {
        "CLEARANCE_REVIEW_DOCKET_BLOCKED": "source_closeout_cards_stop_blocking_handoff_clearance",
        "CLEARANCE_REVIEW_DOCKET_WAITING_EXTERNAL_ARTIFACT": "external_artifacts_present_in_source_clearance_chain",
        "CLEARANCE_REVIEW_DOCKET_WAITING_REFRESH": "upstream_clearance_chain_rebuilt_after_refresh",
        "CLEARANCE_REVIEW_DOCKET_WAITING_HUMAN_REVIEW": "authorized_human_review_completed_outside_this_read_plane",
        "CLEARANCE_REVIEW_DOCKET_INVESTIGATION_REQUIRED": "source_closeout_status_reclassified_to_known_review_terminal_state",
        "CLEARANCE_REVIEW_DOCKET_READY_FOR_AUTHORIZED_REVIEW": "authorized_clearance_reviewer_may_review_source_evidence_outside_this_read_plane",
    }.get(status, "source_closeout_cards_resolved_or_reclassified")


def _review_instruction(status: str, lane: str) -> str:
    if status == "CLEARANCE_REVIEW_DOCKET_BLOCKED":
        return f"{lane} remains blocked at clearance closeout; do not route for authorization until blocking closeout cards are resolved upstream."
    if status == "CLEARANCE_REVIEW_DOCKET_WAITING_EXTERNAL_ARTIFACT":
        return f"{lane} is waiting on external artifacts; attach evidence through governed artifact flows before review."
    if status == "CLEARANCE_REVIEW_DOCKET_WAITING_REFRESH":
        return f"{lane} needs an upstream clearance-chain refresh before any authorized review can be trusted."
    if status == "CLEARANCE_REVIEW_DOCKET_WAITING_HUMAN_REVIEW":
        return f"{lane} requires human review through the governed clearance path; this docket does not perform or record that review."
    if status == "CLEARANCE_REVIEW_DOCKET_READY_FOR_AUTHORIZED_REVIEW":
        return f"{lane} is only observed as ready for authorized review; this read-plane writes no review record, approval, signoff, or decision."
    return f"{lane} needs investigation before review routing because closeout status is not terminal enough for clearance review."


def _docket_from_card(card: dict[str, Any], ordinal: int, source_payload: dict[str, Any]) -> dict[str, Any]:
    status = _docket_status(card)
    readiness = _docket_readiness(status)
    lane = _s(card.get("evidence_lane")) or "UNKNOWN"
    docket_id = "semantic-validator-handoff-clearance-review-docket-" + _digest(
        {
            "schema_version": _SCHEMA_VERSION,
            "source_schema_version": source_payload.get("schema_version"),
            "source_closeout_card_id": card.get("closeout_card_id"),
            "lane": lane,
            "status": status,
        }
    )[:20]
    return {
        "review_docket_id": docket_id,
        "schema_version": _SCHEMA_VERSION,
        "ordinal": ordinal,
        "evidence_lane": lane,
        "docket_status": status,
        "docket_status_rank": _DOCKET_STATUS_RANK.get(status, 99),
        "docket_readiness": readiness,
        "docket_readiness_rank": _DOCKET_READINESS_RANK.get(readiness, 99),
        "ready_for_authorized_review": status == "CLEARANCE_REVIEW_DOCKET_READY_FOR_AUTHORIZED_REVIEW",
        "blocked": readiness == "FAIL_CLOSED",
        "waiting": readiness == "WAITING",
        "requires_authorized_human_review": status in {
            "CLEARANCE_REVIEW_DOCKET_WAITING_HUMAN_REVIEW",
            "CLEARANCE_REVIEW_DOCKET_READY_FOR_AUTHORIZED_REVIEW",
        },
        "source_closeout_card_id": card.get("closeout_card_id"),
        "source_closeout_status": card.get("closeout_status"),
        "source_closeout_readiness": card.get("closeout_readiness"),
        "source_closeout_gate": card.get("closeout_gate"),
        "source_closeout_note": card.get("closeout_note"),
        "source_verification_card_ids": _as_list(card.get("source_verification_card_ids")),
        "source_resolution_step_ids": _as_list(card.get("source_resolution_step_ids")),
        "source_action_ids": _as_list(card.get("source_action_ids")),
        "source_operation_card_ids": _as_list(card.get("source_operation_card_ids")),
        "source_coverage_card_ids": _as_list(card.get("source_coverage_card_ids")),
        "verification_card_count": int(card.get("verification_card_count") or 0),
        "verification_statuses": _as_list(card.get("verification_statuses")),
        "verification_results": _as_list(card.get("verification_results")),
        "phases": _as_list(card.get("phases")),
        "priority": _s(card.get("priority")) or "P3",
        "severity": _s(card.get("severity")) or "INFO",
        "trust_banner": "TRUST_RESTRICTED" if readiness != "AUTHORIZED_REVIEW_OBSERVATION" else _s(card.get("trust_banner")) or "TRUSTED",
        "owner_hint": _s(card.get("owner_hint")) or "human_operator_clearance_owner",
        "owner_hints": _as_list(card.get("owner_hints")) or [_s(card.get("owner_hint")) or "human_operator_clearance_owner"],
        "check_ids": _as_list(card.get("check_ids")),
        "issue_codes": _as_list(card.get("issue_codes")),
        "issue_count": len(_as_list(card.get("issue_codes"))),
        "experiment_ids": _as_list(card.get("experiment_ids")),
        "continuity_ids": _as_list(card.get("continuity_ids")),
        "audit_packet_ids": _as_list(card.get("audit_packet_ids")),
        "blocks_handoff_clearance_count": int(card.get("blocks_handoff_clearance_count") or 0),
        "requires_external_artifact_count": int(card.get("requires_external_artifact_count") or 0),
        "requires_human_review_count": int(card.get("requires_human_review_count") or 0),
        "verification_passed_count": int(card.get("verification_passed_count") or 0),
        "review_gate": _review_gate(status),
        "review_instruction": _review_instruction(status, lane),
        "recommended_operator_path": "authorized_clearance_review_path_only" if readiness == "AUTHORIZED_REVIEW_OBSERVATION" else "return_to_clearance_closeout_sources_before_authorized_review",
        "clearance_review_docket_route": "/ui/semantic-validator-handoff/clearance-review-docket",
        "clearance_closeout_board_route": "/ui/semantic-validator-handoff/clearance-closeout-board",
        "verification_board_route": "/ui/semantic-validator-handoff/clearance-verification-board",
        "resolution_plan_route": "/ui/semantic-validator-handoff/clearance-resolution-plan",
        "action_register_route": "/ui/semantic-validator-handoff/clearance-action-register",
        "operations_board_route": "/ui/semantic-validator-handoff/clearance-operations-board",
        "coverage_board_route": "/ui/semantic-validator-handoff/clearance-coverage-board",
        "evidence_matrix_route": "/ui/semantic-validator-handoff/clearance-evidence-matrix",
        "authority": _authority(),
        "review_record_write_authority": "none_read_plane",
        "review_assertion_authority": "none_read_plane",
        "review_authorization_authority": "none_read_plane",
        "closeout_write_authority": "none_read_plane",
        "closeout_assertion_authority": "none_read_plane",
        "clearance_decision_authority": "none_read_plane",
        "operator_approval_authority": "none_read_plane",
        "signoff_authority": "none_read_plane",
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
        "source_closeout_card": card,
        "summary_line": f"{ordinal}. {lane} · {status} · {readiness} · review_write=false authorize=false approve=false signoff=false submit=false execute=false",
    }


def _sort_docket(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(row.get("docket_status_rank") if row.get("docket_status_rank") is not None else 99),
        int(row.get("docket_readiness_rank") if row.get("docket_readiness_rank") is not None else 99),
        _PRIORITY_RANK.get(_norm(row.get("priority")), 9),
        _SEVERITY_RANK.get(_norm(row.get("severity")), 9),
        _s(row.get("evidence_lane")),
    )


def _haystack(row: dict[str, Any]) -> str:
    keys = (
        "review_docket_id",
        "evidence_lane",
        "docket_status",
        "docket_readiness",
        "source_closeout_status",
        "source_closeout_readiness",
        "priority",
        "severity",
        "trust_banner",
        "owner_hint",
        "review_gate",
        "review_instruction",
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
    docket_status: set[str],
    docket_readiness: set[str],
    closeout_status: set[str],
    closeout_readiness: set[str],
    priority: set[str],
    severity: set[str],
    trust_banner: set[str],
    owner_hint: set[str],
    ready_for_authorized_review: bool | None,
    blocked: bool | None,
    waiting: bool | None,
    requires_authorized_human_review: bool | None,
) -> bool:
    owner_values = {_norm(value) for value in _as_list(row.get("owner_hints"))}
    return (
        _contains("\n".join(_as_list(row.get("experiment_ids"))), experiment_id_contains)
        and _contains(_haystack(row), issue_contains)
        and (not evidence_lane or _norm(row.get("evidence_lane")) in evidence_lane)
        and (not docket_status or _norm(row.get("docket_status")) in docket_status)
        and (not docket_readiness or _norm(row.get("docket_readiness")) in docket_readiness)
        and (not closeout_status or _norm(row.get("source_closeout_status")) in closeout_status)
        and (not closeout_readiness or _norm(row.get("source_closeout_readiness")) in closeout_readiness)
        and (not priority or _norm(row.get("priority")) in priority)
        and (not severity or _norm(row.get("severity")) in severity)
        and (not trust_banner or _norm(row.get("trust_banner")) in trust_banner)
        and (not owner_hint or bool(owner_values & owner_hint) or _norm(row.get("owner_hint")) in owner_hint)
        and (ready_for_authorized_review is None or bool(row.get("ready_for_authorized_review")) is ready_for_authorized_review)
        and (blocked is None or bool(row.get("blocked")) is blocked)
        and (waiting is None or bool(row.get("waiting")) is waiting)
        and (requires_authorized_human_review is None or bool(row.get("requires_authorized_human_review")) is requires_authorized_human_review)
    )


def _degraded(source_payload: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    degraded = [f"SOURCE_CLEARANCE_CLOSEOUT_BOARD::{item}" for item in _as_list(source_payload.get("degraded"))]
    if any(row.get("docket_readiness") == "FAIL_CLOSED" for row in rows):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_REVIEW_DOCKET_FAIL_CLOSED_PRESENT")
    if any(row.get("docket_status") == "CLEARANCE_REVIEW_DOCKET_WAITING_EXTERNAL_ARTIFACT" for row in rows):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_REVIEW_DOCKET_EXTERNAL_ARTIFACT_WAITING")
    if any(row.get("docket_status") == "CLEARANCE_REVIEW_DOCKET_WAITING_REFRESH" for row in rows):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_REVIEW_DOCKET_UPSTREAM_REFRESH_WAITING")
    if any(row.get("docket_status") == "CLEARANCE_REVIEW_DOCKET_INVESTIGATION_REQUIRED" for row in rows):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_REVIEW_DOCKET_INVESTIGATION_REQUIRED")
    return sorted(set(degraded))


