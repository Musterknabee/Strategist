"""Row synthesis and filtering for semantic validator handoff clearance dossiers."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_clearance_dossier_common import (
    _POSTURE_RANK,
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


def _review_posture(gate: dict[str, Any]) -> str:
    status = _s(gate.get("clearance_status"))
    if status == "WAITING_EXTERNAL_ARTIFACT" or bool(gate.get("requires_external_artifact")):
        return "WAITING_EXTERNAL_ARTIFACT"
    if status == "BLOCKED_BY_RESOLUTION_STEP" or bool(gate.get("handoff_clearance_blocked")):
        return "CLEARANCE_BLOCKED"
    if status == "HUMAN_REVIEW_REQUIRED" or bool(gate.get("requires_human_review")):
        return "OPERATOR_REVIEW_OBSERVATION"
    if status == "MONITOR_ONLY":
        return "MONITORING_OBSERVATION"
    return "OBSERVED_CLEAR_NO_ESCALATIONS"


def _operator_brief(posture: str, gate: dict[str, Any]) -> str:
    if posture == "CLEARANCE_BLOCKED":
        return "Handoff clearance is blocked by visible resolution work; do not treat this packet as approved or signed off."
    if posture == "WAITING_EXTERNAL_ARTIFACT":
        return "Handoff clearance is waiting on an external artifact; collect evidence outside this read-plane before rechecking."
    if posture == "OPERATOR_REVIEW_OBSERVATION":
        return "The packet is visible for human review, but this dossier cannot approve, acknowledge, or sign off the handoff."
    if posture == "MONITORING_OBSERVATION":
        return "No blocking gate is visible; monitor upstream resolution and clearance surfaces for drift."
    return "No escalation-derived clearance issue is visible; this is an observation only, not an approval."


def _review_checks(gate: dict[str, Any], posture: str) -> list[dict[str, Any]]:
    status = _s(gate.get("clearance_status")) or "UNKNOWN"
    return [
        {
            "check_id": "resolution_steps_clear",
            "check_state": "PASS" if int(gate.get("source_resolution_step_count") or 0) == 0 else "ATTENTION_REQUIRED",
            "evidence": f"source_resolution_step_count={gate.get('source_resolution_step_count', 0)}",
            "route": gate.get("resolution_plan_route"),
            "write_allowed": False,
        },
        {
            "check_id": "handoff_not_blocked",
            "check_state": "PASS" if not bool(gate.get("handoff_clearance_blocked")) else "BLOCKED",
            "evidence": f"clearance_status={status}",
            "route": gate.get("clearance_route"),
            "write_allowed": False,
        },
        {
            "check_id": "external_artifact_gap_absent",
            "check_state": "PASS" if not bool(gate.get("requires_external_artifact")) else "WAITING_EXTERNAL_ARTIFACT",
            "evidence": f"requires_external_artifact={bool(gate.get('requires_external_artifact'))}",
            "route": gate.get("source_route"),
            "write_allowed": False,
        },
        {
            "check_id": "operator_review_boundary_preserved",
            "check_state": "PASS",
            "evidence": f"posture={posture}; approval_authority=none_read_plane; signoff_authority=none_read_plane",
            "route": "/ui/semantic-validator-handoff/clearance-dossier",
            "write_allowed": False,
        },
    ]


def _dossier_from_gate(gate: dict[str, Any], ordinal: int, source_payload: dict[str, Any]) -> dict[str, Any]:
    posture = _review_posture(gate)
    review_checks = _review_checks(gate, posture)
    dossier_id = "semantic-validator-handoff-clearance-dossier-" + _digest(
        {
            "schema_version": _SCHEMA_VERSION,
            "clearance_gate_id": gate.get("clearance_gate_id"),
            "clearance_status": gate.get("clearance_status"),
            "source_schema_version": source_payload.get("schema_version"),
        }
    )[:20]
    candidate = bool(gate.get("candidate_for_operator_clearance_review")) and posture in {
        "OPERATOR_REVIEW_OBSERVATION",
        "MONITORING_OBSERVATION",
        "OBSERVED_CLEAR_NO_ESCALATIONS",
    }
    return {
        "clearance_dossier_id": dossier_id,
        "schema_version": _SCHEMA_VERSION,
        "ordinal": ordinal,
        "posture_rank": _POSTURE_RANK.get(posture, 99),
        "review_posture": posture,
        "clearance_status": gate.get("clearance_status"),
        "clearance_gate_id": gate.get("clearance_gate_id"),
        "scope_key": gate.get("scope_key"),
        "experiment_id": gate.get("experiment_id"),
        "continuity_id": gate.get("continuity_id"),
        "chain_id": gate.get("chain_id"),
        "chain_digest": gate.get("chain_digest"),
        "audit_packet_id": gate.get("audit_packet_id"),
        "audit_packet_digest": gate.get("audit_packet_digest"),
        "priority": gate.get("priority") or "P3",
        "severity": gate.get("severity") or "INFO",
        "trust_banner": gate.get("trust_banner") or "TRUSTED",
        "owner_hint": gate.get("owner_hint") or "human_operator_clearance_owner",
        "handoff_clearance_blocked": bool(gate.get("handoff_clearance_blocked")),
        "candidate_for_operator_clearance_review": candidate,
        "requires_external_artifact": bool(gate.get("requires_external_artifact")),
        "requires_human_review": bool(gate.get("requires_human_review")),
        "source_resolution_step_count": int(gate.get("source_resolution_step_count") or 0),
        "blocking_resolution_step_count": int(gate.get("blocking_resolution_step_count") or 0),
        "external_artifact_step_count": int(gate.get("external_artifact_step_count") or 0),
        "human_review_step_count": int(gate.get("human_review_step_count") or 0),
        "issue_codes": _as_list(gate.get("issue_codes")),
        "issue_count": int(gate.get("issue_count") or len(_as_list(gate.get("issue_codes")))),
        "phase_set": _as_list(gate.get("phase_set")),
        "operator_brief": _operator_brief(posture, gate),
        "clearance_condition": gate.get("clearance_condition"),
        "safe_instruction": gate.get("safe_instruction"),
        "review_checks": review_checks,
        "review_check_count": 4,
        "failed_or_attention_check_count": sum(1 for check in review_checks if check.get("check_state") != "PASS"),
        "routes": {
            "clearance_dossier": "/ui/semantic-validator-handoff/clearance-dossier",
            "clearance_gate": gate.get("clearance_route") or "/ui/semantic-validator-handoff/clearance-gate",
            "resolution_plan": gate.get("resolution_plan_route") or "/ui/semantic-validator-handoff/resolution-plan",
            "source": gate.get("source_route") or "/ui/semantic-validator-handoff/clearance-gate",
            "audit_packet": "/ui/semantic-validator-handoff/audit-packet",
        },
        "dossier_digest": _digest({"gate": gate, "posture": posture, "schema_version": _SCHEMA_VERSION}),
        "authority": _authority(),
        "dossier_materialization_authority": "none_read_plane",
        "clearance_decision_authority": "none_read_plane",
        "operator_approval_authority": "none_read_plane",
        "signoff_authority": "none_read_plane",
        "resolution_step_acknowledgment_authority": "none_read_plane",
        "repair_execution_authority": "none_read_plane",
        "external_artifact_write_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
        "source_clearance_gate": gate,
        "summary_line": f"{ordinal}. {posture} · {gate.get('experiment_id') or gate.get('scope_key')} · {gate.get('priority')}/{gate.get('severity')} · approval=false signoff=false execute=false",
    }


def _sort_dossier(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(row.get("posture_rank") or 99),
        _PRIORITY_RANK.get(_norm(row.get("priority")), 9),
        _SEVERITY_RANK.get(_norm(row.get("severity")), 9),
        _s(row.get("experiment_id")),
        _s(row.get("clearance_dossier_id")),
    )


def _haystack(row: dict[str, Any]) -> str:
    return "\n".join(
        [
            _s(row.get("clearance_dossier_id")),
            _s(row.get("clearance_gate_id")),
            _s(row.get("scope_key")),
            _s(row.get("experiment_id")),
            _s(row.get("review_posture")),
            _s(row.get("clearance_status")),
            _s(row.get("priority")),
            _s(row.get("severity")),
            _s(row.get("trust_banner")),
            _s(row.get("owner_hint")),
            _s(row.get("operator_brief")),
            _s(row.get("safe_instruction")),
            _s(row.get("clearance_condition")),
            _s(row.get("summary_line")),
        ]
        + _as_list(row.get("issue_codes"))
        + _as_list(row.get("phase_set"))
    )


def _matches(
    row: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    review_posture: set[str],
    clearance_status: set[str],
    priority: set[str],
    severity: set[str],
    trust_banner: set[str],
    owner_hint: set[str],
    handoff_clearance_blocked: bool | None,
    candidate_for_operator_clearance_review: bool | None,
    requires_external_artifact: bool | None,
) -> bool:
    return (
        _contains(row.get("experiment_id"), experiment_id_contains)
        and (not issue_contains or _contains(_haystack(row), issue_contains))
        and (not review_posture or _norm(row.get("review_posture")) in review_posture)
        and (not clearance_status or _norm(row.get("clearance_status")) in clearance_status)
        and (not priority or _norm(row.get("priority")) in priority)
        and (not severity or _norm(row.get("severity")) in severity)
        and (not trust_banner or _norm(row.get("trust_banner")) in trust_banner)
        and (not owner_hint or _norm(row.get("owner_hint")) in owner_hint)
        and (handoff_clearance_blocked is None or bool(row.get("handoff_clearance_blocked")) is handoff_clearance_blocked)
        and (
            candidate_for_operator_clearance_review is None
            or bool(row.get("candidate_for_operator_clearance_review")) is candidate_for_operator_clearance_review
        )
        and (requires_external_artifact is None or bool(row.get("requires_external_artifact")) is requires_external_artifact)
    )


def _degraded(source_payload: dict[str, Any], filtered: list[dict[str, Any]]) -> list[str]:
    degraded: list[str] = []
    if _as_list(source_payload.get("degraded")):
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_GATE_DEGRADED")
    if any(row.get("review_posture") == "CLEARANCE_BLOCKED" for row in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_DOSSIER_BLOCKED")
    if any(row.get("review_posture") == "WAITING_EXTERNAL_ARTIFACT" for row in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_DOSSIER_WAITING_EXTERNAL_ARTIFACT")
    return degraded
