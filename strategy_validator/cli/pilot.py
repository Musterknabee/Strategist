"""
Pilot harness: controlled real-provider probes and observation-only policy hints.

Requires a configured Alpaca or HTTP JSON connector (see promotion_gates.yaml / env).
Does not write the ledger.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, TextIO

from strategy_validator.core.config import load_config
from strategy_validator.validator.market_data_feeds import (
    ProviderBackedLiquidityFeed,
    provider_resilience_from_runtime_policy,
)
from strategy_validator.validator.providers.factory import (
    build_alpaca_market_data_provider,
    build_http_json_market_data_provider,
)

from strategy_validator.cli.pilot_aggregate import (
    load_pilot_records,
    suggest_env_from_summary,
    summarize_records,
)


def _open_out(path: str | None) -> TextIO:
    if path is None or path == "-":
        return sys.stdout
    return open(path, "a", encoding="utf-8")


def _close_out(f: TextIO) -> None:
    if f not in (sys.stdout, sys.stderr):
        f.close()


def run_probe(ns: argparse.Namespace) -> int:
    symbol = (ns.symbol or os.environ.get("PILOT_PROBE_SYMBOL") or "SPY").strip().upper()
    if not symbol:
        sys.stderr.write("PILOT_PROBE_EMPTY_SYMBOL\n")
        return 2

    cfg = load_config()
    rp = cfg.runtime_policy
    prov = build_alpaca_market_data_provider(cfg) or build_http_json_market_data_provider(cfg)
    if prov is None:
        sys.stderr.write(
            "PILOT_NO_PROVIDER: enable Alpaca or HTTP JSON in config/env "
            "(STRATEGY_VALIDATOR_ALPACA_MARKET_DATA_ENABLED / HTTP_…).\n"
        )
        return 3

    policy = provider_resilience_from_runtime_policy(rp)
    feed = ProviderBackedLiquidityFeed(prov, policy=policy)
    now = datetime.now(timezone.utc)
    out = _open_out(ns.output)

    try:
        freeze = __import__(
            "strategy_validator.contracts.interface_freeze", fromlist=["PILOT_RC_INTERFACE_FREEZE"]
        ).PILOT_RC_INTERFACE_FREEZE
        for i in range(ns.rounds):
            t0 = time.perf_counter()
            snap = feed.lookup(symbol, now)
            dt_ms = (time.perf_counter() - t0) * 1000.0
            meta = feed.last_lookup_metadata
            age_s = None
            if snap is not None:
                age_s = (now - snap.snapshot_time).total_seconds()
            rec: dict[str, Any] = {
                "pilot_schema": "1",
                "interface_freeze": freeze,
                "round": i,
                "symbol": symbol,
                "evaluated_at_utc": now.isoformat(),
                "provider_id": getattr(prov, "provider_id", "unknown"),
                "latency_ms": round(dt_ms, 3),
                "snapshot_present": snap is not None,
                "provider_status": getattr(meta, "status", None),
                "circuit_state": getattr(meta, "circuit_state", None),
                "retry_count": getattr(meta, "retry_count", None),
                "error_summary": getattr(meta, "error_summary", None),
                "failure_domain": getattr(meta, "failure_domain", None),
                "failure_code": getattr(meta, "failure_code", None),
                "snapshot_age_s": age_s,
                "source_mode": getattr(snap, "source_mode", None) if snap else None,
            }
            out.write(json.dumps(rec, default=str) + "\n")
            out.flush()
    finally:
        _close_out(out)

    return 0


def run_analyze(ns: argparse.Namespace) -> int:
    if not ns.input.is_file():
        sys.stderr.write(f"PILOT_ANALYZE_MISSING_FILE:{ns.input}\n")
        return 2
    recs = load_pilot_records(ns.input)
    summary = summarize_records(recs)
    sys.stdout.write(json.dumps(summary, indent=2, default=str) + "\n\n")
    for line in suggest_env_from_summary(summary):
        sys.stdout.write(line + "\n")
    sys.stdout.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pilot readiness: probe + analyze")
    sub = parser.add_subparsers(dest="cmd", required=True)

    pp = sub.add_parser("probe", help="Real provider liquidity probe → NDJSON")
    pp.add_argument("--symbol", default="", help="Symbol (default PILOT_PROBE_SYMBOL or SPY).")
    pp.add_argument("--rounds", type=int, default=5, ge=1, le=500)
    pp.add_argument("--output", default=None, help="Append NDJSON (default: stdout).")
    pp.set_defaults(_run=run_probe)

    ap = sub.add_parser("analyze", help="Aggregate probe NDJSON → suggested env from observations")
    ap.add_argument("input", type=Path, help="NDJSON from pilot probe")
    ap.set_defaults(_run=run_analyze)

    ns = parser.parse_args(argv)
    return int(ns._run(ns))


if __name__ == "__main__":
    raise SystemExit(main())
