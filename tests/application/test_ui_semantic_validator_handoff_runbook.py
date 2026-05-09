from __future__ import annotations

from unittest.mock import patch

from strategy_validator.application.ui_semantic_validator_handoff_runbook import (
    build_ui_semantic_validator_handoff_runbook_payload,
)


def _continuity_row(
    *,
    terminal_status: str = "AWAITING_EXTERNAL_CLOSURE_ATTESTATION",
    closure_status: str = "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION",
    open_action: bool = True,
    external_artifact_required: bool = True,
) -> dict[str, object]:
    return {
        "continuity_id": "continuity-1",
        "experiment_id": "EXP-1",
        "terminal_status": terminal_status,
        "current_stage": "closure",
        "severity": "WARN" if open_action else "INFO",
        "trust_banner": "TRUSTED",
        "chain_id": "chain-1",
        "chain_digest": "chain-digest",
        "closure_gate_id": "closure-1",
        "closure_status": closure_status,
        "closure_attestation_recorded": not open_action,
        "closure_attestation_required": True,
        "closure_attestation_id": None if open_action else "att-1",
        "closure_packet_digest": "closure-digest",
        "archive_gate_id": "archive-1",
        "archive_manifest_id": "manifest-1",
        "custody_gate_id": "custody-1",
        "signoff_gate_id": "signoff-1",
        "decision_id": "decision-1",
        "issue_codes": ["EXTERNAL_CLOSURE_ATTESTATION_MISSING"] if open_action else [],
        "issue_count": 1 if open_action else 0,
        "stage_count_expected": 5,
        "stage_count_present": 5,
        "ready_stage_count": 4 if open_action else 5,
        "open_action": open_action,
        "external_artifact_required": external_artifact_required,
        "next_external_artifact_kind": "semantic_validator_handoff_closure_attestation" if external_artifact_required else None,
        "next_external_schema_version": "semantic_validator_handoff_closure_attestation/v1" if external_artifact_required else None,
        "closure_template": {
            "schema_version": "semantic_validator_handoff_closure_attestation/v1",
            "closure_packet_digest": "closure-digest",
            "closed_by": "<REQUIRED_EXTERNALLY>",
            "closure_statement": "<REQUIRED_EXTERNALLY>",
        },
        "recommended_action": "CREATE_EXTERNAL_CLOSURE_ATTESTATION" if open_action else "HANDOFF_CLOSURE_RECORDED_RETAIN_AUDIT_TRAIL",
        "authority": {"execution_allowed": False, "validator_submission_allowed": False},
        "stage_path": [],
        "source_route": "/ui/semantic-validator-handoff/closure",
        "continuity_route": "/ui/semantic-validator-handoff/continuity",
        "summary_line": "EXP-1 · continuity · execute=false",
    }


def _continuity_payload(row: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "ui_semantic_validator_handoff_continuity/v1",
        "search_root": "fixture",
        "degraded": [],
        "summary": {"continuity_count_total": 1, "open_action_count": 1 if row.get("open_action") else 0},
        "continuity_rows": [row],
    }


def test_runbook_converts_external_closure_wait_into_operator_card() -> None:
    with patch(
        "strategy_validator.application.ui_semantic_validator_handoff_runbook.build_ui_semantic_validator_handoff_continuity_payload",
        return_value=_continuity_payload(_continuity_row()),
    ):
        payload = build_ui_semantic_validator_handoff_runbook_payload()

    assert payload["schema_version"] == "ui_semantic_validator_handoff_runbook/v1"
    assert payload["read_plane_only"] is True
    assert payload["execution_authority"] == "none_read_plane"
    assert payload["summary"]["open_runbook_card_count"] == 1
    card = payload["runbook_cards"][0]
    assert card["action_kind"] == "CREATE_EXTERNAL_CLOSURE_ATTESTATION"
    assert card["priority"] == "P1"
    assert card["external_artifact_required"] is True
    assert "closed_by" in card["required_template_fields"]
    assert card["authority"]["validator_submission_allowed"] is False
    assert card["authority"]["execution_allowed"] is False


def test_runbook_retains_closed_chain_as_completed_audit_card() -> None:
    row = _continuity_row(
        terminal_status="CLOSED_WITH_RECORDED_CLOSURE_ATTESTATION",
        closure_status="CLOSURE_ATTESTATION_RECORDED",
        open_action=False,
        external_artifact_required=False,
    )
    with patch(
        "strategy_validator.application.ui_semantic_validator_handoff_runbook.build_ui_semantic_validator_handoff_continuity_payload",
        return_value=_continuity_payload(row),
    ):
        payload = build_ui_semantic_validator_handoff_runbook_payload(completed=True)

    assert payload["summary"]["completed_runbook_card_count"] == 1
    card = payload["runbook_cards"][0]
    assert card["action_kind"] == "RETAIN_AUDIT_TRAIL"
    assert card["completed"] is True
    assert card["priority"] == "P4"
    assert card["authority"]["promotion_allowed"] is False


def test_runbook_escalates_invalid_closure_attestation() -> None:
    row = _continuity_row(
        terminal_status="BLOCKED_INVALID_CLOSURE_ATTESTATION",
        closure_status="CLOSURE_ATTESTATION_DIGEST_MISMATCH",
        open_action=True,
        external_artifact_required=False,
    )
    row["issue_codes"] = ["CLOSURE_PACKET_DIGEST_MISMATCH"]
    with patch(
        "strategy_validator.application.ui_semantic_validator_handoff_runbook.build_ui_semantic_validator_handoff_continuity_payload",
        return_value=_continuity_payload(row),
    ):
        payload = build_ui_semantic_validator_handoff_runbook_payload(priority=("P0",))

    card = payload["runbook_cards"][0]
    assert card["action_kind"] == "REPAIR_CLOSURE_ATTESTATION"
    assert card["priority"] == "P0"
    assert card["blocked"] is True
    assert "BLOCKED_SEMANTIC_VALIDATOR_HANDOFF_RUNBOOK_ACTION_PRESENT" in payload["degraded"]
