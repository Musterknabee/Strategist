"""Coverage-card synthesis and filtering for the clearance coverage board read-plane."""
from __future__ import annotations

from typing import Any, Iterable

from strategy_validator.application.ui_semantic_validator_handoff_clearance_coverage_board_common import (
    _LANE_RANK,
    _PRIORITY_RANK,
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

def _status(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "NO_EVIDENCE_ROWS"
    if any(row.get("blocks_clearance") or row.get("evidence_state") == "BLOCKING_EVIDENCE_GAP" for row in rows):
        return "BLOCKED_BY_EVIDENCE_GAP"
    if any(row.get("requires_external_artifact") or row.get("evidence_state") == "WAITING_EXTERNAL_ARTIFACT" for row in rows):
        return "WAITING_EXTERNAL_ARTIFACT"
    if any(row.get("attention_required") or row.get("evidence_state") == "ATTENTION_REQUIRED" for row in rows):
        return "NEEDS_OPERATOR_REVIEW"
    if all(row.get("evidence_state") == "VERIFIED_OBSERVATION" for row in rows):
        return "OBSERVED_COVERED"
    return "UNKNOWN"


def _coverage_percent(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    return round((sum(1 for row in rows if row.get("evidence_state") == "VERIFIED_OBSERVATION") / len(rows)) * 100)


def _highest(values: Iterable[Any], rank: dict[str, int], default: str) -> str:
    clean = [_s(v) for v in values if _s(v)]
    if not clean:
        return default
    return sorted(clean, key=lambda v: (rank.get(_norm(v), 99), v))[0]


def _operator_instruction(status: str, lane: str, rows: list[dict[str, Any]]) -> str:
    if status == "BLOCKED_BY_EVIDENCE_GAP":
        return f"Triage the blocking clearance evidence rows in {lane}; this board is visibility only and cannot clear, override, approve, sign off, or execute."
    if status == "WAITING_EXTERNAL_ARTIFACT":
        return f"Collect the missing external artifact evidence for {lane} outside this read-plane, then refresh matrix and board surfaces."
    if status == "NEEDS_OPERATOR_REVIEW":
        return f"Review the attention rows in {lane} through their source routes; no acknowledgment or clearance authority exists here."
    if status == "OBSERVED_COVERED":
        return f"{lane} is observed covered by current matrix rows; this is not attestation, clearance, approval, or signoff."
    if rows:
        return f"Inspect {lane} source rows; the board could not derive a stronger coverage state."
    return f"No matrix rows are currently visible for {lane}; refresh upstream clearance surfaces before relying on coverage visibility."


def _board_card(lane: str, rows: list[dict[str, Any]], ordinal: int, source_payload: dict[str, Any]) -> dict[str, Any]:
    status = _status(rows)
    row_ids = [_s(row.get("evidence_matrix_row_id")) for row in rows if _s(row.get("evidence_matrix_row_id"))]
    issue_codes = sorted({code for row in rows for code in _as_list(row.get("issue_codes"))})
    check_ids = sorted({_s(row.get("check_id")) for row in rows if _s(row.get("check_id"))})
    source_routes = sorted({_s(row.get("source_route")) for row in rows if _s(row.get("source_route"))})
    owner_hints = sorted({_s(row.get("owner_hint")) for row in rows if _s(row.get("owner_hint"))})
    phase_set = sorted({phase for row in rows for phase in _as_list(row.get("phase_set"))})
    card_id = "semantic-validator-handoff-clearance-coverage-" + _digest({"schema_version": _SCHEMA_VERSION, "lane": lane, "status": status, "row_ids": row_ids, "source_schema_version": source_payload.get("schema_version")})[:20]
    return {
        "coverage_card_id": card_id,
        "schema_version": _SCHEMA_VERSION,
        "ordinal": ordinal,
        "evidence_lane": lane,
        "evidence_lane_rank": _LANE_RANK.get(lane, 99),
        "coverage_status": status,
        "coverage_status_rank": _STATUS_RANK.get(status, 99),
        "coverage_percent": _coverage_percent(rows),
        "row_count": len(rows),
        "attention_required_count": sum(1 for row in rows if row.get("attention_required")),
        "blocks_clearance_count": sum(1 for row in rows if row.get("blocks_clearance")),
        "requires_external_artifact_count": sum(1 for row in rows if row.get("requires_external_artifact")),
        "verified_observation_count": sum(1 for row in rows if row.get("evidence_state") == "VERIFIED_OBSERVATION"),
        "unknown_evidence_count": sum(1 for row in rows if row.get("evidence_state") in {"UNKNOWN", None, ""}),
        "highest_priority": _highest((row.get("priority") for row in rows), _PRIORITY_RANK, "P3"),
        "highest_severity": _highest((row.get("severity") for row in rows), _SEVERITY_RANK, "INFO"),
        "trust_banner": _highest((row.get("trust_banner") for row in rows), {"UNTRUSTED": 0, "TRUST_RESTRICTED": 1, "TRUSTED": 2}, "TRUSTED"),
        "owner_hints": owner_hints,
        "check_ids": check_ids,
        "issue_codes": issue_codes,
        "issue_count": len(issue_codes),
        "phase_set": phase_set,
        "source_routes": source_routes,
        "sample_row_ids": row_ids[:10],
        "source_matrix_route": "/ui/semantic-validator-handoff/clearance-evidence-matrix",
        "coverage_board_route": "/ui/semantic-validator-handoff/clearance-coverage-board",
        "operator_instruction": _operator_instruction(status, lane, rows),
        "attention_required": status in {"BLOCKED_BY_EVIDENCE_GAP", "WAITING_EXTERNAL_ARTIFACT", "NEEDS_OPERATOR_REVIEW"},
        "blocks_clearance": status == "BLOCKED_BY_EVIDENCE_GAP",
        "requires_external_artifact": status == "WAITING_EXTERNAL_ARTIFACT",
        "authority": _authority(),
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
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
        "source_evidence_rows": rows,
        "summary_line": f"{ordinal}. {lane} · {status} · rows={len(rows)} · coverage={_coverage_percent(rows)}% · assert=false attest=false override=false approve=false signoff=false execute=false",
    }


def _sort_card(card: dict[str, Any]) -> tuple[Any, ...]:
    return (int(card.get("coverage_status_rank") if card.get("coverage_status_rank") is not None else 99), int(card.get("evidence_lane_rank") if card.get("evidence_lane_rank") is not None else 99), _PRIORITY_RANK.get(_norm(card.get("highest_priority")), 9), _SEVERITY_RANK.get(_norm(card.get("highest_severity")), 9), _s(card.get("evidence_lane")))


def _haystack(card: dict[str, Any]) -> str:
    return "\n".join([_s(card.get(k)) for k in ("coverage_card_id", "evidence_lane", "coverage_status", "highest_priority", "highest_severity", "trust_banner", "operator_instruction", "summary_line")] + _as_list(card.get("check_ids")) + _as_list(card.get("issue_codes")) + _as_list(card.get("phase_set")) + _as_list(card.get("owner_hints")) + _as_list(card.get("source_routes")))


def _matches(card: dict[str, Any], *, issue_contains: str | None, evidence_lane: set[str], coverage_status: set[str], priority: set[str], severity: set[str], trust_banner: set[str], attention_required: bool | None, blocks_clearance: bool | None, requires_external_artifact: bool | None) -> bool:
    return ((not issue_contains or _contains(_haystack(card), issue_contains)) and (not evidence_lane or _norm(card.get("evidence_lane")) in evidence_lane) and (not coverage_status or _norm(card.get("coverage_status")) in coverage_status) and (not priority or _norm(card.get("highest_priority")) in priority) and (not severity or _norm(card.get("highest_severity")) in severity) and (not trust_banner or _norm(card.get("trust_banner")) in trust_banner) and (attention_required is None or bool(card.get("attention_required")) is attention_required) and (blocks_clearance is None or bool(card.get("blocks_clearance")) is blocks_clearance) and (requires_external_artifact is None or bool(card.get("requires_external_artifact")) is requires_external_artifact))


def _cards_from_rows(rows: list[dict[str, Any]], source_payload: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        lane = _s(row.get("evidence_lane")) or "UNKNOWN"
        grouped.setdefault(lane, []).append(row)
    cards = [_board_card(lane, members, index, source_payload) for index, (lane, members) in enumerate(sorted(grouped.items(), key=lambda item: _LANE_RANK.get(_norm(item[0]), 99)), start=1)]
    return sorted(cards, key=_sort_card)

def _degraded(source_payload: dict[str, Any], filtered: list[dict[str, Any]]) -> list[str]:
    degraded = []
    if _as_list(source_payload.get("degraded")):
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_EVIDENCE_MATRIX_DEGRADED")
    if any(card.get("blocks_clearance") for card in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_COVERAGE_BOARD_BLOCKED")
    if any(card.get("requires_external_artifact") for card in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_COVERAGE_BOARD_WAITING_EXTERNAL_ARTIFACT")
    if any(card.get("attention_required") for card in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_COVERAGE_BOARD_ATTENTION_REQUIRED")
    return degraded
