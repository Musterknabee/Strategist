from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_operations_board as m


def _coverage_payload() -> dict[str, object]:
    def card(lane: str, status: str, *, rows: int = 1, priority: str = "P2", severity: str = "INFO", external: bool = False, blocked: bool = False) -> dict[str, object]:
        return {
            "coverage_card_id": f"coverage-{lane}",
            "schema_version": "ui_semantic_validator_handoff_clearance_coverage_board/v1",
            "ordinal": rows,
            "evidence_lane": lane,
            "coverage_status": status,
            "coverage_percent": 100 if status == "OBSERVED_COVERED" else 0,
            "row_count": rows,
            "attention_required_count": 0 if status == "OBSERVED_COVERED" else 1,
            "blocks_clearance_count": 1 if blocked else 0,
            "requires_external_artifact_count": 1 if external else 0,
            "verified_observation_count": rows if status == "OBSERVED_COVERED" else 0,
            "unknown_evidence_count": 0,
            "highest_priority": priority,
            "highest_severity": severity,
            "trust_banner": "TRUST_RESTRICTED" if status != "OBSERVED_COVERED" else "TRUSTED",
            "owner_hints": ["human_operator_clearance_owner"],
            "check_ids": [f"check-{lane}"],
            "issue_codes": [f"ISSUE_{lane}"],
            "issue_count": 1,
            "phase_set": ["CLEARANCE"],
            "source_routes": ["/ui/semantic-validator-handoff/clearance-checklist"],
            "sample_row_ids": [f"row-{lane}"],
            "source_matrix_route": "/ui/semantic-validator-handoff/clearance-evidence-matrix",
            "coverage_board_route": "/ui/semantic-validator-handoff/clearance-coverage-board",
            "attention_required": status != "OBSERVED_COVERED",
            "blocks_clearance": blocked,
            "requires_external_artifact": external,
            "source_evidence_rows": [{"experiment_id": "EXP-1", "continuity_id": "CONT-1", "audit_packet_id": f"PKT-{lane}"}],
        }

    return {
        "schema_version": "ui_semantic_validator_handoff_clearance_coverage_board/v1",
        "search_root": "synthetic",
        "degraded": ["SOURCE_DEGRADED"],
        "coverage_cards": [
            card("EXTERNAL_ARTIFACT", "WAITING_EXTERNAL_ARTIFACT", priority="P1", severity="WARN", external=True, blocked=False),
            card("RESOLUTION_PLAN", "BLOCKED_BY_EVIDENCE_GAP", priority="P0", severity="HIGH", blocked=True),
            card("CLEARANCE_GATE", "OBSERVED_COVERED", priority="P3", severity="INFO"),
            card("CLEARANCE_DOSSIER", "NO_EVIDENCE_ROWS", rows=0, priority="P2", severity="LOW"),
        ],
    }


def test_clearance_operations_board_prioritizes_blockers_and_preserves_read_only_authority(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_coverage_board_payload", lambda **_: _coverage_payload())
    payload = m.build_ui_semantic_validator_handoff_clearance_operations_board_payload()
    first = payload["operation_cards"][0]
    assert first["operation_state"] == "BLOCKED_CLEARANCE_OPERATION"
    assert first["action_group"] == "TRIAGE_BLOCKERS"
    assert first["handoff_clearance_blocked"] is True
    assert first["operation_acknowledgment_authority"] == "none_read_plane"
    assert first["clearance_decision_authority"] == "none_read_plane"
    assert first["execution_authority"] == "none_read_plane"
    assert payload["summary"]["operation_acknowledgment_allowed_count"] == 0
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_OPERATIONS_BLOCKED" in payload["degraded"]


def test_clearance_operations_board_filters_external_artifact_work(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_coverage_board_payload", lambda **_: _coverage_payload())
    payload = m.build_ui_semantic_validator_handoff_clearance_operations_board_payload(operation_state=("EXTERNAL_ARTIFACT_OPERATION",))
    assert payload["summary"]["operation_card_count_returned"] == 1
    card = payload["operation_cards"][0]
    assert card["evidence_lane"] == "EXTERNAL_ARTIFACT"
    assert card["requires_external_artifact"] is True
    assert card["action_group"] == "COLLECT_EXTERNAL_ARTIFACTS"
    assert card["external_artifact_write_authority"] == "none_read_plane"


def test_clearance_operations_board_observed_ready_is_not_clearance(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_coverage_board_payload", lambda **_: _coverage_payload())
    payload = m.build_ui_semantic_validator_handoff_clearance_operations_board_payload(ready_for_operator_clearance_review=True)
    assert payload["summary"]["operation_card_count_returned"] == 1
    card = payload["operation_cards"][0]
    assert card["operation_state"] == "COVERAGE_OBSERVED_READY"
    assert card["ready_for_operator_clearance_review"] is True
    assert card["operator_approval_authority"] == "none_read_plane"
    assert card["signoff_authority"] == "none_read_plane"
    assert "not approval or signoff" in card["next_safe_action"]
