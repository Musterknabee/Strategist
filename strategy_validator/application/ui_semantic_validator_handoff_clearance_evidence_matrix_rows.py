"""Matrix row synthesis and filtering for clearance evidence visibility."""
from __future__ import annotations

from typing import Any, Iterable

from strategy_validator.application.ui_semantic_validator_handoff_clearance_evidence_matrix_common import (
    _LANE_RANK,
    _PRIORITY_RANK,
    _SCHEMA_VERSION,
    _SEVERITY_RANK,
    _STATE_RANK,
    _as_list,
    _authority,
    _contains,
    _digest,
    _norm,
    _s,
)


def _evidence_lane(item: dict[str, Any]) -> str:
    check_id = _norm(item.get("check_id"))
    route = _s(item.get("route")).lower()
    if item.get("requires_external_artifact") or "EXTERNAL_ARTIFACT" in check_id:
        return "EXTERNAL_ARTIFACT"
    if "resolution-plan" in route or "RESOLUTION" in check_id:
        return "RESOLUTION_PLAN"
    if "clearance-gate" in route or "HANDOFF_NOT_BLOCKED" in check_id:
        return "CLEARANCE_GATE"
    if "AUTHORITY" in check_id or "BOUNDARY" in check_id:
        return "AUTHORITY_BOUNDARY"
    if "clearance-dossier" in route:
        return "CLEARANCE_DOSSIER"
    return "CLEARANCE_REVIEW"


def _evidence_state(item: dict[str, Any]) -> str:
    check_state = _norm(item.get("check_state"))
    if item.get("blocks_clearance"):
        return "BLOCKING_EVIDENCE_GAP"
    if check_state == "WAITING_EXTERNAL_ARTIFACT" or item.get("requires_external_artifact"):
        return "WAITING_EXTERNAL_ARTIFACT"
    if item.get("attention_required") or check_state in {"ATTENTION_REQUIRED", "BLOCKED"}:
        return "ATTENTION_REQUIRED"
    if check_state == "PASS":
        return "VERIFIED_OBSERVATION"
    return "UNKNOWN"


def _coverage_state(state: str) -> str:
    return {
        "VERIFIED_OBSERVATION": "OBSERVED_PRESENT",
        "WAITING_EXTERNAL_ARTIFACT": "WAITING_EXTERNAL_ARTIFACT",
        "BLOCKING_EVIDENCE_GAP": "MISSING_OR_BLOCKED",
        "ATTENTION_REQUIRED": "NEEDS_OPERATOR_REVIEW",
    }.get(state, "UNKNOWN")


def _instruction(state: str, lane: str, item: dict[str, Any]) -> str:
    check_id = _s(item.get("check_id")) or "unknown_check"
    if state == "BLOCKING_EVIDENCE_GAP":
        return f"Resolve the blocking evidence condition for {check_id} through the {lane.lower()} source route, then refresh this matrix."
    if state == "WAITING_EXTERNAL_ARTIFACT":
        return f"Collect or attach the missing external artifact for {check_id} outside this read-plane, then refresh clearance surfaces."
    if state == "ATTENTION_REQUIRED":
        return f"Inspect {check_id} on the source clearance route; this matrix cannot attest, override, acknowledge, approve, sign off, or execute."
    if state == "VERIFIED_OBSERVATION":
        return f"{check_id} is observed as present/pass in the source checklist; this is visibility only, not clearance or signoff."
    return f"Review {check_id} on the source route; this projection is read-only visibility."


def _matrix_row(item: dict[str, Any], ordinal: int, source_payload: dict[str, Any]) -> dict[str, Any]:
    lane = _evidence_lane(item)
    state = _evidence_state(item)
    row_id = "semantic-validator-handoff-clearance-evidence-" + _digest({"schema_version": _SCHEMA_VERSION, "checklist_item_id": item.get("checklist_item_id"), "lane": lane, "state": state, "source_schema_version": source_payload.get("schema_version")})[:20]
    return {
        "evidence_matrix_row_id": row_id,
        "schema_version": _SCHEMA_VERSION,
        "ordinal": ordinal,
        "evidence_lane": lane,
        "evidence_lane_rank": _LANE_RANK.get(lane, 99),
        "evidence_state": state,
        "evidence_state_rank": _STATE_RANK.get(state, 99),
        "coverage_state": _coverage_state(state),
        "attention_required": state in {"BLOCKING_EVIDENCE_GAP", "WAITING_EXTERNAL_ARTIFACT", "ATTENTION_REQUIRED"},
        "blocks_clearance": bool(item.get("blocks_clearance")) or state == "BLOCKING_EVIDENCE_GAP",
        "requires_external_artifact": bool(item.get("requires_external_artifact")) or state == "WAITING_EXTERNAL_ARTIFACT",
        "checklist_item_id": item.get("checklist_item_id"),
        "check_id": item.get("check_id"),
        "check_state": item.get("check_state"),
        "clearance_dossier_id": item.get("clearance_dossier_id"),
        "clearance_gate_id": item.get("clearance_gate_id"),
        "review_posture": item.get("review_posture"),
        "clearance_status": item.get("clearance_status"),
        "scope_key": item.get("scope_key"),
        "experiment_id": item.get("experiment_id"),
        "continuity_id": item.get("continuity_id"),
        "chain_id": item.get("chain_id"),
        "chain_digest": item.get("chain_digest"),
        "audit_packet_id": item.get("audit_packet_id"),
        "audit_packet_digest": item.get("audit_packet_digest"),
        "priority": item.get("priority") or "P3",
        "severity": item.get("severity") or "INFO",
        "trust_banner": item.get("trust_banner") or "TRUSTED",
        "owner_hint": item.get("owner_hint") or "human_operator_clearance_owner",
        "evidence": item.get("evidence"),
        "source_route": item.get("route") or "/ui/semantic-validator-handoff/clearance-checklist",
        "matrix_route": "/ui/semantic-validator-handoff/clearance-evidence-matrix",
        "operator_instruction": _instruction(state, lane, item),
        "issue_codes": _as_list(item.get("issue_codes")),
        "issue_count": int(item.get("issue_count") or len(_as_list(item.get("issue_codes")))),
        "phase_set": _as_list(item.get("phase_set")),
        "dossier_digest": item.get("dossier_digest"),
        "authority": _authority(),
        "evidence_attestation_authority": "none_read_plane",
        "evidence_override_authority": "none_read_plane",
        "check_acknowledgment_authority": "none_read_plane",
        "check_override_authority": "none_read_plane",
        "clearance_decision_authority": "none_read_plane",
        "operator_approval_authority": "none_read_plane",
        "signoff_authority": "none_read_plane",
        "external_artifact_write_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
        "source_checklist_item": item,
        "summary_line": f"{ordinal}. {lane} · {state} · {item.get('check_id')} · {item.get('experiment_id') or item.get('scope_key')} · attest=false override=false approve=false signoff=false execute=false",
    }


