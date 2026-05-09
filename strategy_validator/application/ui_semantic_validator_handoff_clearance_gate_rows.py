"""Row synthesis and filtering for semantic validator handoff clearance gate read-plane."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_clearance_gate_common import (
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


def _highest_priority(steps: list[dict[str, Any]]) -> str:
    priorities = [_s(step.get("priority")) or "P2" for step in steps]
    return sorted(priorities, key=lambda value: _PRIORITY_RANK.get(_norm(value), 9))[0] if priorities else "P3"


def _highest_severity(steps: list[dict[str, Any]]) -> str:
    severities = [_s(step.get("severity")) or "INFO" for step in steps]
    return sorted(severities, key=lambda value: _SEVERITY_RANK.get(_norm(value), 9))[0] if severities else "INFO"


def _status(steps: list[dict[str, Any]]) -> str:
    if not steps:
        return "OBSERVED_CLEAR_NO_ESCALATIONS"
    if any(step.get("phase") == "BLOCKER_TRIAGE" for step in steps):
        return "BLOCKED_BY_RESOLUTION_STEP"
    if any(bool(step.get("requires_external_artifact")) or step.get("phase") == "EXTERNAL_ARTIFACT_COLLECTION" for step in steps):
        return "WAITING_EXTERNAL_ARTIFACT"
    if any(bool(step.get("blocks_handoff_clearance")) for step in steps):
        return "BLOCKED_BY_RESOLUTION_STEP"
    if any(bool(step.get("requires_human_review")) or step.get("phase") == "OPERATOR_REVIEW" for step in steps):
        return "HUMAN_REVIEW_REQUIRED"
    return "MONITOR_ONLY"


def _gate_instruction(status: str, source_route: str) -> str:
    if status == "BLOCKED_BY_RESOLUTION_STEP":
        return f"Open {source_route}, clear blocker steps outside this read-plane, then refresh this gate before relying on handoff closure."
    if status == "WAITING_EXTERNAL_ARTIFACT":
        return f"Collect or attach external artifacts outside this read-plane, then refresh {source_route} and this gate."
    if status == "HUMAN_REVIEW_REQUIRED":
        return f"Review remaining operator steps via {source_route}; this gate only reports readiness and cannot approve or acknowledge anything."
    if status == "MONITOR_ONLY":
        return f"Monitor {source_route}; no blocking clearance condition is visible in the current resolution steps."
    return "No escalation-derived resolution steps are visible; treat this as an observation only, not an approval or signoff."


def _completion_condition(status: str) -> str:
    return {
        "BLOCKED_BY_RESOLUTION_STEP": "ALL_BLOCKING_RESOLUTION_STEPS_REMOVED_FROM_SOURCE_PLAN",
        "WAITING_EXTERNAL_ARTIFACT": "ALL_EXTERNAL_ARTIFACT_COLLECTION_STEPS_REMOVED_FROM_SOURCE_PLAN",
        "HUMAN_REVIEW_REQUIRED": "ALL_HUMAN_REVIEW_STEPS_REMOVED_OR_FORMALLY_HANDLED_OUTSIDE_THIS_READ_PLANE",
        "MONITOR_ONLY": "NO_NEW_BLOCKER_EXTERNAL_ARTIFACT_OR_HUMAN_REVIEW_STEP_APPEARS",
        "OBSERVED_CLEAR_NO_ESCALATIONS": "NO_ESCALATION_DERIVED_RESOLUTION_STEPS_APPEAR_AFTER_REFRESH",
    }.get(status, "SOURCE_RESOLUTION_PLAN_RECHECKED")


def _gate_from_steps(scope_key: str, steps: list[dict[str, Any]], ordinal: int, source_plan: dict[str, Any]) -> dict[str, Any]:
    first = steps[0] if steps else {}
    status = _status(steps)
    phases = sorted({_s(step.get("phase")) for step in steps if _s(step.get("phase"))})
    issue_codes = sorted({code for step in steps for code in _as_list(step.get("issue_codes"))})
    route = _s(first.get("resolution_route")) or "/ui/semantic-validator-handoff/resolution-plan"
    gate_id = "semantic-validator-handoff-clearance-gate-" + _digest(
        {
            "schema_version": _SCHEMA_VERSION,
            "scope_key": scope_key,
            "step_ids": [step.get("resolution_step_id") for step in steps],
            "source_schema_version": source_plan.get("schema_version"),
        }
    )[:20]
    blocks = status in {"BLOCKED_BY_RESOLUTION_STEP", "WAITING_EXTERNAL_ARTIFACT"}
    review_ready = status in {"MONITOR_ONLY", "OBSERVED_CLEAR_NO_ESCALATIONS"}
    return {
        "clearance_gate_id": gate_id,
        "schema_version": _SCHEMA_VERSION,
        "ordinal": ordinal,
        "gate_rank": _STATUS_RANK.get(status, 99),
        "scope_key": scope_key,
        "experiment_id": first.get("experiment_id"),
        "continuity_id": first.get("continuity_id"),
        "chain_id": first.get("chain_id"),
        "chain_digest": first.get("chain_digest"),
        "audit_packet_id": first.get("audit_packet_id"),
        "audit_packet_digest": first.get("audit_packet_digest"),
        "clearance_status": status,
        "handoff_clearance_blocked": blocks,
        "candidate_for_operator_clearance_review": review_ready,
        "requires_external_artifact": status == "WAITING_EXTERNAL_ARTIFACT" or any(bool(step.get("requires_external_artifact")) for step in steps),
        "requires_human_review": status == "HUMAN_REVIEW_REQUIRED" or any(bool(step.get("requires_human_review")) for step in steps),
        "source_resolution_step_count": len(steps),
        "blocking_resolution_step_count": sum(1 for step in steps if bool(step.get("blocks_handoff_clearance"))),
        "external_artifact_step_count": sum(1 for step in steps if bool(step.get("requires_external_artifact"))),
        "human_review_step_count": sum(1 for step in steps if bool(step.get("requires_human_review"))),
        "phase_set": phases,
        "issue_codes": issue_codes,
        "issue_count": len(issue_codes),
        "priority": _highest_priority(steps),
        "severity": _highest_severity(steps),
        "trust_banner": first.get("trust_banner") or ("TRUST_RESTRICTED" if steps else "TRUSTED"),
        "owner_hint": first.get("owner_hint") or ("human_operator_clearance_owner" if steps else "human_operator_monitoring_owner"),
        "source_route": route,
        "resolution_plan_route": "/ui/semantic-validator-handoff/resolution-plan",
        "clearance_route": "/ui/semantic-validator-handoff/clearance-gate",
        "safe_instruction": _gate_instruction(status, route),
        "clearance_condition": _completion_condition(status),
        "authority": _authority(),
        "clearance_decision_authority": "none_read_plane",
        "operator_approval_authority": "none_read_plane",
        "signoff_authority": "none_read_plane",
        "resolution_step_acknowledgment_authority": "none_read_plane",
        "repair_execution_authority": "none_read_plane",
        "external_artifact_write_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
        "source_resolution_steps": steps,
        "summary_line": f"{ordinal}. {status} · steps={len(steps)} · priority={_highest_priority(steps)} · severity={_highest_severity(steps)} · approve=false signoff=false execute=false",
    }


def _group_steps(steps: list[dict[str, Any]]) -> list[tuple[str, list[dict[str, Any]]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for step in steps:
        key = _s(step.get("experiment_id")) or _s(step.get("audit_packet_id")) or _s(step.get("continuity_id")) or "GLOBAL_SEMANTIC_VALIDATOR_HANDOFF"
        groups[key].append(step)
    return sorted(groups.items(), key=lambda item: item[0])


def _sort_gate(gate: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(gate.get("gate_rank") or 99),
        _PRIORITY_RANK.get(_norm(gate.get("priority")), 9),
        _SEVERITY_RANK.get(_norm(gate.get("severity")), 9),
        _s(gate.get("experiment_id")),
        _s(gate.get("clearance_gate_id")),
    )


def _haystack(gate: dict[str, Any]) -> str:
    return "\n".join(
        [
            _s(gate.get("clearance_gate_id")),
            _s(gate.get("scope_key")),
            _s(gate.get("experiment_id")),
            _s(gate.get("clearance_status")),
            _s(gate.get("priority")),
            _s(gate.get("severity")),
            _s(gate.get("trust_banner")),
            _s(gate.get("owner_hint")),
            _s(gate.get("safe_instruction")),
            _s(gate.get("clearance_condition")),
            _s(gate.get("summary_line")),
        ]
        + _as_list(gate.get("issue_codes"))
        + _as_list(gate.get("phase_set"))
    )


def _matches(
    gate: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    clearance_status: set[str],
    priority: set[str],
    severity: set[str],
    trust_banner: set[str],
    owner_hint: set[str],
    requires_external_artifact: bool | None,
    handoff_clearance_blocked: bool | None,
    candidate_for_operator_clearance_review: bool | None,
) -> bool:
    return (
        _contains(gate.get("experiment_id"), experiment_id_contains)
        and (not issue_contains or _contains(_haystack(gate), issue_contains))
        and (not clearance_status or _norm(gate.get("clearance_status")) in clearance_status)
        and (not priority or _norm(gate.get("priority")) in priority)
        and (not severity or _norm(gate.get("severity")) in severity)
        and (not trust_banner or _norm(gate.get("trust_banner")) in trust_banner)
        and (not owner_hint or _norm(gate.get("owner_hint")) in owner_hint)
        and (requires_external_artifact is None or bool(gate.get("requires_external_artifact")) is requires_external_artifact)
        and (handoff_clearance_blocked is None or bool(gate.get("handoff_clearance_blocked")) is handoff_clearance_blocked)
        and (candidate_for_operator_clearance_review is None or bool(gate.get("candidate_for_operator_clearance_review")) is candidate_for_operator_clearance_review)
    )
