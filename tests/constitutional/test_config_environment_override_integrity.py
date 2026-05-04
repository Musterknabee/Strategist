from __future__ import annotations

from strategy_validator.core.config import load_config
from strategy_validator.validator.readiness import perform_readiness_check


def test_invalid_environment_override_is_exposed_on_runtime_policy(monkeypatch) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_LIVE_MARKET_DATA_FRESHNESS_THRESHOLD_SECONDS', 'not-int')

    config = load_config()

    assert any('STRATEGY_VALIDATOR_LIVE_MARKET_DATA_FRESHNESS_THRESHOLD_SECONDS' in item for item in config.runtime_policy.invalid_environment_overrides)


def test_invalid_environment_override_blocks_production_readiness(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_MODE', 'PRODUCTION')
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', 'test-token')
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))
    monkeypatch.setenv('STRATEGY_VALIDATOR_LIVE_MARKET_DATA_FRESHNESS_THRESHOLD_SECONDS', 'not-int')

    readiness = perform_readiness_check()

    assert readiness.status == 'BLOCKED'
    assert any(blocker.code == 'INVALID_ENVIRONMENT_OVERRIDE' for blocker in readiness.blockers)
