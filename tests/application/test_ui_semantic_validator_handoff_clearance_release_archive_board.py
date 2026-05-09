from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_release_archive_board as m


def _source() -> dict[str, object]:
    def row(lane: str, status: str, readiness: str, ready: bool = False) -> dict[str, object]:
        return {
            "release_closure_id": f"rclose-{lane}",
            "evidence_lane": lane,
            "release_closure_status": status,
            "release_closure_readiness": readiness,
            "ready_for_human_closure_observation": ready,
            "blocked": readiness == "FAIL_CLOSED",
            "waiting": readiness == "WAITING",
            "requires_acceptance_observation": status == "CLEARANCE_RELEASE_CLOSURE_WAITING_ACCEPTANCE",
            "requires_external_artifact": status == "CLEARANCE_RELEASE_CLOSURE_WAITING_EXTERNAL_ARTIFACT",
            "requires_release_completion_review": status == "CLEARANCE_RELEASE_CLOSURE_WAITING_COMPLETION_REVIEW",
            "requires_investigation": status == "CLEARANCE_RELEASE_CLOSURE_INVESTIGATION_REQUIRED",
            "priority": "P2",
            "severity": "INFO",
            "trust_banner": "TRUSTED" if ready else "TRUST_RESTRICTED",
            "owner_hint": "human_operator_clearance_owner",
            "issue_codes": [f"ISSUE_{lane}"],
            "experiment_ids": ["EXP-1"],
            "source_release_completion_status": "SOURCE_COMPLETION",
            "source_release_completion_readiness": "SOURCE_COMPLETION_READINESS",
            "source_release_receipt_status": "SOURCE_RECEIPT",
            "source_release_receipt_readiness": "SOURCE_RECEIPT_READINESS",
        }

    return {
        "schema_version": "ui_semantic_validator_handoff_clearance_release_closure_board/v1",
        "search_root": "synthetic",
        "degraded": ["UPSTREAM_DEGRADED"],
        "release_closures": [
            row("BLOCKER", "CLEARANCE_RELEASE_CLOSURE_BLOCKED", "FAIL_CLOSED"),
            row("EXTERNAL", "CLEARANCE_RELEASE_CLOSURE_WAITING_EXTERNAL_ARTIFACT", "WAITING"),
            row("ACCEPT", "CLEARANCE_RELEASE_CLOSURE_WAITING_ACCEPTANCE", "WAITING"),
            row("REVIEW", "CLEARANCE_RELEASE_CLOSURE_WAITING_COMPLETION_REVIEW", "WAITING"),
            row("INVESTIGATE", "CLEARANCE_RELEASE_CLOSURE_INVESTIGATION_REQUIRED", "WAITING"),
            row("READY", "CLEARANCE_RELEASE_CLOSURE_READY_FOR_HUMAN_CLOSURE_OBSERVATION", "HUMAN_CLOSURE_READY_OBSERVATION", True),
        ],
    }


def test_archive_projects_closures_and_preserves_firewall(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_closure_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_archive_board_payload()
    first = payload["release_archives"][0]
    assert payload["schema_version"] == "ui_semantic_validator_handoff_clearance_release_archive_board/v1"
    assert payload["read_plane_only"] is True
    assert first["release_archive_status"] == "CLEARANCE_RELEASE_ARCHIVE_BLOCKED"
    assert first["release_archive_write_authority"] == "none_read_plane"
    assert first["release_closure_write_authority"] == "none_read_plane"
    assert payload["summary"]["release_archive_write_allowed_count"] == 0
    assert payload["summary"]["release_closure_write_allowed_count"] == 0
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_ARCHIVE_FAIL_CLOSED_PRESENT" in payload["degraded"]


def test_archive_filters_ready(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_closure_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_archive_board_payload(
        ready_for_human_archive_observation=True
    )
    assert payload["summary"]["release_archive_count_returned"] == 1
    assert payload["release_archives"][0]["evidence_lane"] == "READY"
    assert "writes no archive" in payload["release_archives"][0]["release_archive_instruction"]


def test_archive_filters_closure_review(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_closure_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_archive_board_payload(
        release_archive_status=("CLEARANCE_RELEASE_ARCHIVE_WAITING_CLOSURE_REVIEW",)
    )
    assert payload["summary"]["release_archive_count_returned"] == 1
    assert payload["release_archives"][0]["release_archive_gate"] == "release_closure_reclassified_to_known_archive_state"


def test_archive_filters_investigation(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_closure_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_archive_board_payload(
        release_archive_status=("CLEARANCE_RELEASE_ARCHIVE_INVESTIGATION_REQUIRED",)
    )
    assert payload["summary"]["release_archive_count_returned"] == 1
    assert payload["release_archives"][0]["requires_investigation"] is True


def test_archive_latest(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_closure_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_archive_board_latest_payload()
    assert payload["summary"]["release_archive_count_returned"] == 1
    assert payload["latest"] == payload["release_archives"][0]
