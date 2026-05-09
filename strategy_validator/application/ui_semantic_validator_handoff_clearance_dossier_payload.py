"""Public payload builders for semantic validator handoff clearance dossiers."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_clearance_dossier_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _as_list,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_dossier_rows import (
    _degraded,
    _dossier_from_gate,
    _matches,
    _sort_dossier,
)

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the compatibility facade at call time so tests/operators can
    # monkeypatch the historical source-builder symbol without importing submodules.
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_dossier as facade

    return facade.build_ui_semantic_validator_handoff_clearance_gate_payload


def build_ui_semantic_validator_handoff_clearance_dossier_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    review_posture: tuple[str, ...] = (),
    clearance_status: tuple[str, ...] = (),
    priority: tuple[str, ...] = (),
    severity: tuple[str, ...] = (),
    trust_banner: tuple[str, ...] = (),
    owner_hint: tuple[str, ...] = (),
    handoff_clearance_blocked: bool | None = None,
    candidate_for_operator_clearance_review: bool | None = None,
    requires_external_artifact: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    capped = max(1, min(int(limit or 200), _LIMIT_MAX))
    source_payload = _source_builder()(
        repo_root=repo_root,
        search_root=search_root,
        experiment_id_contains=experiment_id_contains,
        issue_contains=issue_contains,
        clearance_status=clearance_status,
        priority=priority,
        severity=severity,
        trust_banner=trust_banner,
        owner_hint=owner_hint,
        requires_external_artifact=requires_external_artifact,
        handoff_clearance_blocked=handoff_clearance_blocked,
        candidate_for_operator_clearance_review=candidate_for_operator_clearance_review,
        limit=_LIMIT_MAX,
    )
    gates = [gate for gate in source_payload.get("clearance_gates", []) if isinstance(gate, dict)]
    dossiers = sorted(
        [_dossier_from_gate(gate, index + 1, source_payload) for index, gate in enumerate(gates)],
        key=_sort_dossier,
    )
    filtered = [
        row
        for row in dossiers
        if _matches(
            row,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            review_posture=_norm_set(review_posture),
            clearance_status=_norm_set(clearance_status),
            priority=_norm_set(priority),
            severity=_norm_set(severity),
            trust_banner=_norm_set(trust_banner),
            owner_hint=_norm_set(owner_hint),
            handoff_clearance_blocked=handoff_clearance_blocked,
            candidate_for_operator_clearance_review=candidate_for_operator_clearance_review,
            requires_external_artifact=requires_external_artifact,
        )
    ]
    returned = filtered[:capped]
    latest = returned[0] if returned else None
    source_degraded = _as_list(source_payload.get("degraded"))
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "dossier_materialization_authority": "none_read_plane",
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
        "source_schema_version": source_payload.get("schema_version"),
        "search_root": source_payload.get("search_root"),
        "filters": {
            "experiment_id_contains": experiment_id_contains,
            "issue_contains": issue_contains,
            "review_posture": list(review_posture or ()),
            "clearance_status": list(clearance_status or ()),
            "priority": list(priority or ()),
            "severity": list(severity or ()),
            "trust_banner": list(trust_banner or ()),
            "owner_hint": list(owner_hint or ()),
            "handoff_clearance_blocked": handoff_clearance_blocked,
            "candidate_for_operator_clearance_review": candidate_for_operator_clearance_review,
            "requires_external_artifact": requires_external_artifact,
            "limit": capped,
        },
        "summary": {
            "source_clearance_gate_count_total": len(gates),
            "clearance_dossier_count_total": len(dossiers),
            "clearance_dossier_count_filtered": len(filtered),
            "clearance_dossier_count_returned": len(returned),
            "blocked_dossier_count": sum(1 for row in filtered if row.get("review_posture") == "CLEARANCE_BLOCKED"),
            "waiting_external_artifact_dossier_count": sum(1 for row in filtered if row.get("review_posture") == "WAITING_EXTERNAL_ARTIFACT"),
            "operator_review_observation_count": sum(1 for row in filtered if row.get("review_posture") == "OPERATOR_REVIEW_OBSERVATION"),
            "monitoring_observation_count": sum(1 for row in filtered if row.get("review_posture") == "MONITORING_OBSERVATION"),
            "observed_clear_dossier_count": sum(1 for row in filtered if row.get("review_posture") == "OBSERVED_CLEAR_NO_ESCALATIONS"),
            "candidate_for_operator_clearance_review_count": sum(1 for row in filtered if row.get("candidate_for_operator_clearance_review")),
            "requires_external_artifact_count": sum(1 for row in filtered if row.get("requires_external_artifact")),
            "handoff_clearance_blocked_count": sum(1 for row in filtered if row.get("handoff_clearance_blocked")),
            "failed_or_attention_check_count": sum(int(row.get("failed_or_attention_check_count") or 0) for row in filtered),
            "dossier_materialization_allowed_count": 0,
            "clearance_decision_allowed_count": 0,
            "operator_approval_allowed_count": 0,
            "signoff_allowed_count": 0,
            "repair_execution_allowed_count": 0,
            "validator_submission_allowed_count": 0,
            "promotion_allowed_count": 0,
            "execution_allowed_count": 0,
            "latest_clearance_dossier_id": None if latest is None else latest.get("clearance_dossier_id"),
        },
        "review_posture_counts": _counts(filtered, "review_posture"),
        "clearance_status_counts": _counts(filtered, "clearance_status"),
        "priority_counts": _counts(filtered, "priority"),
        "severity_counts": _counts(filtered, "severity"),
        "owner_hint_counts": _counts(filtered, "owner_hint"),
        "trust_banner_counts": _counts(filtered, "trust_banner"),
        "source_degraded": source_degraded,
        "degraded": _degraded(source_payload, filtered),
        "guardrails": [
            "read_plane_only_clearance_dossier_no_approval_or_signoff_is_performed_here",
            "clearance_dossiers_are_operator_visibility_packets_not_evidence_mutations",
            "resolution_steps_must_be_acknowledged_or_resolved_outside_this_projection",
            "no_validator_submission_adjudication_promotion_or_execution_authority",
        ],
        "routes": {
            "clearance_dossier": "/ui/semantic-validator-handoff/clearance-dossier",
            "clearance_gate": "/ui/semantic-validator-handoff/clearance-gate",
            "resolution_plan": "/ui/semantic-validator-handoff/resolution-plan",
            "escalation_board": "/ui/semantic-validator-handoff/escalation-board",
            "action_queue": "/ui/semantic-validator-handoff/action-queue",
            "audit_packet": "/ui/semantic-validator-handoff/audit-packet",
        },
        "latest": latest,
        "clearance_dossiers": returned,
    }


def build_ui_semantic_validator_handoff_clearance_dossier_latest_payload(
    *, repo_root: str | Path | None = None, search_root: str | Path | None = None
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_clearance_dossier_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = [
    "build_ui_semantic_validator_handoff_clearance_dossier_payload",
    "build_ui_semantic_validator_handoff_clearance_dossier_latest_payload",
]
