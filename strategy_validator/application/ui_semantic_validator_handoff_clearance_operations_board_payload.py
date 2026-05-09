"""Public payload builders for the clearance operations board read-plane."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_clearance_operations_board_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _as_list,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_operations_board_rows import (
    _degraded,
    _matches,
    _operation_card,
    _sort_card,
)

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the legacy facade at call time so existing tests and
    # operators can monkeypatch the facade builder name without reaching into
    # subphase modules.
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_operations_board as facade

    return facade.build_ui_semantic_validator_handoff_clearance_coverage_board_payload


def build_ui_semantic_validator_handoff_clearance_operations_board_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: tuple[str, ...] = (),
    coverage_status: tuple[str, ...] = (),
    operation_state: tuple[str, ...] = (),
    action_group: tuple[str, ...] = (),
    priority: tuple[str, ...] = (),
    severity: tuple[str, ...] = (),
    trust_banner: tuple[str, ...] = (),
    owner_hint: tuple[str, ...] = (),
    operator_attention_required: bool | None = None,
    handoff_clearance_blocked: bool | None = None,
    requires_external_artifact: bool | None = None,
    ready_for_operator_clearance_review: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    capped = max(1, min(int(limit or 200), _LIMIT_MAX))
    source_payload = _source_builder()(repo_root=repo_root, search_root=search_root, limit=_LIMIT_MAX)
    source_cards = [card for card in source_payload.get("coverage_cards", []) if isinstance(card, dict)]
    cards = [_operation_card(card, index, source_payload) for index, card in enumerate(source_cards, start=1)]
    cards = sorted(cards, key=_sort_card)
    filtered = [
        card
        for card in cards
        if _matches(
            card,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            evidence_lane=_norm_set(evidence_lane),
            coverage_status=_norm_set(coverage_status),
            operation_state=_norm_set(operation_state),
            action_group=_norm_set(action_group),
            priority=_norm_set(priority),
            severity=_norm_set(severity),
            trust_banner=_norm_set(trust_banner),
            owner_hint=_norm_set(owner_hint),
            operator_attention_required=operator_attention_required,
            handoff_clearance_blocked=handoff_clearance_blocked,
            requires_external_artifact=requires_external_artifact,
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
            "coverage_status": list(coverage_status or ()),
            "operation_state": list(operation_state or ()),
            "action_group": list(action_group or ()),
            "priority": list(priority or ()),
            "severity": list(severity or ()),
            "trust_banner": list(trust_banner or ()),
            "owner_hint": list(owner_hint or ()),
            "operator_attention_required": operator_attention_required,
            "handoff_clearance_blocked": handoff_clearance_blocked,
            "requires_external_artifact": requires_external_artifact,
            "ready_for_operator_clearance_review": ready_for_operator_clearance_review,
            "limit": capped,
        },
        "summary": {
            "source_coverage_card_count_total": len(source_cards),
            "operation_card_count_total": len(cards),
            "operation_card_count_filtered": len(filtered),
            "operation_card_count_returned": len(returned),
            "operator_attention_required_count": sum(1 for card in filtered if card.get("operator_attention_required")),
            "blocked_operation_count": sum(1 for card in filtered if card.get("operation_state") == "BLOCKED_CLEARANCE_OPERATION"),
            "external_artifact_operation_count": sum(1 for card in filtered if card.get("operation_state") == "EXTERNAL_ARTIFACT_OPERATION"),
            "operator_review_operation_count": sum(1 for card in filtered if card.get("operation_state") == "OPERATOR_REVIEW_OPERATION"),
            "ready_for_review_operation_count": sum(1 for card in filtered if card.get("ready_for_operator_clearance_review")),
            "no_evidence_operation_count": sum(1 for card in filtered if card.get("operation_state") == "NO_CLEARANCE_EVIDENCE"),
            "unknown_operation_count": sum(1 for card in filtered if card.get("operation_state") == "UNKNOWN_CLEARANCE_OPERATION"),
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
            "adjudication_allowed_count": 0,
            "promotion_allowed_count": 0,
            "execution_allowed_count": 0,
            "latest_operation_card_id": None if latest is None else latest.get("operation_card_id"),
        },
        "operation_state_counts": _counts(filtered, "operation_state"),
        "action_group_counts": _counts(filtered, "action_group"),
        "coverage_status_counts": _counts(filtered, "coverage_status"),
        "evidence_lane_counts": _counts(filtered, "evidence_lane"),
        "priority_counts": _counts(filtered, "highest_priority"),
        "severity_counts": _counts(filtered, "highest_severity"),
        "trust_banner_counts": _counts(filtered, "trust_banner"),
        "owner_hint_counts": _counts(filtered, "owner_hint"),
        "source_degraded": _as_list(source_payload.get("degraded")),
        "degraded": degraded,
        "guardrails": [
            "read_plane_only_clearance_operations_board_no_acknowledgment_assertion_attestation_override_approval_signoff_write_submit_or_execute",
            "operation_cards_are_visibility_and_triage_guidance_not_clearance_decisions",
            "source_coverage_board_and_evidence_matrix_must_be_refreshed_after_external_artifact_or_blocker_resolution",
            "observed_ready_for_review_is_not_operator_clearance_or_signoff",
        ],
        "routes": {
            "clearance_operations_board": "/ui/semantic-validator-handoff/clearance-operations-board",
            "clearance_coverage_board": "/ui/semantic-validator-handoff/clearance-coverage-board",
            "clearance_evidence_matrix": "/ui/semantic-validator-handoff/clearance-evidence-matrix",
            "clearance_checklist": "/ui/semantic-validator-handoff/clearance-checklist",
            "clearance_dossier": "/ui/semantic-validator-handoff/clearance-dossier",
            "clearance_gate": "/ui/semantic-validator-handoff/clearance-gate",
        },
        "latest": latest,
        "operation_cards": returned,
    }


def build_ui_semantic_validator_handoff_clearance_operations_board_latest_payload(*, repo_root: str | Path | None = None, search_root: str | Path | None = None) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_clearance_operations_board_payload(repo_root=repo_root, search_root=search_root, limit=1)



__all__ = [
    "build_ui_semantic_validator_handoff_clearance_operations_board_payload",
    "build_ui_semantic_validator_handoff_clearance_operations_board_latest_payload",
]
