"""Public payload builders for the clearance evidence matrix read-plane."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_clearance_evidence_matrix_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _as_list,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_evidence_matrix_rows import (
    _degraded,
    _matches,
    _matrix_cells,
    _matrix_row,
    _sort_row,
)

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the legacy facade at call time so existing tests and
    # operators can monkeypatch the facade builder name without reaching into
    # subphase modules.
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_evidence_matrix as facade

    return facade.build_ui_semantic_validator_handoff_clearance_checklist_payload


def build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload(*, repo_root: str | Path | None = None, search_root: str | Path | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: tuple[str, ...] = (), evidence_state: tuple[str, ...] = (), check_state: tuple[str, ...] = (), priority: tuple[str, ...] = (), severity: tuple[str, ...] = (), trust_banner: tuple[str, ...] = (), owner_hint: tuple[str, ...] = (), attention_required: bool | None = None, blocks_clearance: bool | None = None, requires_external_artifact: bool | None = None, limit: int = 200) -> dict[str, Any]:
    capped = max(1, min(int(limit or 200), _LIMIT_MAX))
    checklist_payload = _source_builder()(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, check_state=check_state, priority=priority, severity=severity, trust_banner=trust_banner, owner_hint=owner_hint, attention_required=attention_required, blocks_clearance=blocks_clearance, requires_external_artifact=requires_external_artifact, limit=_LIMIT_MAX)
    items = [row for row in checklist_payload.get("checklist_items", []) if isinstance(row, dict)]
    rows = sorted([_matrix_row(item, index, checklist_payload) for index, item in enumerate(items, start=1)], key=_sort_row)
    filtered = [row for row in rows if _matches(row, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=_norm_set(evidence_lane), evidence_state=_norm_set(evidence_state), check_state=_norm_set(check_state), priority=_norm_set(priority), severity=_norm_set(severity), trust_banner=_norm_set(trust_banner), owner_hint=_norm_set(owner_hint), attention_required=attention_required, blocks_clearance=blocks_clearance, requires_external_artifact=requires_external_artifact)]
    returned = filtered[:capped]
    latest = returned[0] if returned else None
    source_degraded = _as_list(checklist_payload.get("degraded"))
    degraded = _degraded(checklist_payload, filtered)
    cells = _matrix_cells(filtered)
    return {"schema_version": _SCHEMA_VERSION, "generated_at_utc": _utc_now(), "read_plane_only": True, "mutation_authority": "none_read_plane", "evidence_attestation_authority": "none_read_plane", "evidence_override_authority": "none_read_plane", "check_acknowledgment_authority": "none_read_plane", "check_override_authority": "none_read_plane", "clearance_decision_authority": "none_read_plane", "operator_approval_authority": "none_read_plane", "signoff_authority": "none_read_plane", "external_artifact_write_authority": "none_read_plane", "artifact_mutation_authority": "none_read_plane", "validator_submission_authority": "none_read_plane", "adjudication_authority": "none_read_plane", "promotion_authority": "none_read_plane", "execution_authority": "none_read_plane", "source_schema_version": checklist_payload.get("schema_version"), "search_root": checklist_payload.get("search_root"), "filters": {"experiment_id_contains": experiment_id_contains, "issue_contains": issue_contains, "evidence_lane": list(evidence_lane or ()), "evidence_state": list(evidence_state or ()), "check_state": list(check_state or ()), "priority": list(priority or ()), "severity": list(severity or ()), "trust_banner": list(trust_banner or ()), "owner_hint": list(owner_hint or ()), "attention_required": attention_required, "blocks_clearance": blocks_clearance, "requires_external_artifact": requires_external_artifact, "limit": capped}, "summary": {"source_checklist_item_count_total": len(items), "evidence_matrix_row_count_total": len(rows), "evidence_matrix_row_count_filtered": len(filtered), "evidence_matrix_row_count_returned": len(returned), "matrix_cell_count": len(cells), "attention_required_count": sum(1 for row in filtered if row.get("attention_required")), "blocked_evidence_count": sum(1 for row in filtered if row.get("evidence_state") == "BLOCKING_EVIDENCE_GAP"), "external_artifact_evidence_count": sum(1 for row in filtered if row.get("evidence_state") == "WAITING_EXTERNAL_ARTIFACT"), "verified_observation_count": sum(1 for row in filtered if row.get("evidence_state") == "VERIFIED_OBSERVATION"), "evidence_attestation_allowed_count": 0, "evidence_override_allowed_count": 0, "check_acknowledgment_allowed_count": 0, "check_override_allowed_count": 0, "clearance_decision_allowed_count": 0, "operator_approval_allowed_count": 0, "signoff_allowed_count": 0, "external_artifact_write_allowed_count": 0, "validator_submission_allowed_count": 0, "promotion_allowed_count": 0, "execution_allowed_count": 0, "latest_evidence_matrix_row_id": None if latest is None else latest.get("evidence_matrix_row_id")}, "evidence_lane_counts": _counts(filtered, "evidence_lane"), "evidence_state_counts": _counts(filtered, "evidence_state"), "coverage_state_counts": _counts(filtered, "coverage_state"), "check_state_counts": _counts(filtered, "check_state"), "priority_counts": _counts(filtered, "priority"), "severity_counts": _counts(filtered, "severity"), "owner_hint_counts": _counts(filtered, "owner_hint"), "trust_banner_counts": _counts(filtered, "trust_banner"), "source_route_counts": _counts(filtered, "source_route"), "source_degraded": source_degraded, "degraded": degraded, "guardrails": ["read_plane_only_clearance_evidence_matrix_no_attestation_or_override_is_performed_here", "matrix_rows_are_operator_visibility_not_clearance_decisions", "external_artifacts_and_source_evidence_must_be_managed_outside_this_projection", "no_acknowledgment_approval_signoff_validator_submission_adjudication_promotion_or_execution_authority"], "routes": {"clearance_evidence_matrix": "/ui/semantic-validator-handoff/clearance-evidence-matrix", "clearance_checklist": "/ui/semantic-validator-handoff/clearance-checklist", "clearance_dossier": "/ui/semantic-validator-handoff/clearance-dossier", "clearance_gate": "/ui/semantic-validator-handoff/clearance-gate", "resolution_plan": "/ui/semantic-validator-handoff/resolution-plan"}, "latest": latest, "matrix_cells": cells, "evidence_rows": returned}


def build_ui_semantic_validator_handoff_clearance_evidence_matrix_latest_payload(*, repo_root: str | Path | None = None, search_root: str | Path | None = None) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = [
    "build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload",
    "build_ui_semantic_validator_handoff_clearance_evidence_matrix_latest_payload",
]
