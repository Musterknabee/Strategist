"""Row synthesis and filtering for semantic validator handoff clearance closeout board."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_clearance_closeout_board_common import (
    _PRIORITY_RANK,
    _READINESS_RANK,
    _SCHEMA_VERSION,
    _SEVERITY_RANK,
    _STATUS_RANK,
    _as_list,
    _authority,
    _best_priority,
    _best_severity,
    _contains,
    _digest,
    _norm,
    _s,
    _uniq,
)


def _closeout_status(cards: list[dict[str, Any]]) -> str:
    statuses = {_s(card.get("verification_status")) for card in cards}
    results = {_s(card.get("verification_result")) for card in cards}
    if not cards:
        return "CLEARANCE_CLOSEOUT_INVESTIGATION_REQUIRED"
    if "FAIL_CLOSED" in results or "BLOCKING_SOURCE_ACTION_VISIBLE" in statuses or any(card.get("blocks_handoff_clearance") for card in cards):
        return "CLEARANCE_CLOSEOUT_BLOCKED"
    if "EXTERNAL_ARTIFACT_STILL_REQUIRED" in statuses or any(card.get("requires_external_artifact") for card in cards):
        return "CLEARANCE_CLOSEOUT_WAITING_EXTERNAL_ARTIFACT"
    if "UPSTREAM_REFRESH_STILL_REQUIRED" in statuses:
        return "CLEARANCE_CLOSEOUT_WAITING_REFRESH"
    if "HUMAN_REVIEW_STILL_REQUIRED" in statuses or any(card.get("requires_human_review") for card in cards):
        return "CLEARANCE_CLOSEOUT_WAITING_HUMAN_REVIEW"
    if "INVESTIGATION_STILL_REQUIRED" in statuses:
        return "CLEARANCE_CLOSEOUT_INVESTIGATION_REQUIRED"
    if cards and all(bool(card.get("verification_passed")) for card in cards):
        return "CLEARANCE_CLOSEOUT_READY_FOR_AUTHORIZED_REVIEW"
    return "CLEARANCE_CLOSEOUT_INVESTIGATION_REQUIRED"

def _readiness(status: str) -> str:
    if status == "CLEARANCE_CLOSEOUT_BLOCKED":
        return "FAIL_CLOSED"
    if status == "CLEARANCE_CLOSEOUT_READY_FOR_AUTHORIZED_REVIEW":
        return "REVIEW_READY_OBSERVATION"
    return "WAITING"

def _closeout_gate(status: str) -> str:
    return {
        "CLEARANCE_CLOSEOUT_BLOCKED": "all_fail_closed_verification_cards_removed_or_reclassified",
        "CLEARANCE_CLOSEOUT_WAITING_EXTERNAL_ARTIFACT": "external_artifact_waiting_cards_removed_or_reclassified",
        "CLEARANCE_CLOSEOUT_WAITING_REFRESH": "upstream_refresh_waiting_cards_removed_or_reclassified",
        "CLEARANCE_CLOSEOUT_WAITING_HUMAN_REVIEW": "human_review_waiting_cards_removed_or_handled_by_authorized_path",
        "CLEARANCE_CLOSEOUT_INVESTIGATION_REQUIRED": "unknown_verification_cards_reclassified_to_known_closeout_status",
        "CLEARANCE_CLOSEOUT_READY_FOR_AUTHORIZED_REVIEW": "authorized_clearance_review_and_signoff_completed_outside_this_read_plane",
    }.get(status, "source_verification_cards_resolved_or_reclassified")

def _closeout_note(status: str, lane: str) -> str:
    if status == "CLEARANCE_CLOSEOUT_BLOCKED":
        return f"{lane} still has fail-closed verification evidence; clearance closeout must remain blocked until source verification cards change."
    if status == "CLEARANCE_CLOSEOUT_WAITING_EXTERNAL_ARTIFACT":
        return f"{lane} still waits on an external artifact; this closeout board can only observe the missing artifact state."
    if status == "CLEARANCE_CLOSEOUT_WAITING_REFRESH":
        return f"{lane} still waits on upstream evidence refresh; rebuild the upstream clearance chain before review."
    if status == "CLEARANCE_CLOSEOUT_WAITING_HUMAN_REVIEW":
        return f"{lane} still requires human review through the governed clearance/signoff path; this board cannot approve it."
    if status == "CLEARANCE_CLOSEOUT_READY_FOR_AUTHORIZED_REVIEW":
        return f"{lane} is observed as ready for authorized clearance review; no approval, signoff, or closeout record is written here."
    return f"{lane} needs investigation before clearance closeout because verification state could not be reduced to a known terminal observation."

def _card(lane: str, cards: list[dict[str, Any]], ordinal: int, source_payload: dict[str, Any]) -> dict[str, Any]:
    status = _closeout_status(cards)
    readiness = _readiness(status)
    priority = _best_priority(cards)
    severity = _best_severity(cards)
    card_id = "semantic-validator-handoff-clearance-closeout-card-" + _digest({"schema_version": _SCHEMA_VERSION, "lane": lane, "status": status, "source_schema_version": source_payload.get("schema_version"), "source_card_ids": [card.get("verification_card_id") for card in cards]})[:20]
    issue_codes = _uniq(code for card in cards for code in _as_list(card.get("issue_codes")))
    owner_hints = _uniq(owner for card in cards for owner in (_as_list(card.get("owner_hints")) or [_s(card.get("owner_hint"))]))
    return {
        "closeout_card_id": card_id,
        "schema_version": _SCHEMA_VERSION,
        "ordinal": ordinal,
        "evidence_lane": lane,
        "closeout_status": status,
        "closeout_status_rank": _STATUS_RANK.get(status, 99),
        "closeout_readiness": readiness,
        "closeout_readiness_rank": _READINESS_RANK.get(readiness, 99),
        "ready_for_authorized_clearance_review": status == "CLEARANCE_CLOSEOUT_READY_FOR_AUTHORIZED_REVIEW",
        "blocked": readiness == "FAIL_CLOSED",
        "waiting": readiness == "WAITING",
        "verification_card_count": len(cards),
        "source_verification_card_ids": _uniq(card.get("verification_card_id") for card in cards),
        "source_resolution_step_ids": _uniq(card.get("source_resolution_step_id") for card in cards),
        "source_action_ids": _uniq(card.get("source_action_id") for card in cards),
        "source_operation_card_ids": _uniq(card.get("source_operation_card_id") for card in cards),
        "source_coverage_card_ids": _uniq(card.get("source_coverage_card_id") for card in cards),
        "verification_statuses": _uniq(card.get("verification_status") for card in cards),
        "verification_results": _uniq(card.get("verification_result") for card in cards),
        "phases": _uniq(card.get("phase") for card in cards),
        "priority": priority,
        "severity": severity,
        "trust_banner": "TRUST_RESTRICTED" if readiness != "REVIEW_READY_OBSERVATION" else "TRUSTED",
        "owner_hint": owner_hints[0] if owner_hints else "human_operator_clearance_owner",
        "owner_hints": owner_hints or ["human_operator_clearance_owner"],
        "check_ids": _uniq(check for card in cards for check in _as_list(card.get("check_ids"))),
        "issue_codes": issue_codes,
        "issue_count": len(issue_codes),
        "experiment_ids": _uniq(exp for card in cards for exp in _as_list(card.get("experiment_ids"))),
        "continuity_ids": _uniq(cid for card in cards for cid in _as_list(card.get("continuity_ids"))),
        "audit_packet_ids": _uniq(aid for card in cards for aid in _as_list(card.get("audit_packet_ids"))),
        "blocks_handoff_clearance_count": sum(1 for card in cards if card.get("blocks_handoff_clearance")),
        "requires_external_artifact_count": sum(1 for card in cards if card.get("requires_external_artifact")),
        "requires_human_review_count": sum(1 for card in cards if card.get("requires_human_review")),
        "verification_passed_count": sum(1 for card in cards if card.get("verification_passed")),
        "closeout_gate": _closeout_gate(status),
        "closeout_note": _closeout_note(status, lane),
        "recommended_operator_path": "governed_clearance_signoff_path_only" if readiness == "REVIEW_READY_OBSERVATION" else "resolve_or_reclassify_source_verification_cards_before_clearance_closeout",
        "clearance_closeout_board_route": "/ui/semantic-validator-handoff/clearance-closeout-board",
        "verification_board_route": "/ui/semantic-validator-handoff/clearance-verification-board",
        "resolution_plan_route": "/ui/semantic-validator-handoff/clearance-resolution-plan",
        "action_register_route": "/ui/semantic-validator-handoff/clearance-action-register",
        "operations_board_route": "/ui/semantic-validator-handoff/clearance-operations-board",
        "coverage_board_route": "/ui/semantic-validator-handoff/clearance-coverage-board",
        "evidence_matrix_route": "/ui/semantic-validator-handoff/clearance-evidence-matrix",
        "authority": _authority(),
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
        "source_verification_cards": cards,
        "summary_line": f"{ordinal}. {lane} · {status} · {readiness} · cards={len(cards)} · closeout_write=false approval=false signoff=false submit=false execute=false",
    }

def _sort_card(card: dict[str, Any]) -> tuple[Any, ...]:
    return (int(card.get("closeout_status_rank") if card.get("closeout_status_rank") is not None else 99), int(card.get("closeout_readiness_rank") if card.get("closeout_readiness_rank") is not None else 99), _PRIORITY_RANK.get(_norm(card.get("priority")), 9), _SEVERITY_RANK.get(_norm(card.get("severity")), 9), _s(card.get("evidence_lane")))

def _haystack(card: dict[str, Any]) -> str:
    keys = ("closeout_card_id", "evidence_lane", "closeout_status", "closeout_readiness", "priority", "severity", "trust_banner", "owner_hint", "closeout_gate", "closeout_note", "recommended_operator_path", "summary_line")
    return "\n".join([_s(card.get(k)) for k in keys] + _as_list(card.get("issue_codes")) + _as_list(card.get("check_ids")) + _as_list(card.get("experiment_ids")) + _as_list(card.get("verification_statuses")) + _as_list(card.get("verification_results")) + _as_list(card.get("phases")))

def _matches(card: dict[str, Any], *, experiment_id_contains: str | None, issue_contains: str | None, evidence_lane: set[str], closeout_status: set[str], closeout_readiness: set[str], priority: set[str], severity: set[str], trust_banner: set[str], owner_hint: set[str], ready_for_authorized_clearance_review: bool | None, blocked: bool | None, waiting: bool | None) -> bool:
    owner_values = {_norm(value) for value in _as_list(card.get("owner_hints"))}
    return (_contains("\n".join(_as_list(card.get("experiment_ids"))), experiment_id_contains) and _contains(_haystack(card), issue_contains) and (not evidence_lane or _norm(card.get("evidence_lane")) in evidence_lane) and (not closeout_status or _norm(card.get("closeout_status")) in closeout_status) and (not closeout_readiness or _norm(card.get("closeout_readiness")) in closeout_readiness) and (not priority or _norm(card.get("priority")) in priority) and (not severity or _norm(card.get("severity")) in severity) and (not trust_banner or _norm(card.get("trust_banner")) in trust_banner) and (not owner_hint or bool(owner_values & owner_hint) or _norm(card.get("owner_hint")) in owner_hint) and (ready_for_authorized_clearance_review is None or bool(card.get("ready_for_authorized_clearance_review")) is ready_for_authorized_clearance_review) and (blocked is None or bool(card.get("blocked")) is blocked) and (waiting is None or bool(card.get("waiting")) is waiting))

def _degraded(source_payload: dict[str, Any], cards: list[dict[str, Any]]) -> list[str]:
    degraded = [f"SOURCE_CLEARANCE_VERIFICATION_BOARD::{item}" for item in _as_list(source_payload.get("degraded"))]
    if any(card.get("closeout_readiness") == "FAIL_CLOSED" for card in cards): degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_CLOSEOUT_FAIL_CLOSED_PRESENT")
    if any(card.get("closeout_status") == "CLEARANCE_CLOSEOUT_WAITING_EXTERNAL_ARTIFACT" for card in cards): degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_CLOSEOUT_EXTERNAL_ARTIFACT_WAITING")
    if any(card.get("closeout_status") == "CLEARANCE_CLOSEOUT_WAITING_REFRESH" for card in cards): degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_CLOSEOUT_UPSTREAM_REFRESH_WAITING")
    if any(card.get("closeout_status") == "CLEARANCE_CLOSEOUT_INVESTIGATION_REQUIRED" for card in cards): degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_CLOSEOUT_INVESTIGATION_REQUIRED")
    return sorted(set(degraded))
