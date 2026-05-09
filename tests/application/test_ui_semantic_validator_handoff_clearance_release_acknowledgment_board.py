from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_release_acknowledgment_board as m


def _source() -> dict[str, object]:
    def row(lane: str, status: str, readiness: str, ready: bool = False) -> dict[str, object]:
        return {
            "release_receipt_id": f"rr-{lane}",
            "evidence_lane": lane,
            "release_receipt_status": status,
            "release_receipt_readiness": readiness,
            "ready_for_human_receipt_observation": ready,
            "blocked": readiness == "FAIL_CLOSED",
            "waiting": readiness == "WAITING",
            "requires_acceptance_observation": status == "CLEARANCE_RELEASE_RECEIPT_WAITING_ACCEPTANCE",
            "requires_external_artifact": status == "CLEARANCE_RELEASE_RECEIPT_WAITING_EXTERNAL_ARTIFACT",
            "requires_release_custody_review": status == "CLEARANCE_RELEASE_RECEIPT_WAITING_CUSTODY_REVIEW",
            "requires_investigation": status == "CLEARANCE_RELEASE_RECEIPT_INVESTIGATION_REQUIRED",
            "priority": "P2",
            "severity": "INFO",
            "trust_banner": "TRUSTED" if ready else "TRUST_RESTRICTED",
            "owner_hint": "human_operator_clearance_owner",
            "issue_codes": [f"ISSUE_{lane}"],
            "experiment_ids": ["EXP-1"],
            "source_release_custody_status": "SOURCE_CUSTODY",
            "source_release_custody_readiness": "SOURCE_CUSTODY_READINESS",
            "source_release_handoff_status": "SOURCE_HANDOFF",
            "source_release_handoff_readiness": "SOURCE_HANDOFF_READINESS",
        }

    return {
        "schema_version": "ui_semantic_validator_handoff_clearance_release_receipt_board/v1",
        "search_root": "synthetic",
        "degraded": ["UPSTREAM_DEGRADED"],
        "release_receipts": [
            row("BLOCKER", "CLEARANCE_RELEASE_RECEIPT_BLOCKED", "FAIL_CLOSED"),
            row("EXTERNAL", "CLEARANCE_RELEASE_RECEIPT_WAITING_EXTERNAL_ARTIFACT", "WAITING"),
            row("ACCEPT", "CLEARANCE_RELEASE_RECEIPT_WAITING_ACCEPTANCE", "WAITING"),
            row("REVIEW", "CLEARANCE_RELEASE_RECEIPT_WAITING_CUSTODY_REVIEW", "WAITING"),
            row("INVESTIGATE", "CLEARANCE_RELEASE_RECEIPT_INVESTIGATION_REQUIRED", "WAITING"),
            row("READY", "CLEARANCE_RELEASE_RECEIPT_READY_FOR_HUMAN_RECEIPT_OBSERVATION", "HUMAN_RECEIPT_READY_OBSERVATION", True),
        ],
    }


def test_acknowledgment_projects_receipts_and_preserves_firewall(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_receipt_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_acknowledgment_board_payload()
    first = payload["release_acknowledgments"][0]
    assert payload["schema_version"] == "ui_semantic_validator_handoff_clearance_release_acknowledgment_board/v1"
    assert payload["read_plane_only"] is True
    assert first["release_acknowledgment_status"] == "CLEARANCE_RELEASE_ACKNOWLEDGMENT_BLOCKED"
    assert first["release_acknowledgment_write_authority"] == "none_read_plane"
    assert first["release_receipt_write_authority"] == "none_read_plane"
    assert payload["summary"]["release_acknowledgment_write_allowed_count"] == 0
    assert payload["summary"]["release_receipt_write_allowed_count"] == 0
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_ACKNOWLEDGMENT_FAIL_CLOSED_PRESENT" in payload["degraded"]


def test_acknowledgment_filters_ready(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_receipt_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_acknowledgment_board_payload(
        ready_for_human_acknowledgment_observation=True
    )
    assert payload["summary"]["release_acknowledgment_count_returned"] == 1
    assert payload["release_acknowledgments"][0]["evidence_lane"] == "READY"
    assert "writes no acknowledgment" in payload["release_acknowledgments"][0]["release_acknowledgment_instruction"]


def test_acknowledgment_filters_receipt_review(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_receipt_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_acknowledgment_board_payload(
        release_acknowledgment_status=("CLEARANCE_RELEASE_ACKNOWLEDGMENT_WAITING_RECEIPT_REVIEW",)
    )
    assert payload["summary"]["release_acknowledgment_count_returned"] == 1
    assert payload["release_acknowledgments"][0]["release_acknowledgment_gate"] == "release_receipt_reclassified_to_known_acknowledgment_state"


def test_acknowledgment_filters_investigation(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_receipt_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_acknowledgment_board_payload(
        release_acknowledgment_status=("CLEARANCE_RELEASE_ACKNOWLEDGMENT_INVESTIGATION_REQUIRED",)
    )
    assert payload["summary"]["release_acknowledgment_count_returned"] == 1
    assert payload["release_acknowledgments"][0]["requires_investigation"] is True


def test_acknowledgment_latest(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_receipt_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_acknowledgment_board_latest_payload()
    assert payload["summary"]["release_acknowledgment_count_returned"] == 1
    assert payload["latest"] == payload["release_acknowledgments"][0]
