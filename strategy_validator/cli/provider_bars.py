"""CLI: ingest optional provider historical bars to local snapshot (research only)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from strategy_validator.cli.deployment_env_check import parse_env_file
from strategy_validator.contracts.provider_historical_data import HistoricalDataRequest
from strategy_validator.research.provider_data_ingestion import ingest_provider_bars_to_snapshot
from strategy_validator.research.provider_historical_snapshot_ingest import run_provider_historical_ingest


def _parse_utc(s: str):
    from datetime import datetime, timezone

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


def _legacy_main(ns: argparse.Namespace) -> int:
    raw_ef = str(getattr(ns, "env_file", "") or "").strip()
    env = _merge_env(Path(raw_ef) if raw_ef else None)
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
    manifest = ingest_provider_bars_to_snapshot(req, env, output_root=Path(ns.output_root))
    payload = {"ok": True, "manifest": manifest.model_dump(mode="json")}
    if ns.json:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(f"status={manifest.provider_status.value} rows={manifest.row_count}\n")
    return 0


def _ingest_main(ns: argparse.Namespace) -> int:
    env = _merge_env(ns.env_file if ns.env_file else None)
    symbols = list(ns.symbol) if ns.symbol else []
    if not symbols and ns.symbols_csv:
        symbols = [s.strip() for s in ns.symbols_csv.split(",") if s.strip()]
    if not symbols:
        sys.stderr.write("ingest: need --symbol (repeat) or --symbols\n")
        return 2
    run = run_provider_historical_ingest(
        provider_id=ns.provider,
        symbols=symbols,
        timeframe=ns.timeframe,
        start_day=ns.start,
        end_day=ns.end,
        as_of_raw=ns.as_of,
        output_root=Path(ns.output_root),
        env=env,
        no_network=not bool(ns.allow_network),
        allow_network=bool(ns.allow_network),
        fixture_manifest=Path(ns.fixture) if str(ns.fixture or "").strip() else None,
        allow_best_effort_as_of=bool(ns.allow_best_effort_as_of),
    )
    payload = {"ok": run.ok, "run": run.model_dump(mode="json")}
    if ns.json:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(f"ok={run.ok} snapshots={len(run.snapshots)} network={run.network_used}\n")
    return 0 if run.ok or ns.allow_failed_exit else 1


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in ("ingest", "--help", "-h", "legacy-ingest"):
        argv = ["legacy-ingest", *argv]

    p = argparse.ArgumentParser(description="Provider historical bars snapshot CLI.")
    sub = p.add_subparsers(dest="cmd")

    legacy = sub.add_parser("legacy-ingest", help="Single-symbol legacy ingest (compat).")
    legacy.add_argument("--provider", required=True)
    legacy.add_argument("--symbol", required=True)
    legacy.add_argument("--timeframe", default="1d")
    legacy.add_argument("--start", required=True)
    legacy.add_argument("--end", required=True)
    legacy.add_argument("--as-of", required=True)
    legacy.add_argument("--output-root", required=True, type=Path)
    legacy.add_argument("--env-file", default="")
    legacy.add_argument("--json", action="store_true")
    legacy.set_defaults(func=_legacy_main)

    ing = sub.add_parser("ingest", help="Multi-symbol snapshot run (provider_historical_snapshot_run/v1).")
    ing.add_argument("--provider", required=True)
    ing.add_argument("--symbol", action="append", help="Repeat per ticker.")
    ing.add_argument("--symbols", dest="symbols_csv", default="", help="Comma-separated alternative.")
    ing.add_argument("--timeframe", default="1d")
    ing.add_argument("--start", required=True, help="YYYY-MM-DD")
    ing.add_argument("--end", required=True, help="YYYY-MM-DD")
    ing.add_argument("--as-of", required=True, help="ISO-8601 UTC")
    ing.add_argument("--output-root", required=True, type=Path)
    ing.add_argument("--env-file", default=None, type=Path)
    ing.add_argument(
        "--allow-network",
        action="store_true",
        help="Permit live provider fetches when keys exist (default: fixture/offline only).",
    )
    ing.add_argument("--fixture", default="", type=str, help="Path to provider snapshot manifest JSON.")
    ing.add_argument("--allow-best-effort-as-of", action="store_true")
    ing.add_argument("--allow-failed-exit", action="store_true", help="Exit 0 even if run.ok is false.")
    ing.add_argument("--json", action="store_true")
    ing.set_defaults(func=_ingest_main)

    ns = p.parse_args(argv)
    if not getattr(ns, "cmd", None):
        p.print_help()
        return 2
    return int(ns.func(ns))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
