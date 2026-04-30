from __future__ import annotations

import json
from datetime import UTC, datetime

from strategy_validator.contracts.control_plane_event_envelope import build_control_plane_event_envelope
from strategy_validator.ledger.operator_actions import (
    append_control_plane_event_envelope,
    read_operator_action_events,
    verify_operator_action_event_chain,
)


def test_control_plane_event_envelope_can_be_journaled(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(tmp_path / "ledger.sqlite3"))
    envelope = build_control_plane_event_envelope(
        event_type="oracle.operator_decision_execution.materialized",
        producer="tests.control_plane",
        payload={"schema_version": "test/v1", "value": 1},
        occurred_at_utc=datetime(2026, 1, 1, tzinfo=UTC),
        actor_id="operator-a",
        target={"board_label": "default"},
        idempotency_key="event-bridge-key",
    )

    first = append_control_plane_event_envelope(envelope)
    second = append_control_plane_event_envelope(envelope)

    assert second.action_event_id == first.action_event_id
    assert first.action == "control-plane-event"
    assert first.operator_id == "operator-a"
    target = json.loads(first.target_payload_json)
    assert target["event_id"] == envelope.event_id
    assert target["payload_digest"] == envelope.payload_digest
    events = read_operator_action_events(idempotency_key="event-bridge-key")
    assert len(events) == 1
    assert verify_operator_action_event_chain().ok is True
