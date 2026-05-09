from __future__ import annotations

from unittest.mock import patch

from strategy_validator.application.ui_semantic_validator_handoff_continuity import (
    build_ui_semantic_validator_handoff_continuity_payload,
)


def _closure_row(*, status: str = "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION", recorded: bool = False) -> dict[str, object]:
    return {
        "closure_gate_id": "closure-1",
        "closure_status": status,
        "closure_attestation_recorded": recorded,
        "closure_attestation_required": True,
        "closure_attestation_id": "att-1" if recorded else None,
        "trust_banner": "TRUSTED",
        "archive_gate_id": "archive-1",
        "archive_manifest_id": "manifest-1",
        "archive_status": "ARCHIVE_MANIFEST_VERIFIED",
        "custody_gate_id": "custody-1",
        "signoff_gate_id": "signoff-1",
        "decision_id": "decision-1",
        "chain_id": "chain-1",
        "chain_digest": "chain-digest",
        "experiment_id": "EXP-1",
        "decision_packet_digest": "decision-digest",
        "custody_packet_digest": "custody-digest",
        "archive_packet_digest": "archive-digest",
        "closure_packet_digest": "closure-digest",
        "issue_codes": [] if recorded else ["EXTERNAL_CLOSURE_ATTESTATION_MISSING"],
        "issue_count": 0 if recorded else 1,
        "closure_template": {"schema_version": "semantic_validator_handoff_closure_attestation/v1"},
        "recommended_action": "HANDOFF_CLOSURE_RECORDED_RETAIN_AUDIT_TRAIL" if recorded else "CREATE_EXTERNAL_CLOSURE_ATTESTATION",
    }


def _closure_payload(row: dict[str, object]) -> dict[str, object]:
    return {"schema_version": "ui_semantic_validator_handoff_closure/v1", "search_root": "fixture", "degraded": [], "closure_gates": [row]}


def test_continuity_reports_external_closure_wait() -> None:
    with patch(
        "strategy_validator.application.ui_semantic_validator_handoff_continuity.build_ui_semantic_validator_handoff_closure_payload",
        return_value=_closure_payload(_closure_row()),
    ):
        payload = build_ui_semantic_validator_handoff_continuity_payload()

    assert payload["schema_version"] == "ui_semantic_validator_handoff_continuity/v1"
    assert payload["read_plane_only"] is True
    assert payload["execution_authority"] == "none_read_plane"
    assert payload["summary"]["open_action_count"] == 1
    row = payload["continuity_rows"][0]
    assert row["terminal_status"] == "AWAITING_EXTERNAL_CLOSURE_ATTESTATION"
    assert row["external_artifact_required"] is True
    assert row["authority"]["validator_submission_allowed"] is False
    assert row["current_stage"] == "closure"


def test_continuity_reports_closed_chain() -> None:
    with patch(
        "strategy_validator.application.ui_semantic_validator_handoff_continuity.build_ui_semantic_validator_handoff_closure_payload",
        return_value=_closure_payload(_closure_row(status="CLOSURE_ATTESTATION_RECORDED", recorded=True)),
    ):
        payload = build_ui_semantic_validator_handoff_continuity_payload(open_action=False)

    assert payload["summary"]["closed_chain_count"] == 1
    row = payload["continuity_rows"][0]
    assert row["terminal_status"] == "CLOSED_WITH_RECORDED_CLOSURE_ATTESTATION"
    assert row["open_action"] is False
    assert row["authority"]["execution_allowed"] is False
    assert row["ready_stage_count"] == row["stage_count_expected"]
