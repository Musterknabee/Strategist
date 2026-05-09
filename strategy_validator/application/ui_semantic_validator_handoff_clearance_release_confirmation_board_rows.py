"""Row synthesis for semantic validator handoff clearance release confirmation board."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_confirmation_board_common import (
    _PRIORITY_RANK,
    _READINESS_RANK,
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

def _status(row: dict[str, Any]) -> str:
    status = _s(row.get("release_acknowledgment_status"))
    readiness = _s(row.get("release_acknowledgment_readiness"))
    if readiness == "FAIL_CLOSED" or status == "CLEARANCE_RELEASE_ACKNOWLEDGMENT_BLOCKED" or row.get("blocked"):
        return "CLEARANCE_RELEASE_CONFIRMATION_BLOCKED"
    if status == "CLEARANCE_RELEASE_ACKNOWLEDGMENT_WAITING_EXTERNAL_ARTIFACT" or row.get("requires_external_artifact"):
        return "CLEARANCE_RELEASE_CONFIRMATION_WAITING_EXTERNAL_ARTIFACT"
    if status == "CLEARANCE_RELEASE_ACKNOWLEDGMENT_WAITING_ACCEPTANCE" or row.get("requires_acceptance_observation"):
        return "CLEARANCE_RELEASE_CONFIRMATION_WAITING_ACCEPTANCE"
    if status == "CLEARANCE_RELEASE_ACKNOWLEDGMENT_WAITING_RECEIPT_REVIEW" or row.get("requires_release_receipt_review"):
        return "CLEARANCE_RELEASE_CONFIRMATION_WAITING_ACKNOWLEDGMENT_REVIEW"
    if status == "CLEARANCE_RELEASE_ACKNOWLEDGMENT_INVESTIGATION_REQUIRED" or row.get("requires_investigation"):
        return "CLEARANCE_RELEASE_CONFIRMATION_INVESTIGATION_REQUIRED"
    if status == "CLEARANCE_RELEASE_ACKNOWLEDGMENT_READY_FOR_HUMAN_ACKNOWLEDGMENT_OBSERVATION" or row.get("ready_for_human_acknowledgment_observation"):
        return "CLEARANCE_RELEASE_CONFIRMATION_READY_FOR_HUMAN_CONFIRMATION_OBSERVATION"
    return "CLEARANCE_RELEASE_CONFIRMATION_WAITING_ACKNOWLEDGMENT_REVIEW"

def _readiness(status: str) -> str:
    if status == "CLEARANCE_RELEASE_CONFIRMATION_BLOCKED":
        return "FAIL_CLOSED"
    if status == "CLEARANCE_RELEASE_CONFIRMATION_READY_FOR_HUMAN_CONFIRMATION_OBSERVATION":
        return "HUMAN_CONFIRMATION_READY_OBSERVATION"
    return "WAITING"

def _gate(status: str) -> str:
    return {
        "CLEARANCE_RELEASE_CONFIRMATION_BLOCKED": "source_release_acknowledgment_stops_confirmation_observation",
        "CLEARANCE_RELEASE_CONFIRMATION_WAITING_EXTERNAL_ARTIFACT": "external_artifacts_present_before_confirmation_review",
        "CLEARANCE_RELEASE_CONFIRMATION_WAITING_ACCEPTANCE": "acceptance_observation_present_before_confirmation_review",
        "CLEARANCE_RELEASE_CONFIRMATION_WAITING_ACKNOWLEDGMENT_REVIEW": "release_acknowledgment_reclassified_to_known_confirmation_state",
        "CLEARANCE_RELEASE_CONFIRMATION_INVESTIGATION_REQUIRED": "release_acknowledgment_investigation_resolved_before_confirmation_review",
        "CLEARANCE_RELEASE_CONFIRMATION_READY_FOR_HUMAN_CONFIRMATION_OBSERVATION": "authorized_human_may_record_external_confirmation_outside_this_read_plane_after_review",
    }.get(status, "source_release_acknowledgment_resolved_or_reclassified")

def _instruction(status: str, lane: str) -> str:
    if status == "CLEARANCE_RELEASE_CONFIRMATION_READY_FOR_HUMAN_CONFIRMATION_OBSERVATION":
        return f"{lane} is only observed as ready for human confirmation review; this read-plane writes no confirmation, acknowledgment, receipt, custody, handoff, release, packet, signoff, approval, decision, or record."
    if status == "CLEARANCE_RELEASE_CONFIRMATION_BLOCKED":
        return f"{lane} remains fail-closed in release acknowledgment observation; do not confirm, acknowledge, record receipt, transfer custody, release, approve, or execute from this read-plane."
    if status == "CLEARANCE_RELEASE_CONFIRMATION_WAITING_EXTERNAL_ARTIFACT":
        return f"{lane} is waiting on external artifacts before a human confirmation observation can be trusted."
    if status == "CLEARANCE_RELEASE_CONFIRMATION_WAITING_ACCEPTANCE":
        return f"{lane} still needs acceptance evidence before release confirmation review is trustworthy."
    if status == "CLEARANCE_RELEASE_CONFIRMATION_WAITING_ACKNOWLEDGMENT_REVIEW":
        return f"{lane} needs acknowledgment board review/reclassification before confirmation routing."
    return f"{lane} requires investigation before any release confirmation observation."

def _row(row: dict[str, Any], ordinal: int, source_payload: dict[str, Any]) -> dict[str, Any]:
    status = _status(row)
    readiness = _readiness(status)
    lane = _s(row.get("evidence_lane")) or "UNKNOWN"
    confirmation_id = "semantic-validator-handoff-clearance-release-confirmation-" + _digest(
        {
            "schema_version": _SCHEMA_VERSION,
            "source_release_acknowledgment_id": row.get("release_acknowledgment_id"),
            "lane": lane,
            "status": status,
        }
    )[:20]
    out = dict(row)
    out.update(
        {
            "release_confirmation_id": confirmation_id,
            "schema_version": _SCHEMA_VERSION,
            "ordinal": ordinal,
            "evidence_lane": lane,
            "release_confirmation_status": status,
            "release_confirmation_status_rank": _STATUS_RANK.get(status, 99),
            "release_confirmation_readiness": readiness,
            "release_confirmation_readiness_rank": _READINESS_RANK.get(readiness, 99),
            "ready_for_human_confirmation_observation": status
            == "CLEARANCE_RELEASE_CONFIRMATION_READY_FOR_HUMAN_CONFIRMATION_OBSERVATION",
            "blocked": readiness == "FAIL_CLOSED",
            "waiting": readiness == "WAITING",
            "requires_external_artifact": status == "CLEARANCE_RELEASE_CONFIRMATION_WAITING_EXTERNAL_ARTIFACT",
            "requires_acceptance_observation": status == "CLEARANCE_RELEASE_CONFIRMATION_WAITING_ACCEPTANCE",
            "requires_release_acknowledgment_review": status == "CLEARANCE_RELEASE_CONFIRMATION_WAITING_ACKNOWLEDGMENT_REVIEW",
            "requires_investigation": status == "CLEARANCE_RELEASE_CONFIRMATION_INVESTIGATION_REQUIRED",
            "source_release_acknowledgment_id": row.get("release_acknowledgment_id"),
            "source_release_acknowledgment_status": row.get("release_acknowledgment_status"),
            "source_release_acknowledgment_readiness": row.get("release_acknowledgment_readiness"),
            "source_release_acknowledgment_gate": row.get("release_acknowledgment_gate"),
            "source_release_acknowledgment_instruction": row.get("release_acknowledgment_instruction"),
            "release_confirmation_gate": _gate(status),
            "release_confirmation_instruction": _instruction(status, lane),
            "recommended_operator_path": _gate(status),
            "clearance_release_confirmation_board_route": "/ui/semantic-validator-handoff/clearance-release-confirmation-board",
            "clearance_release_acknowledgment_board_route": "/ui/semantic-validator-handoff/clearance-release-acknowledgment-board",
            "authority": _authority(),
            "release_confirmation_write_authority": "none_read_plane",
            "release_confirmation_assertion_authority": "none_read_plane",
            "release_acknowledgment_write_authority": "none_read_plane",
            "release_acknowledgment_assertion_authority": "none_read_plane",
            "release_receipt_write_authority": "none_read_plane",
            "release_receipt_assertion_authority": "none_read_plane",
            "custody_receipt_record_authority": "none_read_plane",
            "release_custody_write_authority": "none_read_plane",
            "release_custody_assertion_authority": "none_read_plane",
            "custody_transfer_authority": "none_read_plane",
            "release_handoff_write_authority": "none_read_plane",
            "release_packet_write_authority": "none_read_plane",
            "release_record_write_authority": "none_read_plane",
            "release_authorization_authority": "none_read_plane",
            "handoff_release_authority": "none_read_plane",
            "operator_signoff_authority": "none_read_plane",
            "operator_approval_authority": "none_read_plane",
            "clearance_decision_authority": "none_read_plane",
            "artifact_mutation_authority": "none_read_plane",
            "validator_submission_authority": "none_read_plane",
            "adjudication_authority": "none_read_plane",
            "promotion_authority": "none_read_plane",
            "execution_authority": "none_read_plane",
            "source_release_acknowledgment": row,
            "summary_line": f"{lane}: {status} / {readiness}; confirmation visibility only, no confirmation record, acknowledgment record, receipt record, custody transfer, or release authority.",
        }
    )
    return out

def _matches(row: dict[str, Any], **kw: Any) -> bool:
    return (
        _contains(" ".join(_as_list(row.get("experiment_ids"))), kw["experiment_id_contains"])
        and _contains(" ".join(_as_list(row.get("issue_codes"))), kw["issue_contains"])
        and (not kw["evidence_lane"] or _norm(row.get("evidence_lane")) in kw["evidence_lane"])
        and (not kw["release_confirmation_status"] or _norm(row.get("release_confirmation_status")) in kw["release_confirmation_status"])
        and (not kw["release_confirmation_readiness"] or _norm(row.get("release_confirmation_readiness")) in kw["release_confirmation_readiness"])
        and (not kw["release_acknowledgment_status"] or _norm(row.get("source_release_acknowledgment_status")) in kw["release_acknowledgment_status"])
        and (not kw["release_acknowledgment_readiness"] or _norm(row.get("source_release_acknowledgment_readiness")) in kw["release_acknowledgment_readiness"])
        and (not kw["release_receipt_status"] or _norm(row.get("source_release_receipt_status")) in kw["release_receipt_status"])
        and (not kw["release_receipt_readiness"] or _norm(row.get("source_release_receipt_readiness")) in kw["release_receipt_readiness"])
        and (not kw["release_custody_status"] or _norm(row.get("source_release_custody_status")) in kw["release_custody_status"])
        and (not kw["release_custody_readiness"] or _norm(row.get("source_release_custody_readiness")) in kw["release_custody_readiness"])
        and (not kw["release_handoff_status"] or _norm(row.get("source_release_handoff_status")) in kw["release_handoff_status"])
        and (not kw["release_handoff_readiness"] or _norm(row.get("source_release_handoff_readiness")) in kw["release_handoff_readiness"])
        and (not kw["release_packet_status"] or _norm(row.get("source_release_packet_status")) in kw["release_packet_status"])
        and (not kw["release_packet_readiness"] or _norm(row.get("source_release_packet_readiness")) in kw["release_packet_readiness"])
        and (not kw["release_status"] or _norm(row.get("source_release_status")) in kw["release_status"])
        and (not kw["release_readiness"] or _norm(row.get("source_release_readiness")) in kw["release_readiness"])
        and (not kw["acceptance_status"] or _norm(row.get("source_acceptance_status")) in kw["acceptance_status"])
        and (not kw["acceptance_readiness"] or _norm(row.get("source_acceptance_readiness")) in kw["acceptance_readiness"])
        and (not kw["priority"] or _norm(row.get("priority")) in kw["priority"])
        and (not kw["severity"] or _norm(row.get("severity")) in kw["severity"])
        and (not kw["trust_banner"] or _norm(row.get("trust_banner")) in kw["trust_banner"])
        and (not kw["owner_hint"] or _norm(row.get("owner_hint")) in kw["owner_hint"])
        and (kw["ready_for_human_confirmation_observation"] is None or bool(row.get("ready_for_human_confirmation_observation")) is kw["ready_for_human_confirmation_observation"])
        and (kw["blocked"] is None or bool(row.get("blocked")) is kw["blocked"])
        and (kw["waiting"] is None or bool(row.get("waiting")) is kw["waiting"])
        and (kw["requires_acceptance_observation"] is None or bool(row.get("requires_acceptance_observation")) is kw["requires_acceptance_observation"])
        and (kw["requires_external_artifact"] is None or bool(row.get("requires_external_artifact")) is kw["requires_external_artifact"])
        and (kw["requires_release_acknowledgment_review"] is None or bool(row.get("requires_release_acknowledgment_review")) is kw["requires_release_acknowledgment_review"])
    )

def _sort(row: dict[str, Any]) -> tuple[int, int, int, str, str]:
    rank = row.get("release_confirmation_status_rank")
    return (
        int(rank) if rank is not None else 99,
        _PRIORITY_RANK.get(_s(row.get("priority")), 99),
        _SEVERITY_RANK.get(_s(row.get("severity")), 99),
        _s(row.get("evidence_lane")),
        _s(row.get("release_confirmation_id")),
    )

def _degraded(source_payload: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    out = list(_as_list(source_payload.get("degraded")))
    if any(r.get("blocked") for r in rows):
        out.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_CONFIRMATION_FAIL_CLOSED_PRESENT")
    if any(r.get("requires_external_artifact") for r in rows):
        out.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_CONFIRMATION_EXTERNAL_ARTIFACTS_PENDING")
    if any(r.get("requires_acceptance_observation") for r in rows):
        out.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_CONFIRMATION_ACCEPTANCE_OBSERVATION_PENDING")
    if any(r.get("requires_release_acknowledgment_review") for r in rows):
        out.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_CONFIRMATION_ACKNOWLEDGMENT_REVIEW_PENDING")
    if any(r.get("requires_investigation") for r in rows):
        out.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_CONFIRMATION_INVESTIGATION_REQUIRED")
    return sorted(dict.fromkeys(out))
