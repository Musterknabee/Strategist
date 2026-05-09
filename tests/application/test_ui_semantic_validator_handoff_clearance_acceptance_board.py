from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_acceptance_board as m


def _signoff_packet_payload() -> dict[str, object]:
    def packet(lane: str, status: str, readiness: str, *, ready: bool = False, priority: str = "P2", severity: str = "INFO") -> dict[str, object]:
        return {"signoff_packet_id": f"signoff-{lane}-{status}", "schema_version": "ui_semantic_validator_handoff_clearance_signoff_packet/v1", "evidence_lane": lane, "signoff_status": status, "signoff_readiness": readiness, "ready_for_human_signoff_observation": ready, "blocked": readiness == "FAIL_CLOSED", "waiting": readiness == "WAITING", "requires_authorized_review": status == "CLEARANCE_SIGNOFF_PACKET_WAITING_AUTHORIZED_REVIEW", "requires_external_artifact": status == "CLEARANCE_SIGNOFF_PACKET_WAITING_EXTERNAL_ARTIFACT", "source_review_docket_id": f"docket-{lane}", "source_docket_status": "CLEARANCE_REVIEW_DOCKET_READY_FOR_AUTHORIZED_REVIEW" if ready else "CLEARANCE_REVIEW_DOCKET_BLOCKED", "source_docket_readiness": "AUTHORIZED_REVIEW_OBSERVATION" if ready else "FAIL_CLOSED", "source_closeout_card_id": f"closeout-{lane}", "source_closeout_status": "CLEARANCE_CLOSEOUT_READY_FOR_AUTHORIZED_REVIEW" if ready else "CLEARANCE_CLOSEOUT_BLOCKED", "source_closeout_readiness": "REVIEW_READY_OBSERVATION" if ready else "FAIL_CLOSED", "source_verification_card_ids": [f"verification-{lane}"], "source_resolution_step_ids": [f"step-{lane}"], "source_action_ids": [f"action-{lane}"], "source_operation_card_ids": [f"operation-{lane}"], "source_coverage_card_ids": [f"coverage-{lane}"], "verification_card_count": 2, "verification_statuses": ["READY_FOR_AUTHORIZED_REVIEW_OBSERVED" if ready else "BLOCKING_SOURCE_ACTION_VISIBLE"], "verification_results": ["REVIEW_OBSERVATION" if ready else "FAIL_CLOSED"], "phases": ["CLEARANCE_ACCEPTANCE_OBSERVATION" if ready else "BLOCKER_TRIAGE"], "priority": priority, "severity": severity, "trust_banner": "TRUSTED" if ready else "TRUST_RESTRICTED", "owner_hint": "human_operator_clearance_owner", "owner_hints": ["human_operator_clearance_owner"], "check_ids": [f"check-{lane}"], "issue_codes": [f"ISSUE_{lane}"], "experiment_ids": ["EXP-1"], "continuity_ids": ["CONT-1"], "audit_packet_ids": [f"PKT-{lane}"], "blocks_handoff_clearance_count": 1 if readiness == "FAIL_CLOSED" else 0, "requires_external_artifact_count": 1 if status == "CLEARANCE_SIGNOFF_PACKET_WAITING_EXTERNAL_ARTIFACT" else 0, "requires_human_review_count": 1 if status == "CLEARANCE_SIGNOFF_PACKET_WAITING_AUTHORIZED_REVIEW" else 0, "verification_passed_count": 2 if ready else 0, "signoff_gate": "authorized_human_signoff_may_review_source_evidence_outside_this_read_plane" if ready else "source_review_docket_stops_clearance_signoff_packet_routing", "signoff_instruction": f"Signoff instruction for {lane}"}
    return {"schema_version": "ui_semantic_validator_handoff_clearance_signoff_packet/v1", "search_root": "synthetic", "degraded": ["SOURCE_SIGNOFF_PACKET_DEGRADED"], "signoff_packets": [packet("BLOCKER", "CLEARANCE_SIGNOFF_PACKET_BLOCKED", "FAIL_CLOSED", priority="P0", severity="HIGH"), packet("EXTERNAL", "CLEARANCE_SIGNOFF_PACKET_WAITING_EXTERNAL_ARTIFACT", "WAITING", priority="P1", severity="WARN"), packet("HUMAN", "CLEARANCE_SIGNOFF_PACKET_WAITING_AUTHORIZED_REVIEW", "WAITING", priority="P2", severity="MEDIUM"), packet("READY", "CLEARANCE_SIGNOFF_PACKET_READY_FOR_HUMAN_SIGNOFF_OBSERVATION", "SIGNOFF_READY_OBSERVATION", ready=True, priority="P3", severity="INFO")]}


def test_clearance_acceptance_board_projects_signoff_packets_and_preserves_firewall(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_signoff_packet_payload", lambda **_: _signoff_packet_payload())
    payload = m.build_ui_semantic_validator_handoff_clearance_acceptance_board_payload()
    first = payload["acceptance_cards"][0]
    assert payload["schema_version"] == "ui_semantic_validator_handoff_clearance_acceptance_board/v1"
    assert payload["read_plane_only"] is True
    assert first["acceptance_status"] == "CLEARANCE_ACCEPTANCE_BLOCKED"
    assert first["acceptance_readiness"] == "FAIL_CLOSED"
    assert first["acceptance_record_write_authority"] == "none_read_plane"
    assert first["acceptance_assertion_authority"] == "none_read_plane"
    assert first["operator_signoff_authority"] == "none_read_plane"
    assert first["operator_approval_authority"] == "none_read_plane"
    assert first["clearance_decision_authority"] == "none_read_plane"
    assert payload["summary"]["acceptance_record_write_allowed_count"] == 0
    assert payload["summary"]["acceptance_authorization_allowed_count"] == 0
    assert payload["summary"]["operator_signoff_allowed_count"] == 0
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_ACCEPTANCE_BOARD_FAIL_CLOSED_PRESENT" in payload["degraded"]


def test_clearance_acceptance_board_filters_ready_for_acceptance_observation(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_signoff_packet_payload", lambda **_: _signoff_packet_payload())
    payload = m.build_ui_semantic_validator_handoff_clearance_acceptance_board_payload(ready_for_acceptance_observation=True)
    assert payload["summary"]["acceptance_card_count_returned"] == 1
    row = payload["acceptance_cards"][0]
    assert row["evidence_lane"] == "READY"
    assert row["acceptance_status"] == "CLEARANCE_ACCEPTANCE_READY_FOR_OBSERVATION"
    assert row["acceptance_readiness"] == "ACCEPTANCE_READY_OBSERVATION"
    assert row["ready_for_acceptance_observation"] is True
    assert row["acceptance_record_write_authority"] == "none_read_plane"
    assert row["operator_signoff_authority"] == "none_read_plane"
    assert "writes no acceptance" in row["acceptance_instruction"]


def test_clearance_acceptance_board_filters_authorized_review_waiting(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_signoff_packet_payload", lambda **_: _signoff_packet_payload())
    payload = m.build_ui_semantic_validator_handoff_clearance_acceptance_board_payload(acceptance_status=("CLEARANCE_ACCEPTANCE_WAITING_AUTHORIZED_REVIEW",))
    assert payload["summary"]["acceptance_card_count_returned"] == 1
    row = payload["acceptance_cards"][0]
    assert row["evidence_lane"] == "HUMAN"
    assert row["waiting"] is True
    assert row["requires_authorized_review"] is True
    assert row["signoff_record_write_authority"] == "none_read_plane"
    assert "authorized review" in row["acceptance_instruction"]
