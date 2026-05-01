from __future__ import annotations

from strategy_validator.brokers.alpaca_paper import (
    dry_run_paper_order,
    evaluate_alpaca_paper_policy,
)
from strategy_validator.contracts.paper_broker import PaperBrokerOrderIntent, PaperBrokerPolicyStatus


def test_live_mode_blocked() -> None:
    env = {
        "ALPACA_API_KEY": "k",
        "ALPACA_API_SECRET": "s",
        "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
        "ALPACA_TRADING_MODE": "live",
    }
    pol, _, blocks = evaluate_alpaca_paper_policy(env)
    assert pol == PaperBrokerPolicyStatus.BLOCKED_BY_POLICY
    assert blocks


def test_missing_keys_pending() -> None:
    pol, _, blocks = evaluate_alpaca_paper_policy({})
    assert pol == PaperBrokerPolicyStatus.PENDING_KEY


def test_dry_run_no_secrets_in_result() -> None:
    env = {
        "ALPACA_API_KEY": "k",
        "ALPACA_API_SECRET": "s",
        "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
        "ALPACA_TRADING_MODE": "paper",
    }
    intent = PaperBrokerOrderIntent(tracking_id="t1", symbol="SPY", side="buy", qty=1.0)
    res = dry_run_paper_order(intent, env)
    assert res.ok is True
    dumped = res.model_dump_json()
    assert "ALPACA" not in dumped
    assert "secret" not in dumped.lower()
