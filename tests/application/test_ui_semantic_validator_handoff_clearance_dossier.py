from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_dossier as d


def _gate(kind: str = "blocked") -> dict[str, object]:
    if kind == "clear":
        status = "OBSERVED_CLEAR_NO_ESCALATIONS"
        blocked = False
        external = False
        review = False
        candidate = True
        priority = "P3"
        severity = "INFO"
        steps = 0
    elif kind == "external":
        status = "WAITING_EXTERNAL_ARTIFACT"
        blocked = True
        external = True
        review = True
        candidate = False
        priority = "P1"
        severity = "WARN"
        steps = 1
    else:
        status = "BLOCKED_BY_RESOLUTION_STEP"
        blocked = True
        external = False
        review = True
        candidate = False
        priority = "P0"
        severity = "HIGH"
        steps = 1
    return {
        "schema_version": "ui_semantic_validator_handoff_clearance_gate/v1",
        "search_root": "synthetic",
        "degraded": ["SOURCE_DEGRADED"] if kind == "blocked" else [],
        "summary": {"clearance_gate_count_total": 1},
        "clearance_gates": [
            {
                "clearance_gate_id": f"gate-{kind}",
                "schema_version": "ui_semantic_validator_handoff_clearance_gate/v1",
                "ordinal": 1,
                "scope_key": "EXP-DOSSIER-1" if kind != "clear" else "GLOBAL_SEMANTIC_VALIDATOR_HANDOFF",
                "experiment_id": "EXP-DOSSIER-1" if kind != "clear" else None,
                "clearance_status": status,
                "handoff_clearance_blocked": blocked,
                "candidate_for_operator_clearance_review": candidate,
                "requires_external_artifact": external,
                "requires_human_review": review,
                "source_resolution_step_count": steps,
                "blocking_resolution_step_count": 1 if blocked and not external else 0,
                "external_artifact_step_count": 1 if external else 0,
                "human_review_step_count": 1 if review else 0,
                "phase_set": ["BLOCKER_TRIAGE"] if kind == "blocked" else ["EXTERNAL_ARTIFACT_COLLECTION"] if kind == "external" else [],
                "issue_codes": ["ISSUE"] if kind != "clear" else [],
                "issue_count": 1 if kind != "clear" else 0,
                "priority": priority,
                "severity": severity,
                "trust_banner": "TRUST_RESTRICTED" if kind != "clear" else "TRUSTED",
                "owner_hint": "human_operator_clearance_owner",
                "source_route": "/ui/semantic-validator-handoff/clearance-gate",
                "resolution_plan_route": "/ui/semantic-validator-handoff/resolution-plan",
                "clearance_route": "/ui/semantic-validator-handoff/clearance-gate",
                "clearance_condition": "CONDITION",
                "safe_instruction": "SAFE",
                "source_resolution_steps": [],
            }
        ],
    }


def test_clearance_dossier_blocks_without_approval_authority(monkeypatch):
    monkeypatch.setattr(d, "build_ui_semantic_validator_handoff_clearance_gate_payload", lambda **_: _gate("blocked"))
    payload = d.build_ui_semantic_validator_handoff_clearance_dossier_payload(review_posture=("CLEARANCE_BLOCKED",))
    dossier = payload["clearance_dossiers"][0]
    assert dossier["review_posture"] == "CLEARANCE_BLOCKED"
    assert dossier["handoff_clearance_blocked"] is True
    assert dossier["candidate_for_operator_clearance_review"] is False
    assert dossier["operator_approval_authority"] == "none_read_plane"
    assert dossier["signoff_authority"] == "none_read_plane"
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_DOSSIER_BLOCKED" in payload["degraded"]


def test_clearance_dossier_external_artifact_wait(monkeypatch):
    monkeypatch.setattr(d, "build_ui_semantic_validator_handoff_clearance_gate_payload", lambda **_: _gate("external"))
    payload = d.build_ui_semantic_validator_handoff_clearance_dossier_payload(requires_external_artifact=True)
    dossier = payload["clearance_dossiers"][0]
    assert dossier["review_posture"] == "WAITING_EXTERNAL_ARTIFACT"
    assert dossier["requires_external_artifact"] is True
    assert any(check["check_state"] == "WAITING_EXTERNAL_ARTIFACT" for check in dossier["review_checks"])
    assert dossier["external_artifact_write_authority"] == "none_read_plane"


def test_clearance_dossier_observed_clear_is_not_signoff(monkeypatch):
    monkeypatch.setattr(d, "build_ui_semantic_validator_handoff_clearance_gate_payload", lambda **_: _gate("clear"))
    payload = d.build_ui_semantic_validator_handoff_clearance_dossier_payload(candidate_for_operator_clearance_review=True)
    dossier = payload["clearance_dossiers"][0]
    assert dossier["review_posture"] == "OBSERVED_CLEAR_NO_ESCALATIONS"
    assert dossier["candidate_for_operator_clearance_review"] is True
    assert dossier["failed_or_attention_check_count"] == 0
    assert dossier["clearance_decision_authority"] == "none_read_plane"
    assert dossier["execution_authority"] == "none_read_plane"
