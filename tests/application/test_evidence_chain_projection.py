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


def _append_decision_event(*, experiment_id: str, sequence_number: int, previous_event_hash: str | None) -> LedgerEvent:
    created_at = datetime(2026, 5, 2, 10, sequence_number, tzinfo=timezone.utc)
    payload_json = _canonical_json({"experiment_id": experiment_id, "state": "INVALID", "evidence_bundle": {}})
    event = LedgerEvent(
        experiment_id=experiment_id,
        sequence_number=sequence_number,
        event_type="adjudication.state_transition",
        promotion_state="INVALID",
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


def test_evidence_chain_projection_combines_decision_and_operator_streams(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(tmp_path / "ledger.sqlite3"))

    first = _append_decision_event(experiment_id="exp-a", sequence_number=1, previous_event_hash=None)
    _append_decision_event(experiment_id="exp-a", sequence_number=2, previous_event_hash=first.event_hash)
    append_operator_action_event(
        action="claim-item",
        operator_id="jp",
        target={"work_item_key": "wk-1", "idempotency_key": "ev-chain-1"},
        summary_line="claimed wk-1",
        created_at_utc=datetime(2026, 5, 2, 10, 3, tzinfo=timezone.utc),
    )

    payload = build_ui_evidence_chain_payload(readonly=True)

    assert payload["schema_version"] == "ui_evidence_chain/v1"
    assert payload["read_plane_only"] is True
    assert payload["promotion_authority"] == "NONE"
    assert payload["execution_authority"] == "NONE"
    assert payload["ok"] is True
    assert payload["summary"]["decision_ledger_event_count"] == 2
    assert payload["summary"]["operator_action_event_count"] == 1
    assert payload["summary"]["event_count_total"] == 3
    streams = payload["streams"]
    assert streams["decision_ledger"]["chain_ok"] is True
    assert streams["operator_action_journal"]["chain_ok"] is True
    timeline = payload["timeline"]["entries"]
    assert {entry["stream_family"] for entry in timeline} == {"decision_ledger", "operator_action_journal"}
    assert all("event_hash" in entry for entry in timeline)


def test_evidence_chain_projection_degrades_without_creating_readonly_storage(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    missing = tmp_path / "missing" / "ledger.sqlite3"
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(missing))

    payload = build_ui_evidence_chain_payload(readonly=True)

    assert payload["schema_version"] == "ui_evidence_chain/v1"
    assert payload["ok"] is False
    assert payload["summary"]["event_count_total"] == 0
    assert payload["degraded"]
    assert not missing.exists()
