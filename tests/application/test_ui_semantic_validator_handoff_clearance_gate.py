from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_gate as c


def _plan(kind: str = "blocked") -> dict[str, object]:
    if kind == "empty":
        return {
            "schema_version": "ui_semantic_validator_handoff_resolution_plan/v1",
            "search_root": "synthetic",
            "degraded": [],
            "summary": {"source_escalation_count_total": 0},
            "resolution_steps": [],
        }
    if kind == "external":
        phase = "EXTERNAL_ARTIFACT_COLLECTION"
        state = "WAITING_EXTERNAL_ARTIFACT"
        priority = "P1"
        severity = "WARN"
        external = True
        blocked = True
    elif kind == "review":
        phase = "OPERATOR_REVIEW"
        state = "HUMAN_REVIEW_REQUIRED"
        priority = "P2"
        severity = "INFO"
        external = False
        blocked = False
    else:
        phase = "BLOCKER_TRIAGE"
        state = "BLOCKING_HUMAN_TRIAGE_REQUIRED"
        priority = "P0"
        severity = "HIGH"
        external = False
        blocked = True
    return {
        "schema_version": "ui_semantic_validator_handoff_resolution_plan/v1",
        "search_root": "synthetic",
        "degraded": ["SOURCE_DEGRADED"] if kind == "blocked" else [],
        "summary": {"source_escalation_count_total": 1},
        "resolution_steps": [
            {
                "resolution_step_id": f"step-{kind}",
                "phase": phase,
                "step_state": state,
                "experiment_id": "EXP-CLEAR-1",
                "continuity_id": "cont-1",
                "audit_packet_id": "packet-1",
                "audit_packet_digest": "digest-1",
                "priority": priority,
                "severity": severity,
                "trust_banner": "TRUST_RESTRICTED",
                "owner_hint": "human_operator_clearance_owner",
                "resolution_route": "/ui/semantic-validator-handoff/resolution-plan",
                "issue_codes": ["ISSUE"],
                "requires_external_artifact": external,
                "requires_human_review": True,
                "blocks_handoff_clearance": blocked,
            }
        ],
    }


def test_clearance_gate_blocks_on_blocking_resolution_step(monkeypatch):
    monkeypatch.setattr(c, "build_ui_semantic_validator_handoff_resolution_plan_payload", lambda **_: _plan("blocked"))
    payload = c.build_ui_semantic_validator_handoff_clearance_gate_payload(handoff_clearance_blocked=True)
    gate = payload["clearance_gates"][0]
    assert gate["clearance_status"] == "BLOCKED_BY_RESOLUTION_STEP"
    assert gate["handoff_clearance_blocked"] is True
    assert gate["candidate_for_operator_clearance_review"] is False
    assert gate["authority"]["clearance_decision_allowed"] is False
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_BLOCKED" in payload["degraded"]


def test_clearance_gate_waits_for_external_artifact(monkeypatch):
    monkeypatch.setattr(c, "build_ui_semantic_validator_handoff_resolution_plan_payload", lambda **_: _plan("external"))
    payload = c.build_ui_semantic_validator_handoff_clearance_gate_payload(requires_external_artifact=True)
    gate = payload["clearance_gates"][0]
    assert gate["clearance_status"] == "WAITING_EXTERNAL_ARTIFACT"
    assert gate["requires_external_artifact"] is True
    assert gate["handoff_clearance_blocked"] is True
    assert gate["external_artifact_write_authority"] == "none_read_plane"


def test_clearance_gate_observed_clear_when_no_resolution_steps(monkeypatch):
    monkeypatch.setattr(c, "build_ui_semantic_validator_handoff_resolution_plan_payload", lambda **_: _plan("empty"))
    payload = c.build_ui_semantic_validator_handoff_clearance_gate_payload(candidate_for_operator_clearance_review=True)
    gate = payload["clearance_gates"][0]
    assert gate["clearance_status"] == "OBSERVED_CLEAR_NO_ESCALATIONS"
    assert gate["candidate_for_operator_clearance_review"] is True
    assert gate["clearance_decision_authority"] == "none_read_plane"
    assert payload["summary"]["observed_clear_gate_count"] == 1
