from __future__ import annotations

from unittest.mock import patch

from strategy_validator.application.ui_semantic_validator_handoff_exceptions import (
    build_ui_semantic_validator_handoff_exceptions_payload,
)


def _runbook_card(
    *,
    action_kind: str = "CREATE_EXTERNAL_CLOSURE_ATTESTATION",
    priority: str = "P1",
    severity: str = "WARN",
    completed: bool = False,
    blocked: bool = False,
    external_artifact_required: bool = True,
) -> dict[str, object]:
    return {
        "runbook_card_id": f"card-{action_kind}",
        "continuity_id": "continuity-1",
        "experiment_id": "EXP-1",
        "chain_id": "chain-1",
        "chain_digest": "chain-digest",
        "closure_gate_id": "closure-1",
        "archive_gate_id": "archive-1",
        "decision_id": "decision-1",
        "terminal_status": "AWAITING_EXTERNAL_CLOSURE_ATTESTATION" if not blocked else "BLOCKED_INVALID_CLOSURE_ATTESTATION",
        "closure_status": "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION" if not blocked else "CLOSURE_ATTESTATION_DIGEST_MISMATCH",
        "current_stage": "closure",
        "action_kind": action_kind,
        "priority": priority,
        "severity": severity,
        "completed": completed,
        "blocked": blocked,
        "external_artifact_required": external_artifact_required,
        "next_external_artifact_kind": "semantic_validator_handoff_closure_attestation" if external_artifact_required else None,
        "next_external_schema_version": "semantic_validator_handoff_closure_attestation/v1" if external_artifact_required else None,
        "required_template_fields": ["closed_by", "closure_statement"] if external_artifact_required else [],
        "first_issue_code": "EXTERNAL_CLOSURE_ATTESTATION_MISSING" if not blocked else "CLOSURE_PACKET_DIGEST_MISMATCH",
        "issue_codes": ["EXTERNAL_CLOSURE_ATTESTATION_MISSING"] if not blocked else ["CLOSURE_PACKET_DIGEST_MISMATCH"],
        "issue_count": 1,
        "closure_packet_digest": "closure-digest",
        "operator_action": action_kind.replace("_", " ").capitalize(),
        "checklist": ["Inspect row", "Repair externally"],
        "source_route": "/ui/semantic-validator-handoff/runbook",
        "next_route": "/ui/semantic-validator-handoff/closure",
        "continuity_route": "/ui/semantic-validator-handoff/continuity",
        "authority": {"execution_allowed": False, "validator_submission_allowed": False},
        "summary_line": "EXP-1 · runbook · execute=false",
    }


def _runbook_payload(*cards: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "ui_semantic_validator_handoff_runbook/v1",
        "search_root": "fixture",
        "degraded": [],
        "summary": {
            "runbook_card_count_total": len(cards),
            "open_runbook_card_count": sum(1 for card in cards if not card.get("completed")),
        },
        "runbook_cards": list(cards),
    }


def test_exceptions_queue_promotes_external_artifact_wait() -> None:
    with patch(
        "strategy_validator.application.ui_semantic_validator_handoff_exceptions.build_ui_semantic_validator_handoff_runbook_payload",
        return_value=_runbook_payload(_runbook_card()),
    ):
        payload = build_ui_semantic_validator_handoff_exceptions_payload()

    assert payload["schema_version"] == "ui_semantic_validator_handoff_exceptions/v1"
    assert payload["read_plane_only"] is True
    assert payload["execution_authority"] == "none_read_plane"
    assert payload["summary"]["open_exception_count"] == 1
    row = payload["exception_rows"][0]
    assert row["exception_state"] == "AWAITING_EXTERNAL_ARTIFACT"
    assert row["exception_kind"] == "EXTERNAL_ARTIFACT_REQUIRED_EXCEPTION"
    assert row["authority"]["validator_submission_allowed"] is False
    assert row["authority"]["execution_allowed"] is False


def test_exceptions_queue_escalates_blocked_integrity_issue() -> None:
    with patch(
        "strategy_validator.application.ui_semantic_validator_handoff_exceptions.build_ui_semantic_validator_handoff_runbook_payload",
        return_value=_runbook_payload(
            _runbook_card(
                action_kind="REPAIR_CLOSURE_ATTESTATION",
                priority="P0",
                severity="BLOCKED",
                blocked=True,
                external_artifact_required=False,
            )
        ),
    ):
        payload = build_ui_semantic_validator_handoff_exceptions_payload(priority=("P0",))

    assert payload["summary"]["blocked_exception_count"] == 1
    row = payload["exception_rows"][0]
    assert row["exception_state"] == "BLOCKED"
    assert row["exception_kind"] == "BLOCKED_INTEGRITY_EXCEPTION"
    assert row["escalation_lane"] == "operator_integrity_repair"
    assert "BLOCKED_SEMANTIC_VALIDATOR_HANDOFF_EXCEPTION_PRESENT" in payload["degraded"]


def test_exceptions_queue_excludes_resolved_by_default() -> None:
    with patch(
        "strategy_validator.application.ui_semantic_validator_handoff_exceptions.build_ui_semantic_validator_handoff_runbook_payload",
        return_value=_runbook_payload(
            _runbook_card(completed=True, severity="INFO", external_artifact_required=False),
            _runbook_card(),
        ),
    ):
        payload = build_ui_semantic_validator_handoff_exceptions_payload()

    assert payload["summary"]["exception_count_total"] == 2
    assert payload["summary"]["exception_count_returned"] == 1
    assert payload["summary"]["resolved_exception_excluded_count"] == 1


def test_exceptions_queue_can_include_resolved_audit_notes() -> None:
    with patch(
        "strategy_validator.application.ui_semantic_validator_handoff_exceptions.build_ui_semantic_validator_handoff_runbook_payload",
        return_value=_runbook_payload(_runbook_card(completed=True, severity="INFO", external_artifact_required=False)),
    ):
        payload = build_ui_semantic_validator_handoff_exceptions_payload(include_resolved=True)

    row = payload["exception_rows"][0]
    assert row["exception_state"] == "RESOLVED_AUDIT_RETENTION"
    assert row["exception_kind"] == "AUDIT_RETENTION_NOTE"
    assert row["completed"] is True
