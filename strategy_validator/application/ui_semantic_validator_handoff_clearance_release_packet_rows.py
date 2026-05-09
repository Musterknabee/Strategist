"""Row synthesis for semantic validator handoff clearance release packet."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_packet_common import (
    _PACKET_READINESS_RANK,
    _PACKET_STATUS_RANK,
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

def _packet_status(row: dict[str, Any]) -> str:
    status, readiness = _s(row.get("release_status")), _s(row.get("release_readiness"))
    if readiness == "FAIL_CLOSED" or status == "CLEARANCE_RELEASE_BLOCKED" or row.get("blocked"): return "CLEARANCE_RELEASE_PACKET_BLOCKED"
    if status == "CLEARANCE_RELEASE_WAITING_EXTERNAL_ARTIFACT" or row.get("requires_external_artifact"): return "CLEARANCE_RELEASE_PACKET_WAITING_EXTERNAL_ARTIFACT"
    if status == "CLEARANCE_RELEASE_WAITING_ACCEPTANCE" or row.get("requires_acceptance_observation") or row.get("waiting"): return "CLEARANCE_RELEASE_PACKET_WAITING_ACCEPTANCE"
    if status == "CLEARANCE_RELEASE_READY_FOR_OBSERVATION" or row.get("ready_for_release_observation"): return "CLEARANCE_RELEASE_PACKET_READY_FOR_HUMAN_RELEASE_OBSERVATION"
    return "CLEARANCE_RELEASE_PACKET_INVESTIGATION_REQUIRED"

def _packet_readiness(status: str) -> str:
    return "FAIL_CLOSED" if status == "CLEARANCE_RELEASE_PACKET_BLOCKED" else "HUMAN_RELEASE_READY_OBSERVATION" if status == "CLEARANCE_RELEASE_PACKET_READY_FOR_HUMAN_RELEASE_OBSERVATION" else "WAITING"

def _packet_gate(status: str) -> str:
    return {"CLEARANCE_RELEASE_PACKET_BLOCKED": "source_release_readiness_card_stops_release_packet_observation", "CLEARANCE_RELEASE_PACKET_WAITING_EXTERNAL_ARTIFACT": "external_artifacts_present_before_human_release_packet_review", "CLEARANCE_RELEASE_PACKET_WAITING_ACCEPTANCE": "source_acceptance_and_release_readiness_observed_before_human_release_review", "CLEARANCE_RELEASE_PACKET_INVESTIGATION_REQUIRED": "release_readiness_card_status_reclassified_to_known_release_packet_state", "CLEARANCE_RELEASE_PACKET_READY_FOR_HUMAN_RELEASE_OBSERVATION": "authorized_human_may_release_clearance_outside_this_read_plane_after_packet_review"}.get(status, "source_release_readiness_card_resolved_or_reclassified")

def _packet_instruction(status: str, lane: str) -> str:
    if status == "CLEARANCE_RELEASE_PACKET_BLOCKED": return f"{lane} remains fail-closed in release readiness; do not create, sign, or execute a release from this read-plane."
    if status == "CLEARANCE_RELEASE_PACKET_WAITING_EXTERNAL_ARTIFACT": return f"{lane} is waiting on governed external artifacts before any human release packet can be reviewed."
    if status == "CLEARANCE_RELEASE_PACKET_WAITING_ACCEPTANCE": return f"{lane} still needs acceptance/release-readiness observation before a human release packet can be trusted."
    if status == "CLEARANCE_RELEASE_PACKET_READY_FOR_HUMAN_RELEASE_OBSERVATION": return f"{lane} is only observed as ready for human release review; this read-plane writes no packet, release, acceptance, signoff, approval, decision, or record."
    return f"{lane} requires investigation because release readiness is not classified enough for packet routing."

def _packet_from_release(row: dict[str, Any], ordinal: int, source_payload: dict[str, Any]) -> dict[str, Any]:
    status = _packet_status(row); readiness = _packet_readiness(status); lane = _s(row.get("evidence_lane")) or "UNKNOWN"
    packet_id = "semantic-validator-handoff-clearance-release-packet-" + _digest({"schema_version": _SCHEMA_VERSION, "source_schema_version": source_payload.get("schema_version"), "source_release_readiness_card_id": row.get("release_readiness_card_id"), "lane": lane, "status": status})[:20]
    packet = dict(row)
    packet.update({"release_packet_id": packet_id, "schema_version": _SCHEMA_VERSION, "ordinal": ordinal, "evidence_lane": lane, "release_packet_status": status, "release_packet_status_rank": _PACKET_STATUS_RANK.get(status, 99), "release_packet_readiness": readiness, "release_packet_readiness_rank": _PACKET_READINESS_RANK.get(readiness, 99), "ready_for_human_release_observation": status == "CLEARANCE_RELEASE_PACKET_READY_FOR_HUMAN_RELEASE_OBSERVATION", "blocked": readiness == "FAIL_CLOSED", "waiting": readiness == "WAITING", "requires_acceptance_observation": status == "CLEARANCE_RELEASE_PACKET_WAITING_ACCEPTANCE", "requires_external_artifact": status == "CLEARANCE_RELEASE_PACKET_WAITING_EXTERNAL_ARTIFACT", "requires_investigation": status == "CLEARANCE_RELEASE_PACKET_INVESTIGATION_REQUIRED", "source_release_readiness_card_id": row.get("release_readiness_card_id"), "source_release_status": row.get("release_status"), "source_release_readiness": row.get("release_readiness"), "source_release_gate": row.get("release_gate"), "source_release_instruction": row.get("release_instruction"), "release_packet_gate": _packet_gate(status), "release_packet_instruction": _packet_instruction(status, lane), "recommended_operator_path": _packet_gate(status), "clearance_release_packet_route": "/ui/semantic-validator-handoff/clearance-release-packet", "clearance_release_readiness_board_route": "/ui/semantic-validator-handoff/clearance-release-readiness-board", "authority": _authority(), "release_packet_write_authority": "none_read_plane", "release_packet_assertion_authority": "none_read_plane", "release_record_write_authority": "none_read_plane", "release_assertion_authority": "none_read_plane", "release_authorization_authority": "none_read_plane", "handoff_release_authority": "none_read_plane", "acceptance_record_write_authority": "none_read_plane", "operator_signoff_authority": "none_read_plane", "operator_approval_authority": "none_read_plane", "clearance_decision_authority": "none_read_plane", "artifact_mutation_authority": "none_read_plane", "validator_submission_authority": "none_read_plane", "adjudication_authority": "none_read_plane", "promotion_authority": "none_read_plane", "execution_authority": "none_read_plane", "source_release_readiness_card": row, "summary_line": f"{lane}: {status} / {readiness}; packet visibility only, no release write authority."})
    return packet

def _rank(value: Any, fallback: int = 99) -> int:
    return int(value) if value is not None else fallback

def _sort_packet(row: dict[str, Any]) -> tuple[int, int, int, str, str]:
    return (_rank(row.get("release_packet_status_rank")), _PRIORITY_RANK.get(_s(row.get("priority")), 99), _SEVERITY_RANK.get(_s(row.get("severity")), 99), _s(row.get("evidence_lane")), _s(row.get("release_packet_id")))

def _matches(row: dict[str, Any], *, experiment_id_contains: str | None, issue_contains: str | None, evidence_lane: set[str], release_packet_status: set[str], release_packet_readiness: set[str], release_status: set[str], release_readiness: set[str], acceptance_status: set[str], acceptance_readiness: set[str], priority: set[str], severity: set[str], trust_banner: set[str], owner_hint: set[str], ready_for_human_release_observation: bool | None, blocked: bool | None, waiting: bool | None, requires_acceptance_observation: bool | None, requires_external_artifact: bool | None) -> bool:
    return (_contains(" ".join(_as_list(row.get("experiment_ids"))), experiment_id_contains) and _contains(" ".join(_as_list(row.get("issue_codes"))), issue_contains) and (not evidence_lane or _norm(row.get("evidence_lane")) in evidence_lane) and (not release_packet_status or _norm(row.get("release_packet_status")) in release_packet_status) and (not release_packet_readiness or _norm(row.get("release_packet_readiness")) in release_packet_readiness) and (not release_status or _norm(row.get("source_release_status")) in release_status) and (not release_readiness or _norm(row.get("source_release_readiness")) in release_readiness) and (not acceptance_status or _norm(row.get("source_acceptance_status")) in acceptance_status) and (not acceptance_readiness or _norm(row.get("source_acceptance_readiness")) in acceptance_readiness) and (not priority or _norm(row.get("priority")) in priority) and (not severity or _norm(row.get("severity")) in severity) and (not trust_banner or _norm(row.get("trust_banner")) in trust_banner) and (not owner_hint or _norm(row.get("owner_hint")) in owner_hint) and (ready_for_human_release_observation is None or bool(row.get("ready_for_human_release_observation")) is ready_for_human_release_observation) and (blocked is None or bool(row.get("blocked")) is blocked) and (waiting is None or bool(row.get("waiting")) is waiting) and (requires_acceptance_observation is None or bool(row.get("requires_acceptance_observation")) is requires_acceptance_observation) and (requires_external_artifact is None or bool(row.get("requires_external_artifact")) is requires_external_artifact))

def _degraded(source_payload: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    degraded = [f"SOURCE_CLEARANCE_RELEASE_READINESS_BOARD::{item}" for item in _as_list(source_payload.get("degraded"))]
    if any(row.get("release_packet_readiness") == "FAIL_CLOSED" for row in rows): degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_PACKET_FAIL_CLOSED_PRESENT")
    if any(row.get("release_packet_status") == "CLEARANCE_RELEASE_PACKET_WAITING_EXTERNAL_ARTIFACT" for row in rows): degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_PACKET_EXTERNAL_ARTIFACT_WAITING")
    if any(row.get("release_packet_status") == "CLEARANCE_RELEASE_PACKET_INVESTIGATION_REQUIRED" for row in rows): degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_PACKET_INVESTIGATION_REQUIRED")
    return sorted(set(degraded))
