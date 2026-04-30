from __future__ import annotations

import json
from datetime import UTC, datetime

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
from strategy_validator.projections.control_plane_event_index import (
    build_control_plane_event_projection_index,
    write_control_plane_event_projection_index,
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


def test_control_plane_event_projection_index_matches_sidecar_and_journal(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(tmp_path / "ledger.sqlite3"))
    artifact_root = tmp_path / "artifacts"
    request = build_operator_decision_execution_request(
        execution_root=artifact_root,
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

    index = build_control_plane_event_projection_index(artifact_root)
    assert index.ok is True
    assert index.event_count == 1
    assert index.fully_indexed_count == 1
    assert index.entries[0].status == "MATCHED"
    assert index.entries[0].fully_indexed is True

    output_path = tmp_path / "index.json"
    written = write_control_plane_event_projection_index(
        event_root=artifact_root,
        output_path=output_path,
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert written.ok is True
    assert payload["schema_version"] == "control_plane_event_projection_index/v1"
    assert payload["entries"][0]["fully_indexed"] is True
