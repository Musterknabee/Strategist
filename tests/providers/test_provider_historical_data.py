from __future__ import annotations

from datetime import datetime, timezone

from strategy_validator.contracts.provider_historical_data import HistoricalDataRequest, ProviderIngestionRuntimeStatus
from strategy_validator.providers.historical_data import fetch_tiingo_daily


def test_tiingo_missing_key_pending() -> None:
    req = HistoricalDataRequest(
        provider_id="tiingo",
        symbol="SPY",
        timeframe="1d",
        start_utc=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_utc=datetime(2024, 1, 10, tzinfo=timezone.utc),
        as_of_utc=datetime(2024, 2, 1, tzinfo=timezone.utc),
    )
    res = fetch_tiingo_daily(req, token="")
    assert res.provider_status == ProviderIngestionRuntimeStatus.PENDING_KEY


def test_tiingo_mock_transport_writes_bars() -> None:
    sample = b'[{"date":"2024-01-02","open":1,"high":1,"low":1,"close":1,"volume":10}]'

    def transport(url: str, headers: dict[str, str]) -> tuple[int, bytes]:
        assert "token=secret" in url
        return 200, sample

    req = HistoricalDataRequest(
        provider_id="tiingo",
        symbol="SPY",
        timeframe="1d",
        start_utc=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_utc=datetime(2024, 12, 31, tzinfo=timezone.utc),
        as_of_utc=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    res = fetch_tiingo_daily(req, token="secret", transport=transport)
    assert res.provider_status == ProviderIngestionRuntimeStatus.OK
    assert len(res.bars) == 1
    assert "token=" not in str(res.model_dump())
