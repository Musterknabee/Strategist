from __future__ import annotations

from pathlib import Path

from strategy_validator.cli.ledger_ops import verify_ledger, verify_operator_action_journal
from strategy_validator.ledger.operator_actions import (
    read_operator_action_events_readonly,
    verify_operator_action_event_chain_readonly,
)
from strategy_validator.projections.operator_action_event_index import build_operator_action_event_projection_index


def test_operator_action_readonly_helpers_do_not_create_missing_ledger(monkeypatch, tmp_path: Path) -> None:
    database_path = tmp_path / "missing" / "ledger.sqlite3"
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(database_path))

    assert read_operator_action_events_readonly() == ()
    report = verify_operator_action_event_chain_readonly()
    index = build_operator_action_event_projection_index(database_path=database_path, readonly=True)

    assert report.ok is False
    assert report.event_count == 0
    assert "operator_action_events" in report.issues[0]
    assert index.event_count == 0
    assert index.ok is False
    assert "operator_action_events" in index.chain_issues[0]
    assert not database_path.exists()
    assert not database_path.parent.exists()


def test_ledger_ops_diagnostics_do_not_bootstrap_missing_ledger(tmp_path: Path) -> None:
    database_path = tmp_path / "missing" / "ledger.sqlite3"

    ledger_payload = verify_ledger(database_path=str(database_path))
    operator_payload = verify_operator_action_journal(database_path=str(database_path))

    assert ledger_payload["ok"] is False
    assert ledger_payload["database_exists"] is False
    assert ledger_payload["hash_chain"] is None
    assert operator_payload["ok"] is False
    assert operator_payload["database_exists"] is False
    assert operator_payload["issues"] == ["ledger database does not exist"]
    assert not database_path.exists()
    assert not database_path.parent.exists()


def test_operator_action_readonly_verify_fails_existing_database_without_journal(monkeypatch, tmp_path: Path) -> None:
    import sqlite3

    database_path = tmp_path / "ledger.sqlite3"
    sqlite3.connect(database_path).close()
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(database_path))

    report = verify_operator_action_event_chain_readonly()

    assert report.ok is False
    assert report.event_count == 0
    assert "operator_action_events" in report.issues[0]
