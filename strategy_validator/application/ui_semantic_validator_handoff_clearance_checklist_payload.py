"""Public payload builders for the semantic validator handoff clearance checklist."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_clearance_checklist_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _as_list,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_checklist_rows import (
    _degraded,
    _items_from_dossiers,
    _matches,
    _sort_item,
)

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the legacy facade at call time so tests and operators can
    # monkeypatch the facade source-builder name without reaching into subphase modules.
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_checklist as facade

    return facade.build_ui_semantic_validator_handoff_clearance_dossier_payload


def build_ui_semantic_validator_handoff_clearance_checklist_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    check_id_contains: str | None = None,
    check_state: tuple[str, ...] = (),
    review_posture: tuple[str, ...] = (),
    clearance_status: tuple[str, ...] = (),
    priority: tuple[str, ...] = (),
    severity: tuple[str, ...] = (),
    trust_banner: tuple[str, ...] = (),
    owner_hint: tuple[str, ...] = (),
    attention_required: bool | None = None,
    blocks_clearance: bool | None = None,
    requires_external_artifact: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    capped = max(1, min(int(limit or 200), _LIMIT_MAX))
    source_payload = _source_builder()(
        repo_root=repo_root,
        search_root=search_root,
        experiment_id_contains=experiment_id_contains,
        issue_contains=issue_contains,
        review_posture=review_posture,
        clearance_status=clearance_status,
        priority=priority,
        severity=severity,
        trust_banner=trust_banner,
        owner_hint=owner_hint,
        requires_external_artifact=requires_external_artifact,
        limit=_LIMIT_MAX,
    )
    dossiers = [row for row in source_payload.get("clearance_dossiers", []) if isinstance(row, dict)]
    all_items = sorted(_items_from_dossiers(dossiers, source_payload), key=_sort_item)
    filtered = [
        item
        for item in all_items
        if _matches(
            item,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            check_id_contains=check_id_contains,
            check_state=_norm_set(check_state),
            review_posture=_norm_set(review_posture),
            clearance_status=_norm_set(clearance_status),
            priority=_norm_set(priority),
            severity=_norm_set(severity),
            trust_banner=_norm_set(trust_banner),
            owner_hint=_norm_set(owner_hint),
            attention_required=attention_required,
            blocks_clearance=blocks_clearance,
            requires_external_artifact=requires_external_artifact,
        )
    ]
    returned = filtered[:capped]
    latest = returned[0] if returned else None
    source_degraded = _as_list(source_payload.get("degraded"))
    degraded = _degraded(source_payload, filtered)
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "check_acknowledgment_authority": "none_read_plane",
        "check_override_authority": "none_read_plane",
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
            "check_id_contains": check_id_contains,
            "check_state": list(check_state or ()),
            "review_posture": list(review_posture or ()),
            "clearance_status": list(clearance_status or ()),
            "priority": list(priority or ()),
            "severity": list(severity or ()),
            "trust_banner": list(trust_banner or ()),
            "owner_hint": list(owner_hint or ()),
            "attention_required": attention_required,
            "blocks_clearance": blocks_clearance,
            "requires_external_artifact": requires_external_artifact,
            "limit": capped,
        },
        "summary": {
            "source_clearance_dossier_count_total": len(dossiers),
            "checklist_item_count_total": len(all_items),
            "checklist_item_count_filtered": len(filtered),
            "checklist_item_count_returned": len(returned),
            "attention_required_count": sum(1 for item in filtered if item.get("attention_required")),
            "blocked_check_count": sum(1 for item in filtered if item.get("blocks_clearance")),
            "external_artifact_check_count": sum(1 for item in filtered if item.get("requires_external_artifact")),
            "pass_check_count": sum(1 for item in filtered if item.get("check_state") == "PASS"),
            "check_acknowledgment_allowed_count": 0,
            "check_override_allowed_count": 0,
            "dossier_materialization_allowed_count": 0,
            "clearance_decision_allowed_count": 0,
            "operator_approval_allowed_count": 0,
            "signoff_allowed_count": 0,
            "repair_execution_allowed_count": 0,
            "validator_submission_allowed_count": 0,
            "promotion_allowed_count": 0,
            "execution_allowed_count": 0,
            "latest_checklist_item_id": None if latest is None else latest.get("checklist_item_id"),
        },
        "check_state_counts": _counts(filtered, "check_state"),
        "check_id_counts": _counts(filtered, "check_id"),
        "review_posture_counts": _counts(filtered, "review_posture"),
        "clearance_status_counts": _counts(filtered, "clearance_status"),
        "priority_counts": _counts(filtered, "priority"),
        "severity_counts": _counts(filtered, "severity"),
        "owner_hint_counts": _counts(filtered, "owner_hint"),
        "trust_banner_counts": _counts(filtered, "trust_banner"),
        "route_counts": _counts(filtered, "route"),
        "source_degraded": source_degraded,
        "degraded": degraded,
        "guardrails": [
            "read_plane_only_clearance_checklist_no_acknowledgment_or_override_is_performed_here",
            "checklist_items_are_operator_visibility_rows_not_clearance_decisions",
            "external_artifacts_and_resolution_steps_must_be_handled_outside_this_projection",
            "no_approval_signoff_validator_submission_adjudication_promotion_or_execution_authority",
        ],
        "routes": {
            "clearance_checklist": "/ui/semantic-validator-handoff/clearance-checklist",
            "clearance_dossier": "/ui/semantic-validator-handoff/clearance-dossier",
            "clearance_gate": "/ui/semantic-validator-handoff/clearance-gate",
            "resolution_plan": "/ui/semantic-validator-handoff/resolution-plan",
            "audit_packet": "/ui/semantic-validator-handoff/audit-packet",
        },
        "latest": latest,
        "checklist_items": returned,
    }


def build_ui_semantic_validator_handoff_clearance_checklist_latest_payload(
    *, repo_root: str | Path | None = None, search_root: str | Path | None = None
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_clearance_checklist_payload(
        repo_root=repo_root, search_root=search_root, limit=1
    )


__all__ = [
    "build_ui_semantic_validator_handoff_clearance_checklist_payload",
    "build_ui_semantic_validator_handoff_clearance_checklist_latest_payload",
]
