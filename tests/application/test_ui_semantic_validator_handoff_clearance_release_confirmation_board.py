from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_release_confirmation_board as m


def _source() -> dict[str, object]:
    def row(lane: str, status: str, readiness: str, ready: bool = False) -> dict[str, object]:
        return {
            "release_acknowledgment_id": f"ra-{lane}",
            "evidence_lane": lane,
            "release_acknowledgment_status": status,
            "release_acknowledgment_readiness": readiness,
            "ready_for_human_acknowledgment_observation": ready,
            "blocked": readiness == "FAIL_CLOSED",
            "waiting": readiness == "WAITING",
            "requires_acceptance_observation": status == "CLEARANCE_RELEASE_ACKNOWLEDGMENT_WAITING_ACCEPTANCE",
            "requires_external_artifact": status == "CLEARANCE_RELEASE_ACKNOWLEDGMENT_WAITING_EXTERNAL_ARTIFACT",
            "requires_release_receipt_review": status == "CLEARANCE_RELEASE_ACKNOWLEDGMENT_WAITING_RECEIPT_REVIEW",
            "requires_investigation": status == "CLEARANCE_RELEASE_ACKNOWLEDGMENT_INVESTIGATION_REQUIRED",
            "priority": "P2",
            "severity": "INFO",
            "trust_banner": "TRUSTED" if ready else "TRUST_RESTRICTED",
            "owner_hint": "human_operator_clearance_owner",
            "issue_codes": [f"ISSUE_{lane}"],
            "experiment_ids": ["EXP-1"],
            "source_release_receipt_status": "SOURCE_RECEIPT",
            "source_release_receipt_readiness": "SOURCE_RECEIPT_READINESS",
            "source_release_custody_status": "SOURCE_CUSTODY",
            "source_release_custody_readiness": "SOURCE_CUSTODY_READINESS",
        }

    return {
        "schema_version": "ui_semantic_validator_handoff_clearance_release_acknowledgment_board/v1",
        "search_root": "synthetic",
        "degraded": ["UPSTREAM_DEGRADED"],
        "release_acknowledgments": [
            row("BLOCKER", "CLEARANCE_RELEASE_ACKNOWLEDGMENT_BLOCKED", "FAIL_CLOSED"),
            row("EXTERNAL", "CLEARANCE_RELEASE_ACKNOWLEDGMENT_WAITING_EXTERNAL_ARTIFACT", "WAITING"),
            row("ACCEPT", "CLEARANCE_RELEASE_ACKNOWLEDGMENT_WAITING_ACCEPTANCE", "WAITING"),
            row("REVIEW", "CLEARANCE_RELEASE_ACKNOWLEDGMENT_WAITING_RECEIPT_REVIEW", "WAITING"),
            row("INVESTIGATE", "CLEARANCE_RELEASE_ACKNOWLEDGMENT_INVESTIGATION_REQUIRED", "WAITING"),
            row("READY", "CLEARANCE_RELEASE_ACKNOWLEDGMENT_READY_FOR_HUMAN_ACKNOWLEDGMENT_OBSERVATION", "HUMAN_ACKNOWLEDGMENT_READY_OBSERVATION", True),
        ],
    }


def test_confirmation_projects_acknowledgments_and_preserves_firewall(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_acknowledgment_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_confirmation_board_payload()
    first = payload["release_confirmations"][0]
    assert payload["schema_version"] == "ui_semantic_validator_handoff_clearance_release_confirmation_board/v1"
    assert payload["read_plane_only"] is True
    assert first["release_confirmation_status"] == "CLEARANCE_RELEASE_CONFIRMATION_BLOCKED"
    assert first["release_confirmation_write_authority"] == "none_read_plane"
    assert first["release_acknowledgment_write_authority"] == "none_read_plane"
    assert payload["summary"]["release_confirmation_write_allowed_count"] == 0
    assert payload["summary"]["release_acknowledgment_write_allowed_count"] == 0
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_CONFIRMATION_FAIL_CLOSED_PRESENT" in payload["degraded"]


def test_confirmation_filters_ready(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_acknowledgment_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_confirmation_board_payload(
        ready_for_human_confirmation_observation=True
    )
    assert payload["summary"]["release_confirmation_count_returned"] == 1
    assert payload["release_confirmations"][0]["evidence_lane"] == "READY"
    assert "writes no confirmation" in payload["release_confirmations"][0]["release_confirmation_instruction"]


def test_confirmation_filters_acknowledgment_review(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_acknowledgment_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_confirmation_board_payload(
        release_confirmation_status=("CLEARANCE_RELEASE_CONFIRMATION_WAITING_ACKNOWLEDGMENT_REVIEW",)
    )
    assert payload["summary"]["release_confirmation_count_returned"] == 1
    assert payload["release_confirmations"][0]["release_confirmation_gate"] == "release_acknowledgment_reclassified_to_known_confirmation_state"


def test_confirmation_filters_investigation(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_acknowledgment_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_confirmation_board_payload(
        release_confirmation_status=("CLEARANCE_RELEASE_CONFIRMATION_INVESTIGATION_REQUIRED",)
    )
    assert payload["summary"]["release_confirmation_count_returned"] == 1
    assert payload["release_confirmations"][0]["requires_investigation"] is True


def test_confirmation_latest(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_acknowledgment_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_confirmation_board_latest_payload()
    assert payload["summary"]["release_confirmation_count_returned"] == 1
    assert payload["latest"] == payload["release_confirmations"][0]
