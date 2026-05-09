from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_evidence_matrix as m


def _checklist(kind: str = "blocked") -> dict[str, object]:
    if kind == "clear":
        items = [
            {"checklist_item_id": "item-pass-resolution", "check_id": "resolution_steps_clear", "check_state": "PASS", "attention_required": False, "blocks_clearance": False, "requires_external_artifact": False, "route": "/ui/semantic-validator-handoff/resolution-plan", "scope_key": "GLOBAL_SEMANTIC_VALIDATOR_HANDOFF", "priority": "P3", "severity": "INFO", "trust_banner": "TRUSTED", "owner_hint": "human_operator_clearance_owner", "evidence": "source_resolution_step_count=0", "issue_codes": [], "phase_set": []},
            {"checklist_item_id": "item-pass-boundary", "check_id": "operator_review_boundary_preserved", "check_state": "PASS", "attention_required": False, "blocks_clearance": False, "requires_external_artifact": False, "route": "/ui/semantic-validator-handoff/clearance-dossier", "scope_key": "GLOBAL_SEMANTIC_VALIDATOR_HANDOFF", "priority": "P3", "severity": "INFO", "trust_banner": "TRUSTED", "owner_hint": "human_operator_clearance_owner", "evidence": "approval_authority=none_read_plane", "issue_codes": [], "phase_set": []},
        ]
        degraded: list[str] = []
    elif kind == "external":
        items = [{"checklist_item_id": "item-external", "check_id": "external_artifact_gap_absent", "check_state": "WAITING_EXTERNAL_ARTIFACT", "attention_required": True, "blocks_clearance": False, "requires_external_artifact": True, "route": "/ui/semantic-validator-handoff/clearance-gate", "experiment_id": "EXP-MATRIX-1", "scope_key": "EXP-MATRIX-1", "priority": "P1", "severity": "WARN", "trust_banner": "TRUST_RESTRICTED", "owner_hint": "human_operator_clearance_owner", "evidence": "requires_external_artifact=True", "issue_codes": ["EXTERNAL_ARTIFACT_REQUIRED"], "phase_set": ["EXTERNAL_ARTIFACT_COLLECTION"]}]
        degraded = ["SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_CHECKLIST_WAITING_EXTERNAL_ARTIFACT"]
    else:
        items = [
            {"checklist_item_id": "item-blocked", "check_id": "handoff_not_blocked", "check_state": "BLOCKED", "attention_required": True, "blocks_clearance": True, "requires_external_artifact": False, "route": "/ui/semantic-validator-handoff/clearance-gate", "experiment_id": "EXP-MATRIX-1", "scope_key": "EXP-MATRIX-1", "priority": "P0", "severity": "HIGH", "trust_banner": "TRUST_RESTRICTED", "owner_hint": "human_operator_clearance_owner", "evidence": "clearance_status=BLOCKED_BY_RESOLUTION_STEP", "issue_codes": ["BLOCKED_RESOLUTION_STEP"], "phase_set": ["BLOCKER_TRIAGE"]},
            {"checklist_item_id": "item-attention", "check_id": "resolution_steps_clear", "check_state": "ATTENTION_REQUIRED", "attention_required": True, "blocks_clearance": False, "requires_external_artifact": False, "route": "/ui/semantic-validator-handoff/resolution-plan", "experiment_id": "EXP-MATRIX-1", "scope_key": "EXP-MATRIX-1", "priority": "P1", "severity": "WARN", "trust_banner": "TRUST_RESTRICTED", "owner_hint": "human_operator_clearance_owner", "evidence": "source_resolution_step_count=1", "issue_codes": ["RESOLUTION_STEP_PRESENT"], "phase_set": ["BLOCKER_TRIAGE"]},
        ]
        degraded = ["SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_CHECKLIST_BLOCKED"]
    return {"schema_version": "ui_semantic_validator_handoff_clearance_checklist/v1", "search_root": "synthetic", "degraded": degraded, "summary": {"checklist_item_count_total": len(items)}, "checklist_items": items}


def test_clearance_evidence_matrix_prioritizes_blocking_evidence_without_authority(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_checklist_payload", lambda **_: _checklist("blocked"))
    payload = m.build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload(blocks_clearance=True)
    row = payload["evidence_rows"][0]
    assert row["evidence_state"] == "BLOCKING_EVIDENCE_GAP"
    assert row["evidence_lane"] == "CLEARANCE_GATE"
    assert row["blocks_clearance"] is True
    assert row["evidence_attestation_authority"] == "none_read_plane"
    assert row["evidence_override_authority"] == "none_read_plane"
    assert row["operator_approval_authority"] == "none_read_plane"
    assert row["signoff_authority"] == "none_read_plane"
    assert row["execution_authority"] == "none_read_plane"
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_EVIDENCE_MATRIX_BLOCKED" in payload["degraded"]


def test_clearance_evidence_matrix_external_artifact_filter(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_checklist_payload", lambda **_: _checklist("external"))
    payload = m.build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload(evidence_lane=("EXTERNAL_ARTIFACT",))
    assert payload["summary"]["external_artifact_evidence_count"] == 1
    row = payload["evidence_rows"][0]
    assert row["evidence_lane"] == "EXTERNAL_ARTIFACT"
    assert row["evidence_state"] == "WAITING_EXTERNAL_ARTIFACT"
    assert row["external_artifact_write_authority"] == "none_read_plane"
    assert payload["matrix_cells"][0]["requires_external_artifact_count"] == 1


def test_clearance_evidence_matrix_passes_are_visibility_not_clearance(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_checklist_payload", lambda **_: _checklist("clear"))
    payload = m.build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload(evidence_state=("VERIFIED_OBSERVATION",))
    assert payload["summary"]["attention_required_count"] == 0
    assert payload["summary"]["verified_observation_count"] == 2
    assert payload["summary"]["evidence_attestation_allowed_count"] == 0
    assert payload["summary"]["operator_approval_allowed_count"] == 0
    assert payload["summary"]["signoff_allowed_count"] == 0
    assert {row["evidence_state"] for row in payload["evidence_rows"]} == {"VERIFIED_OBSERVATION"}
    assert all(row["clearance_decision_authority"] == "none_read_plane" for row in payload["evidence_rows"])
