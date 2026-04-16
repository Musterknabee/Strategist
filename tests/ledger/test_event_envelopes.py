from __future__ import annotations

from datetime import datetime

from strategy_validator.ledger._append_only import LedgerEvent
from strategy_validator.ledger.reader import iter_event_envelopes


def test_iter_event_envelopes_uses_ledger_events(monkeypatch) -> None:
    event = LedgerEvent(
        experiment_id='exp-1',
        sequence_number=1,
        event_type='manifest.recorded',
        promotion_state='INVALID',
        event_payload_json='{"experiment_id": "exp-1", "state": "INVALID"}',
        manifest_hash='m1',
        event_hash='h1',
        previous_event_hash=None,
        created_at_utc=datetime(2026, 1, 1),
        writer_identity='orchestrator',
    )
    monkeypatch.setattr('strategy_validator.ledger.reader.read_events', lambda experiment_id=None: (event,))
    envelopes = iter_event_envelopes('exp-1')
    assert len(envelopes) == 1
    assert envelopes[0].aggregate_id == 'exp-1'
    assert envelopes[0].payload['state'] == 'INVALID'
