"""Public payload builders for semantic validator handoff clearance release completion board."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_completion_board_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _as_list,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_completion_board_rows import (
    _degraded,
    _matches,
    _row,
    _sort,
)

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the compatibility facade at call time so tests/operators can
    # monkeypatch the historical source-builder symbol without importing submodules.
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_release_completion_board as facade

    return facade.build_ui_semantic_validator_handoff_clearance_release_confirmation_board_payload


def build_ui_semantic_validator_handoff_clearance_release_completion_board_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: Iterable[str] | None = None,
    release_completion_status: Iterable[str] | None = None,
    release_completion_readiness: Iterable[str] | None = None,
    release_confirmation_status: Iterable[str] | None = None,
    release_confirmation_readiness: Iterable[str] | None = None,
    release_acknowledgment_status: Iterable[str] | None = None,
    release_acknowledgment_readiness: Iterable[str] | None = None,
    release_receipt_status: Iterable[str] | None = None,
    release_receipt_readiness: Iterable[str] | None = None,
    release_custody_status: Iterable[str] | None = None,
    release_custody_readiness: Iterable[str] | None = None,
    release_handoff_status: Iterable[str] | None = None,
    release_handoff_readiness: Iterable[str] | None = None,
    release_packet_status: Iterable[str] | None = None,
    release_packet_readiness: Iterable[str] | None = None,
    release_status: Iterable[str] | None = None,
    release_readiness: Iterable[str] | None = None,
    acceptance_status: Iterable[str] | None = None,
    acceptance_readiness: Iterable[str] | None = None,
    priority: Iterable[str] | None = None,
    severity: Iterable[str] | None = None,
    trust_banner: Iterable[str] | None = None,
    owner_hint: Iterable[str] | None = None,
    ready_for_human_completion_observation: bool | None = None,
    blocked: bool | None = None,
    waiting: bool | None = None,
    requires_acceptance_observation: bool | None = None,
    requires_external_artifact: bool | None = None,
    requires_release_confirmation_review: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    source_payload = _source_builder()(
        repo_root=repo_root,
        search_root=search_root,
        limit=_LIMIT_MAX,
    )
    source_rows = list(source_payload.get("release_confirmations") or [])
    rows = sorted((_row(row, i, source_payload) for i, row in enumerate(source_rows, 1)), key=_sort)
    kw = dict(
        experiment_id_contains=experiment_id_contains,
        issue_contains=issue_contains,
        evidence_lane=_norm_set(evidence_lane),
        release_completion_status=_norm_set(release_completion_status),
        release_completion_readiness=_norm_set(release_completion_readiness),
        release_confirmation_status=_norm_set(release_confirmation_status),
        release_confirmation_readiness=_norm_set(release_confirmation_readiness),
        release_acknowledgment_status=_norm_set(release_acknowledgment_status),
        release_acknowledgment_readiness=_norm_set(release_acknowledgment_readiness),
        release_receipt_status=_norm_set(release_receipt_status),
        release_receipt_readiness=_norm_set(release_receipt_readiness),
        release_custody_status=_norm_set(release_custody_status),
        release_custody_readiness=_norm_set(release_custody_readiness),
        release_handoff_status=_norm_set(release_handoff_status),
        release_handoff_readiness=_norm_set(release_handoff_readiness),
        release_packet_status=_norm_set(release_packet_status),
        release_packet_readiness=_norm_set(release_packet_readiness),
        release_status=_norm_set(release_status),
        release_readiness=_norm_set(release_readiness),
        acceptance_status=_norm_set(acceptance_status),
        acceptance_readiness=_norm_set(acceptance_readiness),
        priority=_norm_set(priority),
        severity=_norm_set(severity),
        trust_banner=_norm_set(trust_banner),
        owner_hint=_norm_set(owner_hint),
        ready_for_human_completion_observation=ready_for_human_completion_observation,
        blocked=blocked,
        waiting=waiting,
        requires_acceptance_observation=requires_acceptance_observation,
        requires_external_artifact=requires_external_artifact,
        requires_release_confirmation_review=requires_release_confirmation_review,
    )
    filtered = [row for row in rows if _matches(row, **kw)]
    capped = max(1, min(int(limit or 200), _LIMIT_MAX))
    returned = filtered[:capped]
    latest = returned[0] if returned else None
    summary = {
        "source_release_confirmation_count_total": len(source_rows),
        "release_completion_count_total": len(rows),
        "release_completion_count_filtered": len(filtered),
        "release_completion_count_returned": len(returned),
        "fail_closed_count": sum(1 for row in filtered if row.get("release_completion_readiness") == "FAIL_CLOSED"),
        "waiting_count": sum(1 for row in filtered if row.get("release_completion_readiness") == "WAITING"),
        "human_completion_ready_observation_count": sum(
            1
            for row in filtered
            if row.get("release_completion_readiness") == "HUMAN_COMPLETION_READY_OBSERVATION"
        ),
        "ready_for_human_completion_observation_count": sum(
            1 for row in filtered if row.get("ready_for_human_completion_observation")
        ),
        "blocked_count": sum(1 for row in filtered if row.get("blocked")),
        "requires_acceptance_observation_count": sum(1 for row in filtered if row.get("requires_acceptance_observation")),
        "requires_external_artifact_count": sum(1 for row in filtered if row.get("requires_external_artifact")),
        "requires_release_confirmation_review_count": sum(1 for row in filtered if row.get("requires_release_confirmation_review")),
        "release_completion_write_allowed_count": 0,
        "release_completion_assertion_allowed_count": 0,
        "release_confirmation_write_allowed_count": 0,
        "release_confirmation_assertion_allowed_count": 0,
        "release_acknowledgment_write_allowed_count": 0,
        "release_receipt_write_allowed_count": 0,
        "custody_receipt_record_allowed_count": 0,
        "release_custody_write_allowed_count": 0,
        "custody_transfer_allowed_count": 0,
        "release_record_write_allowed_count": 0,
        "handoff_release_allowed_count": 0,
        "operator_approval_allowed_count": 0,
        "clearance_decision_allowed_count": 0,
        "execution_allowed_count": 0,
        "latest_release_completion_id": None if latest is None else latest.get("release_completion_id"),
    }
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "release_completion_write_authority": "none_read_plane",
        "release_completion_assertion_authority": "none_read_plane",
        "release_confirmation_write_authority": "none_read_plane",
        "release_confirmation_assertion_authority": "none_read_plane",
        "release_acknowledgment_write_authority": "none_read_plane",
        "release_acknowledgment_assertion_authority": "none_read_plane",
        "release_receipt_write_authority": "none_read_plane",
        "release_receipt_assertion_authority": "none_read_plane",
        "custody_receipt_record_authority": "none_read_plane",
        "release_custody_write_authority": "none_read_plane",
        "release_custody_assertion_authority": "none_read_plane",
        "custody_transfer_authority": "none_read_plane",
        "release_handoff_write_authority": "none_read_plane",
        "release_handoff_assertion_authority": "none_read_plane",
        "release_packet_write_authority": "none_read_plane",
        "release_record_write_authority": "none_read_plane",
        "release_assertion_authority": "none_read_plane",
        "release_authorization_authority": "none_read_plane",
        "handoff_release_authority": "none_read_plane",
        "acceptance_record_write_authority": "none_read_plane",
        "operator_signoff_authority": "none_read_plane",
        "operator_approval_authority": "none_read_plane",
        "clearance_decision_authority": "none_read_plane",
        "artifact_mutation_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "adjudication_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
        "source_schema_version": source_payload.get("schema_version"),
        "search_root": source_payload.get("search_root"),
        "filters": {},
        "summary": summary,
        "release_completion_status_counts": _counts(filtered, "release_completion_status"),
        "release_completion_readiness_counts": _counts(filtered, "release_completion_readiness"),
        "source_release_confirmation_status_counts": _counts(filtered, "source_release_confirmation_status"),
        "source_release_confirmation_readiness_counts": _counts(filtered, "source_release_confirmation_readiness"),
        "source_release_acknowledgment_status_counts": _counts(filtered, "source_release_acknowledgment_status"),
        "source_release_acknowledgment_readiness_counts": _counts(filtered, "source_release_acknowledgment_readiness"),
        "source_release_receipt_status_counts": _counts(filtered, "source_release_receipt_status"),
        "source_release_receipt_readiness_counts": _counts(filtered, "source_release_receipt_readiness"),
        "source_release_custody_status_counts": _counts(filtered, "source_release_custody_status"),
        "source_release_custody_readiness_counts": _counts(filtered, "source_release_custody_readiness"),
        "source_release_handoff_status_counts": _counts(filtered, "source_release_handoff_status"),
        "source_release_handoff_readiness_counts": _counts(filtered, "source_release_handoff_readiness"),
        "source_release_packet_status_counts": _counts(filtered, "source_release_packet_status"),
        "source_release_packet_readiness_counts": _counts(filtered, "source_release_packet_readiness"),
        "source_release_status_counts": _counts(filtered, "source_release_status"),
        "source_release_readiness_counts": _counts(filtered, "source_release_readiness"),
        "source_acceptance_status_counts": _counts(filtered, "source_acceptance_status"),
        "source_acceptance_readiness_counts": _counts(filtered, "source_acceptance_readiness"),
        "evidence_lane_counts": _counts(filtered, "evidence_lane"),
        "priority_counts": _counts(filtered, "priority"),
        "severity_counts": _counts(filtered, "severity"),
        "trust_banner_counts": _counts(filtered, "trust_banner"),
        "owner_hint_counts": _counts(filtered, "owner_hint"),
        "source_degraded": _as_list(source_payload.get("degraded")),
        "degraded": _degraded(source_payload, filtered),
        "guardrails": [
            "read_plane_only_clearance_release_completion_no_completion_confirmation_acknowledgment_receipt_custody_transfer_handoff_packet_release_acceptance_signoff_approval_or_decision_is_written_here",
            "completion_cards_are_observations_derived_from_release_confirmations_not_operator_actions",
            "no_override_approval_signoff_validator_submission_adjudication_promotion_or_execution_authority",
        ],
        "routes": {
            "clearance_release_completion_board": "/ui/semantic-validator-handoff/clearance-release-completion-board",
            "clearance_release_confirmation_board": "/ui/semantic-validator-handoff/clearance-release-confirmation-board",
            "clearance_release_acknowledgment_board": "/ui/semantic-validator-handoff/clearance-release-acknowledgment-board",
        },
        "latest": latest,
        "release_completions": returned,
    }


def build_ui_semantic_validator_handoff_clearance_release_completion_board_latest_payload(
    *, repo_root: str | Path | None = None, search_root: str | Path | None = None
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_clearance_release_completion_board_payload(
        repo_root=repo_root, search_root=search_root, limit=1
    )


__all__ = [
    "build_ui_semantic_validator_handoff_clearance_release_completion_board_payload",
    "build_ui_semantic_validator_handoff_clearance_release_completion_board_latest_payload",
]
