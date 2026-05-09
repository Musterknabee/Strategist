"""Public payload builders for semantic validator handoff clearance signoff packet."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_clearance_signoff_packet_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _as_list,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_signoff_packet_rows import (
    _degraded,
    _matches,
    _packet_from_docket,
    _sort_packet,
)

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the compatibility facade at call time so tests/operators can
    # monkeypatch the historical source-builder symbol without importing submodules.
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_signoff_packet as facade

    return facade.build_ui_semantic_validator_handoff_clearance_review_docket_payload


def build_ui_semantic_validator_handoff_clearance_signoff_packet_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: tuple[str, ...] = (),
    signoff_status: tuple[str, ...] = (),
    signoff_readiness: tuple[str, ...] = (),
    docket_status: tuple[str, ...] = (),
    docket_readiness: tuple[str, ...] = (),
    closeout_status: tuple[str, ...] = (),
    priority: tuple[str, ...] = (),
    severity: tuple[str, ...] = (),
    trust_banner: tuple[str, ...] = (),
    owner_hint: tuple[str, ...] = (),
    ready_for_human_signoff_observation: bool | None = None,
    blocked: bool | None = None,
    waiting: bool | None = None,
    requires_authorized_review: bool | None = None,
    requires_external_artifact: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    capped = max(1, min(int(limit or 200), _LIMIT_MAX))
    source_payload = _source_builder()(
        repo_root=repo_root,
        search_root=search_root,
        limit=_LIMIT_MAX,
    )
    source_rows = [row for row in source_payload.get("review_dockets", []) if isinstance(row, dict)]
    rows = sorted(
        [_packet_from_docket(row, index, source_payload) for index, row in enumerate(source_rows, start=1)],
        key=_sort_packet,
    )
    filtered = [
        row
        for row in rows
        if _matches(
            row,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            evidence_lane=_norm_set(evidence_lane),
            signoff_status=_norm_set(signoff_status),
            signoff_readiness=_norm_set(signoff_readiness),
            docket_status=_norm_set(docket_status),
            docket_readiness=_norm_set(docket_readiness),
            closeout_status=_norm_set(closeout_status),
            priority=_norm_set(priority),
            severity=_norm_set(severity),
            trust_banner=_norm_set(trust_banner),
            owner_hint=_norm_set(owner_hint),
            ready_for_human_signoff_observation=ready_for_human_signoff_observation,
            blocked=blocked,
            waiting=waiting,
            requires_authorized_review=requires_authorized_review,
            requires_external_artifact=requires_external_artifact,
        )
    ]
    returned = filtered[:capped]
    latest = returned[0] if returned else None
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "signoff_packet_write_authority": "none_read_plane",
        "signoff_record_write_authority": "none_read_plane",
        "signoff_assertion_authority": "none_read_plane",
        "operator_signoff_authority": "none_read_plane",
        "operator_approval_authority": "none_read_plane",
        "review_record_write_authority": "none_read_plane",
        "review_assertion_authority": "none_read_plane",
        "review_authorization_authority": "none_read_plane",
        "closeout_write_authority": "none_read_plane",
        "closeout_assertion_authority": "none_read_plane",
        "clearance_decision_authority": "none_read_plane",
        "verification_write_authority": "none_read_plane",
        "verification_assertion_authority": "none_read_plane",
        "completion_assertion_authority": "none_read_plane",
        "repair_execution_authority": "none_read_plane",
        "action_execution_authority": "none_read_plane",
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
            "signoff_status": list(signoff_status or ()),
            "signoff_readiness": list(signoff_readiness or ()),
            "docket_status": list(docket_status or ()),
            "docket_readiness": list(docket_readiness or ()),
            "closeout_status": list(closeout_status or ()),
            "priority": list(priority or ()),
            "severity": list(severity or ()),
            "trust_banner": list(trust_banner or ()),
            "owner_hint": list(owner_hint or ()),
            "ready_for_human_signoff_observation": ready_for_human_signoff_observation,
            "blocked": blocked,
            "waiting": waiting,
            "requires_authorized_review": requires_authorized_review,
            "requires_external_artifact": requires_external_artifact,
            "limit": capped,
        },
        "summary": {
            "source_review_docket_count_total": len(source_rows),
            "signoff_packet_count_total": len(rows),
            "signoff_packet_count_filtered": len(filtered),
            "signoff_packet_count_returned": len(returned),
            "fail_closed_count": sum(1 for row in filtered if row.get("signoff_readiness") == "FAIL_CLOSED"),
            "waiting_count": sum(1 for row in filtered if row.get("signoff_readiness") == "WAITING"),
            "signoff_ready_observation_count": sum(1 for row in filtered if row.get("signoff_readiness") == "SIGNOFF_READY_OBSERVATION"),
            "ready_for_human_signoff_observation_count": sum(1 for row in filtered if row.get("ready_for_human_signoff_observation")),
            "blocked_count": sum(1 for row in filtered if row.get("blocked")),
            "requires_authorized_review_count": sum(1 for row in filtered if row.get("requires_authorized_review")),
            "requires_external_artifact_count": sum(1 for row in filtered if row.get("requires_external_artifact")),
            "signoff_packet_write_allowed_count": 0,
            "signoff_record_write_allowed_count": 0,
            "signoff_assertion_allowed_count": 0,
            "operator_signoff_allowed_count": 0,
            "operator_approval_allowed_count": 0,
            "review_record_write_allowed_count": 0,
            "review_assertion_allowed_count": 0,
            "review_authorization_allowed_count": 0,
            "closeout_write_allowed_count": 0,
            "closeout_assertion_allowed_count": 0,
            "clearance_decision_allowed_count": 0,
            "verification_write_allowed_count": 0,
            "verification_assertion_allowed_count": 0,
            "completion_assertion_allowed_count": 0,
            "repair_execution_allowed_count": 0,
            "action_execution_allowed_count": 0,
            "external_artifact_write_allowed_count": 0,
            "artifact_mutation_allowed_count": 0,
            "validator_submission_allowed_count": 0,
            "adjudication_allowed_count": 0,
            "promotion_allowed_count": 0,
            "execution_allowed_count": 0,
            "latest_signoff_packet_id": None if latest is None else latest.get("signoff_packet_id"),
        },
        "signoff_status_counts": _counts(filtered, "signoff_status"),
        "signoff_readiness_counts": _counts(filtered, "signoff_readiness"),
        "source_docket_status_counts": _counts(filtered, "source_docket_status"),
        "source_docket_readiness_counts": _counts(filtered, "source_docket_readiness"),
        "source_closeout_status_counts": _counts(filtered, "source_closeout_status"),
        "evidence_lane_counts": _counts(filtered, "evidence_lane"),
        "priority_counts": _counts(filtered, "priority"),
        "severity_counts": _counts(filtered, "severity"),
        "trust_banner_counts": _counts(filtered, "trust_banner"),
        "owner_hint_counts": _counts(filtered, "owner_hint"),
        "source_degraded": _as_list(source_payload.get("degraded")),
        "degraded": _degraded(source_payload, filtered),
        "guardrails": [
            "read_plane_only_clearance_signoff_packet_no_packet_write_signoff_record_approval_or_decision_is_written_here",
            "signoff_packets_are_observations_derived_from_review_docket_rows_not_operator_actions",
            "ready_for_human_signoff_observation_only_means_review_docket_sources_observe_signoff_readiness",
            "no_override_approval_signoff_validator_submission_adjudication_promotion_or_execution_authority",
        ],
        "routes": {
            "clearance_signoff_packet": "/ui/semantic-validator-handoff/clearance-signoff-packet",
            "clearance_review_docket": "/ui/semantic-validator-handoff/clearance-review-docket",
            "clearance_closeout_board": "/ui/semantic-validator-handoff/clearance-closeout-board",
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
        "signoff_packets": returned,
    }


def build_ui_semantic_validator_handoff_clearance_signoff_packet_latest_payload(
    *, repo_root: str | Path | None = None, search_root: str | Path | None = None
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_clearance_signoff_packet_payload(
        repo_root=repo_root,
        search_root=search_root,
        limit=1,
    )


__all__ = [
    "build_ui_semantic_validator_handoff_clearance_signoff_packet_payload",
    "build_ui_semantic_validator_handoff_clearance_signoff_packet_latest_payload",
]
