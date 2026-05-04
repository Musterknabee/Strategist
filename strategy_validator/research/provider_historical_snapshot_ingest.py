"""Orchestrate provider historical snapshot CLI runs (fixture / no-network / optional live)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.contracts.provider_historical_data import (
    HistoricalDataRequest,
    ProviderHistoricalPitStatus,
)
from strategy_validator.contracts.provider_historical_snapshot import (
    ProviderHistoricalSnapshotManifest,
    ProviderHistoricalSnapshotRequest,
    ProviderHistoricalSnapshotRun,
    ProviderHistoricalSnapshotStatus,
)
from strategy_validator.research.provider_data_ingestion import ingest_provider_bars_to_snapshot
from strategy_validator.research.provider_historical_snapshot_io import (
    finalize_manifest_sha,
    manifest_from_legacy_ingestion,
    write_snapshot_run,
)


def _parse_day_start(s: str) -> datetime:
    return datetime.fromisoformat(s.strip() + "T00:00:00+00:00").astimezone(timezone.utc)


def _parse_day_end(s: str) -> datetime:
    return datetime.fromisoformat(s.strip() + "T23:59:59+00:00").astimezone(timezone.utc)


def _parse_as_of(s: str) -> datetime:
    raw = s.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def run_provider_historical_ingest(
    *,
    provider_id: str,
    symbols: list[str],
    timeframe: str,
    start_day: str,
    end_day: str,
    as_of_raw: str,
    output_root: Path,
    env: dict[str, str],
    no_network: bool,
    allow_network: bool,
    fixture_manifest: Path | None,
    allow_best_effort_as_of: bool,
) -> ProviderHistoricalSnapshotRun:
    """Build a ``provider_historical_snapshot_run/v1`` under *output_root*."""
    _ = allow_best_effort_as_of
    syms = [s.strip().upper() for s in symbols if s.strip()]
    if not syms:
        raise ValueError("symbols required")
    as_of = _parse_as_of(as_of_raw)
    start_utc = _parse_day_start(start_day)
    end_utc = _parse_day_end(end_day)
    req = ProviderHistoricalSnapshotRequest(
        provider_id=provider_id.strip(),
        symbols=syms,
        timeframe=timeframe.strip(),
        start_utc=start_utc,
        end_utc=end_utc,
        as_of_utc=as_of,
        access_type="fixture" if fixture_manifest else ("none" if no_network else "api"),
        key_required=True,
    )
    now = datetime.now(timezone.utc)
    warns: list[str] = []
    blocks: list[str] = []
    snaps: list[ProviderHistoricalSnapshotManifest] = []
    network_used = False
    fix_path: str | None = None

    if fixture_manifest is not None:
        fix_path = str(fixture_manifest.resolve())
        data = json.loads(fixture_manifest.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("schema_version") == "provider_historical_snapshot_run/v1":
            run = ProviderHistoricalSnapshotRun.model_validate(data)
            write_snapshot_run(run, output_root=output_root)
            return run
        m = ProviderHistoricalSnapshotManifest.model_validate(data)
        if not m.manifest_sha256:
            m = finalize_manifest_sha(m)
        snaps.append(m)
        ok = m.provider_status == ProviderHistoricalSnapshotStatus.OK
        run = ProviderHistoricalSnapshotRun(
            generated_at_utc=now,
            request=req,
            snapshots=snaps,
            network_used=False,
            fixture_path=fix_path,
            ok=ok,
            warnings=warns,
            blockers=blocks,
        )
        write_snapshot_run(run, output_root=output_root)
        return run

    if no_network or not allow_network:
        for sym in syms:
            snaps.append(
                finalize_manifest_sha(
                    ProviderHistoricalSnapshotManifest(
                        provider_id=provider_id.strip(),
                        symbols=[sym],
                        timeframe=timeframe.strip(),
                        start_utc=start_utc,
                        end_utc=end_utc,
                        as_of_utc=as_of,
                        access_type="none",
                        key_required=True,
                        key_configured=False,
                        provider_status=ProviderHistoricalSnapshotStatus.PENDING_KEY,
                        pit_status=ProviderHistoricalPitStatus.BLOCKED_PROVIDER_UNAVAILABLE,
                        license_scope="freemium_research_only_unverified",
                        trust_level="unverified_freemium",
                        retrieved_at_utc=now,
                        bars_path="",
                        bars_sha256="",
                        row_count=0,
                        warnings=["NO_NETWORK_WITHOUT_FIXTURE"],
                        blockers=["PROVIDER_KEY_OR_FIXTURE_REQUIRED"],
                    )
                )
            )
        run = ProviderHistoricalSnapshotRun(
            generated_at_utc=now,
            request=req,
            snapshots=snaps,
            network_used=False,
            fixture_path=None,
            ok=False,
            warnings=warns + ["INGEST_DID_NOT_PRODUCE_OK_STATUS_UNDER_NO_NETWORK"],
            blockers=blocks,
        )
        write_snapshot_run(run, output_root=output_root)
        return run

    network_used = True
    sub_root = output_root / "raw_ingest"
    sub_root.mkdir(parents=True, exist_ok=True)
    for sym in syms:
        hreq = HistoricalDataRequest(
            provider_id=provider_id.strip(),
            symbol=sym,
            timeframe=timeframe.strip(),
            start_utc=start_utc,
            end_utc=end_utc,
            as_of_utc=as_of,
        )
        leg = ingest_provider_bars_to_snapshot(hreq, env, output_root=sub_root)
        m = manifest_from_legacy_ingestion(leg, access_type="api")
        m = finalize_manifest_sha(m)
        snaps.append(m)

    ok = bool(snaps) and all(s.provider_status == ProviderHistoricalSnapshotStatus.OK for s in snaps)
    run = ProviderHistoricalSnapshotRun(
        generated_at_utc=now,
        request=req,
        snapshots=snaps,
        network_used=network_used,
        fixture_path=fix_path,
        ok=ok,
        warnings=warns,
        blockers=blocks,
    )
    write_snapshot_run(run, output_root=output_root)
    return run


__all__ = ["run_provider_historical_ingest"]
