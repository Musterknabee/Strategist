from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_release_disposition_board as m


def _source() -> dict[str, object]:
    def row(lane: str, status: str, readiness: str, ready: bool = False) -> dict[str, object]:
        return {
            "release_retention_id": f"rclose-{lane}",
            "evidence_lane": lane,
            "release_retention_status": status,
            "release_retention_readiness": readiness,
            "ready_for_human_retention_observation": ready,
            "blocked": readiness == "FAIL_CLOSED",
            "waiting": readiness == "WAITING",
            "requires_acceptance_observation": status == "CLEARANCE_RELEASE_RETENTION_WAITING_ACCEPTANCE",
            "requires_external_artifact": status == "CLEARANCE_RELEASE_RETENTION_WAITING_EXTERNAL_ARTIFACT",
            "requires_release_archive_review": status == "CLEARANCE_RELEASE_RETENTION_WAITING_ARCHIVE_REVIEW",
            "requires_investigation": status == "CLEARANCE_RELEASE_RETENTION_INVESTIGATION_REQUIRED",
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
        "schema_version": "ui_semantic_validator_handoff_clearance_release_retention_board/v1",
        "search_root": "synthetic",
        "degraded": ["UPSTREAM_DEGRADED"],
        "release_retentions": [
            row("BLOCKER", "CLEARANCE_RELEASE_RETENTION_BLOCKED", "FAIL_CLOSED"),
            row("EXTERNAL", "CLEARANCE_RELEASE_RETENTION_WAITING_EXTERNAL_ARTIFACT", "WAITING"),
            row("ACCEPT", "CLEARANCE_RELEASE_RETENTION_WAITING_ACCEPTANCE", "WAITING"),
            row("REVIEW", "CLEARANCE_RELEASE_RETENTION_WAITING_ARCHIVE_REVIEW", "WAITING"),
            row("INVESTIGATE", "CLEARANCE_RELEASE_RETENTION_INVESTIGATION_REQUIRED", "WAITING"),
            row("READY", "CLEARANCE_RELEASE_RETENTION_READY_FOR_HUMAN_RETENTION_OBSERVATION", "HUMAN_RETENTION_READY_OBSERVATION", True),
        ],
    }


def test_disposition_projects_retentions_and_preserves_firewall(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_retention_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_disposition_board_payload()
    first = payload["release_dispositions"][0]
    assert payload["schema_version"] == "ui_semantic_validator_handoff_clearance_release_disposition_board/v1"
    assert payload["read_plane_only"] is True
    assert first["release_disposition_status"] == "CLEARANCE_RELEASE_DISPOSITION_BLOCKED"
    assert first["release_disposition_write_authority"] == "none_read_plane"
    assert first["release_disposition_write_authority"] == "none_read_plane"
    assert payload["summary"]["release_disposition_write_allowed_count"] == 0
    assert payload["summary"]["release_disposition_write_allowed_count"] == 0
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_DISPOSITION_FAIL_CLOSED_PRESENT" in payload["degraded"]


def test_disposition_filters_ready(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_retention_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_disposition_board_payload(
        ready_for_human_disposition_observation=True
    )
    assert payload["summary"]["release_disposition_count_returned"] == 1
    assert payload["release_dispositions"][0]["evidence_lane"] == "READY"
    assert "writes no disposition" in payload["release_dispositions"][0]["release_disposition_instruction"]


def test_disposition_filters_retention_review(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_retention_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_disposition_board_payload(
        release_disposition_status=("CLEARANCE_RELEASE_DISPOSITION_WAITING_RETENTION_REVIEW",)
    )
    assert payload["summary"]["release_disposition_count_returned"] == 1
    assert payload["release_dispositions"][0]["release_disposition_gate"] == "release_retention_reclassified_to_known_disposition_state"


def test_disposition_filters_investigation(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_retention_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_disposition_board_payload(
        release_disposition_status=("CLEARANCE_RELEASE_DISPOSITION_INVESTIGATION_REQUIRED",)
    )
    assert payload["summary"]["release_disposition_count_returned"] == 1
    assert payload["release_dispositions"][0]["requires_investigation"] is True


def test_disposition_latest(monkeypatch) -> None:
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_release_retention_board_payload", lambda **_: _source())
    payload = m.build_ui_semantic_validator_handoff_clearance_release_disposition_board_latest_payload()
    assert payload["summary"]["release_disposition_count_returned"] == 1
    assert payload["latest"] == payload["release_dispositions"][0]
