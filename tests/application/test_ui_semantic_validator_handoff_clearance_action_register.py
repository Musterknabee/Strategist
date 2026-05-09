from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_action_register as m


def _operations_payload() -> dict[str, object]:
    def card(lane: str, state: str, *, priority: str = "P2", severity: str = "INFO", ready: bool = False) -> dict[str, object]:
        return {
            "operation_card_id": f"operation-{lane}",
            "schema_version": "ui_semantic_validator_handoff_clearance_operations_board/v1",
            "ordinal": 1,
            "operation_state": state,
            "operation_state_rank": 0,
            "action_group": {
                "BLOCKED_CLEARANCE_OPERATION": "TRIAGE_BLOCKERS",
                "EXTERNAL_ARTIFACT_OPERATION": "COLLECT_EXTERNAL_ARTIFACTS",
                "OPERATOR_REVIEW_OPERATION": "OPERATOR_REVIEW",
                "NO_CLEARANCE_EVIDENCE": "REFRESH_UPSTREAM_EVIDENCE",
                "COVERAGE_OBSERVED_READY": "READINESS_REVIEW",
            }.get(state, "INVESTIGATE_UNKNOWN"),
            "action_group_rank": 0,
            "evidence_lane": lane,
            "coverage_status": "OBSERVED_COVERED" if ready else "NEEDS_OPERATOR_REVIEW",
            "coverage_percent": 100 if ready else 25,
            "source_coverage_card_id": f"coverage-{lane}",
            "row_count": 2,
            "highest_priority": priority,
            "highest_severity": severity,
            "trust_banner": "TRUSTED" if ready else "TRUST_RESTRICTED",
            "owner_hints": ["human_operator_clearance_owner"],
            "owner_hint": "human_operator_clearance_owner",
            "check_ids": [f"check-{lane}"],
            "issue_codes": [f"ISSUE_{lane}"],
            "issue_count": 1,
            "phase_set": ["CLEARANCE"],
            "source_routes": ["/ui/semantic-validator-handoff/clearance-checklist"],
            "experiment_ids": ["EXP-1"],
            "continuity_ids": ["CONT-1"],
            "audit_packet_ids": [f"PKT-{lane}"],
            "operator_attention_required": not ready,
            "handoff_clearance_blocked": state == "BLOCKED_CLEARANCE_OPERATION",
            "requires_external_artifact": state == "EXTERNAL_ARTIFACT_OPERATION",
            "ready_for_operator_clearance_review": ready,
            "source_matrix_route": "/ui/semantic-validator-handoff/clearance-evidence-matrix",
            "coverage_board_route": "/ui/semantic-validator-handoff/clearance-coverage-board",
            "operations_board_route": "/ui/semantic-validator-handoff/clearance-operations-board",
            "next_safe_action": f"Next safe action for {lane}; not approval or signoff.",
        }

    return {
        "schema_version": "ui_semantic_validator_handoff_clearance_operations_board/v1",
        "search_root": "synthetic",
        "degraded": ["SOURCE_OPS_DEGRADED"],
        "operation_cards": [
            card("EXTERNAL_ARTIFACT", "EXTERNAL_ARTIFACT_OPERATION", priority="P1", severity="WARN"),
            card("RESOLUTION_PLAN", "BLOCKED_CLEARANCE_OPERATION", priority="P0", severity="HIGH"),
            card("CHECKLIST", "OPERATOR_REVIEW_OPERATION", priority="P2", severity="MEDIUM"),
            card("CLEARANCE_GATE", "COVERAGE_OBSERVED_READY", priority="P3", severity="INFO", ready=True),
        ],
    }


def test_clearance_action_register_prioritizes_blocked_actions_and_preserves_firewall(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_operations_board_payload", lambda **_: _operations_payload())

    payload = m.build_ui_semantic_validator_handoff_clearance_action_register_payload()
    first = payload["action_rows"][0]

    assert first["action_state"] == "BLOCKED_ACTION"
    assert first["action_type"] == "TRIAGE_CLEARANCE_BLOCKER"
    assert first["blocked"] is True
    assert first["action_acknowledgment_authority"] == "none_read_plane"
    assert first["action_execution_authority"] == "none_read_plane"
    assert first["operator_approval_authority"] == "none_read_plane"
    assert first["signoff_authority"] == "none_read_plane"
    assert first["execution_authority"] == "none_read_plane"
    assert payload["summary"]["action_acknowledgment_allowed_count"] == 0
    assert payload["summary"]["action_execution_allowed_count"] == 0
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_ACTION_REGISTER_BLOCKED" in payload["degraded"]


def test_clearance_action_register_filters_external_artifact_actions(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_operations_board_payload", lambda **_: _operations_payload())

    payload = m.build_ui_semantic_validator_handoff_clearance_action_register_payload(action_state=("WAITING_EXTERNAL_ARTIFACT",))

    assert payload["summary"]["action_count_returned"] == 1
    row = payload["action_rows"][0]
    assert row["evidence_lane"] == "EXTERNAL_ARTIFACT"
    assert row["action_type"] == "COLLECT_EXTERNAL_ARTIFACT"
    assert row["requires_external_artifact"] is True
    assert row["external_artifact_write_authority"] == "none_read_plane"


def test_clearance_action_register_ready_candidate_is_not_clearance(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_operations_board_payload", lambda **_: _operations_payload())

    payload = m.build_ui_semantic_validator_handoff_clearance_action_register_payload(ready_for_operator_clearance_review=True)

    assert payload["summary"]["action_count_returned"] == 1
    row = payload["action_rows"][0]
    assert row["action_state"] == "READY_REVIEW_CANDIDATE"
    assert row["ready_for_operator_clearance_review"] is True
    assert row["clearance_decision_authority"] == "none_read_plane"
    assert row["operator_approval_authority"] == "none_read_plane"
    assert row["signoff_authority"] == "none_read_plane"
    assert "does not approve or sign off" in row["operator_action"]
