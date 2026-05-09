from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_release_packet as m


def _source() -> dict[str, object]:
    def row(lane: str, status: str, readiness: str, ready: bool = False, priority: str = "P2", severity: str = "INFO") -> dict[str, object]:
        return {"release_readiness_card_id": f"rr-{lane}", "evidence_lane": lane, "release_status": status, "release_readiness": readiness, "ready_for_release_observation": ready, "blocked": readiness == "FAIL_CLOSED", "waiting": readiness == "WAITING", "requires_acceptance_observation": status == "CLEARANCE_RELEASE_WAITING_ACCEPTANCE", "requires_external_artifact": status == "CLEARANCE_RELEASE_WAITING_EXTERNAL_ARTIFACT", "source_acceptance_card_id": f"acc-{lane}", "source_acceptance_status": "CLEARANCE_ACCEPTANCE_READY_FOR_OBSERVATION" if ready else "CLEARANCE_ACCEPTANCE_BLOCKED", "source_acceptance_readiness": "ACCEPTANCE_READY_OBSERVATION" if ready else "FAIL_CLOSED", "priority": priority, "severity": severity, "trust_banner": "TRUSTED" if ready else "TRUST_RESTRICTED", "owner_hint": "human_operator_clearance_owner", "issue_codes": [f"ISSUE_{lane}"], "experiment_ids": ["EXP-1"], "release_gate": "source_release_gate", "release_instruction": f"Release instruction {lane}"}
    return {"schema_version": "ui_semantic_validator_handoff_clearance_release_readiness_board/v1", "search_root": "synthetic", "degraded": ["UPSTREAM_DEGRADED"], "release_readiness_cards": [row("BLOCKER", "CLEARANCE_RELEASE_BLOCKED", "FAIL_CLOSED", priority="P0", severity="HIGH"), row("EXTERNAL", "CLEARANCE_RELEASE_WAITING_EXTERNAL_ARTIFACT", "WAITING", priority="P1", severity="WARN"), row("ACCEPT", "CLEARANCE_RELEASE_WAITING_ACCEPTANCE", "WAITING"), row("READY", "CLEARANCE_RELEASE_READY_FOR_OBSERVATION", "RELEASE_READY_OBSERVATION", ready=True)]}


def test_clearance_release_packet_projects_release_readiness_cards_and_preserves_firewall(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_readiness_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_packet_payload()
    first = payload["release_packets"][0]
    assert payload["schema_version"] == "ui_semantic_validator_handoff_clearance_release_packet/v1"
    assert payload["read_plane_only"] is True
    assert first["release_packet_status"] == "CLEARANCE_RELEASE_PACKET_BLOCKED"
    assert first["release_packet_readiness"] == "FAIL_CLOSED"
    assert first["release_packet_write_authority"] == "none_read_plane"
    assert first["release_record_write_authority"] == "none_read_plane"
    assert first["handoff_release_authority"] == "none_read_plane"
    assert first["operator_approval_authority"] == "none_read_plane"
    assert payload["summary"]["release_packet_write_allowed_count"] == 0
    assert payload["summary"]["handoff_release_allowed_count"] == 0
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_PACKET_FAIL_CLOSED_PRESENT" in payload["degraded"]


def test_clearance_release_packet_filters_ready_for_human_release_observation(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_readiness_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_packet_payload(ready_for_human_release_observation=True)
    assert payload["summary"]["release_packet_count_returned"] == 1
    row = payload["release_packets"][0]
    assert row["evidence_lane"] == "READY"
    assert row["release_packet_status"] == "CLEARANCE_RELEASE_PACKET_READY_FOR_HUMAN_RELEASE_OBSERVATION"
    assert row["release_packet_readiness"] == "HUMAN_RELEASE_READY_OBSERVATION"
    assert row["handoff_release_authority"] == "none_read_plane"
    assert "writes no packet" in row["release_packet_instruction"]


def test_clearance_release_packet_filters_waiting_acceptance(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_readiness_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_packet_payload(release_packet_status=("CLEARANCE_RELEASE_PACKET_WAITING_ACCEPTANCE",))
    assert payload["summary"]["release_packet_count_returned"] == 1
    row = payload["release_packets"][0]
    assert row["evidence_lane"] == "ACCEPT"
    assert row["waiting"] is True
    assert row["requires_acceptance_observation"] is True
    assert "acceptance/release-readiness" in row["release_packet_instruction"]
