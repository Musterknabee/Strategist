"""Public payload builders for semantic validator handoff clearance gate."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_clearance_gate_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _as_list,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_gate_rows import (
    _gate_from_steps,
    _group_steps,
    _matches,
    _sort_gate,
)

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the compatibility facade at call time so tests/operators can
    # monkeypatch the historical source-builder symbol without importing submodules.
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_gate as facade

    return facade.build_ui_semantic_validator_handoff_resolution_plan_payload


def build_ui_semantic_validator_handoff_clearance_gate_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    clearance_status: tuple[str, ...] = (),
    priority: tuple[str, ...] = (),
    severity: tuple[str, ...] = (),
    trust_banner: tuple[str, ...] = (),
    owner_hint: tuple[str, ...] = (),
    requires_external_artifact: bool | None = None,
    handoff_clearance_blocked: bool | None = None,
    candidate_for_operator_clearance_review: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    capped = max(1, min(int(limit or 200), _LIMIT_MAX))
    source_plan = _source_builder()(
        repo_root=repo_root,
        search_root=search_root,
        experiment_id_contains=experiment_id_contains,
        issue_contains=issue_contains,
        priority=priority,
        severity=severity,
        trust_banner=trust_banner,
        owner_hint=owner_hint,
        requires_external_artifact=requires_external_artifact,
        blocks_handoff_clearance=handoff_clearance_blocked,
        limit=_LIMIT_MAX,
    )
    steps = [step for step in source_plan.get("resolution_steps", []) if isinstance(step, dict)]
    if steps:
        gates = [_gate_from_steps(key, grouped, index + 1, source_plan) for index, (key, grouped) in enumerate(_group_steps(steps))]
    else:
        gates = [_gate_from_steps("GLOBAL_SEMANTIC_VALIDATOR_HANDOFF", [], 1, source_plan)]
    sorted_gates = sorted(gates, key=_sort_gate)
    filtered = [
        gate
        for gate in sorted_gates
        if _matches(
            gate,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            clearance_status=_norm_set(clearance_status),
            priority=_norm_set(priority),
            severity=_norm_set(severity),
            trust_banner=_norm_set(trust_banner),
            owner_hint=_norm_set(owner_hint),
            requires_external_artifact=requires_external_artifact,
            handoff_clearance_blocked=handoff_clearance_blocked,
            candidate_for_operator_clearance_review=candidate_for_operator_clearance_review,
        )
    ]
    returned = filtered[:capped]
    latest = returned[0] if returned else None
    source_degraded = _as_list(source_plan.get("degraded"))
    degraded: list[str] = []
    if source_degraded:
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_RESOLUTION_PLAN_DEGRADED")
    if any(gate.get("clearance_status") == "BLOCKED_BY_RESOLUTION_STEP" for gate in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_BLOCKED")
    if any(gate.get("clearance_status") == "WAITING_EXTERNAL_ARTIFACT" for gate in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_WAITING_EXTERNAL_ARTIFACT")
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "clearance_decision_authority": "none_read_plane",
        "operator_approval_authority": "none_read_plane",
        "signoff_authority": "none_read_plane",
        "resolution_step_acknowledgment_authority": "none_read_plane",
        "repair_execution_authority": "none_read_plane",
        "external_artifact_write_authority": "none_read_plane",
        "artifact_mutation_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "adjudication_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
        "source_schema_version": source_plan.get("schema_version"),
        "search_root": source_plan.get("search_root"),
        "filters": {
            "experiment_id_contains": experiment_id_contains,
            "issue_contains": issue_contains,
            "clearance_status": list(clearance_status or ()),
            "priority": list(priority or ()),
            "severity": list(severity or ()),
            "trust_banner": list(trust_banner or ()),
            "owner_hint": list(owner_hint or ()),
            "requires_external_artifact": requires_external_artifact,
            "handoff_clearance_blocked": handoff_clearance_blocked,
            "candidate_for_operator_clearance_review": candidate_for_operator_clearance_review,
            "limit": capped,
        },
        "summary": {
            "source_resolution_step_count_total": len(steps),
            "clearance_gate_count_total": len(gates),
            "clearance_gate_count_filtered": len(filtered),
            "clearance_gate_count_returned": len(returned),
            "blocked_gate_count": sum(1 for gate in filtered if gate.get("clearance_status") == "BLOCKED_BY_RESOLUTION_STEP"),
            "waiting_external_artifact_gate_count": sum(1 for gate in filtered if gate.get("clearance_status") == "WAITING_EXTERNAL_ARTIFACT"),
            "human_review_gate_count": sum(1 for gate in filtered if gate.get("clearance_status") == "HUMAN_REVIEW_REQUIRED"),
            "monitor_only_gate_count": sum(1 for gate in filtered if gate.get("clearance_status") == "MONITOR_ONLY"),
            "observed_clear_gate_count": sum(1 for gate in filtered if gate.get("clearance_status") == "OBSERVED_CLEAR_NO_ESCALATIONS"),
            "handoff_clearance_blocked_count": sum(1 for gate in filtered if gate.get("handoff_clearance_blocked")),
            "candidate_for_operator_clearance_review_count": sum(1 for gate in filtered if gate.get("candidate_for_operator_clearance_review")),
            "requires_external_artifact_count": sum(1 for gate in filtered if gate.get("requires_external_artifact")),
            "requires_human_review_count": sum(1 for gate in filtered if gate.get("requires_human_review")),
            "clearance_decision_allowed_count": 0,
            "operator_approval_allowed_count": 0,
            "signoff_allowed_count": 0,
            "resolution_step_acknowledgment_allowed_count": 0,
            "repair_execution_allowed_count": 0,
            "validator_submission_allowed_count": 0,
            "promotion_allowed_count": 0,
            "execution_allowed_count": 0,
            "latest_clearance_gate_id": None if latest is None else latest.get("clearance_gate_id"),
        },
        "clearance_status_counts": _counts(filtered, "clearance_status"),
        "priority_counts": _counts(filtered, "priority"),
        "severity_counts": _counts(filtered, "severity"),
        "owner_hint_counts": _counts(filtered, "owner_hint"),
        "trust_banner_counts": _counts(filtered, "trust_banner"),
        "source_route_counts": _counts(filtered, "source_route"),
        "source_degraded": source_degraded,
        "degraded": degraded,
        "guardrails": [
            "read_plane_only_clearance_gate_no_approval_or_signoff_is_performed_here",
            "resolution_steps_must_be_acknowledged_or_resolved_outside_this_projection",
            "external_artifacts_must_be_created_outside_this_projection",
            "no_validator_submission_adjudication_promotion_or_execution_authority",
        ],
        "routes": {
            "clearance_gate": "/ui/semantic-validator-handoff/clearance-gate",
            "resolution_plan": "/ui/semantic-validator-handoff/resolution-plan",
            "escalation_board": "/ui/semantic-validator-handoff/escalation-board",
            "action_queue": "/ui/semantic-validator-handoff/action-queue",
            "audit_packet": "/ui/semantic-validator-handoff/audit-packet",
        },
        "latest": latest,
        "clearance_gates": returned,
    }


def build_ui_semantic_validator_handoff_clearance_gate_latest_payload(
    *, repo_root: str | Path | None = None, search_root: str | Path | None = None
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_clearance_gate_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = [
    "build_ui_semantic_validator_handoff_clearance_gate_payload",
    "build_ui_semantic_validator_handoff_clearance_gate_latest_payload",
]
