from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_resolution_plan as m


def _action_register_payload() -> dict[str, object]:
    def row(lane: str, state: str, *, priority: str = "P2", severity: str = "INFO", ready: bool = False) -> dict[str, object]:
        return {
            "action_id": f"action-{lane}",
            "schema_version": "ui_semantic_validator_handoff_clearance_action_register/v1",
            "action_state": state,
            "action_type": "REVIEW_READY_COVERAGE" if ready else "TRIAGE_CLEARANCE_BLOCKER",
            "evidence_lane": lane,
            "operation_state": "OPERATOR_REVIEW_OPERATION" if ready else "BLOCKED_CLEARANCE_OPERATION",
            "action_group": "OPERATOR_REVIEW" if ready else "TRIAGE_BLOCKERS",
            "coverage_status": "OBSERVED_COVERED" if ready else "NEEDS_OPERATOR_REVIEW",
            "coverage_percent": 100 if ready else 25,
            "source_operation_card_id": f"operation-{lane}",
            "source_coverage_card_id": f"coverage-{lane}",
            "priority": priority,
            "severity": severity,
            "trust_banner": "TRUSTED" if ready else "TRUST_RESTRICTED",
            "owner_hint": "human_operator_clearance_owner",
            "owner_hints": ["human_operator_clearance_owner"],
            "check_ids": [f"check-{lane}"],
            "issue_codes": [f"ISSUE_{lane}"],
            "issue_count": 1,
            "phase_set": ["CLEARANCE"],
            "experiment_ids": ["EXP-1"],
            "continuity_ids": ["CONT-1"],
            "audit_packet_ids": [f"PKT-{lane}"],
            "blocked": state == "BLOCKED_ACTION",
            "requires_external_artifact": state == "WAITING_EXTERNAL_ARTIFACT",
            "requires_human_review": state in {"HUMAN_REVIEW_REQUIRED", "READY_REVIEW_CANDIDATE"},
            "ready_for_operator_clearance_review": ready,
            "operator_action": f"Operator action for {lane}; no approval or signoff.",
        }

    return {
        "schema_version": "ui_semantic_validator_handoff_clearance_action_register/v1",
        "search_root": "synthetic",
        "degraded": ["SOURCE_ACTION_DEGRADED"],
        "action_rows": [
            row("EXTERNAL", "WAITING_EXTERNAL_ARTIFACT", priority="P1", severity="WARN"),
            row("BLOCKER", "BLOCKED_ACTION", priority="P0", severity="HIGH"),
            row("REVIEW", "HUMAN_REVIEW_REQUIRED", priority="P2", severity="MEDIUM"),
            row("READY", "READY_REVIEW_CANDIDATE", priority="P3", severity="INFO", ready=True),
        ],
    }


def test_clearance_resolution_plan_prioritizes_blockers_and_preserves_firewall(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_action_register_payload", lambda **_: _action_register_payload())

    payload = m.build_ui_semantic_validator_handoff_clearance_resolution_plan_payload()
    first = payload["resolution_steps"][0]

    assert first["phase"] == "BLOCKER_TRIAGE"
    assert first["step_state"] == "BLOCKED_UNTIL_SOURCE_RECLASSIFIED"
    assert first["blocks_handoff_clearance"] is True
    assert first["plan_materialization_authority"] == "none_read_plane"
    assert first["repair_execution_authority"] == "none_read_plane"
    assert first["operator_approval_authority"] == "none_read_plane"
    assert first["signoff_authority"] == "none_read_plane"
    assert payload["summary"]["plan_materialization_allowed_count"] == 0
    assert payload["summary"]["repair_execution_allowed_count"] == 0
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RESOLUTION_PLAN_BLOCKER_TRIAGE_PRESENT" in payload["degraded"]


def test_clearance_resolution_plan_filters_external_artifact_collection(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_action_register_payload", lambda **_: _action_register_payload())

    payload = m.build_ui_semantic_validator_handoff_clearance_resolution_plan_payload(phase=("EXTERNAL_ARTIFACT_COLLECTION",))

    assert payload["summary"]["resolution_step_count_returned"] == 1
    step = payload["resolution_steps"][0]
    assert step["evidence_lane"] == "EXTERNAL"
    assert step["requires_external_artifact"] is True
    assert step["external_artifact_write_authority"] == "none_read_plane"
    assert "outside this read-plane" in step["safe_instruction"]


def test_clearance_resolution_plan_ready_candidate_is_not_clearance(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_action_register_payload", lambda **_: _action_register_payload())

    payload = m.build_ui_semantic_validator_handoff_clearance_resolution_plan_payload(ready_for_operator_clearance_review=True)

    assert payload["summary"]["resolution_step_count_returned"] == 1
    step = payload["resolution_steps"][0]
    assert step["phase"] == "AUTHORIZED_CLEARANCE_REVIEW"
    assert step["clearance_decision_authority"] == "none_read_plane"
    assert step["operator_approval_authority"] == "none_read_plane"
    assert step["signoff_authority"] == "none_read_plane"
    assert "authorized clearance/signoff path" in step["safe_instruction"]
