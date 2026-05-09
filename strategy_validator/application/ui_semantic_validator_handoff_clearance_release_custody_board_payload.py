"""Public payload builders for semantic validator handoff clearance release custody board."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_custody_board_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _as_list,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_custody_board_rows import (
    _degraded,
    _matches,
    _row,
    _sort,
)

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the compatibility facade at call time so tests/operators can
    # monkeypatch the historical source-builder symbol without importing submodules.
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_release_custody_board as facade

    return facade.build_ui_semantic_validator_handoff_clearance_release_handoff_board_payload


def build_ui_semantic_validator_handoff_clearance_release_custody_board_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: Iterable[str] | None = None,
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
    ready_for_human_custody_observation: bool | None = None,
    blocked: bool | None = None,
    waiting: bool | None = None,
    requires_acceptance_observation: bool | None = None,
    requires_external_artifact: bool | None = None,
    requires_release_handoff_review: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    source_payload = _source_builder()(repo_root=repo_root, search_root=search_root, limit=_LIMIT_MAX)
    source_rows = list(source_payload.get("release_handoffs") or [])
    rows = [_row(row, ordinal, source_payload) for ordinal, row in enumerate(source_rows, start=1)]
    rows.sort(key=_sort)
    filtered = [
        row
        for row in rows
        if _matches(
            row,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            evidence_lane=_norm_set(evidence_lane),
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
            ready_for_human_custody_observation=ready_for_human_custody_observation,
            blocked=blocked,
            waiting=waiting,
            requires_acceptance_observation=requires_acceptance_observation,
            requires_external_artifact=requires_external_artifact,
            requires_release_handoff_review=requires_release_handoff_review,
        )
    ]
    capped = max(1, min(int(limit or 200), _LIMIT_MAX))
    returned = filtered[:capped]
    latest = returned[0] if returned else None
    summary = {
        "source_release_handoff_count_total": len(source_rows),
        "release_custody_count_total": len(rows),
        "release_custody_count_filtered": len(filtered),
        "release_custody_count_returned": len(returned),
        "fail_closed_count": sum(1 for row in filtered if row.get("release_custody_readiness") == "FAIL_CLOSED"),
        "waiting_count": sum(1 for row in filtered if row.get("release_custody_readiness") == "WAITING"),
        "human_custody_ready_observation_count": sum(1 for row in filtered if row.get("release_custody_readiness") == "HUMAN_CUSTODY_READY_OBSERVATION"),
        "ready_for_human_custody_observation_count": sum(1 for row in filtered if row.get("ready_for_human_custody_observation")),
        "blocked_count": sum(1 for row in filtered if row.get("blocked")),
        "requires_acceptance_observation_count": sum(1 for row in filtered if row.get("requires_acceptance_observation")),
        "requires_external_artifact_count": sum(1 for row in filtered if row.get("requires_external_artifact")),
        "requires_release_handoff_review_count": sum(1 for row in filtered if row.get("requires_release_handoff_review")),
        "release_custody_write_allowed_count": 0,
        "custody_transfer_allowed_count": 0,
        "release_handoff_write_allowed_count": 0,
        "release_packet_write_allowed_count": 0,
        "release_record_write_allowed_count": 0,
        "handoff_release_allowed_count": 0,
        "operator_approval_allowed_count": 0,
        "clearance_decision_allowed_count": 0,
        "execution_allowed_count": 0,
        "latest_release_custody_id": None if latest is None else latest.get("release_custody_id"),
    }
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
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
        "filters": {
            "experiment_id_contains": experiment_id_contains,
            "issue_contains": issue_contains,
            "evidence_lane": list(evidence_lane or ()),
            "release_custody_status": list(release_custody_status or ()),
            "release_custody_readiness": list(release_custody_readiness or ()),
            "release_handoff_status": list(release_handoff_status or ()),
            "release_handoff_readiness": list(release_handoff_readiness or ()),
            "release_packet_status": list(release_packet_status or ()),
            "release_packet_readiness": list(release_packet_readiness or ()),
            "release_status": list(release_status or ()),
            "release_readiness": list(release_readiness or ()),
            "acceptance_status": list(acceptance_status or ()),
            "acceptance_readiness": list(acceptance_readiness or ()),
            "priority": list(priority or ()),
            "severity": list(severity or ()),
            "trust_banner": list(trust_banner or ()),
            "owner_hint": list(owner_hint or ()),
            "ready_for_human_custody_observation": ready_for_human_custody_observation,
            "blocked": blocked,
            "waiting": waiting,
            "requires_acceptance_observation": requires_acceptance_observation,
            "requires_external_artifact": requires_external_artifact,
            "requires_release_handoff_review": requires_release_handoff_review,
            "limit": capped,
        },
        "summary": summary,
        "release_custody_status_counts": _counts(filtered, "release_custody_status"),
        "release_custody_readiness_counts": _counts(filtered, "release_custody_readiness"),
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
            "read_plane_only_clearance_release_custody_no_custody_transfer_handoff_packet_release_acceptance_signoff_approval_or_decision_is_written_here",
            "custody_cards_are_observations_derived_from_release_handoffs_not_operator_actions",
            "no_override_approval_signoff_validator_submission_adjudication_promotion_or_execution_authority",
        ],
        "routes": {
            "clearance_release_custody_board": "/ui/semantic-validator-handoff/clearance-release-custody-board",
            "clearance_release_handoff_board": "/ui/semantic-validator-handoff/clearance-release-handoff-board",
        },
        "latest": latest,
        "release_custodies": returned,
    }


def build_ui_semantic_validator_handoff_clearance_release_custody_board_latest_payload(
    *, repo_root: str | Path | None = None, search_root: str | Path | None = None
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_clearance_release_custody_board_payload(
        repo_root=repo_root, search_root=search_root, limit=1
    )


__all__ = [
    "build_ui_semantic_validator_handoff_clearance_release_custody_board_payload",
    "build_ui_semantic_validator_handoff_clearance_release_custody_board_latest_payload",
]
