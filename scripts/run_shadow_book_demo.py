#!/usr/bin/env python3
"""Run a deterministic paper-only Shadow Book demo (no broker/network/orders)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from strategy_validator.application.shadow_book_ops import create_shadow_book, mark_to_market, simulate_daily_fills
from strategy_validator.contracts.shadow_book import ShadowBookAllocation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", default="artifacts")
    parser.add_argument("--book-id", default="shadow-book-demo")
    parser.add_argument("--date", default="2026-01-02")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--json", action="store_true")
    ns = parser.parse_args(argv)
    os.environ["STRATEGY_VALIDATOR_ARTIFACT_ROOT"] = str(Path(ns.artifact_root).resolve())
    book = create_shadow_book(
        book_id=ns.book_id,
        starting_capital=100_000.0,
        allocations=[ShadowBookAllocation(strategy_id="momentum-SPY", target_weight=0.25, notional=25_000.0)],
        overwrite=ns.overwrite,
    )
    d = date.fromisoformat(ns.date)
    fills = simulate_daily_fills(ns.book_id, as_of_date=d)
    snap = mark_to_market(ns.book_id, as_of_date=d)
    payload = {
        "ok": True,
        "schema_version": "shadow_book_demo/v1",
        "book_id": ns.book_id,
        "book_manifest_sha256": book.manifest_sha256,
        "fill_count": len(fills),
        "snapshot_sha256": snap.snapshot_sha256,
        "status": snap.status.value,
        "no_live_trading": True,
        "no_broker_orders": True,
    }
    sys.stdout.write(json.dumps(payload, indent=2 if ns.json else None, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
