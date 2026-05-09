from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_clearance_checklist as c


def _dossier(kind: str = "blocked") -> dict[str, object]:
    if kind == "clear":
        posture = "OBSERVED_CLEAR_NO_ESCALATIONS"
        status = "OBSERVED_CLEAR_NO_ESCALATIONS"
        blocked = False
        external = False
        checks = [
            {"check_id": "resolution_steps_clear", "check_state": "PASS", "evidence": "source_resolution_step_count=0", "route": "/ui/semantic-validator-handoff/resolution-plan", "write_allowed": False},
            {"check_id": "handoff_not_blocked", "check_state": "PASS", "evidence": "clearance_status=OBSERVED_CLEAR_NO_ESCALATIONS", "route": "/ui/semantic-validator-handoff/clearance-gate", "write_allowed": False},
            {"check_id": "external_artifact_gap_absent", "check_state": "PASS", "evidence": "requires_external_artifact=False", "route": "/ui/semantic-validator-handoff/clearance-gate", "write_allowed": False},
            {"check_id": "operator_review_boundary_preserved", "check_state": "PASS", "evidence": "approval_authority=none_read_plane", "route": "/ui/semantic-validator-handoff/clearance-dossier", "write_allowed": False},
        ]
    elif kind == "external":
        posture = "WAITING_EXTERNAL_ARTIFACT"
        status = "WAITING_EXTERNAL_ARTIFACT"
        blocked = True
        external = True
        checks = [
            {"check_id": "resolution_steps_clear", "check_state": "ATTENTION_REQUIRED", "evidence": "source_resolution_step_count=1", "route": "/ui/semantic-validator-handoff/resolution-plan", "write_allowed": False},
            {"check_id": "external_artifact_gap_absent", "check_state": "WAITING_EXTERNAL_ARTIFACT", "evidence": "requires_external_artifact=True", "route": "/ui/semantic-validator-handoff/clearance-gate", "write_allowed": False},
            {"check_id": "operator_review_boundary_preserved", "check_state": "PASS", "evidence": "approval_authority=none_read_plane", "route": "/ui/semantic-validator-handoff/clearance-dossier", "write_allowed": False},
        ]
    else:
        posture = "CLEARANCE_BLOCKED"
        status = "BLOCKED_BY_RESOLUTION_STEP"
        blocked = True
        external = False
        checks = [
            {"check_id": "resolution_steps_clear", "check_state": "ATTENTION_REQUIRED", "evidence": "source_resolution_step_count=1", "route": "/ui/semantic-validator-handoff/resolution-plan", "write_allowed": False},
            {"check_id": "handoff_not_blocked", "check_state": "BLOCKED", "evidence": "clearance_status=BLOCKED_BY_RESOLUTION_STEP", "route": "/ui/semantic-validator-handoff/clearance-gate", "write_allowed": False},
            {"check_id": "operator_review_boundary_preserved", "check_state": "PASS", "evidence": "approval_authority=none_read_plane", "route": "/ui/semantic-validator-handoff/clearance-dossier", "write_allowed": False},
        ]
    return {
        "schema_version": "ui_semantic_validator_handoff_clearance_dossier/v1",
        "search_root": "synthetic",
        "degraded": ["SOURCE_DEGRADED"] if kind == "blocked" else [],
        "summary": {"clearance_dossier_count_total": 1},
        "clearance_dossiers": [
            {
                "clearance_dossier_id": f"dossier-{kind}",
                "schema_version": "ui_semantic_validator_handoff_clearance_dossier/v1",
                "ordinal": 1,
                "review_posture": posture,
                "clearance_status": status,
                "clearance_gate_id": f"gate-{kind}",
                "scope_key": "EXP-CHECKLIST-1" if kind != "clear" else "GLOBAL_SEMANTIC_VALIDATOR_HANDOFF",
                "experiment_id": "EXP-CHECKLIST-1" if kind != "clear" else None,
                "priority": "P0" if kind == "blocked" else "P1" if kind == "external" else "P3",
                "severity": "HIGH" if kind == "blocked" else "WARN" if kind == "external" else "INFO",
                "trust_banner": "TRUST_RESTRICTED" if kind != "clear" else "TRUSTED",
                "owner_hint": "human_operator_clearance_owner",
                "handoff_clearance_blocked": blocked,
                "candidate_for_operator_clearance_review": not blocked,
                "requires_external_artifact": external,
                "requires_human_review": blocked,
                "issue_codes": ["ISSUE"] if kind != "clear" else [],
                "issue_count": 1 if kind != "clear" else 0,
                "phase_set": ["BLOCKER_TRIAGE"] if kind == "blocked" else ["EXTERNAL_ARTIFACT_COLLECTION"] if kind == "external" else [],
                "routes": {"clearance_dossier": "/ui/semantic-validator-handoff/clearance-dossier"},
                "dossier_digest": f"digest-{kind}",
                "review_checks": checks,
            }
        ],
    }


def test_clearance_checklist_flattens_blocked_checks_without_ack_authority(monkeypatch):
    monkeypatch.setattr(c, "build_ui_semantic_validator_handoff_clearance_dossier_payload", lambda **_: _dossier("blocked"))
    payload = c.build_ui_semantic_validator_handoff_clearance_checklist_payload(blocks_clearance=True)
    item = payload["checklist_items"][0]
    assert item["check_state"] == "BLOCKED"
    assert item["blocks_clearance"] is True
    assert item["check_acknowledgment_authority"] == "none_read_plane"
    assert item["check_override_authority"] == "none_read_plane"
    assert item["operator_approval_authority"] == "none_read_plane"
    assert item["signoff_authority"] == "none_read_plane"
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_CHECKLIST_BLOCKED" in payload["degraded"]


def test_clearance_checklist_external_artifact_filter(monkeypatch):
    monkeypatch.setattr(c, "build_ui_semantic_validator_handoff_clearance_dossier_payload", lambda **_: _dossier("external"))
    payload = c.build_ui_semantic_validator_handoff_clearance_checklist_payload(requires_external_artifact=True)
    assert payload["summary"]["external_artifact_check_count"] == 1
    item = payload["checklist_items"][0]
    assert item["check_id"] == "external_artifact_gap_absent"
    assert item["check_state"] == "WAITING_EXTERNAL_ARTIFACT"
    assert item["external_artifact_write_authority"] == "none_read_plane"


def test_clearance_checklist_clear_passes_are_observation_not_signoff(monkeypatch):
    monkeypatch.setattr(c, "build_ui_semantic_validator_handoff_clearance_dossier_payload", lambda **_: _dossier("clear"))
    payload = c.build_ui_semantic_validator_handoff_clearance_checklist_payload(check_state=("PASS",))
    assert payload["summary"]["attention_required_count"] == 0
    assert payload["summary"]["pass_check_count"] == 4
    assert payload["summary"]["signoff_allowed_count"] == 0
    assert all(item["check_state"] == "PASS" for item in payload["checklist_items"])
    assert all(item["execution_authority"] == "none_read_plane" for item in payload["checklist_items"])
