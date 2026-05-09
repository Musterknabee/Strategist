from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_release_handoff_board as m


def _source() -> dict[str, object]:
    def row(
        lane: str,
        status: str,
        readiness: str,
        ready: bool = False,
        priority: str = "P2",
        severity: str = "INFO",
    ) -> dict[str, object]:
        return {
            "release_packet_id": f"rp-{lane}",
            "evidence_lane": lane,
            "release_packet_status": status,
            "release_packet_readiness": readiness,
            "ready_for_human_release_observation": ready,
            "blocked": readiness == "FAIL_CLOSED",
            "waiting": readiness == "WAITING",
            "requires_acceptance_observation": status == "CLEARANCE_RELEASE_PACKET_WAITING_ACCEPTANCE",
            "requires_external_artifact": status == "CLEARANCE_RELEASE_PACKET_WAITING_EXTERNAL_ARTIFACT",
            "requires_investigation": status == "CLEARANCE_RELEASE_PACKET_INVESTIGATION_REQUIRED",
            "source_release_readiness_card_id": f"rr-{lane}",
            "source_release_status": "CLEARANCE_RELEASE_READY_FOR_OBSERVATION" if ready else "CLEARANCE_RELEASE_BLOCKED",
            "source_release_readiness": "RELEASE_READY_OBSERVATION" if ready else "FAIL_CLOSED",
            "source_acceptance_status": "CLEARANCE_ACCEPTANCE_READY_FOR_OBSERVATION" if ready else "CLEARANCE_ACCEPTANCE_BLOCKED",
            "source_acceptance_readiness": "ACCEPTANCE_READY_OBSERVATION" if ready else "FAIL_CLOSED",
            "priority": priority,
            "severity": severity,
            "trust_banner": "TRUSTED" if ready else "TRUST_RESTRICTED",
            "owner_hint": "human_operator_clearance_owner",
            "issue_codes": [f"ISSUE_{lane}"],
            "experiment_ids": ["EXP-1"],
            "release_packet_gate": "source_release_packet_gate",
            "release_packet_instruction": f"Release packet instruction {lane}",
        }

    return {
        "schema_version": "ui_semantic_validator_handoff_clearance_release_packet/v1",
        "search_root": "synthetic",
        "degraded": ["UPSTREAM_DEGRADED"],
        "release_packets": [
            row("BLOCKER", "CLEARANCE_RELEASE_PACKET_BLOCKED", "FAIL_CLOSED", priority="P0", severity="HIGH"),
            row("EXTERNAL", "CLEARANCE_RELEASE_PACKET_WAITING_EXTERNAL_ARTIFACT", "WAITING", priority="P1", severity="WARN"),
            row("ACCEPT", "CLEARANCE_RELEASE_PACKET_WAITING_ACCEPTANCE", "WAITING"),
            row("REVIEW", "CLEARANCE_RELEASE_PACKET_INVESTIGATION_REQUIRED", "WAITING"),
            row("READY", "CLEARANCE_RELEASE_PACKET_READY_FOR_HUMAN_RELEASE_OBSERVATION", "HUMAN_RELEASE_READY_OBSERVATION", ready=True),
        ],
    }


def test_clearance_release_handoff_board_projects_release_packets_and_preserves_firewall(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_packet_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_handoff_board_payload()
    first = payload["release_handoffs"][0]
    assert payload["schema_version"] == "ui_semantic_validator_handoff_clearance_release_handoff_board/v1"
    assert payload["read_plane_only"] is True
    assert first["release_handoff_status"] == "CLEARANCE_RELEASE_HANDOFF_BLOCKED"
    assert first["release_handoff_readiness"] == "FAIL_CLOSED"
    assert first["release_handoff_write_authority"] == "none_read_plane"
    assert first["release_packet_write_authority"] == "none_read_plane"
    assert first["release_record_write_authority"] == "none_read_plane"
    assert first["handoff_release_authority"] == "none_read_plane"
    assert first["operator_approval_authority"] == "none_read_plane"
    assert payload["summary"]["release_handoff_write_allowed_count"] == 0
    assert payload["summary"]["handoff_release_allowed_count"] == 0
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_HANDOFF_FAIL_CLOSED_PRESENT" in payload["degraded"]


def test_clearance_release_handoff_board_filters_ready_for_human_transfer_observation(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_packet_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_handoff_board_payload(
        ready_for_human_transfer_observation=True
    )
    assert payload["summary"]["release_handoff_count_returned"] == 1
    row = payload["release_handoffs"][0]
    assert row["evidence_lane"] == "READY"
    assert row["release_handoff_status"] == "CLEARANCE_RELEASE_HANDOFF_READY_FOR_HUMAN_TRANSFER_OBSERVATION"
    assert row["release_handoff_readiness"] == "HUMAN_TRANSFER_READY_OBSERVATION"
    assert row["handoff_release_authority"] == "none_read_plane"
    assert "writes no handoff" in row["release_handoff_instruction"]


def test_clearance_release_handoff_board_filters_release_packet_review(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_packet_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_handoff_board_payload(
        release_handoff_status=("CLEARANCE_RELEASE_HANDOFF_INVESTIGATION_REQUIRED",)
    )
    assert payload["summary"]["release_handoff_count_returned"] == 1
    row = payload["release_handoffs"][0]
    assert row["evidence_lane"] == "REVIEW"
    assert row["requires_investigation"] is True
    assert row["release_handoff_gate"] == "release_packet_investigation_resolved_before_handoff_transfer_review"


def test_clearance_release_handoff_board_filters_external_artifacts(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_packet_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_handoff_board_payload(
        requires_external_artifact=True
    )
    assert payload["summary"]["release_handoff_count_returned"] == 1
    row = payload["release_handoffs"][0]
    assert row["evidence_lane"] == "EXTERNAL"
    assert row["release_handoff_status"] == "CLEARANCE_RELEASE_HANDOFF_WAITING_EXTERNAL_ARTIFACT"
    assert row["waiting"] is True


def test_clearance_release_handoff_latest_uses_limit_one(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_packet_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_handoff_board_latest_payload()
    assert payload["summary"]["release_handoff_count_returned"] == 1
    assert payload["latest"] == payload["release_handoffs"][0]
