from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from strategy_validator.contracts.control_plane_event_envelope import ControlPlaneEventEnvelope, verify_control_plane_event_envelope
from strategy_validator.control_plane.operator_decision_execution import (
    build_operator_decision_execution_request,
    materialize_operator_decision_execution,
)
from strategy_validator.control_plane.operator_transition_policy import (
    OracleOperatorTransitionPolicy,
    OracleOperatorTransitionPolicyItem,
)
from strategy_validator.control_plane.operator_workboard_actions import (
    OracleOperatorWorkboardActionContract,
    OracleOperatorWorkboardActionContractItem,
)


def _action_contract() -> OracleOperatorWorkboardActionContract:
    item = OracleOperatorWorkboardActionContractItem(
        work_item_key="work-1",
        action_contract_key="work-1:board",
        queue_key="queue-1",
        board_label="board",
        review_target="strategy:demo",
        priority_band="STANDARD_PRIORITY",
        action_name="claim",
        action_state="ACTION_EXECUTABLE",
        actor_lane="operator",
        dispatch_posture="DISPATCH_ALLOWED",
        claim_operability="CLAIM_OPERABLE",
        permitted_now=True,
        rationale="demo item is executable",
    )
    return OracleOperatorWorkboardActionContract(
        board_label="board",
        queue_key="queue-1",
        review_target="strategy:demo",
        priority_band="STANDARD_PRIORITY",
        contract_count=1,
        summary_line="demo",
        items=(item,),
    )


def _transition_policy() -> OracleOperatorTransitionPolicy:
    item = OracleOperatorTransitionPolicyItem(
        action_contract_key="work-1:board",
        work_item_key="work-1",
        policy_key="policy:work-1:board",
        current_action_state="ACTION_EXECUTABLE",
        policy_decision="ALLOW_EXECUTION",
        default_transition="EXECUTED",
        allowed_transitions=("ACKNOWLEDGED", "EXECUTED"),
        rationale="demo transition is allowed",
    )
    return OracleOperatorTransitionPolicy(
        schema_version="oracle_operator_transition_policy/v1",
        board_label="board",
        queue_key="queue-1",
        review_target="strategy:demo",
        priority_band="STANDARD_PRIORITY",
        policy_count=1,
        summary_line="demo",
        items=(item,),
    )


def test_operator_decision_execution_writes_event_backed_sidecar(tmp_path) -> None:
    request = build_operator_decision_execution_request(
        execution_root=tmp_path,
        board_label="board",
        actor_label="operator-1",
        emitted_at_utc=datetime(2026, 1, 1, tzinfo=UTC),
    )

    report = materialize_operator_decision_execution(
        request,
        transition_policy=_transition_policy(),
        action_contract=_action_contract(),
    )

    summary_path = tmp_path / "ORACLE_OPERATOR_DECISION_EXECUTION.json"
    markdown_path = tmp_path / "ORACLE_OPERATOR_DECISION_EXECUTION.md"
    event_path = tmp_path / "ORACLE_OPERATOR_DECISION_EXECUTION.event.json"

    assert report.execution_count == 1
    assert summary_path.exists()
    assert markdown_path.exists()
    assert event_path.exists()

    event_payload = json.loads(event_path.read_text(encoding="utf-8"))
    assert event_payload["event_type"] == "oracle.operator_decision_execution.materialized"
    assert event_payload["producer"] == "strategy_validator.control_plane.operator_decision_execution"
    assert event_payload["actor_id"] == "operator-1"
    assert event_payload["payload"] == json.loads(summary_path.read_text(encoding="utf-8"))
    assert event_payload["evidence_refs"] == [str(summary_path), str(markdown_path)]

    ok, issues = verify_control_plane_event_envelope(ControlPlaneEventEnvelope(**event_payload))
    assert ok is True
    assert issues == ()


def test_operator_decision_execution_uses_event_backed_writer() -> None:
    source = (Path(__file__).resolve().parents[2] / "strategy_validator/control_plane/operator_decision_execution.py").read_text(
        encoding="utf-8"
    )

    assert "write_event_backed_json_markdown_artifacts(" in source
    assert "event_output_path.write_text" not in source
    assert "event_envelope_for_materialized_payload" not in source

from strategy_validator.ledger.operator_actions import read_operator_action_events, verify_operator_action_event_chain


def test_operator_decision_execution_can_record_event_sidecar_to_operator_journal(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(tmp_path / "ledger.sqlite3"))
    request = build_operator_decision_execution_request(
        execution_root=tmp_path / "artifacts",
        board_label="board",
        actor_label="operator-1",
        emitted_at_utc=datetime(2026, 1, 1, tzinfo=UTC),
        record_event_to_operator_journal=True,
    )

    materialize_operator_decision_execution(
        request,
        transition_policy=_transition_policy(),
        action_contract=_action_contract(),
    )

    event_payload = json.loads((tmp_path / "artifacts" / "ORACLE_OPERATOR_DECISION_EXECUTION.event.json").read_text(encoding="utf-8"))
    journal_events = read_operator_action_events(idempotency_key=event_payload["idempotency_key"])

    assert len(journal_events) == 1
    assert journal_events[0].action == "control-plane-event"
    assert journal_events[0].operator_id == "operator-1"
    assert journal_events[0].target_payload["event_id"] == event_payload["event_id"]
    assert journal_events[0].target_payload["payload_digest"] == event_payload["payload_digest"]
    assert verify_operator_action_event_chain().ok is True
