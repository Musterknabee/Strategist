from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_release_completion_board as m


def _source() -> dict[str, object]:
    def row(lane: str, status: str, readiness: str, ready: bool = False) -> dict[str, object]:
        return {
            "release_confirmation_id": f"rc-{lane}",
            "evidence_lane": lane,
            "release_confirmation_status": status,
            "release_confirmation_readiness": readiness,
            "ready_for_human_confirmation_observation": ready,
            "blocked": readiness == "FAIL_CLOSED",
            "waiting": readiness == "WAITING",
            "requires_acceptance_observation": status == "CLEARANCE_RELEASE_CONFIRMATION_WAITING_ACCEPTANCE",
            "requires_external_artifact": status == "CLEARANCE_RELEASE_CONFIRMATION_WAITING_EXTERNAL_ARTIFACT",
            "requires_release_acknowledgment_review": status == "CLEARANCE_RELEASE_CONFIRMATION_WAITING_ACKNOWLEDGMENT_REVIEW",
            "requires_investigation": status == "CLEARANCE_RELEASE_CONFIRMATION_INVESTIGATION_REQUIRED",
            "priority": "P2",
            "severity": "INFO",
            "trust_banner": "TRUSTED" if ready else "TRUST_RESTRICTED",
            "owner_hint": "human_operator_clearance_owner",
            "issue_codes": [f"ISSUE_{lane}"],
            "experiment_ids": ["EXP-1"],
            "source_release_acknowledgment_status": "SOURCE_ACK",
            "source_release_acknowledgment_readiness": "SOURCE_ACK_READINESS",
            "source_release_receipt_status": "SOURCE_RECEIPT",
            "source_release_receipt_readiness": "SOURCE_RECEIPT_READINESS",
        }

    return {
        "schema_version": "ui_semantic_validator_handoff_clearance_release_confirmation_board/v1",
        "search_root": "synthetic",
        "degraded": ["UPSTREAM_DEGRADED"],
        "release_confirmations": [
            row("BLOCKER", "CLEARANCE_RELEASE_CONFIRMATION_BLOCKED", "FAIL_CLOSED"),
            row("EXTERNAL", "CLEARANCE_RELEASE_CONFIRMATION_WAITING_EXTERNAL_ARTIFACT", "WAITING"),
            row("ACCEPT", "CLEARANCE_RELEASE_CONFIRMATION_WAITING_ACCEPTANCE", "WAITING"),
            row("REVIEW", "CLEARANCE_RELEASE_CONFIRMATION_WAITING_ACKNOWLEDGMENT_REVIEW", "WAITING"),
            row("INVESTIGATE", "CLEARANCE_RELEASE_CONFIRMATION_INVESTIGATION_REQUIRED", "WAITING"),
            row("READY", "CLEARANCE_RELEASE_CONFIRMATION_READY_FOR_HUMAN_CONFIRMATION_OBSERVATION", "HUMAN_CONFIRMATION_READY_OBSERVATION", True),
        ],
    }


def test_completion_projects_confirmations_and_preserves_firewall(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_confirmation_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_completion_board_payload()
    first = payload["release_completions"][0]
    assert payload["schema_version"] == "ui_semantic_validator_handoff_clearance_release_completion_board/v1"
    assert payload["read_plane_only"] is True
    assert first["release_completion_status"] == "CLEARANCE_RELEASE_COMPLETION_BLOCKED"
    assert first["release_completion_write_authority"] == "none_read_plane"
    assert first["release_confirmation_write_authority"] == "none_read_plane"
    assert payload["summary"]["release_completion_write_allowed_count"] == 0
    assert payload["summary"]["release_confirmation_write_allowed_count"] == 0
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_COMPLETION_FAIL_CLOSED_PRESENT" in payload["degraded"]


def test_completion_filters_ready(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_confirmation_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_completion_board_payload(
        ready_for_human_completion_observation=True
    )
    assert payload["summary"]["release_completion_count_returned"] == 1
    assert payload["release_completions"][0]["evidence_lane"] == "READY"
    assert "writes no completion" in payload["release_completions"][0]["release_completion_instruction"]


def test_completion_filters_confirmation_review(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_confirmation_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_completion_board_payload(
        release_completion_status=("CLEARANCE_RELEASE_COMPLETION_WAITING_CONFIRMATION_REVIEW",)
    )
    assert payload["summary"]["release_completion_count_returned"] == 1
    assert payload["release_completions"][0]["release_completion_gate"] == "release_confirmation_reclassified_to_known_completion_state"


def test_completion_filters_investigation(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_confirmation_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_completion_board_payload(
        release_completion_status=("CLEARANCE_RELEASE_COMPLETION_INVESTIGATION_REQUIRED",)
    )
    assert payload["summary"]["release_completion_count_returned"] == 1
    assert payload["release_completions"][0]["requires_investigation"] is True


def test_completion_latest(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_confirmation_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_completion_board_latest_payload()
    assert payload["summary"]["release_completion_count_returned"] == 1
    assert payload["latest"] == payload["release_completions"][0]
