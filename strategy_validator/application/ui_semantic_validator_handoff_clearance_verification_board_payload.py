"""Public payload builders for semantic validator handoff clearance verification board."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_clearance_verification_board_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _as_list,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_verification_board_rows import (
    _card,
    _degraded,
    _matches,
    _sort_card,
)

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the compatibility facade at call time so tests/operators can
    # monkeypatch the historical source-builder symbol without importing submodules.
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_verification_board as facade

    return facade.build_ui_semantic_validator_handoff_clearance_resolution_plan_payload


def build_ui_semantic_validator_handoff_clearance_verification_board_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: tuple[str, ...] = (),
    verification_status: tuple[str, ...] = (),
    verification_result: tuple[str, ...] = (),
    phase: tuple[str, ...] = (),
    step_state: tuple[str, ...] = (),
    action_state: tuple[str, ...] = (),
    priority: tuple[str, ...] = (),
    severity: tuple[str, ...] = (),
    trust_banner: tuple[str, ...] = (),
    owner_hint: tuple[str, ...] = (),
    blocks_handoff_clearance: bool | None = None,
    requires_external_artifact: bool | None = None,
    requires_human_review: bool | None = None,
    ready_for_operator_clearance_review: bool | None = None,
    verification_passed: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    capped = max(1, min(int(limit or 200), _LIMIT_MAX))
    source_payload = _source_builder()(repo_root=repo_root, search_root=search_root, limit=_LIMIT_MAX)
    source_steps = [row for row in source_payload.get("resolution_steps", []) if isinstance(row, dict)]
    cards = sorted(
        [_card(step, index, source_payload) for index, step in enumerate(source_steps, start=1)],
        key=_sort_card,
    )
    filtered = [
        card
        for card in cards
        if _matches(
            card,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            evidence_lane=_norm_set(evidence_lane),
            verification_status=_norm_set(verification_status),
            verification_result=_norm_set(verification_result),
            phase=_norm_set(phase),
            step_state=_norm_set(step_state),
            action_state=_norm_set(action_state),
            priority=_norm_set(priority),
            severity=_norm_set(severity),
            trust_banner=_norm_set(trust_banner),
            owner_hint=_norm_set(owner_hint),
            blocks_handoff_clearance=blocks_handoff_clearance,
            requires_external_artifact=requires_external_artifact,
            requires_human_review=requires_human_review,
            ready_for_operator_clearance_review=ready_for_operator_clearance_review,
            verification_passed=verification_passed,
        )
    ]
    returned = filtered[:capped]
    latest = returned[0] if returned else None
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "verification_write_authority": "none_read_plane",
        "verification_assertion_authority": "none_read_plane",
        "completion_assertion_authority": "none_read_plane",
        "resolution_step_acknowledgment_authority": "none_read_plane",
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
            "verification_status": list(verification_status or ()),
            "verification_result": list(verification_result or ()),
            "phase": list(phase or ()),
            "step_state": list(step_state or ()),
            "action_state": list(action_state or ()),
            "priority": list(priority or ()),
            "severity": list(severity or ()),
            "trust_banner": list(trust_banner or ()),
            "owner_hint": list(owner_hint or ()),
            "blocks_handoff_clearance": blocks_handoff_clearance,
            "requires_external_artifact": requires_external_artifact,
            "requires_human_review": requires_human_review,
            "ready_for_operator_clearance_review": ready_for_operator_clearance_review,
            "verification_passed": verification_passed,
            "limit": capped,
        },
        "summary": {
            "source_resolution_step_count_total": len(source_steps),
            "verification_card_count_total": len(cards),
            "verification_card_count_filtered": len(filtered),
            "verification_card_count_returned": len(returned),
            "fail_closed_count": sum(1 for card in filtered if card.get("verification_result") == "FAIL_CLOSED"),
            "waiting_count": sum(1 for card in filtered if card.get("verification_result") == "WAITING"),
            "review_observation_count": sum(
                1 for card in filtered if card.get("verification_result") == "REVIEW_OBSERVATION"
            ),
            "verification_passed_count": sum(1 for card in filtered if card.get("verification_passed")),
            "blocks_handoff_clearance_count": sum(1 for card in filtered if card.get("blocks_handoff_clearance")),
            "requires_external_artifact_count": sum(1 for card in filtered if card.get("requires_external_artifact")),
            "requires_human_review_count": sum(1 for card in filtered if card.get("requires_human_review")),
            "ready_for_operator_clearance_review_count": sum(
                1 for card in filtered if card.get("ready_for_operator_clearance_review")
            ),
            "verification_write_allowed_count": 0,
            "verification_assertion_allowed_count": 0,
            "completion_assertion_allowed_count": 0,
            "resolution_step_acknowledgment_allowed_count": 0,
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
            "latest_verification_card_id": None if latest is None else latest.get("verification_card_id"),
        },
        "verification_status_counts": _counts(filtered, "verification_status"),
        "verification_result_counts": _counts(filtered, "verification_result"),
        "phase_counts": _counts(filtered, "phase"),
        "step_state_counts": _counts(filtered, "step_state"),
        "action_state_counts": _counts(filtered, "action_state"),
        "evidence_lane_counts": _counts(filtered, "evidence_lane"),
        "priority_counts": _counts(filtered, "priority"),
        "severity_counts": _counts(filtered, "severity"),
        "trust_banner_counts": _counts(filtered, "trust_banner"),
        "owner_hint_counts": _counts(filtered, "owner_hint"),
        "source_degraded": _as_list(source_payload.get("degraded")),
        "degraded": _degraded(source_payload, filtered),
        "guardrails": [
            "read_plane_only_clearance_verification_board_no_verification_record_or_completion_assertion_is_written_here",
            "verification_cards_are_observations_not_clearance_decisions_approvals_signoffs_or_acknowledgments",
            "source_resolution_steps_must_disappear_or_reclassify_before_this_board_can_stop_reporting_waiting_or_fail_closed_states",
            "no_override_approval_signoff_validator_submission_adjudication_promotion_or_execution_authority",
        ],
        "routes": {
            "clearance_verification_board": "/ui/semantic-validator-handoff/clearance-verification-board",
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
        "verification_cards": returned,
    }


def build_ui_semantic_validator_handoff_clearance_verification_board_latest_payload(
    *, repo_root: str | Path | None = None, search_root: str | Path | None = None
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_clearance_verification_board_payload(
        repo_root=repo_root, search_root=search_root, limit=1
    )


__all__ = [
    "build_ui_semantic_validator_handoff_clearance_verification_board_payload",
    "build_ui_semantic_validator_handoff_clearance_verification_board_latest_payload",
]
