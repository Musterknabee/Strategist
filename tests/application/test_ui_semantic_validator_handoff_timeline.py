from __future__ import annotations

from unittest.mock import patch

from strategy_validator.application.ui_semantic_validator_handoff_timeline import build_ui_semantic_validator_handoff_timeline_payload


def _stage(stage: str, *, present: bool = True, ready: bool = True, issue_codes: list[str] | None = None) -> dict[str, object]:
    return {
        "stage": stage,
        "label": stage.title(),
        "route": f"/ui/semantic-validator-handoff/{stage}",
        "record_id": f"{stage}-1" if present else None,
        "digest": f"{stage}-digest" if present else None,
        "present": present,
        "ready": ready,
        "status": "PRESENT" if stage != "closure" else "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION",
        "issue_codes": issue_codes or [],
    }


def _continuity_row(*, terminal_status: str = "AWAITING_EXTERNAL_CLOSURE_ATTESTATION", external_required: bool = True) -> dict[str, object]:
    return {
        "continuity_id": "continuity-1",
        "experiment_id": "EXP-1",
        "chain_id": "chain-1",
        "chain_digest": "chain-digest",
        "terminal_status": terminal_status,
        "current_stage": "closure",
        "closure_status": "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION" if external_required else "CLOSURE_ATTESTATION_RECORDED",
        "trust_banner": "TRUST_RESTRICTED",
        "open_action": external_required,
        "external_artifact_required": external_required,
        "next_external_artifact_kind": "semantic_validator_handoff_closure_attestation" if external_required else None,
        "next_external_schema_version": "semantic_validator_handoff_closure_attestation/v1" if external_required else None,
        "stage_path": [
            _stage("decision"),
            _stage("signoff"),
            _stage("custody"),
            _stage("archive"),
            _stage("closure", ready=not external_required, issue_codes=["EXTERNAL_CLOSURE_ATTESTATION_MISSING"] if external_required else []),
        ],
        "continuity_route": "/ui/semantic-validator-handoff/continuity",
        "summary_line": "EXP-1 · continuity · execute=false",
    }


def _continuity_payload(*rows: dict[str, object], degraded: list[str] | None = None) -> dict[str, object]:
    return {
        "schema_version": "ui_semantic_validator_handoff_continuity/v1",
        "search_root": "fixture",
        "degraded": degraded or [],
        "summary": {"continuity_count_total": len(rows)},
        "continuity_rows": list(rows),
    }


def test_timeline_flattens_continuity_stage_path_and_marks_external_artifact_wait() -> None:
    with patch(
        "strategy_validator.application.ui_semantic_validator_handoff_timeline.build_ui_semantic_validator_handoff_continuity_payload",
        return_value=_continuity_payload(_continuity_row()),
    ):
        payload = build_ui_semantic_validator_handoff_timeline_payload(event_state=("AWAITING_EXTERNAL_ARTIFACT",))

    assert payload["schema_version"] == "ui_semantic_validator_handoff_timeline/v1"
    assert payload["read_plane_only"] is True
    assert payload["execution_authority"] == "none_read_plane"
    assert payload["summary"]["timeline_event_count_total"] == 5
    assert payload["summary"]["external_artifact_required_count"] == 1
    row = payload["timeline_events"][0]
    assert row["stage"] == "closure"
    assert row["event_state"] == "AWAITING_EXTERNAL_ARTIFACT"
    assert row["operator_focus"] == "CREATE_EXTERNAL_CLOSURE_ATTESTATION"
    assert row["authority"]["validator_submission_allowed"] is False
    assert "SEMANTIC_VALIDATOR_HANDOFF_TIMELINE_EXTERNAL_ARTIFACT_REQUIRED" in payload["degraded"]


def test_timeline_can_hide_ready_events_and_surface_missing_evidence() -> None:
    row = _continuity_row()
    row["stage_path"] = [
        _stage("decision"),
        _stage("signoff"),
        _stage("custody", present=False, ready=False, issue_codes=["CUSTODY_EVIDENCE_MISSING"]),
        _stage("archive"),
        _stage("closure", ready=False, issue_codes=["EXTERNAL_CLOSURE_ATTESTATION_MISSING"]),
    ]
    with patch(
        "strategy_validator.application.ui_semantic_validator_handoff_timeline.build_ui_semantic_validator_handoff_continuity_payload",
        return_value=_continuity_payload(row),
    ):
        payload = build_ui_semantic_validator_handoff_timeline_payload(include_ready=False, stage=("custody",))

    assert payload["summary"]["timeline_event_count_returned"] == 1
    event = payload["timeline_events"][0]
    assert event["event_state"] == "MISSING_EVIDENCE"
    assert event["operator_focus"] == "RESTORE_CUSTODY_EVIDENCE"
    assert "MISSING_SEMANTIC_VALIDATOR_HANDOFF_STAGE_EVIDENCE_PRESENT" in payload["degraded"]


def test_timeline_reports_closed_chain_as_recorded_ready() -> None:
    with patch(
        "strategy_validator.application.ui_semantic_validator_handoff_timeline.build_ui_semantic_validator_handoff_continuity_payload",
        return_value=_continuity_payload(_continuity_row(terminal_status="CLOSED_WITH_RECORDED_CLOSURE_ATTESTATION", external_required=False)),
    ):
        payload = build_ui_semantic_validator_handoff_timeline_payload()

    assert payload["summary"]["ready_event_count"] == 5
    assert payload["summary"]["blocked_event_count"] == 0
    assert payload["summary"]["external_artifact_required_count"] == 0
    assert set(payload["event_state_counts"]) == {"RECORDED_READY"}
    assert payload["execution_authority"] == "none_read_plane"
