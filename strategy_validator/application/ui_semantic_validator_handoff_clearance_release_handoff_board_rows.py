"""Row synthesis for semantic validator handoff clearance release handoff board."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_handoff_board_common import (
    _HANDOFF_READINESS_RANK,
    _HANDOFF_STATUS_RANK,
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

def _handoff_status(row: dict[str, Any]) -> str:
    packet_status = _s(row.get("release_packet_status"))
    packet_readiness = _s(row.get("release_packet_readiness"))
    if packet_readiness == "FAIL_CLOSED" or packet_status == "CLEARANCE_RELEASE_PACKET_BLOCKED" or row.get("blocked"):
        return "CLEARANCE_RELEASE_HANDOFF_BLOCKED"
    if packet_status == "CLEARANCE_RELEASE_PACKET_WAITING_EXTERNAL_ARTIFACT" or row.get("requires_external_artifact"):
        return "CLEARANCE_RELEASE_HANDOFF_WAITING_EXTERNAL_ARTIFACT"
    if packet_status == "CLEARANCE_RELEASE_PACKET_WAITING_ACCEPTANCE" or row.get("requires_acceptance_observation"):
        return "CLEARANCE_RELEASE_HANDOFF_WAITING_ACCEPTANCE"
    if packet_status == "CLEARANCE_RELEASE_PACKET_INVESTIGATION_REQUIRED" or row.get("requires_investigation"):
        return "CLEARANCE_RELEASE_HANDOFF_INVESTIGATION_REQUIRED"
    if packet_status == "CLEARANCE_RELEASE_PACKET_READY_FOR_HUMAN_RELEASE_OBSERVATION" or row.get("ready_for_human_release_observation"):
        return "CLEARANCE_RELEASE_HANDOFF_READY_FOR_HUMAN_TRANSFER_OBSERVATION"
    return "CLEARANCE_RELEASE_HANDOFF_WAITING_PACKET_REVIEW"

def _handoff_readiness(status: str) -> str:
    if status == "CLEARANCE_RELEASE_HANDOFF_BLOCKED":
        return "FAIL_CLOSED"
    if status == "CLEARANCE_RELEASE_HANDOFF_READY_FOR_HUMAN_TRANSFER_OBSERVATION":
        return "HUMAN_TRANSFER_READY_OBSERVATION"
    return "WAITING"

def _handoff_gate(status: str) -> str:
    return {
        "CLEARANCE_RELEASE_HANDOFF_BLOCKED": "source_release_packet_stops_handoff_transfer_observation",
        "CLEARANCE_RELEASE_HANDOFF_WAITING_EXTERNAL_ARTIFACT": "external_artifacts_present_before_handoff_transfer_review",
        "CLEARANCE_RELEASE_HANDOFF_WAITING_ACCEPTANCE": "acceptance_observation_present_before_handoff_transfer_review",
        "CLEARANCE_RELEASE_HANDOFF_WAITING_PACKET_REVIEW": "release_packet_reclassified_to_known_handoff_state",
        "CLEARANCE_RELEASE_HANDOFF_INVESTIGATION_REQUIRED": "release_packet_investigation_resolved_before_handoff_transfer_review",
        "CLEARANCE_RELEASE_HANDOFF_READY_FOR_HUMAN_TRANSFER_OBSERVATION": "authorized_human_may_perform_external_handoff_outside_this_read_plane_after_review",
    }.get(status, "source_release_packet_resolved_or_reclassified")

def _handoff_instruction(status: str, lane: str) -> str:
    if status == "CLEARANCE_RELEASE_HANDOFF_BLOCKED":
        return f"{lane} remains fail-closed in release packet observation; do not transfer, release, approve, or execute from this read-plane."
    if status == "CLEARANCE_RELEASE_HANDOFF_WAITING_EXTERNAL_ARTIFACT":
        return f"{lane} is waiting on external artifacts before a human handoff transfer can be observed."
    if status == "CLEARANCE_RELEASE_HANDOFF_WAITING_ACCEPTANCE":
        return f"{lane} still needs acceptance evidence before handoff transfer review is trustworthy."
    if status == "CLEARANCE_RELEASE_HANDOFF_WAITING_PACKET_REVIEW":
        return f"{lane} needs release packet review/reclassification before handoff transfer routing."
    if status == "CLEARANCE_RELEASE_HANDOFF_READY_FOR_HUMAN_TRANSFER_OBSERVATION":
        return f"{lane} is only observed as ready for human handoff transfer review; this read-plane writes no handoff, release, packet, signoff, approval, decision, or record."
    return f"{lane} requires investigation before any handoff transfer observation."

def _handoff_from_packet(row: dict[str, Any], ordinal: int, source_payload: dict[str, Any]) -> dict[str, Any]:
    status = _handoff_status(row)
    readiness = _handoff_readiness(status)
    lane = _s(row.get("evidence_lane")) or "UNKNOWN"
    handoff_id = "semantic-validator-handoff-clearance-release-handoff-" + _digest(
        {
            "schema_version": _SCHEMA_VERSION,
            "source_schema_version": source_payload.get("schema_version"),
            "source_release_packet_id": row.get("release_packet_id"),
            "lane": lane,
            "status": status,
        }
    )[:20]
    handoff = dict(row)
    handoff.update(
        {
            "release_handoff_id": handoff_id,
            "schema_version": _SCHEMA_VERSION,
            "ordinal": ordinal,
            "evidence_lane": lane,
            "release_handoff_status": status,
            "release_handoff_status_rank": _HANDOFF_STATUS_RANK.get(status, 99),
            "release_handoff_readiness": readiness,
            "release_handoff_readiness_rank": _HANDOFF_READINESS_RANK.get(readiness, 99),
            "ready_for_human_transfer_observation": status == "CLEARANCE_RELEASE_HANDOFF_READY_FOR_HUMAN_TRANSFER_OBSERVATION",
            "blocked": readiness == "FAIL_CLOSED",
            "waiting": readiness == "WAITING",
            "requires_external_artifact": status == "CLEARANCE_RELEASE_HANDOFF_WAITING_EXTERNAL_ARTIFACT",
            "requires_acceptance_observation": status == "CLEARANCE_RELEASE_HANDOFF_WAITING_ACCEPTANCE",
            "requires_release_packet_review": status == "CLEARANCE_RELEASE_HANDOFF_WAITING_PACKET_REVIEW",
            "requires_investigation": status == "CLEARANCE_RELEASE_HANDOFF_INVESTIGATION_REQUIRED",
            "source_release_packet_id": row.get("release_packet_id"),
            "source_release_packet_status": row.get("release_packet_status"),
            "source_release_packet_readiness": row.get("release_packet_readiness"),
            "source_release_packet_gate": row.get("release_packet_gate"),
            "source_release_packet_instruction": row.get("release_packet_instruction"),
            "source_release_readiness_card_id": row.get("source_release_readiness_card_id"),
            "source_release_status": row.get("source_release_status"),
            "source_release_readiness": row.get("source_release_readiness"),
            "release_handoff_gate": _handoff_gate(status),
            "release_handoff_instruction": _handoff_instruction(status, lane),
            "recommended_operator_path": _handoff_gate(status),
            "clearance_release_handoff_board_route": "/ui/semantic-validator-handoff/clearance-release-handoff-board",
            "clearance_release_packet_route": "/ui/semantic-validator-handoff/clearance-release-packet",
            "clearance_release_readiness_board_route": "/ui/semantic-validator-handoff/clearance-release-readiness-board",
            "authority": _authority(),
            "release_handoff_write_authority": "none_read_plane",
            "release_handoff_assertion_authority": "none_read_plane",
            "release_packet_write_authority": "none_read_plane",
            "release_record_write_authority": "none_read_plane",
            "release_authorization_authority": "none_read_plane",
            "handoff_release_authority": "none_read_plane",
            "acceptance_record_write_authority": "none_read_plane",
            "operator_signoff_authority": "none_read_plane",
            "operator_approval_authority": "none_read_plane",
            "clearance_decision_authority": "none_read_plane",
            "artifact_mutation_authority": "none_read_plane",
            "validator_submission_authority": "none_read_plane",
            "adjudication_authority": "none_read_plane",
            "promotion_authority": "none_read_plane",
            "execution_authority": "none_read_plane",
            "source_release_packet": row,
            "summary_line": f"{lane}: {status} / {readiness}; handoff visibility only, no release or transfer write authority.",
        }
    )
    return handoff

def _rank(value: Any, fallback: int = 99) -> int:
    return int(value) if value is not None else fallback

def _sort_handoff(row: dict[str, Any]) -> tuple[int, int, int, str, str]:
    return (
        _rank(row.get("release_handoff_status_rank")),
        _PRIORITY_RANK.get(_s(row.get("priority")), 99),
        _SEVERITY_RANK.get(_s(row.get("severity")), 99),
        _s(row.get("evidence_lane")),
        _s(row.get("release_handoff_id")),
    )

def _matches(
    row: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    evidence_lane: set[str],
    release_handoff_status: set[str],
    release_handoff_readiness: set[str],
    release_packet_status: set[str],
    release_packet_readiness: set[str],
    release_status: set[str],
    release_readiness: set[str],
    acceptance_status: set[str],
    acceptance_readiness: set[str],
    priority: set[str],
    severity: set[str],
    trust_banner: set[str],
    owner_hint: set[str],
    ready_for_human_transfer_observation: bool | None,
    blocked: bool | None,
    waiting: bool | None,
    requires_acceptance_observation: bool | None,
    requires_external_artifact: bool | None,
    requires_release_packet_review: bool | None,
) -> bool:
    return (
        _contains(" ".join(_as_list(row.get("experiment_ids"))), experiment_id_contains)
        and _contains(" ".join(_as_list(row.get("issue_codes"))), issue_contains)
        and (not evidence_lane or _norm(row.get("evidence_lane")) in evidence_lane)
        and (not release_handoff_status or _norm(row.get("release_handoff_status")) in release_handoff_status)
        and (not release_handoff_readiness or _norm(row.get("release_handoff_readiness")) in release_handoff_readiness)
        and (not release_packet_status or _norm(row.get("source_release_packet_status")) in release_packet_status)
        and (not release_packet_readiness or _norm(row.get("source_release_packet_readiness")) in release_packet_readiness)
        and (not release_status or _norm(row.get("source_release_status")) in release_status)
        and (not release_readiness or _norm(row.get("source_release_readiness")) in release_readiness)
        and (not acceptance_status or _norm(row.get("source_acceptance_status")) in acceptance_status)
        and (not acceptance_readiness or _norm(row.get("source_acceptance_readiness")) in acceptance_readiness)
        and (not priority or _norm(row.get("priority")) in priority)
        and (not severity or _norm(row.get("severity")) in severity)
        and (not trust_banner or _norm(row.get("trust_banner")) in trust_banner)
        and (not owner_hint or _norm(row.get("owner_hint")) in owner_hint)
        and (ready_for_human_transfer_observation is None or bool(row.get("ready_for_human_transfer_observation")) is ready_for_human_transfer_observation)
        and (blocked is None or bool(row.get("blocked")) is blocked)
        and (waiting is None or bool(row.get("waiting")) is waiting)
        and (requires_acceptance_observation is None or bool(row.get("requires_acceptance_observation")) is requires_acceptance_observation)
        and (requires_external_artifact is None or bool(row.get("requires_external_artifact")) is requires_external_artifact)
        and (requires_release_packet_review is None or bool(row.get("requires_release_packet_review")) is requires_release_packet_review)
    )

def _degraded(source_payload: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    degraded = list(_as_list(source_payload.get("degraded")))
    if any(row.get("blocked") for row in rows):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_HANDOFF_FAIL_CLOSED_PRESENT")
    if any(row.get("requires_external_artifact") for row in rows):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_HANDOFF_EXTERNAL_ARTIFACTS_PENDING")
    if any(row.get("requires_acceptance_observation") for row in rows):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_HANDOFF_ACCEPTANCE_OBSERVATION_PENDING")
    if any(row.get("requires_release_packet_review") for row in rows):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_HANDOFF_PACKET_REVIEW_PENDING")
    if any(row.get("requires_investigation") for row in rows):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_HANDOFF_INVESTIGATION_REQUIRED")
    return sorted(dict.fromkeys(degraded))