def _sort_row(row: dict[str, Any]) -> tuple[Any, ...]:
    return (int(row.get("evidence_state_rank") if row.get("evidence_state_rank") is not None else 99), int(row.get("evidence_lane_rank") if row.get("evidence_lane_rank") is not None else 99), _PRIORITY_RANK.get(_norm(row.get("priority")), 9), _SEVERITY_RANK.get(_norm(row.get("severity")), 9), _s(row.get("experiment_id")), _s(row.get("clearance_dossier_id")), _s(row.get("check_id")))


def _haystack(row: dict[str, Any]) -> str:
    return "\n".join([_s(row.get(k)) for k in ("evidence_matrix_row_id", "evidence_lane", "evidence_state", "coverage_state", "check_id", "check_state", "experiment_id", "scope_key", "review_posture", "clearance_status", "priority", "severity", "trust_banner", "owner_hint", "evidence", "operator_instruction", "summary_line")] + _as_list(row.get("issue_codes")) + _as_list(row.get("phase_set")))


def _matches(row: dict[str, Any], *, experiment_id_contains: str | None, issue_contains: str | None, evidence_lane: set[str], evidence_state: set[str], check_state: set[str], priority: set[str], severity: set[str], trust_banner: set[str], owner_hint: set[str], attention_required: bool | None, blocks_clearance: bool | None, requires_external_artifact: bool | None) -> bool:
    return (_contains(row.get("experiment_id"), experiment_id_contains) and (not issue_contains or _contains(_haystack(row), issue_contains)) and (not evidence_lane or _norm(row.get("evidence_lane")) in evidence_lane) and (not evidence_state or _norm(row.get("evidence_state")) in evidence_state) and (not check_state or _norm(row.get("check_state")) in check_state) and (not priority or _norm(row.get("priority")) in priority) and (not severity or _norm(row.get("severity")) in severity) and (not trust_banner or _norm(row.get("trust_banner")) in trust_banner) and (not owner_hint or _norm(row.get("owner_hint")) in owner_hint) and (attention_required is None or bool(row.get("attention_required")) is attention_required) and (blocks_clearance is None or bool(row.get("blocks_clearance")) is blocks_clearance) and (requires_external_artifact is None or bool(row.get("requires_external_artifact")) is requires_external_artifact))


def _matrix_cells(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((_s(row.get("evidence_lane")) or "UNKNOWN", _s(row.get("evidence_state")) or "UNKNOWN"), []).append(row)
    cells = []
    for (lane, state), members in grouped.items():
        cells.append({"cell_id": f"{lane}:{state}", "evidence_lane": lane, "evidence_state": state, "coverage_state": _coverage_state(state), "row_count": len(members), "attention_required_count": sum(1 for row in members if row.get("attention_required")), "blocks_clearance_count": sum(1 for row in members if row.get("blocks_clearance")), "requires_external_artifact_count": sum(1 for row in members if row.get("requires_external_artifact")), "sample_row_ids": [str(row.get("evidence_matrix_row_id")) for row in members[:5]]})
    return sorted(cells, key=lambda cell: (_STATE_RANK.get(_norm(cell.get("evidence_state")), 99), _LANE_RANK.get(_norm(cell.get("evidence_lane")), 99)))


def _degraded(checklist_payload: dict[str, Any], filtered: list[dict[str, Any]]) -> list[str]:
    source_degraded = _as_list(checklist_payload.get("degraded"))
    degraded: list[str] = []
    if source_degraded:
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_CHECKLIST_DEGRADED")
    if any(row.get("blocks_clearance") for row in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_EVIDENCE_MATRIX_BLOCKED")
    if any(row.get("requires_external_artifact") for row in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_EVIDENCE_MATRIX_WAITING_EXTERNAL_ARTIFACT")
    if any(row.get("attention_required") for row in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_EVIDENCE_MATRIX_ATTENTION_REQUIRED")
    return degraded
