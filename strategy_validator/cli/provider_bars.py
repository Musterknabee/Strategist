"""CLI: ingest optional provider historical bars to local snapshot (research only)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.cli.deployment_env_check import parse_env_file
from strategy_validator.contracts.provider_historical_data import HistoricalDataRequest
from strategy_validator.research.provider_data_ingestion import ingest_provider_bars_to_snapshot


def _parse_utc(s: str) -> datetime:
    raw = s.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _merge_env(env_file: Path | None) -> dict[str, str]:
    base = {k: str(v) for k, v in os.environ.items()}
    if env_file is None:
        return base
    vals, _ = parse_env_file(env_file)
    return {**base, **vals}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ingest provider historical bars to a local CSV snapshot.")
    p.add_argument("--provider", required=True, help="tiingo | alpha_vantage")
    p.add_argument("--symbol", required=True)
    p.add_argument("--timeframe", default="1d")
    p.add_argument("--start", required=True, help="YYYY-MM-DD")
    p.add_argument("--end", required=True, help="YYYY-MM-DD")
    p.add_argument("--as-of", required=True, help="ISO-8601 UTC")
    p.add_argument("--output-root", required=True, type=Path)
    p.add_argument("--env-file", default="", help="Optional deployment.env path")
    p.add_argument("--json", action="store_true")
    ns = p.parse_args(argv)

    raw_env = (ns.env_file or "").strip()
    env = _merge_env(Path(raw_env) if raw_env else None)
    start = _parse_utc(ns.start + "T00:00:00Z")
    end = _parse_utc(ns.end + "T23:59:59Z")
    as_of = _parse_utc(ns.as_of)
    req = HistoricalDataRequest(
        provider_id=ns.provider,
        symbol=ns.symbol,
        timeframe=ns.timeframe,
        start_utc=start,
        end_utc=end,
        as_of_utc=as_of,
    )
    manifest = ingest_provider_bars_to_snapshot(req, env, output_root=ns.output_root)
    payload = {"ok": True, "manifest": manifest.model_dump(mode="json")}
    if ns.json:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(f"status={manifest.provider_status.value} rows={manifest.row_count}\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
