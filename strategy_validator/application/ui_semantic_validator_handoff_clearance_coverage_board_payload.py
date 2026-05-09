"""Public payload builders for the clearance coverage board read-plane."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_clearance_coverage_board_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _as_list,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_coverage_board_rows import (
    _cards_from_rows,
    _degraded,
    _matches,
)

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the legacy facade at call time so existing tests and
    # operators can monkeypatch the facade builder name without reaching into
    # subphase modules.
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_coverage_board as facade

    return facade.build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload


def build_ui_semantic_validator_handoff_clearance_coverage_board_payload(*, repo_root: str | Path | None = None, search_root: str | Path | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: tuple[str, ...] = (), evidence_state: tuple[str, ...] = (), coverage_status: tuple[str, ...] = (), check_state: tuple[str, ...] = (), priority: tuple[str, ...] = (), severity: tuple[str, ...] = (), trust_banner: tuple[str, ...] = (), owner_hint: tuple[str, ...] = (), attention_required: bool | None = None, blocks_clearance: bool | None = None, requires_external_artifact: bool | None = None, limit: int = 200) -> dict[str, Any]:
    capped = max(1, min(int(limit or 200), _LIMIT_MAX))
    matrix_payload = _source_builder()(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=evidence_lane, evidence_state=evidence_state, check_state=check_state, priority=priority, severity=severity, trust_banner=trust_banner, owner_hint=owner_hint, attention_required=attention_required, blocks_clearance=blocks_clearance, requires_external_artifact=requires_external_artifact, limit=_LIMIT_MAX)
    rows = [row for row in matrix_payload.get("evidence_rows", []) if isinstance(row, dict)]
    cards = _cards_from_rows(rows, matrix_payload)
    filtered = [card for card in cards if _matches(card, issue_contains=issue_contains, evidence_lane=_norm_set(evidence_lane), coverage_status=_norm_set(coverage_status), priority=_norm_set(priority), severity=_norm_set(severity), trust_banner=_norm_set(trust_banner), attention_required=attention_required, blocks_clearance=blocks_clearance, requires_external_artifact=requires_external_artifact)]
    returned = filtered[:capped]
    latest = returned[0] if returned else None
    source_degraded = _as_list(matrix_payload.get("degraded"))
    degraded = _degraded(matrix_payload, filtered)
    return {"schema_version": _SCHEMA_VERSION, "generated_at_utc": _utc_now(), "read_plane_only": True, "mutation_authority": "none_read_plane", "coverage_assertion_authority": "none_read_plane", "evidence_attestation_authority": "none_read_plane", "evidence_override_authority": "none_read_plane", "check_acknowledgment_authority": "none_read_plane", "check_override_authority": "none_read_plane", "clearance_decision_authority": "none_read_plane", "operator_approval_authority": "none_read_plane", "signoff_authority": "none_read_plane", "external_artifact_write_authority": "none_read_plane", "artifact_mutation_authority": "none_read_plane", "validator_submission_authority": "none_read_plane", "adjudication_authority": "none_read_plane", "promotion_authority": "none_read_plane", "execution_authority": "none_read_plane", "source_schema_version": matrix_payload.get("schema_version"), "search_root": matrix_payload.get("search_root"), "filters": {"experiment_id_contains": experiment_id_contains, "issue_contains": issue_contains, "evidence_lane": list(evidence_lane or ()), "evidence_state": list(evidence_state or ()), "coverage_status": list(coverage_status or ()), "check_state": list(check_state or ()), "priority": list(priority or ()), "severity": list(severity or ()), "trust_banner": list(trust_banner or ()), "owner_hint": list(owner_hint or ()), "attention_required": attention_required, "blocks_clearance": blocks_clearance, "requires_external_artifact": requires_external_artifact, "limit": capped}, "summary": {"source_evidence_matrix_row_count_total": len(rows), "coverage_card_count_total": len(cards), "coverage_card_count_filtered": len(filtered), "coverage_card_count_returned": len(returned), "attention_required_count": sum(1 for card in filtered if card.get("attention_required")), "blocked_lane_count": sum(1 for card in filtered if card.get("coverage_status") == "BLOCKED_BY_EVIDENCE_GAP"), "external_artifact_lane_count": sum(1 for card in filtered if card.get("coverage_status") == "WAITING_EXTERNAL_ARTIFACT"), "operator_review_lane_count": sum(1 for card in filtered if card.get("coverage_status") == "NEEDS_OPERATOR_REVIEW"), "observed_covered_lane_count": sum(1 for card in filtered if card.get("coverage_status") == "OBSERVED_COVERED"), "coverage_assertion_allowed_count": 0, "evidence_attestation_allowed_count": 0, "evidence_override_allowed_count": 0, "check_acknowledgment_allowed_count": 0, "check_override_allowed_count": 0, "clearance_decision_allowed_count": 0, "operator_approval_allowed_count": 0, "signoff_allowed_count": 0, "external_artifact_write_allowed_count": 0, "validator_submission_allowed_count": 0, "promotion_allowed_count": 0, "execution_allowed_count": 0, "latest_coverage_card_id": None if latest is None else latest.get("coverage_card_id")}, "coverage_status_counts": _counts(filtered, "coverage_status"), "evidence_lane_counts": _counts(filtered, "evidence_lane"), "priority_counts": _counts(filtered, "highest_priority"), "severity_counts": _counts(filtered, "highest_severity"), "trust_banner_counts": _counts(filtered, "trust_banner"), "source_degraded": source_degraded, "degraded": degraded, "guardrails": ["read_plane_only_clearance_coverage_board_no_coverage_assertion_or_attestation_is_performed_here", "coverage_cards_are_operator_visibility_not_clearance_decisions", "matrix_rows_and_external_artifacts_must_be_resolved_outside_this_projection", "no_acknowledgment_override_approval_signoff_validator_submission_adjudication_promotion_or_execution_authority"], "routes": {"clearance_coverage_board": "/ui/semantic-validator-handoff/clearance-coverage-board", "clearance_evidence_matrix": "/ui/semantic-validator-handoff/clearance-evidence-matrix", "clearance_checklist": "/ui/semantic-validator-handoff/clearance-checklist", "clearance_dossier": "/ui/semantic-validator-handoff/clearance-dossier", "clearance_gate": "/ui/semantic-validator-handoff/clearance-gate"}, "latest": latest, "coverage_cards": returned}


def build_ui_semantic_validator_handoff_clearance_coverage_board_latest_payload(*, repo_root: str | Path | None = None, search_root: str | Path | None = None) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_clearance_coverage_board_payload(repo_root=repo_root, search_root=search_root, limit=1)

__all__ = [
    "build_ui_semantic_validator_handoff_clearance_coverage_board_payload",
    "build_ui_semantic_validator_handoff_clearance_coverage_board_latest_payload",
]
