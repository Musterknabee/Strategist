from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_review_docket as m


def _closeout_board_payload() -> dict[str, object]:
    def card(lane: str, status: str, readiness: str, *, ready: bool = False, priority: str = "P2", severity: str = "INFO") -> dict[str, object]:
        return {
            "closeout_card_id": f"closeout-{lane}-{status}",
            "schema_version": "ui_semantic_validator_handoff_clearance_closeout_board/v1",
            "evidence_lane": lane,
            "closeout_status": status,
            "closeout_readiness": readiness,
            "ready_for_authorized_clearance_review": ready,
            "blocked": readiness == "FAIL_CLOSED",
            "waiting": readiness == "WAITING",
            "verification_card_count": 2,
            "source_verification_card_ids": [f"verification-{lane}"],
            "source_resolution_step_ids": [f"step-{lane}"],
            "source_action_ids": [f"action-{lane}"],
            "source_operation_card_ids": [f"operation-{lane}"],
            "source_coverage_card_ids": [f"coverage-{lane}"],
            "verification_statuses": ["READY_FOR_AUTHORIZED_REVIEW_OBSERVED" if ready else "BLOCKING_SOURCE_ACTION_VISIBLE"],
            "verification_results": ["REVIEW_OBSERVATION" if ready else "FAIL_CLOSED"],
            "phases": ["AUTHORIZED_CLEARANCE_REVIEW" if ready else "BLOCKER_TRIAGE"],
            "priority": priority,
            "severity": severity,
            "trust_banner": "TRUSTED" if ready else "TRUST_RESTRICTED",
            "owner_hint": "human_operator_clearance_owner",
            "owner_hints": ["human_operator_clearance_owner"],
            "check_ids": [f"check-{lane}"],
            "issue_codes": [f"ISSUE_{lane}"],
            "experiment_ids": ["EXP-1"],
            "continuity_ids": ["CONT-1"],
            "audit_packet_ids": [f"PKT-{lane}"],
            "blocks_handoff_clearance_count": 1 if readiness == "FAIL_CLOSED" else 0,
            "requires_external_artifact_count": 1 if status == "CLEARANCE_CLOSEOUT_WAITING_EXTERNAL_ARTIFACT" else 0,
            "requires_human_review_count": 1 if status == "CLEARANCE_CLOSEOUT_WAITING_HUMAN_REVIEW" else 0,
            "verification_passed_count": 2 if ready else 0,
            "closeout_gate": "authorized_clearance_review_and_signoff_completed_outside_this_read_plane" if ready else "source_cards_resolved",
            "closeout_note": f"Closeout note for {lane}",
        }

    return {
        "schema_version": "ui_semantic_validator_handoff_clearance_closeout_board/v1",
        "search_root": "synthetic",
        "degraded": ["SOURCE_CLOSEOUT_DEGRADED"],
        "closeout_cards": [
            card("BLOCKER", "CLEARANCE_CLOSEOUT_BLOCKED", "FAIL_CLOSED", priority="P0", severity="HIGH"),
            card("EXTERNAL", "CLEARANCE_CLOSEOUT_WAITING_EXTERNAL_ARTIFACT", "WAITING", priority="P1", severity="WARN"),
            card("HUMAN", "CLEARANCE_CLOSEOUT_WAITING_HUMAN_REVIEW", "WAITING", priority="P2", severity="MEDIUM"),
            card("READY", "CLEARANCE_CLOSEOUT_READY_FOR_AUTHORIZED_REVIEW", "REVIEW_READY_OBSERVATION", ready=True, priority="P3", severity="INFO"),
        ],
    }


def test_clearance_review_docket_projects_closeout_cards_and_preserves_firewall(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_closeout_board_payload", lambda **_: _closeout_board_payload())
    payload = m.build_ui_semantic_validator_handoff_clearance_review_docket_payload()
    first = payload["review_dockets"][0]
    assert payload["schema_version"] == "ui_semantic_validator_handoff_clearance_review_docket/v1"
    assert payload["read_plane_only"] is True
    assert first["docket_status"] == "CLEARANCE_REVIEW_DOCKET_BLOCKED"
    assert first["docket_readiness"] == "FAIL_CLOSED"
    assert first["review_record_write_authority"] == "none_read_plane"
    assert first["review_authorization_authority"] == "none_read_plane"
    assert first["clearance_decision_authority"] == "none_read_plane"
    assert first["operator_approval_authority"] == "none_read_plane"
    assert first["signoff_authority"] == "none_read_plane"
    assert payload["summary"]["review_record_write_allowed_count"] == 0
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_REVIEW_DOCKET_FAIL_CLOSED_PRESENT" in payload["degraded"]


def test_clearance_review_docket_filters_ready_for_authorized_review(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_closeout_board_payload", lambda **_: _closeout_board_payload())
    payload = m.build_ui_semantic_validator_handoff_clearance_review_docket_payload(ready_for_authorized_review=True)
    assert payload["summary"]["review_docket_count_returned"] == 1
    row = payload["review_dockets"][0]
    assert row["evidence_lane"] == "READY"
    assert row["docket_status"] == "CLEARANCE_REVIEW_DOCKET_READY_FOR_AUTHORIZED_REVIEW"
    assert row["docket_readiness"] == "AUTHORIZED_REVIEW_OBSERVATION"
    assert row["ready_for_authorized_review"] is True
    assert row["review_record_write_authority"] == "none_read_plane"
    assert row["review_authorization_authority"] == "none_read_plane"
    assert "writes no review record" in row["review_instruction"]


def test_clearance_review_docket_filters_external_artifact_waiting(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_closeout_board_payload", lambda **_: _closeout_board_payload())
    payload = m.build_ui_semantic_validator_handoff_clearance_review_docket_payload(docket_status=("CLEARANCE_REVIEW_DOCKET_WAITING_EXTERNAL_ARTIFACT",))
    assert payload["summary"]["review_docket_count_returned"] == 1
    row = payload["review_dockets"][0]
    assert row["evidence_lane"] == "EXTERNAL"
    assert row["waiting"] is True
    assert row["external_artifact_write_authority"] == "none_read_plane"
    assert "external artifacts" in row["review_instruction"]
