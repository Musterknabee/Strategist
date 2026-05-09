"""Public payload builders for the clearance action register read-plane."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_clearance_action_register_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _as_list,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_action_register_rows import (
    _degraded,
    _matches,
    _register_action,
    _sort_action,
)

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the legacy facade at call time so existing tests and
    # operators can monkeypatch the facade builder name without reaching into
    # subphase modules.
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_action_register as facade

    return facade.build_ui_semantic_validator_handoff_clearance_operations_board_payload


def build_ui_semantic_validator_handoff_clearance_action_register_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: tuple[str, ...] = (),
    action_state: tuple[str, ...] = (),
    action_type: tuple[str, ...] = (),
    operation_state: tuple[str, ...] = (),
    action_group: tuple[str, ...] = (),
    priority: tuple[str, ...] = (),
    severity: tuple[str, ...] = (),
    trust_banner: tuple[str, ...] = (),
    owner_hint: tuple[str, ...] = (),
    blocked: bool | None = None,
    requires_external_artifact: bool | None = None,
    requires_human_review: bool | None = None,
    ready_for_operator_clearance_review: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    capped = max(1, min(int(limit or 200), _LIMIT_MAX))
    source_payload = _source_builder()(repo_root=repo_root, search_root=search_root, limit=_LIMIT_MAX)
    source_cards = [card for card in source_payload.get("operation_cards", []) if isinstance(card, dict)]
    actions = [_register_action(card, index, source_payload) for index, card in enumerate(source_cards, start=1)]
    actions = sorted(actions, key=_sort_action)
    filtered = [
        row
        for row in actions
        if _matches(
            row,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            evidence_lane=_norm_set(evidence_lane),
            action_state=_norm_set(action_state),
            action_type=_norm_set(action_type),
            operation_state=_norm_set(operation_state),
            action_group=_norm_set(action_group),
            priority=_norm_set(priority),
            severity=_norm_set(severity),
            trust_banner=_norm_set(trust_banner),
            owner_hint=_norm_set(owner_hint),
            blocked=blocked,
            requires_external_artifact=requires_external_artifact,
            requires_human_review=requires_human_review,
            ready_for_operator_clearance_review=ready_for_operator_clearance_review,
        )
    ]
    returned = filtered[:capped]
    latest = returned[0] if returned else None
    degraded = _degraded(source_payload, filtered)
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "action_acknowledgment_authority": "none_read_plane",
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
            "action_state": list(action_state or ()),
            "action_type": list(action_type or ()),
            "operation_state": list(operation_state or ()),
            "action_group": list(action_group or ()),
            "priority": list(priority or ()),
            "severity": list(severity or ()),
            "trust_banner": list(trust_banner or ()),
            "owner_hint": list(owner_hint or ()),
            "blocked": blocked,
            "requires_external_artifact": requires_external_artifact,
            "requires_human_review": requires_human_review,
            "ready_for_operator_clearance_review": ready_for_operator_clearance_review,
            "limit": capped,
        },
        "summary": {
            "source_operation_card_count_total": len(source_cards),
            "action_count_total": len(actions),
            "action_count_filtered": len(filtered),
            "action_count_returned": len(returned),
            "blocked_action_count": sum(1 for row in filtered if row.get("action_state") == "BLOCKED_ACTION"),
            "external_artifact_action_count": sum(1 for row in filtered if row.get("action_state") == "WAITING_EXTERNAL_ARTIFACT"),
            "human_review_action_count": sum(1 for row in filtered if row.get("requires_human_review")),
            "refresh_required_action_count": sum(1 for row in filtered if row.get("action_state") == "REFRESH_REQUIRED"),
            "ready_review_candidate_count": sum(1 for row in filtered if row.get("ready_for_operator_clearance_review")),
            "action_acknowledgment_allowed_count": 0,
            "action_execution_allowed_count": 0,
            "operation_acknowledgment_allowed_count": 0,
            "coverage_assertion_allowed_count": 0,
            "evidence_attestation_allowed_count": 0,
            "evidence_override_allowed_count": 0,
            "check_acknowledgment_allowed_count": 0,
            "check_override_allowed_count": 0,
            "clearance_decision_allowed_count": 0,
            "operator_approval_allowed_count": 0,
            "signoff_allowed_count": 0,
            "external_artifact_write_allowed_count": 0,
            "validator_submission_allowed_count": 0,
            "promotion_allowed_count": 0,
            "execution_allowed_count": 0,
            "latest_action_id": None if latest is None else latest.get("action_id"),
        },
        "action_state_counts": _counts(filtered, "action_state"),
        "action_type_counts": _counts(filtered, "action_type"),
        "operation_state_counts": _counts(filtered, "operation_state"),
        "action_group_counts": _counts(filtered, "action_group"),
        "evidence_lane_counts": _counts(filtered, "evidence_lane"),
        "priority_counts": _counts(filtered, "priority"),
        "severity_counts": _counts(filtered, "severity"),
        "trust_banner_counts": _counts(filtered, "trust_banner"),
        "owner_hint_counts": _counts(filtered, "owner_hint"),
        "source_degraded": _as_list(source_payload.get("degraded")),
        "degraded": degraded,
        "guardrails": [
            "read_plane_only_clearance_action_register_no_action_acknowledgment_or_execution_is_performed_here",
            "action_rows_are_operator_visibility_not_clearance_decisions_or_signoffs",
            "external_artifacts_and_source_evidence_must_be_resolved_outside_this_projection",
            "no_override_approval_signoff_validator_submission_adjudication_promotion_or_execution_authority",
        ],
        "routes": {
            "clearance_action_register": "/ui/semantic-validator-handoff/clearance-action-register",
            "clearance_operations_board": "/ui/semantic-validator-handoff/clearance-operations-board",
            "clearance_coverage_board": "/ui/semantic-validator-handoff/clearance-coverage-board",
            "clearance_evidence_matrix": "/ui/semantic-validator-handoff/clearance-evidence-matrix",
            "clearance_checklist": "/ui/semantic-validator-handoff/clearance-checklist",
            "clearance_dossier": "/ui/semantic-validator-handoff/clearance-dossier",
            "clearance_gate": "/ui/semantic-validator-handoff/clearance-gate",
        },
        "latest": latest,
        "action_rows": returned,
    }


def build_ui_semantic_validator_handoff_clearance_action_register_latest_payload(
    *, repo_root: str | Path | None = None, search_root: str | Path | None = None
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_clearance_action_register_payload(
        repo_root=repo_root, search_root=search_root, limit=1
    )


__all__ = [
    "build_ui_semantic_validator_handoff_clearance_action_register_payload",
    "build_ui_semantic_validator_handoff_clearance_action_register_latest_payload",
]
