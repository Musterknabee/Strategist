from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_closeout_board as m


def _verification_board_payload() -> dict[str, object]:
    def card(lane: str, status: str, result: str, *, passed: bool = False, priority: str = "P2", severity: str = "INFO") -> dict[str, object]:
        return {"verification_card_id": f"verification-{lane}-{status}", "schema_version": "ui_semantic_validator_handoff_clearance_verification_board/v1", "verification_status": status, "verification_result": result, "verification_passed": passed, "evidence_lane": lane, "phase": "AUTHORIZED_CLEARANCE_REVIEW" if passed else "BLOCKER_TRIAGE", "step_state": "READY_FOR_AUTHORIZED_CLEARANCE_REVIEW" if passed else "BLOCKED_CLEARANCE_STEP", "action_state": "READY_REVIEW_CANDIDATE" if passed else "BLOCKED_ACTION", "source_resolution_step_id": f"step-{lane}", "source_action_id": f"action-{lane}", "source_operation_card_id": f"operation-{lane}", "source_coverage_card_id": f"coverage-{lane}", "priority": priority, "severity": severity, "trust_banner": "TRUSTED" if passed else "TRUST_RESTRICTED", "owner_hint": "human_operator_clearance_owner", "owner_hints": ["human_operator_clearance_owner"], "check_ids": [f"check-{lane}"], "issue_codes": [f"ISSUE_{lane}"], "experiment_ids": ["EXP-1"], "continuity_ids": ["CONT-1"], "audit_packet_ids": [f"PKT-{lane}"], "blocks_handoff_clearance": status == "BLOCKING_SOURCE_ACTION_VISIBLE", "requires_external_artifact": status == "EXTERNAL_ARTIFACT_STILL_REQUIRED", "requires_human_review": status == "HUMAN_REVIEW_STILL_REQUIRED", "verification_gate": "source_resolution_step_resolved_or_reclassified", "verification_note": f"Verification note for {lane}"}
    return {"schema_version": "ui_semantic_validator_handoff_clearance_verification_board/v1", "search_root": "synthetic", "degraded": ["SOURCE_VERIFY_DEGRADED"], "verification_cards": [card("BLOCKER", "BLOCKING_SOURCE_ACTION_VISIBLE", "FAIL_CLOSED", priority="P0", severity="HIGH"), card("EXTERNAL", "EXTERNAL_ARTIFACT_STILL_REQUIRED", "WAITING", priority="P1", severity="WARN"), card("REVIEW", "HUMAN_REVIEW_STILL_REQUIRED", "WAITING", priority="P2", severity="MEDIUM"), card("READY", "READY_FOR_AUTHORIZED_REVIEW_OBSERVED", "REVIEW_OBSERVATION", passed=True, priority="P3", severity="INFO")]}


def test_clearance_closeout_board_groups_verification_cards_and_preserves_firewall(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_verification_board_payload", lambda **_: _verification_board_payload())
    payload = m.build_ui_semantic_validator_handoff_clearance_closeout_board_payload()
    first = payload["closeout_cards"][0]
    assert payload["schema_version"] == "ui_semantic_validator_handoff_clearance_closeout_board/v1"
    assert payload["read_plane_only"] is True
    assert first["closeout_status"] == "CLEARANCE_CLOSEOUT_BLOCKED"
    assert first["closeout_readiness"] == "FAIL_CLOSED"
    assert first["closeout_write_authority"] == "none_read_plane"
    assert first["clearance_decision_authority"] == "none_read_plane"
    assert first["operator_approval_authority"] == "none_read_plane"
    assert first["signoff_authority"] == "none_read_plane"
    assert payload["summary"]["closeout_write_allowed_count"] == 0
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_CLOSEOUT_FAIL_CLOSED_PRESENT" in payload["degraded"]


def test_clearance_closeout_board_filters_external_artifact_waiting(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_verification_board_payload", lambda **_: _verification_board_payload())
    payload = m.build_ui_semantic_validator_handoff_clearance_closeout_board_payload(closeout_status=("CLEARANCE_CLOSEOUT_WAITING_EXTERNAL_ARTIFACT",))
    assert payload["summary"]["closeout_card_count_returned"] == 1
    card = payload["closeout_cards"][0]
    assert card["evidence_lane"] == "EXTERNAL"
    assert card["closeout_readiness"] == "WAITING"
    assert card["external_artifact_write_authority"] == "none_read_plane"
    assert "external artifact" in card["closeout_note"]


def test_clearance_closeout_ready_observation_is_not_approval_or_signoff(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_verification_board_payload", lambda **_: _verification_board_payload())
    payload = m.build_ui_semantic_validator_handoff_clearance_closeout_board_payload(ready_for_authorized_clearance_review=True)
    assert payload["summary"]["closeout_card_count_returned"] == 1
    card = payload["closeout_cards"][0]
    assert card["evidence_lane"] == "READY"
    assert card["closeout_status"] == "CLEARANCE_CLOSEOUT_READY_FOR_AUTHORIZED_REVIEW"
    assert card["closeout_readiness"] == "REVIEW_READY_OBSERVATION"
    assert card["closeout_write_authority"] == "none_read_plane"
    assert card["operator_approval_authority"] == "none_read_plane"
    assert card["signoff_authority"] == "none_read_plane"
    assert "no approval" in card["closeout_note"].lower()
