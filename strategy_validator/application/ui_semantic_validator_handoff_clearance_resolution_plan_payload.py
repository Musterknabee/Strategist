"""Public payload builders for semantic validator handoff clearance resolution plan."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_clearance_resolution_plan_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _as_list,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_resolution_plan_rows import (
    _degraded,
    _matches,
    _resolution_step,
    _sort_step,
)

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the compatibility facade at call time so tests/operators can
    # monkeypatch the historical source-builder symbol without importing submodules.
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_resolution_plan as facade

    return facade.build_ui_semantic_validator_handoff_clearance_action_register_payload


def build_ui_semantic_validator_handoff_clearance_resolution_plan_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: tuple[str, ...] = (),
    phase: tuple[str, ...] = (),
    step_state: tuple[str, ...] = (),
    action_state: tuple[str, ...] = (),
    action_type: tuple[str, ...] = (),
    priority: tuple[str, ...] = (),
    severity: tuple[str, ...] = (),
    trust_banner: tuple[str, ...] = (),
    owner_hint: tuple[str, ...] = (),
    blocks_handoff_clearance: bool | None = None,
    requires_external_artifact: bool | None = None,
    requires_human_review: bool | None = None,
    ready_for_operator_clearance_review: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    capped = max(1, min(int(limit or 200), _LIMIT_MAX))
    source_payload = _source_builder()(repo_root=repo_root, search_root=search_root, limit=_LIMIT_MAX)
    source_actions = [row for row in source_payload.get("action_rows", []) if isinstance(row, dict)]
    steps = sorted(
        [_resolution_step(action, index, source_payload) for index, action in enumerate(source_actions, start=1)],
        key=_sort_step,
    )
    filtered = [
        step
        for step in steps
        if _matches(
            step,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            evidence_lane=_norm_set(evidence_lane),
            phase=_norm_set(phase),
            step_state=_norm_set(step_state),
            action_state=_norm_set(action_state),
            action_type=_norm_set(action_type),
            priority=_norm_set(priority),
            severity=_norm_set(severity),
            trust_banner=_norm_set(trust_banner),
            owner_hint=_norm_set(owner_hint),
            blocks_handoff_clearance=blocks_handoff_clearance,
            requires_external_artifact=requires_external_artifact,
            requires_human_review=requires_human_review,
            ready_for_operator_clearance_review=ready_for_operator_clearance_review,
        )
    ]
    returned = filtered[:capped]
    latest = returned[0] if returned else None
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "plan_materialization_authority": "none_read_plane",
        "step_acknowledgment_authority": "none_read_plane",
        "repair_execution_authority": "none_read_plane",
        "action_execution_authority": "none_read_plane",
        "operation_acknowledgment_authority": "none_read_plane",
        "coverage_assertion_authority": "none_read_plane",
        "evidence_attestation_authority": "none_read_plane",
        "evidence_override_authority": "none_read_plane",
        "check_acknowledgment_authority": "none_read_plane",
        "check_override_authority": "none_read_plane",
        "clearance_decision_authority": "none_read_plane",
        "operator_approval_authority": "none_read_plane",
        "signoff_authority": "none_read_plane",
        "external_artifact_write_authority": "none_read_plane",
        "artifact_mutation_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "adjudication_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
        "source_schema_version": source_payload.get("schema_version"),
        "search_root": source_payload.get("search_root"),
        "filters": {
            "experiment_id_contains": experiment_id_contains,
            "issue_contains": issue_contains,
            "evidence_lane": list(evidence_lane or ()),
            "phase": list(phase or ()),
            "step_state": list(step_state or ()),
            "action_state": list(action_state or ()),
            "action_type": list(action_type or ()),
            "priority": list(priority or ()),
            "severity": list(severity or ()),
            "trust_banner": list(trust_banner or ()),
            "owner_hint": list(owner_hint or ()),
            "blocks_handoff_clearance": blocks_handoff_clearance,
            "requires_external_artifact": requires_external_artifact,
            "requires_human_review": requires_human_review,
            "ready_for_operator_clearance_review": ready_for_operator_clearance_review,
            "limit": capped,
        },
        "summary": {
            "source_action_count_total": len(source_actions),
            "resolution_step_count_total": len(steps),
            "resolution_step_count_filtered": len(filtered),
            "resolution_step_count_returned": len(returned),
            "blocker_triage_count": sum(1 for step in filtered if step.get("phase") == "BLOCKER_TRIAGE"),
            "external_artifact_collection_count": sum(1 for step in filtered if step.get("phase") == "EXTERNAL_ARTIFACT_COLLECTION"),
            "human_operator_review_count": sum(1 for step in filtered if step.get("phase") == "HUMAN_OPERATOR_REVIEW"),
            "upstream_evidence_refresh_count": sum(1 for step in filtered if step.get("phase") == "UPSTREAM_EVIDENCE_REFRESH"),
            "unknown_state_investigation_count": sum(1 for step in filtered if step.get("phase") == "UNKNOWN_STATE_INVESTIGATION"),
            "authorized_clearance_review_count": sum(1 for step in filtered if step.get("phase") == "AUTHORIZED_CLEARANCE_REVIEW"),
            "blocks_handoff_clearance_count": sum(1 for step in filtered if step.get("blocks_handoff_clearance")),
            "requires_external_artifact_count": sum(1 for step in filtered if step.get("requires_external_artifact")),
            "requires_human_review_count": sum(1 for step in filtered if step.get("requires_human_review")),
            "ready_for_operator_clearance_review_count": sum(1 for step in filtered if step.get("ready_for_operator_clearance_review")),
            "plan_materialization_allowed_count": 0,
            "step_acknowledgment_allowed_count": 0,
            "repair_execution_allowed_count": 0,
            "action_execution_allowed_count": 0,
            "coverage_assertion_allowed_count": 0,
            "evidence_override_allowed_count": 0,
            "clearance_decision_allowed_count": 0,
            "operator_approval_allowed_count": 0,
            "signoff_allowed_count": 0,
            "external_artifact_write_allowed_count": 0,
            "validator_submission_allowed_count": 0,
            "promotion_allowed_count": 0,
            "execution_allowed_count": 0,
            "latest_resolution_step_id": None if latest is None else latest.get("resolution_step_id"),
        },
        "phase_counts": _counts(filtered, "phase"),
        "step_state_counts": _counts(filtered, "step_state"),
        "action_state_counts": _counts(filtered, "action_state"),
        "action_type_counts": _counts(filtered, "action_type"),
        "evidence_lane_counts": _counts(filtered, "evidence_lane"),
        "priority_counts": _counts(filtered, "priority"),
        "severity_counts": _counts(filtered, "severity"),
        "trust_banner_counts": _counts(filtered, "trust_banner"),
        "owner_hint_counts": _counts(filtered, "owner_hint"),
        "source_degraded": _as_list(source_payload.get("degraded")),
        "degraded": _degraded(source_payload, filtered),
        "guardrails": [
            "read_plane_only_clearance_resolution_plan_no_plan_materialization_acknowledgment_or_repair_is_performed_here",
            "resolution_steps_are_operator_visibility_not_clearance_decisions_approvals_or_signoffs",
            "external_artifacts_source_evidence_and_repairs_must_be_resolved_outside_this_projection",
            "no_override_approval_signoff_validator_submission_adjudication_promotion_or_execution_authority",
        ],
        "routes": {
            "clearance_resolution_plan": "/ui/semantic-validator-handoff/clearance-resolution-plan",
            "clearance_action_register": "/ui/semantic-validator-handoff/clearance-action-register",
            "clearance_operations_board": "/ui/semantic-validator-handoff/clearance-operations-board",
            "clearance_coverage_board": "/ui/semantic-validator-handoff/clearance-coverage-board",
            "clearance_evidence_matrix": "/ui/semantic-validator-handoff/clearance-evidence-matrix",
            "clearance_checklist": "/ui/semantic-validator-handoff/clearance-checklist",
            "clearance_dossier": "/ui/semantic-validator-handoff/clearance-dossier",
            "clearance_gate": "/ui/semantic-validator-handoff/clearance-gate",
        },
        "latest": latest,
        "resolution_steps": returned,
    }


def build_ui_semantic_validator_handoff_clearance_resolution_plan_latest_payload(
    *, repo_root: str | Path | None = None, search_root: str | Path | None = None
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_clearance_resolution_plan_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = [
    "build_ui_semantic_validator_handoff_clearance_resolution_plan_payload",
    "build_ui_semantic_validator_handoff_clearance_resolution_plan_latest_payload",
]
