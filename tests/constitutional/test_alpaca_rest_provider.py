from __future__ import annotations

from datetime import datetime, timezone

import pytest

from strategy_validator.validator.providers.alpaca_rest_provider import AlpacaRestMarketDataProvider


@pytest.mark.constitutional
def test_alpaca_borrow_disabled_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    p = AlpacaRestMarketDataProvider(
        "alpaca_test",
        enable_borrow_from_trading_api=False,
    )
    monkeypatch.setenv("ALPACA_KID", "k")
    monkeypatch.setenv("ALPACA_SEC", "s")
    ts = datetime(2026, 4, 12, tzinfo=timezone.utc)
    assert p.provide_borrow("AAPL", ts) is None


@pytest.mark.constitutional
@pytest.mark.constitutional
def test_alpaca_raises_on_missing_quotes(monkeypatch: pytest.MonkeyPatch) -> None:
    p = AlpacaRestMarketDataProvider(
        "alpaca_test",
        api_key_id_env="ALPACA_KID",
        api_secret_key_env="ALPACA_SEC",
    )
    monkeypatch.setenv("ALPACA_KID", "kid")
    monkeypatch.setenv("ALPACA_SEC", "sec")
    monkeypatch.setattr(p, "_snapshot", lambda _sym: {"latestQuote": {}, "prevDailyBar": {"v": 1e6, "vw": 100.0}})
    ts = datetime(2026, 4, 12, tzinfo=timezone.utc)
    with pytest.raises(RuntimeError, match="ALPACA_LIQUIDITY_MISSING_QUOTES"):
        p.provide_liquidity("AAPL", ts)


@pytest.mark.constitutional
def test_alpaca_maps_snapshot_to_live_liquidity(monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = {
        "symbol": "AAPL",
        "latestQuote": {"bp": 100.0, "ap": 100.2, "t": "2026-04-12T15:00:00Z"},
        "latestTrade": {"p": 100.1, "t": "2026-04-12T15:00:01Z"},
        "prevDailyBar": {"v": 1_000_000, "vw": 99.5, "c": 100.0},
    }
    p = AlpacaRestMarketDataProvider(
        "alpaca_test",
        api_key_id_env="ALPACA_KID",
        api_secret_key_env="ALPACA_SEC",
    )
    monkeypatch.setenv("ALPACA_KID", "kid")
    monkeypatch.setenv("ALPACA_SEC", "sec")
    monkeypatch.setattr(p, "_snapshot", lambda _sym: fixture)
    ts = datetime(2026, 4, 12, tzinfo=timezone.utc)
    liq = p.provide_liquidity("AAPL", ts)
    assert liq is not None
    assert liq.source_mode == "LIVE"
    assert liq.spread_bps > 0
    assert liq.adv_notional > 0
    assert p.provide_borrow("AAPL", ts) is None


@pytest.mark.constitutional
def test_alpaca_borrow_etb_from_trading_asset(monkeypatch: pytest.MonkeyPatch) -> None:
    p = AlpacaRestMarketDataProvider(
        "alpaca_borrow",
        api_key_id_env="ALPACA_KID",
        api_secret_key_env="ALPACA_SEC",
        enable_borrow_from_trading_api=True,
        trading_base_url="https://paper-api.alpaca.markets",
        etb_borrow_cost_bps=18.0,
        htb_borrow_cost_bps=400.0,
    )
    monkeypatch.setenv("ALPACA_KID", "kid")
    monkeypatch.setenv("ALPACA_SEC", "sec")
    monkeypatch.setattr(
        p,
        "_trading_asset",
        lambda _s: {"symbol": "AAPL", "shortable": True, "easy_to_borrow": True},
    )
    ts = datetime(2026, 4, 12, tzinfo=timezone.utc)
    brw = p.provide_borrow("AAPL", ts)
    assert brw is not None
    assert brw.source_mode == "LIVE"
    assert brw.borrow_available is True
    assert brw.locate_required is False
    assert brw.borrow_cost_bps == 18.0


@pytest.mark.constitutional
def test_alpaca_borrow_htb_sets_locate_and_higher_cost(monkeypatch: pytest.MonkeyPatch) -> None:
    p = AlpacaRestMarketDataProvider(
        "alpaca_borrow",
        api_key_id_env="ALPACA_KID",
        api_secret_key_env="ALPACA_SEC",
        enable_borrow_from_trading_api=True,
        etb_borrow_cost_bps=15.0,
        htb_borrow_cost_bps=275.0,
    )
    monkeypatch.setenv("ALPACA_KID", "kid")
    monkeypatch.setenv("ALPACA_SEC", "sec")
    monkeypatch.setattr(
        p,
        "_trading_asset",
        lambda _s: {"symbol": "GME", "shortable": True, "easy_to_borrow": False},
    )
    ts = datetime(2026, 4, 12, tzinfo=timezone.utc)
    brw = p.provide_borrow("GME", ts)
    assert brw is not None
    assert brw.borrow_available is True
    assert brw.locate_required is True
    assert brw.borrow_cost_bps == 275.0


@pytest.mark.constitutional
def test_alpaca_borrow_not_shortable(monkeypatch: pytest.MonkeyPatch) -> None:
    p = AlpacaRestMarketDataProvider(
        "alpaca_borrow",
        api_key_id_env="ALPACA_KID",
        api_secret_key_env="ALPACA_SEC",
        enable_borrow_from_trading_api=True,
    )
    monkeypatch.setenv("ALPACA_KID", "kid")
    monkeypatch.setenv("ALPACA_SEC", "sec")
    monkeypatch.setattr(
        p,
        "_trading_asset",
        lambda _s: {"symbol": "XYZ", "shortable": False, "easy_to_borrow": False},
    )
    ts = datetime(2026, 4, 12, tzinfo=timezone.utc)
    brw = p.provide_borrow("XYZ", ts)
    assert brw is not None
    assert brw.borrow_available is False
    assert brw.borrow_cost_bps == 0.0


@pytest.mark.constitutional
def test_alpaca_borrow_unknown_symbol_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    p = AlpacaRestMarketDataProvider(
        "alpaca_borrow",
        api_key_id_env="ALPACA_KID",
        api_secret_key_env="ALPACA_SEC",
        enable_borrow_from_trading_api=True,
    )
    monkeypatch.setenv("ALPACA_KID", "kid")
    monkeypatch.setenv("ALPACA_SEC", "sec")
    monkeypatch.setattr(p, "_trading_asset", lambda _s: None)
    ts = datetime(2026, 4, 12, tzinfo=timezone.utc)
    assert p.provide_borrow("NOPE", ts) is None
