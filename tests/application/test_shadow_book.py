from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from strategy_validator.application.shadow_book_ops import (
    build_ui_shadow_book_latest_payload,
    create_shadow_book,
    mark_to_market,
    simulate_daily_fills,
)
from strategy_validator.contracts.shadow_book import ShadowBookAllocation, ShadowBookStatus


def test_shadow_book_create_and_simulate_day(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    prices = tmp_path / "prices.json"
    prices.write_text(json.dumps({"prices": {"SPY": 101.0}}), encoding="utf-8")
    book = create_shadow_book(
        book_id="demo-book",
        starting_capital=100_000,
        allocations=[ShadowBookAllocation(strategy_id="momentum-SPY", target_weight=0.25, notional=25_000)],
        repo_root=tmp_path,
    )
    assert book.no_broker_orders is True
    fills = simulate_daily_fills("demo-book", as_of_date=date(2026, 1, 2), price_fixture=prices, repo_root=tmp_path)
    assert len(fills) == 1
    assert fills[0].no_broker_order is True
    snap = mark_to_market("demo-book", as_of_date=date(2026, 1, 2), price_fixture=prices, repo_root=tmp_path)
    assert snap.snapshot_sha256
    payload = build_ui_shadow_book_latest_payload(repo_root=tmp_path)
    assert payload["schema_version"] == "ui_shadow_book/v1"
    assert payload["no_order_controls"] is True
    assert payload["latest"]["book_id"] == "demo-book"
    assert "STRATEGY_VALIDATOR_API_TOKEN" not in str(payload)


def test_shadow_book_drawdown_freezes(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    high = tmp_path / "high.json"
    low = tmp_path / "low.json"
    high.write_text(json.dumps({"prices": {"SPY": 100.0}}), encoding="utf-8")
    low.write_text(json.dumps({"prices": {"SPY": 1.0}}), encoding="utf-8")
    create_shadow_book(
        book_id="risk-book",
        starting_capital=100_000,
        allocations=[ShadowBookAllocation(strategy_id="momentum-SPY", target_weight=1.0, notional=100_000)],
        repo_root=tmp_path,
    )
    simulate_daily_fills("risk-book", as_of_date=date(2026, 1, 2), price_fixture=high, repo_root=tmp_path)
    snap = mark_to_market("risk-book", as_of_date=date(2026, 1, 2), price_fixture=low, repo_root=tmp_path)
    assert snap.status == ShadowBookStatus.FROZEN_BY_RULE
    assert snap.risk_summary is not None
    assert "MAX_DRAWDOWN_EXCEEDED" in snap.risk_summary.blockers
