from __future__ import annotations

from unittest.mock import patch

from strategy_validator.application.ui_semantic_validator_handoff_evidence_gaps import build_ui_semantic_validator_handoff_evidence_gaps_payload


def _event(*, stage: str = "closure", event_state: str = "AWAITING_EXTERNAL_ARTIFACT", severity: str = "WARN", present: bool = True, ready: bool = False, blocking: bool = True, external_required: bool = True, issue_codes: list[str] | None = None) -> dict[str, object]:
    issues = issue_codes if issue_codes is not None else (["EXTERNAL_CLOSURE_ATTESTATION_MISSING"] if external_required else [])
    return {
        "timeline_event_id": f"event-{stage}-{event_state}", "continuity_id": "continuity-1", "experiment_id": "EXP-1", "chain_id": "chain-1", "chain_digest": "chain-digest", "terminal_status": "AWAITING_EXTERNAL_CLOSURE_ATTESTATION", "current_stage": stage, "closure_status": "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION", "stage": stage, "stage_label": stage.title(), "stage_position": 5 if stage == "closure" else 3, "stage_route": f"/ui/semantic-validator-handoff/{stage}", "stage_status": "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION", "record_id": f"{stage}-1" if present else None, "digest": f"{stage}-digest" if present else None, "present": present, "ready": ready, "event_state": event_state, "severity": severity, "blocking": blocking, "external_artifact_required": external_required, "next_external_artifact_kind": "semantic_validator_handoff_closure_attestation" if external_required else None, "next_external_schema_version": "semantic_validator_handoff_closure_attestation/v1" if external_required else None, "operator_focus": "CREATE_EXTERNAL_CLOSURE_ATTESTATION", "issue_codes": issues, "issue_count": len(issues), "continuity_route": "/ui/semantic-validator-handoff/continuity", "runbook_route": "/ui/semantic-validator-handoff/runbook", "exceptions_route": "/ui/semantic-validator-handoff/exceptions", "summary_line": "EXP-1 · closure · wait · execute=false",
    }


def _timeline_payload(*events: dict[str, object], degraded: list[str] | None = None) -> dict[str, object]:
    return {"schema_version": "ui_semantic_validator_handoff_timeline/v1", "search_root": "fixture", "degraded": degraded or [], "summary": {"timeline_event_count_total": len(events)}, "timeline_events": list(events)}


def test_evidence_gaps_surfaces_external_closure_attestation_gap() -> None:
    with patch("strategy_validator.application.ui_semantic_validator_handoff_evidence_gaps.build_ui_semantic_validator_handoff_timeline_payload", return_value=_timeline_payload(_event())):
        payload = build_ui_semantic_validator_handoff_evidence_gaps_payload()
    assert payload["schema_version"] == "ui_semantic_validator_handoff_evidence_gaps/v1"
    assert payload["read_plane_only"] is True
    assert payload["execution_authority"] == "none_read_plane"
    assert payload["summary"]["external_artifact_gap_count"] == 1
    row = payload["gap_rows"][0]
    assert row["gap_kind"] == "EXTERNAL_ARTIFACT_GAP"
    assert row["gap_state"] == "AWAITING_EXTERNAL_ARTIFACT"
    assert row["priority"] == "P1"
    assert row["authority"]["validator_submission_allowed"] is False
    assert row["authority"]["execution_allowed"] is False
    assert "SEMANTIC_VALIDATOR_HANDOFF_EXTERNAL_ARTIFACT_GAP_PRESENT" in payload["degraded"]


def test_evidence_gaps_escalates_missing_stage_evidence() -> None:
    event = _event(stage="custody", event_state="MISSING_EVIDENCE", present=False, ready=False, blocking=True, external_required=False, issue_codes=["CUSTODY_EVIDENCE_MISSING"])
    with patch("strategy_validator.application.ui_semantic_validator_handoff_evidence_gaps.build_ui_semantic_validator_handoff_timeline_payload", return_value=_timeline_payload(event)):
        payload = build_ui_semantic_validator_handoff_evidence_gaps_payload(priority=("P0",))
    assert payload["summary"]["blocked_gap_count"] == 1
    assert payload["summary"]["missing_evidence_gap_count"] == 1
    row = payload["gap_rows"][0]
    assert row["gap_kind"] == "MISSING_STAGE_EVIDENCE_GAP"
    assert row["gap_state"] == "BLOCKED"
    assert row["repair_route"] == "/ui/semantic-validator-handoff/custody"
    assert "MISSING_SEMANTIC_VALIDATOR_HANDOFF_EVIDENCE_GAP_PRESENT" in payload["degraded"]


def test_evidence_gaps_excludes_resolved_ready_events_by_default() -> None:
    with patch("strategy_validator.application.ui_semantic_validator_handoff_evidence_gaps.build_ui_semantic_validator_handoff_timeline_payload", return_value=_timeline_payload(_event(stage="decision", event_state="RECORDED_READY", severity="INFO", ready=True, blocking=False, external_required=False, issue_codes=[]), _event())):
        payload = build_ui_semantic_validator_handoff_evidence_gaps_payload()
    assert payload["summary"]["gap_count_total"] == 2
    assert payload["summary"]["gap_count_returned"] == 1
    assert payload["summary"]["resolved_gap_excluded_count"] == 1
    assert payload["gap_rows"][0]["gap_kind"] == "EXTERNAL_ARTIFACT_GAP"


def test_evidence_gaps_can_include_resolved_audit_references() -> None:
    with patch("strategy_validator.application.ui_semantic_validator_handoff_evidence_gaps.build_ui_semantic_validator_handoff_timeline_payload", return_value=_timeline_payload(_event(stage="decision", event_state="RECORDED_READY", severity="INFO", ready=True, blocking=False, external_required=False, issue_codes=[]))):
        payload = build_ui_semantic_validator_handoff_evidence_gaps_payload(include_resolved=True)
    row = payload["gap_rows"][0]
    assert row["gap_kind"] == "RESOLVED_AUDIT_REFERENCE"
    assert row["gap_state"] == "RESOLVED"
    assert row["resolved"] is True
    assert payload["summary"]["resolved_gap_excluded_count"] == 0
