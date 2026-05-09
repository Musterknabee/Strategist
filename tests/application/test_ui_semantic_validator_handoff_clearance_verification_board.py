from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_verification_board as m


def _resolution_plan_payload() -> dict[str, object]:
    def step(lane: str, phase: str, *, priority: str = "P2", severity: str = "INFO", ready: bool = False) -> dict[str, object]:
        return {
            "resolution_step_id": f"step-{lane}",
            "schema_version": "ui_semantic_validator_handoff_clearance_resolution_plan/v1",
            "phase": phase,
            "evidence_lane": lane,
            "step_state": "READY_FOR_AUTHORIZED_CLEARANCE_REVIEW" if ready else "WAITING_ON_HUMAN_REVIEW",
            "action_state": "READY_REVIEW_CANDIDATE" if ready else "BLOCKED_ACTION",
            "action_type": "REVIEW_READY_COVERAGE" if ready else "TRIAGE_CLEARANCE_BLOCKER",
            "operation_state": "OPERATOR_REVIEW_OPERATION" if ready else "BLOCKED_CLEARANCE_OPERATION",
            "action_group": "OPERATOR_REVIEW" if ready else "TRIAGE_BLOCKERS",
            "coverage_status": "OBSERVED_COVERED" if ready else "NEEDS_OPERATOR_REVIEW",
            "coverage_percent": 100 if ready else 25,
            "source_action_id": f"action-{lane}",
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
            "blocks_handoff_clearance": phase == "BLOCKER_TRIAGE",
            "requires_external_artifact": phase == "EXTERNAL_ARTIFACT_COLLECTION",
            "requires_human_review": phase in {"HUMAN_OPERATOR_REVIEW", "AUTHORIZED_CLEARANCE_REVIEW"},
            "ready_for_operator_clearance_review": ready,
            "completion_gate": "source_resolution_step_resolved",
            "verification_hint": "Rebuild clearance resolution plan.",
            "safe_instruction": f"Safe instruction for {lane}; not approval or signoff.",
        }

    return {
        "schema_version": "ui_semantic_validator_handoff_clearance_resolution_plan/v1",
        "search_root": "synthetic",
        "degraded": ["SOURCE_PLAN_DEGRADED"],
        "resolution_steps": [
            step("BLOCKER", "BLOCKER_TRIAGE", priority="P0", severity="HIGH"),
            step("EXTERNAL", "EXTERNAL_ARTIFACT_COLLECTION", priority="P1", severity="WARN"),
            step("REVIEW", "HUMAN_OPERATOR_REVIEW", priority="P2", severity="MEDIUM"),
            step("READY", "AUTHORIZED_CLEARANCE_REVIEW", priority="P3", severity="INFO", ready=True),
        ],
    }


def test_clearance_verification_board_fails_closed_for_visible_blockers_and_preserves_firewall(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_resolution_plan_payload", lambda **_: _resolution_plan_payload())

    payload = m.build_ui_semantic_validator_handoff_clearance_verification_board_payload()
    first = payload["verification_cards"][0]

    assert first["verification_status"] == "BLOCKING_SOURCE_ACTION_VISIBLE"
    assert first["verification_result"] == "FAIL_CLOSED"
    assert first["verification_passed"] is False
    assert first["verification_write_authority"] == "none_read_plane"
    assert first["completion_assertion_authority"] == "none_read_plane"
    assert first["operator_approval_authority"] == "none_read_plane"
    assert first["signoff_authority"] == "none_read_plane"
    assert payload["summary"]["verification_write_allowed_count"] == 0
    assert payload["summary"]["completion_assertion_allowed_count"] == 0
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_VERIFICATION_FAIL_CLOSED_PRESENT" in payload["degraded"]


def test_clearance_verification_board_filters_external_artifact_status(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_resolution_plan_payload", lambda **_: _resolution_plan_payload())

    payload = m.build_ui_semantic_validator_handoff_clearance_verification_board_payload(verification_status=("EXTERNAL_ARTIFACT_STILL_REQUIRED",))

    assert payload["summary"]["verification_card_count_returned"] == 1
    card = payload["verification_cards"][0]
    assert card["evidence_lane"] == "EXTERNAL"
    assert card["verification_result"] == "WAITING"
    assert card["external_artifact_write_authority"] == "none_read_plane"
    assert "outside this read-plane" in card["verification_note"]


def test_clearance_verification_board_ready_observation_is_not_clearance(monkeypatch):
    monkeypatch.setattr(m, "build_ui_semantic_validator_handoff_clearance_resolution_plan_payload", lambda **_: _resolution_plan_payload())

    payload = m.build_ui_semantic_validator_handoff_clearance_verification_board_payload(verification_passed=True)

    assert payload["summary"]["verification_card_count_returned"] == 1
    card = payload["verification_cards"][0]
    assert card["verification_status"] == "READY_FOR_AUTHORIZED_REVIEW_OBSERVED"
    assert card["verification_result"] == "REVIEW_OBSERVATION"
    assert card["clearance_decision_authority"] == "none_read_plane"
    assert card["operator_approval_authority"] == "none_read_plane"
    assert card["signoff_authority"] == "none_read_plane"
    assert "governed clearance/signoff path" in card["verification_note"]
