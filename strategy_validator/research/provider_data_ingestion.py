"""Persist provider historical bars to local governed snapshots (research only)."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.contracts.provider_historical_data import (
    HistoricalDataRequest,
    ProviderDataIngestionManifest,
    ProviderHistoricalPitStatus,
    ProviderIngestionRuntimeStatus,
)
from strategy_validator.providers.historical_data import fetch_provider_bars
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def _bars_csv_lines(bars: list) -> bytes:
    header = "timestamp_utc,open,high,low,close,volume\n"
    parts = [header]
    for b in bars:
        parts.append(
            f"{b.timestamp_utc.isoformat()},{b.open},{b.high},{b.low},{b.close},{b.volume}\n"
        )
    return "".join(parts).encode("utf-8")


def ingest_provider_bars_to_snapshot(
    req: HistoricalDataRequest,
    env: dict[str, str],
    *,
    output_root: Path,
    transport=None,
) -> ProviderDataIngestionManifest:
    out = output_root.resolve()
    out.mkdir(parents=True, exist_ok=True)
    retrieved = datetime.now(timezone.utc)
    res = fetch_provider_bars(req, env, transport=transport)
    if res.provider_status == ProviderIngestionRuntimeStatus.PENDING_KEY:
        m = ProviderDataIngestionManifest(
            provider_id=req.provider_id,
            symbol=req.symbol,
            timeframe=req.timeframe,
            start_utc=req.start_utc,
            end_utc=req.end_utc,
            as_of_utc=req.as_of_utc,
            retrieved_at_utc=retrieved,
            published_at_utc=None,
            pit_status=ProviderHistoricalPitStatus.BLOCKED_PROVIDER_UNAVAILABLE,
            bars_path="",
            bars_sha256="",
            row_count=0,
            provider_status=ProviderIngestionRuntimeStatus.PENDING_KEY,
            warnings=list(res.warnings),
            blockers=list(res.blockers) or ["PROVIDER_KEY_PENDING"],
        )
        body = m.model_dump(mode="json")
        m = m.model_copy(update={"manifest_sha256": canonical_json_sha256(body)})
        return m

    if res.provider_status != ProviderIngestionRuntimeStatus.OK or not res.bars:
        m = ProviderDataIngestionManifest(
            provider_id=req.provider_id,
            symbol=req.symbol,
            timeframe=req.timeframe,
            start_utc=req.start_utc,
            end_utc=req.end_utc,
            as_of_utc=req.as_of_utc,
            retrieved_at_utc=res.retrieved_at_utc,
            published_at_utc=res.published_at_utc,
            pit_status=res.pit_status,
            bars_path="",
            bars_sha256="",
            row_count=0,
            provider_status=res.provider_status,
            warnings=list(res.warnings),
            blockers=list(res.blockers) or ["NO_BARS_RETURNED"],
        )
        body = m.model_dump(mode="json")
        m = m.model_copy(update={"manifest_sha256": canonical_json_sha256(body)})
        return m

    sub = out / req.provider_id.strip().lower() / req.symbol.strip().upper() / req.timeframe.strip()
    sub.mkdir(parents=True, exist_ok=True)
    fname = (
        f"{req.start_utc.date().isoformat()}_{req.end_utc.date().isoformat()}"
        f"_asof_{req.as_of_utc.strftime('%Y%m%dT%H%M%SZ')}.csv"
    )
    path = sub / fname
    raw = _bars_csv_lines(res.bars)
    path.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    m = ProviderDataIngestionManifest(
        provider_id=req.provider_id,
        symbol=req.symbol,
        timeframe=req.timeframe,
        start_utc=req.start_utc,
        end_utc=req.end_utc,
        as_of_utc=req.as_of_utc,
        retrieved_at_utc=res.retrieved_at_utc,
        published_at_utc=res.published_at_utc,
        pit_status=res.pit_status,
        bars_path=str(path.resolve()),
        bars_sha256=digest,
        row_count=len(res.bars),
        license_scope=res.license_scope,
        provider_status=ProviderIngestionRuntimeStatus.OK,
        warnings=list(res.warnings),
        blockers=list(res.blockers),
    )
    body = m.model_dump(mode="json")
    m = m.model_copy(update={"manifest_sha256": canonical_json_sha256(body)})
    man_path = sub / (fname.replace(".csv", "_manifest.json"))
    man_path.write_text(
        m.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return m


__all__ = ["ingest_provider_bars_to_snapshot"]
