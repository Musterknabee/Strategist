from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_release_readiness_board as m


def _acceptance_board_payload() -> dict[str, object]:
    def card(lane: str, status: str, readiness: str, *, ready: bool = False, priority: str = "P2", severity: str = "INFO") -> dict[str, object]:
        return {"acceptance_card_id": f"acceptance-{lane}-{status}", "schema_version": "ui_semantic_validator_handoff_clearance_acceptance_board/v1", "evidence_lane": lane, "acceptance_status": status, "acceptance_readiness": readiness, "ready_for_acceptance_observation": ready, "blocked": readiness == "FAIL_CLOSED", "waiting": readiness == "WAITING", "requires_authorized_review": status == "CLEARANCE_ACCEPTANCE_WAITING_AUTHORIZED_REVIEW", "requires_external_artifact": status == "CLEARANCE_ACCEPTANCE_WAITING_EXTERNAL_ARTIFACT", "source_signoff_packet_id": f"signoff-{lane}", "source_signoff_status": "CLEARANCE_SIGNOFF_PACKET_READY_FOR_HUMAN_SIGNOFF_OBSERVATION" if ready else "CLEARANCE_SIGNOFF_PACKET_BLOCKED", "source_signoff_readiness": "SIGNOFF_READY_OBSERVATION" if ready else "FAIL_CLOSED", "source_review_docket_id": f"docket-{lane}", "source_docket_status": "CLEARANCE_REVIEW_DOCKET_READY_FOR_AUTHORIZED_REVIEW" if ready else "CLEARANCE_REVIEW_DOCKET_BLOCKED", "source_docket_readiness": "AUTHORIZED_REVIEW_OBSERVATION" if ready else "FAIL_CLOSED", "source_closeout_card_id": f"closeout-{lane}", "source_closeout_status": "CLEARANCE_CLOSEOUT_READY_FOR_AUTHORIZED_REVIEW" if ready else "CLEARANCE_CLOSEOUT_BLOCKED", "source_closeout_readiness": "REVIEW_READY_OBSERVATION" if ready else "FAIL_CLOSED", "source_verification_card_ids": [f"verification-{lane}"], "source_resolution_step_ids": [f"step-{lane}"], "source_action_ids": [f"action-{lane}"], "source_operation_card_ids": [f"operation-{lane}"], "source_coverage_card_ids": [f"coverage-{lane}"], "verification_card_count": 2, "verification_statuses": ["READY_FOR_AUTHORIZED_REVIEW_OBSERVED" if ready else "BLOCKING_SOURCE_ACTION_VISIBLE"], "verification_results": ["REVIEW_OBSERVATION" if ready else "FAIL_CLOSED"], "phases": ["CLEARANCE_RELEASE_READINESS_OBSERVATION" if ready else "BLOCKER_TRIAGE"], "priority": priority, "severity": severity, "trust_banner": "TRUSTED" if ready else "TRUST_RESTRICTED", "owner_hint": "human_operator_clearance_owner", "owner_hints": ["human_operator_clearance_owner"], "check_ids": [f"check-{lane}"], "issue_codes": [f"ISSUE_{lane}"], "experiment_ids": ["EXP-1"], "continuity_ids": ["CONT-1"], "audit_packet_ids": [f"PKT-{lane}"], "blocks_handoff_clearance_count": 1 if readiness == "FAIL_CLOSED" else 0, "requires_external_artifact_count": 1 if status == "CLEARANCE_ACCEPTANCE_WAITING_EXTERNAL_ARTIFACT" else 0, "requires_human_review_count": 1 if status == "CLEARANCE_ACCEPTANCE_WAITING_AUTHORIZED_REVIEW" else 0, "verification_passed_count": 2 if ready else 0, "acceptance_gate": "authorized_human_may_accept_clearance_outside_this_read_plane_after_source_review" if ready else "source_signoff_packet_stops_clearance_acceptance_observation", "acceptance_instruction": f"Acceptance instruction for {lane}"}
    return {"schema_version": "ui_semantic_validator_handoff_clearance_acceptance_board/v1", "search_root": "synthetic", "degraded": ["SOURCE_ACCEPTANCE_BOARD_DEGRADED"], "acceptance_cards": [card("BLOCKER", "CLEARANCE_ACCEPTANCE_BLOCKED", "FAIL_CLOSED", priority="P0", severity="HIGH"), card("EXTERNAL", "CLEARANCE_ACCEPTANCE_WAITING_EXTERNAL_ARTIFACT", "WAITING", priority="P1", severity="WARN"), card("HUMAN", "CLEARANCE_ACCEPTANCE_WAITING_AUTHORIZED_REVIEW", "WAITING", priority="P2", severity="MEDIUM"), card("READY", "CLEARANCE_ACCEPTANCE_READY_FOR_OBSERVATION", "ACCEPTANCE_READY_OBSERVATION", ready=True, priority="P3", severity="INFO")]}


def test_clearance_release_readiness_board_projects_acceptance_cards_and_preserves_firewall(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_acceptance_board_payload", lambda **_: _acceptance_board_payload())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_readiness_board_payload()
    first = payload["release_readiness_cards"][0]
    assert payload["schema_version"] == "ui_semantic_validator_handoff_clearance_release_readiness_board/v1"
    assert payload["read_plane_only"] is True
    assert first["release_status"] == "CLEARANCE_RELEASE_BLOCKED"
    assert first["release_readiness"] == "FAIL_CLOSED"
    assert first["release_record_write_authority"] == "none_read_plane"
    assert first["release_assertion_authority"] == "none_read_plane"
    assert first["handoff_release_authority"] == "none_read_plane"
    assert first["operator_approval_authority"] == "none_read_plane"
    assert first["clearance_decision_authority"] == "none_read_plane"
    assert payload["summary"]["release_record_write_allowed_count"] == 0
    assert payload["summary"]["release_authorization_allowed_count"] == 0
    assert payload["summary"]["handoff_release_allowed_count"] == 0
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_READINESS_BOARD_FAIL_CLOSED_PRESENT" in payload["degraded"]


def test_clearance_release_readiness_board_filters_ready_for_release_observation(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_acceptance_board_payload", lambda **_: _acceptance_board_payload())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_readiness_board_payload(ready_for_release_observation=True)
    assert payload["summary"]["release_readiness_card_count_returned"] == 1
    row = payload["release_readiness_cards"][0]
    assert row["evidence_lane"] == "READY"
    assert row["release_status"] == "CLEARANCE_RELEASE_READY_FOR_OBSERVATION"
    assert row["release_readiness"] == "RELEASE_READY_OBSERVATION"
    assert row["ready_for_release_observation"] is True
    assert row["release_record_write_authority"] == "none_read_plane"
    assert row["handoff_release_authority"] == "none_read_plane"
    assert "writes no release" in row["release_instruction"]


def test_clearance_release_readiness_board_filters_acceptance_waiting(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_acceptance_board_payload", lambda **_: _acceptance_board_payload())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_readiness_board_payload(release_status=("CLEARANCE_RELEASE_WAITING_ACCEPTANCE",))
    assert payload["summary"]["release_readiness_card_count_returned"] == 1
    row = payload["release_readiness_cards"][0]
    assert row["evidence_lane"] == "HUMAN"
    assert row["waiting"] is True
    assert row["requires_acceptance_observation"] is True
    assert row["acceptance_record_write_authority"] == "none_read_plane"
    assert "acceptance observation" in row["release_instruction"]
