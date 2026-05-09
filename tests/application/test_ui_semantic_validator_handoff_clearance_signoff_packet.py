from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_signoff_packet as m


def _review_docket_payload() -> dict[str, object]:
    def docket(lane: str, status: str, readiness: str, *, ready: bool = False, priority: str = "P2", severity: str = "INFO") -> dict[str, object]:
        return {
            "review_docket_id": f"docket-{lane}-{status}",
            "schema_version": "ui_semantic_validator_handoff_clearance_review_docket/v1",
            "evidence_lane": lane,
            "docket_status": status,
            "docket_readiness": readiness,
            "ready_for_authorized_review": ready,
            "blocked": readiness == "FAIL_CLOSED",
            "waiting": readiness == "WAITING",
            "requires_authorized_human_review": status in {"CLEARANCE_REVIEW_DOCKET_WAITING_HUMAN_REVIEW", "CLEARANCE_REVIEW_DOCKET_READY_FOR_AUTHORIZED_REVIEW"},
            "source_closeout_card_id": f"closeout-{lane}",
            "source_closeout_status": "CLEARANCE_CLOSEOUT_READY_FOR_AUTHORIZED_REVIEW" if ready else "CLEARANCE_CLOSEOUT_BLOCKED",
            "source_closeout_readiness": "REVIEW_READY_OBSERVATION" if ready else "FAIL_CLOSED",
            "source_closeout_gate": "source-closeout-gate",
            "source_verification_card_ids": [f"verification-{lane}"],
            "source_resolution_step_ids": [f"step-{lane}"],
            "source_action_ids": [f"action-{lane}"],
            "source_operation_card_ids": [f"operation-{lane}"],
            "source_coverage_card_ids": [f"coverage-{lane}"],
            "verification_card_count": 2,
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
            "requires_external_artifact_count": 1 if status == "CLEARANCE_REVIEW_DOCKET_WAITING_EXTERNAL_ARTIFACT" else 0,
            "requires_human_review_count": 1 if status == "CLEARANCE_REVIEW_DOCKET_WAITING_HUMAN_REVIEW" else 0,
            "verification_passed_count": 2 if ready else 0,
            "review_gate": "authorized_clearance_reviewer_may_review_source_evidence_outside_this_read_plane" if ready else "source_closeout_cards_stop_blocking_handoff_clearance",
            "review_instruction": f"Review instruction for {lane}",
        }

    return {
        "schema_version": "ui_semantic_validator_handoff_clearance_review_docket/v1",
        "search_root": "synthetic",
        "degraded": ["SOURCE_REVIEW_DOCKET_DEGRADED"],
        "review_dockets": [
            docket("BLOCKER", "CLEARANCE_REVIEW_DOCKET_BLOCKED", "FAIL_CLOSED", priority="P0", severity="HIGH"),
            docket("EXTERNAL", "CLEARANCE_REVIEW_DOCKET_WAITING_EXTERNAL_ARTIFACT", "WAITING", priority="P1", severity="WARN"),
            docket("HUMAN", "CLEARANCE_REVIEW_DOCKET_WAITING_HUMAN_REVIEW", "WAITING", priority="P2", severity="MEDIUM"),
            docket("READY", "CLEARANCE_REVIEW_DOCKET_READY_FOR_AUTHORIZED_REVIEW", "AUTHORIZED_REVIEW_OBSERVATION", ready=True, priority="P3", severity="INFO"),
        ],
    }


def test_clearance_signoff_packet_projects_review_dockets_and_preserves_firewall(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_review_docket_payload", lambda **_: _review_docket_payload())
    payload = m.build_ui_semantic_validator_handoff_clearance_signoff_packet_payload()
    first = payload["signoff_packets"][0]
    assert payload["schema_version"] == "ui_semantic_validator_handoff_clearance_signoff_packet/v1"
    assert payload["read_plane_only"] is True
    assert first["signoff_status"] == "CLEARANCE_SIGNOFF_PACKET_BLOCKED"
    assert first["signoff_readiness"] == "FAIL_CLOSED"
    assert first["signoff_packet_write_authority"] == "none_read_plane"
    assert first["signoff_record_write_authority"] == "none_read_plane"
    assert first["operator_signoff_authority"] == "none_read_plane"
    assert first["operator_approval_authority"] == "none_read_plane"
    assert first["clearance_decision_authority"] == "none_read_plane"
    assert payload["summary"]["signoff_packet_write_allowed_count"] == 0
    assert payload["summary"]["operator_signoff_allowed_count"] == 0
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_SIGNOFF_PACKET_FAIL_CLOSED_PRESENT" in payload["degraded"]


def test_clearance_signoff_packet_filters_ready_for_human_signoff_observation(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_review_docket_payload", lambda **_: _review_docket_payload())
    payload = m.build_ui_semantic_validator_handoff_clearance_signoff_packet_payload(ready_for_human_signoff_observation=True)
    assert payload["summary"]["signoff_packet_count_returned"] == 1
    row = payload["signoff_packets"][0]
    assert row["evidence_lane"] == "READY"
    assert row["signoff_status"] == "CLEARANCE_SIGNOFF_PACKET_READY_FOR_HUMAN_SIGNOFF_OBSERVATION"
    assert row["signoff_readiness"] == "SIGNOFF_READY_OBSERVATION"
    assert row["ready_for_human_signoff_observation"] is True
    assert row["signoff_record_write_authority"] == "none_read_plane"
    assert row["operator_signoff_authority"] == "none_read_plane"
    assert "writes no signoff packet" in row["signoff_instruction"]


def test_clearance_signoff_packet_filters_authorized_review_waiting(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_review_docket_payload", lambda **_: _review_docket_payload())
    payload = m.build_ui_semantic_validator_handoff_clearance_signoff_packet_payload(signoff_status=("CLEARANCE_SIGNOFF_PACKET_WAITING_AUTHORIZED_REVIEW",))
    assert payload["summary"]["signoff_packet_count_returned"] == 1
    row = payload["signoff_packets"][0]
    assert row["evidence_lane"] == "HUMAN"
    assert row["waiting"] is True
    assert row["requires_authorized_review"] is True
    assert row["review_record_write_authority"] == "none_read_plane"
    assert "authorized human review" in row["signoff_instruction"]
