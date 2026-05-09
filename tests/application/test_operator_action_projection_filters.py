from __future__ import annotations

from pathlib import Path

from strategy_validator.application.operator_action_projection import build_operator_action_event_index_payload
from strategy_validator.ledger.operator_actions import append_operator_action_event


def test_operator_action_projection_filters_and_counts(monkeypatch, tmp_path: Path) -> None:
    database_path = tmp_path / "ledger.sqlite3"
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(database_path))

    append_operator_action_event(
        action="claim-item",
        operator_id="jp",
        target={"work_item_key": "wk-1", "review_target": "candidate-a", "idempotency_key": "claim-wk-1"},
        accepted=True,
        status="accepted",
        summary_line="Claimed candidate-a for review",
    )
    append_operator_action_event(
        action="renew-lease",
        operator_id="ops",
        target={"work_item_key": "wk-2", "review_target": "candidate-b", "idempotency_key": "renew-wk-2"},
        accepted=True,
        status="accepted",
        summary_line="Renewed candidate-b review lease",
    )
    append_operator_action_event(
        action="claim-item",
        operator_id="jp",
        target={"work_item_key": "wk-3", "review_target": "candidate-c", "idempotency_key": "claim-wk-3"},
        accepted=False,
        status="rejected",
        summary_line="Rejected candidate-c claim",
    )

    payload = build_operator_action_event_index_payload(
        readonly=True,
        operator_id="jp",
        action=("claim-item",),
        accepted=False,
        limit=10,
    )

    assert payload["schema_version"] == "operator_action_event_projection_index/v1"
    assert payload["read_plane_only"] is True
    assert payload["unfiltered_event_count"] == 3
    assert payload["event_count"] == 1
    assert payload["rejected_event_count"] == 1
    assert payload["action_counts"] == {"claim-item": 1}
    assert payload["operator_counts"] == {"jp": 1}
    assert payload["entries"][0]["status"] == "rejected"
    assert payload["entries"][0]["summary_line"] == "Rejected candidate-c claim"
    assert payload["entries"][0]["work_item_key"] == "wk-3"
