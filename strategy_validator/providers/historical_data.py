"""Optional historical market data fetchers (no startup side effects)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from strategy_validator.contracts.provider_historical_data import (
    HistoricalBar,
    HistoricalDataProviderResult,
    HistoricalDataRequest,
    ProviderHistoricalPitStatus,
    ProviderIngestionRuntimeStatus,
)

FetchTransport = Callable[[str, dict[str, str]], tuple[int, bytes]]


def _default_transport(url: str, headers: dict[str, str]) -> tuple[int, bytes]:
    req = Request(url, headers=headers, method="GET")
    with urlopen(req, timeout=30) as resp:  # noqa: S310 - controlled research CLI
        code = int(getattr(resp, "status", 200) or 200)
        return code, resp.read()


def _parse_iso_date(s: str) -> datetime:
    raw = s.strip()
    if "T" in raw:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
    else:
        dt = datetime.fromisoformat(raw + "T00:00:00+00:00")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _window_ok(ts: datetime, req: HistoricalDataRequest) -> bool:
    return req.start_utc <= ts <= req.end_utc


def fetch_tiingo_daily(
    req: HistoricalDataRequest,
    *,
    token: str,
    transport: FetchTransport | None = None,
) -> HistoricalDataProviderResult:
    transport = transport or _default_transport
    now = datetime.now(timezone.utc)
    if not token.strip():
        return HistoricalDataProviderResult(
            provider_id="tiingo",
            provider_status=ProviderIngestionRuntimeStatus.PENDING_KEY,
            pit_status=ProviderHistoricalPitStatus.BLOCKED_PROVIDER_UNAVAILABLE,
            retrieved_at_utc=now,
            warnings=[],
            blockers=["TIINGO_TOKEN_MISSING"],
        )
    sym = req.symbol.strip().upper()
    start = req.start_utc.date().isoformat()
    end = req.end_utc.date().isoformat()
    url = f"https://api.tiingo.com/tiingo/daily/{sym}/prices?startDate={start}&endDate={end}&token={token}"
    try:
        code, body = transport(url, {"Content-Type": "application/json"})
    except (OSError, HTTPError, URLError) as exc:
        return HistoricalDataProviderResult(
            provider_id="tiingo",
            provider_status=ProviderIngestionRuntimeStatus.UNAVAILABLE,
            pit_status=ProviderHistoricalPitStatus.BLOCKED_PROVIDER_UNAVAILABLE,
            retrieved_at_utc=now,
            warnings=[f"TRANSPORT_ERROR:{exc.__class__.__name__}"],
            blockers=[],
        )
    if code != 200:
        return HistoricalDataProviderResult(
            provider_id="tiingo",
            provider_status=ProviderIngestionRuntimeStatus.DEGRADED,
            pit_status=ProviderHistoricalPitStatus.BLOCKED_PROVIDER_UNAVAILABLE,
            retrieved_at_utc=now,
            warnings=[f"HTTP_{code}"],
            blockers=[],
        )
    try:
        rows = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return HistoricalDataProviderResult(
            provider_id="tiingo",
            provider_status=ProviderIngestionRuntimeStatus.BLOCKED,
            pit_status=ProviderHistoricalPitStatus.BLOCKED_PROVIDER_UNAVAILABLE,
            retrieved_at_utc=now,
            blockers=["TIINGO_JSON_PARSE"],
        )
    if not isinstance(rows, list):
        return HistoricalDataProviderResult(
            provider_id="tiingo",
            provider_status=ProviderIngestionRuntimeStatus.BLOCKED,
            pit_status=ProviderHistoricalPitStatus.BLOCKED_PROVIDER_UNAVAILABLE,
            retrieved_at_utc=now,
            blockers=["TIINGO_UNEXPECTED_SHAPE"],
        )
    bars: list[HistoricalBar] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        ds = str(row.get("date", "")).strip()
        if not ds:
            continue
        ts = _parse_iso_date(ds)
        if not _window_ok(ts, req):
            continue
        try:
            o = float(row.get("open", 0) or 0)
            h = float(row.get("high", 0) or 0)
            l = float(row.get("low", 0) or 0)
            c = float(row.get("close", 0) or 0)
            v = float(row.get("volume", 0) or 0)
        except (TypeError, ValueError):
            continue
        bars.append(
            HistoricalBar(
                timestamp_utc=ts,
                open=o,
                high=h,
                low=l,
                close=c,
                volume=v,
            )
        )
    bars.sort(key=lambda b: b.timestamp_utc)
    return HistoricalDataProviderResult(
        provider_id="tiingo",
        provider_status=ProviderIngestionRuntimeStatus.OK,
        pit_status=ProviderHistoricalPitStatus.MISSING_RELEASE_TIMESTAMPS,
        bars=bars,
        retrieved_at_utc=now,
        published_at_utc=None,
        warnings=["PIT_BEST_EFFORT_PROVIDER_DAILY_NO_OFFICIAL_RELEASE_TS"],
        blockers=[],
    )


def fetch_alpha_vantage_daily(
    req: HistoricalDataRequest,
    *,
    api_key: str,
    transport: FetchTransport | None = None,
) -> HistoricalDataProviderResult:
    transport = transport or _default_transport
    now = datetime.now(timezone.utc)
    if not api_key.strip():
        return HistoricalDataProviderResult(
            provider_id="alpha_vantage",
            provider_status=ProviderIngestionRuntimeStatus.PENDING_KEY,
            pit_status=ProviderHistoricalPitStatus.BLOCKED_PROVIDER_UNAVAILABLE,
            retrieved_at_utc=now,
            blockers=["ALPHA_VANTAGE_KEY_MISSING"],
        )
    sym = req.symbol.strip().upper()
    url = (
        "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED"
        f"&symbol={sym}&outputsize=full&apikey={api_key}"
    )
    try:
        code, body = transport(url, {})
    except (OSError, HTTPError, URLError) as exc:
        return HistoricalDataProviderResult(
            provider_id="alpha_vantage",
            provider_status=ProviderIngestionRuntimeStatus.UNAVAILABLE,
            pit_status=ProviderHistoricalPitStatus.BLOCKED_PROVIDER_UNAVAILABLE,
            retrieved_at_utc=now,
            warnings=[f"TRANSPORT_ERROR:{exc.__class__.__name__}"],
        )
    if code != 200:
        return HistoricalDataProviderResult(
            provider_id="alpha_vantage",
            provider_status=ProviderIngestionRuntimeStatus.DEGRADED,
            pit_status=ProviderHistoricalPitStatus.BLOCKED_PROVIDER_UNAVAILABLE,
            retrieved_at_utc=now,
            warnings=[f"HTTP_{code}"],
        )
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return HistoricalDataProviderResult(
            provider_id="alpha_vantage",
            provider_status=ProviderIngestionRuntimeStatus.BLOCKED,
            pit_status=ProviderHistoricalPitStatus.BLOCKED_PROVIDER_UNAVAILABLE,
            retrieved_at_utc=now,
            blockers=["ALPHA_VANTAGE_JSON_PARSE"],
        )
    if "Note" in payload or "Information" in payload:
        return HistoricalDataProviderResult(
            provider_id="alpha_vantage",
            provider_status=ProviderIngestionRuntimeStatus.DEGRADED,
            pit_status=ProviderHistoricalPitStatus.BLOCKED_PROVIDER_UNAVAILABLE,
            retrieved_at_utc=now,
            warnings=["ALPHA_VANTAGE_RATE_LIMIT_OR_INFO_MESSAGE"],
        )
    series = payload.get("Time Series (Daily)")
    if not isinstance(series, dict):
        return HistoricalDataProviderResult(
            provider_id="alpha_vantage",
            provider_status=ProviderIngestionRuntimeStatus.BLOCKED,
            pit_status=ProviderHistoricalPitStatus.BLOCKED_PROVIDER_UNAVAILABLE,
            retrieved_at_utc=now,
            blockers=["ALPHA_VANTAGE_NO_TIME_SERIES"],
        )
    bars: list[HistoricalBar] = []
    for day, row in series.items():
        if not isinstance(row, dict):
            continue
        ts = _parse_iso_date(str(day))
        if not _window_ok(ts, req):
            continue
        try:
            o = float(row.get("1. open", 0) or 0)
            h = float(row.get("2. high", 0) or 0)
            l = float(row.get("3. low", 0) or 0)
            c = float(row.get("4. close", 0) or 0)
            v = float(row.get("6. volume", 0) or 0)
        except (TypeError, ValueError):
            continue
        bars.append(
            HistoricalBar(timestamp_utc=ts, open=o, high=h, low=l, close=c, volume=v)
        )
    bars.sort(key=lambda b: b.timestamp_utc)
    return HistoricalDataProviderResult(
        provider_id="alpha_vantage",
        provider_status=ProviderIngestionRuntimeStatus.OK,
        pit_status=ProviderHistoricalPitStatus.MISSING_RELEASE_TIMESTAMPS,
        bars=bars,
        retrieved_at_utc=now,
        warnings=["PIT_BEST_EFFORT_ALPHA_VANTAGE_DAILY"],
        blockers=[],
    )


def fetch_provider_bars(
    req: HistoricalDataRequest,
    env: dict[str, str],
    *,
    transport: FetchTransport | None = None,
) -> HistoricalDataProviderResult:
    pid = req.provider_id.strip().lower()
    if pid in ("tiingo",):
        return fetch_tiingo_daily(req, token=env.get("TIINGO_API_KEY", ""), transport=transport)
    if pid in ("alpha_vantage", "alphavantage"):
        return fetch_alpha_vantage_daily(
            req, api_key=env.get("ALPHA_VANTAGE_API_KEY", ""), transport=transport
        )
    now = datetime.now(timezone.utc)
    return HistoricalDataProviderResult(
        provider_id=pid,
        provider_status=ProviderIngestionRuntimeStatus.UNAVAILABLE,
        pit_status=ProviderHistoricalPitStatus.BLOCKED_PROVIDER_UNAVAILABLE,
        retrieved_at_utc=now,
        blockers=[f"UNKNOWN_PROVIDER:{pid}"],
    )


__all__ = [
    "fetch_alpha_vantage_daily",
    "fetch_provider_bars",
    "fetch_tiingo_daily",
]
