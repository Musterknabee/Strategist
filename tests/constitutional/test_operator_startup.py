"""Startup / operator validation CLI tests."""
from __future__ import annotations

import pytest

from strategy_validator.cli.startup_check import main


@pytest.mark.constitutional
def test_startup_check_exits_zero_on_ready_dev(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    db = tmp_path / "ledger.sqlite3"
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(db))
    code = main([])
    assert code == 0


@pytest.mark.constitutional
def test_startup_check_flags_http_connector_misconfig(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    db = tmp_path / "ledger.sqlite3"
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(db))
    monkeypatch.setenv("STRATEGY_VALIDATOR_HTTP_MARKET_DATA_ENABLED", "True")
    monkeypatch.setenv("STRATEGY_VALIDATOR_HTTP_MARKET_DATA_API_KEY_ENV_VAR", "MISSING_SECRET_XYZ")
    code = main([])
    assert code == 1


@pytest.mark.constitutional
def test_startup_check_flags_alpaca_missing_credentials(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    db = tmp_path / "ledger.sqlite3"
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(db))
    monkeypatch.setenv("STRATEGY_VALIDATOR_ALPACA_MARKET_DATA_ENABLED", "True")
    monkeypatch.delenv("APCA_API_KEY_ID", raising=False)
    monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)
    code = main([])
    assert code == 1


@pytest.mark.constitutional
def test_startup_check_flags_insecure_alpaca_trading_url(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    db = tmp_path / "ledger.sqlite3"
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(db))
    monkeypatch.setenv("STRATEGY_VALIDATOR_ALPACA_MARKET_DATA_ENABLED", "True")
    monkeypatch.setenv("STRATEGY_VALIDATOR_ALPACA_ENABLE_BORROW_FROM_TRADING_API", "True")
    monkeypatch.setenv("STRATEGY_VALIDATOR_ALPACA_TRADING_BASE_URL", "http://insecure.example/v1")
    monkeypatch.setenv("APCA_API_KEY_ID", "x")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "y")
    code = main([])
    assert code == 1


@pytest.mark.constitutional
def test_startup_check_json_exit_follows_readiness(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys) -> None:
    db = tmp_path / "ledger.sqlite3"
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(db))
    code = main(["--json"])
    captured = capsys.readouterr().out
    assert '"heartbeat"' in captured or "heartbeat" in captured
    assert code == 0
