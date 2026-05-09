from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_coverage_board as m


def _matrix(kind: str = "blocked") -> dict[str, object]:
    if kind == "clear":
        rows = [
            {"evidence_matrix_row_id": "row-resolution-pass", "evidence_lane": "RESOLUTION_PLAN", "evidence_state": "VERIFIED_OBSERVATION", "coverage_state": "OBSERVED_PRESENT", "attention_required": False, "blocks_clearance": False, "requires_external_artifact": False, "check_id": "resolution_steps_clear", "source_route": "/ui/semantic-validator-handoff/resolution-plan", "priority": "P3", "severity": "INFO", "trust_banner": "TRUSTED", "owner_hint": "human_operator_clearance_owner", "issue_codes": [], "phase_set": []},
            {"evidence_matrix_row_id": "row-boundary-pass", "evidence_lane": "AUTHORITY_BOUNDARY", "evidence_state": "VERIFIED_OBSERVATION", "coverage_state": "OBSERVED_PRESENT", "attention_required": False, "blocks_clearance": False, "requires_external_artifact": False, "check_id": "operator_review_boundary_preserved", "source_route": "/ui/semantic-validator-handoff/clearance-dossier", "priority": "P3", "severity": "INFO", "trust_banner": "TRUSTED", "owner_hint": "human_operator_clearance_owner", "issue_codes": [], "phase_set": []},
        ]
        degraded: list[str] = []
    elif kind == "external":
        rows = [{"evidence_matrix_row_id": "row-external", "evidence_lane": "EXTERNAL_ARTIFACT", "evidence_state": "WAITING_EXTERNAL_ARTIFACT", "coverage_state": "WAITING_EXTERNAL_ARTIFACT", "attention_required": True, "blocks_clearance": False, "requires_external_artifact": True, "check_id": "external_artifact_gap_absent", "source_route": "/ui/semantic-validator-handoff/clearance-gate", "priority": "P1", "severity": "WARN", "trust_banner": "TRUST_RESTRICTED", "owner_hint": "human_operator_clearance_owner", "issue_codes": ["EXTERNAL_ARTIFACT_REQUIRED"], "phase_set": ["EXTERNAL_ARTIFACT_COLLECTION"]}]
        degraded = ["SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_EVIDENCE_MATRIX_WAITING_EXTERNAL_ARTIFACT"]
    else:
        rows = [
            {"evidence_matrix_row_id": "row-blocked", "evidence_lane": "CLEARANCE_GATE", "evidence_state": "BLOCKING_EVIDENCE_GAP", "coverage_state": "MISSING_OR_BLOCKED", "attention_required": True, "blocks_clearance": True, "requires_external_artifact": False, "check_id": "handoff_not_blocked", "source_route": "/ui/semantic-validator-handoff/clearance-gate", "priority": "P0", "severity": "HIGH", "trust_banner": "TRUST_RESTRICTED", "owner_hint": "human_operator_clearance_owner", "issue_codes": ["BLOCKED_RESOLUTION_STEP"], "phase_set": ["BLOCKER_TRIAGE"]},
            {"evidence_matrix_row_id": "row-review", "evidence_lane": "RESOLUTION_PLAN", "evidence_state": "ATTENTION_REQUIRED", "coverage_state": "NEEDS_OPERATOR_REVIEW", "attention_required": True, "blocks_clearance": False, "requires_external_artifact": False, "check_id": "resolution_steps_clear", "source_route": "/ui/semantic-validator-handoff/resolution-plan", "priority": "P1", "severity": "WARN", "trust_banner": "TRUST_RESTRICTED", "owner_hint": "human_operator_clearance_owner", "issue_codes": ["RESOLUTION_STEP_PRESENT"], "phase_set": ["BLOCKER_TRIAGE"]},
        ]
        degraded = ["SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_EVIDENCE_MATRIX_BLOCKED"]
    return {"schema_version": "ui_semantic_validator_handoff_clearance_evidence_matrix/v1", "search_root": "synthetic", "degraded": degraded, "summary": {"evidence_matrix_row_count_total": len(rows)}, "evidence_rows": rows}


def test_clearance_coverage_board_prioritizes_blocked_lane_without_authority(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload", lambda **_: _matrix("blocked"))
    payload = m.build_ui_semantic_validator_handoff_clearance_coverage_board_payload(blocks_clearance=True)
    card = payload["coverage_cards"][0]
    assert card["coverage_status"] == "BLOCKED_BY_EVIDENCE_GAP"
    assert card["evidence_lane"] == "CLEARANCE_GATE"
    assert card["blocks_clearance"] is True
    assert card["coverage_assertion_authority"] == "none_read_plane"
    assert card["evidence_attestation_authority"] == "none_read_plane"
    assert card["operator_approval_authority"] == "none_read_plane"
    assert card["signoff_authority"] == "none_read_plane"
    assert card["execution_authority"] == "none_read_plane"
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_COVERAGE_BOARD_BLOCKED" in payload["degraded"]


def test_clearance_coverage_board_external_artifact_filter(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload", lambda **_: _matrix("external"))
    payload = m.build_ui_semantic_validator_handoff_clearance_coverage_board_payload(coverage_status=("WAITING_EXTERNAL_ARTIFACT",))
    assert payload["summary"]["external_artifact_lane_count"] == 1
    card = payload["coverage_cards"][0]
    assert card["evidence_lane"] == "EXTERNAL_ARTIFACT"
    assert card["coverage_status"] == "WAITING_EXTERNAL_ARTIFACT"
    assert card["requires_external_artifact_count"] == 1
    assert card["external_artifact_write_authority"] == "none_read_plane"


def test_clearance_coverage_board_observed_coverage_is_not_clearance(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload", lambda **_: _matrix("clear"))
    payload = m.build_ui_semantic_validator_handoff_clearance_coverage_board_payload(coverage_status=("OBSERVED_COVERED",))
    assert payload["summary"]["observed_covered_lane_count"] == 2
    assert payload["summary"]["coverage_assertion_allowed_count"] == 0
    assert payload["summary"]["evidence_attestation_allowed_count"] == 0
    assert payload["summary"]["operator_approval_allowed_count"] == 0
    assert payload["summary"]["signoff_allowed_count"] == 0
    assert {card["coverage_status"] for card in payload["coverage_cards"]} == {"OBSERVED_COVERED"}
    assert all(card["clearance_decision_authority"] == "none_read_plane" for card in payload["coverage_cards"])
