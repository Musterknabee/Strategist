from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.evidence_chain_projection import build_ui_evidence_chain_payload
from strategy_validator.ledger._append_only import LedgerEvent, append_event
from strategy_validator.ledger.operator_actions import append_operator_action_event


def _canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _event_hash(event: LedgerEvent) -> str:
    return hashlib.sha256(
        _canonical_json(
            {
                "experiment_id": event.experiment_id,
                "sequence_number": event.sequence_number,
                "event_type": event.event_type,
                "promotion_state": event.promotion_state,
                "event_payload_json": event.event_payload_json,
                "manifest_hash": event.manifest_hash,
                "previous_event_hash": event.previous_event_hash,
                "created_at_utc": event.created_at_utc.isoformat(),
                "writer_identity": event.writer_identity,
            }
        ).encode("utf-8")
    ).hexdigest()


def _append_decision_event(*, experiment_id: str, sequence_number: int, state: str, previous_event_hash: str | None) -> LedgerEvent:
    created_at = datetime(2026, 5, 3, 8, sequence_number, tzinfo=timezone.utc)
    payload_json = _canonical_json({"experiment_id": experiment_id, "state": state, "evidence_bundle": {}})
    event = LedgerEvent(
        experiment_id=experiment_id,
        sequence_number=sequence_number,
        event_type="adjudication.state_transition",
        promotion_state=state,
        event_payload_json=payload_json,
        manifest_hash=hashlib.sha256(payload_json.encode("utf-8")).hexdigest(),
        event_hash="pending",
        previous_event_hash=previous_event_hash,
        created_at_utc=created_at,
        writer_identity="test.orchestrator",
    )
    event = LedgerEvent(**{**event.__dict__, "event_hash": _event_hash(event)})
    append_event(event)
    return event


def test_evidence_chain_projection_filters_timeline_and_counts(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(tmp_path / "ledger.sqlite3"))

    first = _append_decision_event(experiment_id="exp-alpha", sequence_number=1, state="INVALID", previous_event_hash=None)
    _append_decision_event(experiment_id="exp-alpha", sequence_number=2, state="APPROVED", previous_event_hash=first.event_hash)
    append_operator_action_event(
        action="claim-item",
        operator_id="jp",
        target={"work_item_key": "wk-claim", "review_target": "candidate-a", "idempotency_key": "claim-1"},
        summary_line="claimed candidate-a",
        created_at_utc=datetime(2026, 5, 3, 8, 3, tzinfo=timezone.utc),
    )
    append_operator_action_event(
        action="renew-lease",
        operator_id="ops",
        target={"work_item_key": "wk-renew", "review_target": "candidate-b", "idempotency_key": "renew-1"},
        summary_line="renewed candidate-b",
        created_at_utc=datetime(2026, 5, 3, 8, 4, tzinfo=timezone.utc),
    )

    payload = build_ui_evidence_chain_payload(
        readonly=True,
        stream_family=("operator_action_journal",),
        actor_contains="jp",
        aggregate_contains="wk-claim",
        event_type_contains="claim",
        chained=True,
        limit=10,
    )

    assert payload["schema_version"] == "ui_evidence_chain/v1"
    assert payload["filters"]["stream_family"] == ["operator_action_journal"]
    assert payload["summary"]["event_count_total"] == 4
    assert payload["summary"]["filtered_event_count"] == 1
    assert payload["summary"]["returned_event_count"] == 1
    assert payload["summary"]["stream_family_counts"] == {"operator_action_journal": 1}
    assert payload["summary"]["status_counts"] == {"accepted": 1}
    assert payload["summary"]["unchained_filtered_event_count"] == 0
    assert payload["timeline"]["filtered_count"] == 1
    entry = payload["timeline"]["entries"][0]
    assert entry["actor_id"] == "jp"
    assert entry["aggregate_id"] == "wk-claim"
    assert entry["event_type"] == "claim-item"
    assert entry["summary_line"] == "claimed candidate-a"


def test_evidence_chain_projection_filters_by_status_and_limit(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(tmp_path / "ledger.sqlite3"))

    first = _append_decision_event(experiment_id="exp-beta", sequence_number=1, state="INVALID", previous_event_hash=None)
    _append_decision_event(experiment_id="exp-beta", sequence_number=2, state="APPROVED", previous_event_hash=first.event_hash)
    append_operator_action_event(
        action="claim-item",
        operator_id="jp",
        target={"work_item_key": "wk-claim", "idempotency_key": "claim-2"},
        accepted=False,
        status="rejected",
        summary_line="rejected duplicate claim",
        created_at_utc=datetime(2026, 5, 3, 8, 5, tzinfo=timezone.utc),
    )

    payload = build_ui_evidence_chain_payload(readonly=True, status=("APPROVED", "rejected"), limit=1)

    assert payload["summary"]["filtered_event_count"] == 2
    assert payload["summary"]["returned_event_count"] == 1
    assert payload["timeline"]["limit"] == 1
    assert payload["timeline"]["entries"][0]["status"] == "rejected"
    assert payload["guardrails"]
