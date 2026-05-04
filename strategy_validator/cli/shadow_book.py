"""CLI for paper-only Shadow Book artifacts (simulated fills; no broker orders)."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from strategy_validator.application.shadow_book_ops import (
    apply_allocation_result,
    build_ui_shadow_book_latest_payload,
    create_shadow_book,
    freeze_shadow_book,
    mark_to_market,
    simulate_daily_fills,
)
from strategy_validator.contracts.shadow_book import ShadowBookAllocation


def _emit(payload: dict[str, object], *, as_json: bool) -> None:
    sys.stdout.write(json.dumps(payload, indent=2 if as_json else None, sort_keys=True) + "\n")


def _parse_date(raw: str) -> date:
    return date.fromisoformat(raw)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_create = sub.add_parser("create", help="Create a paper-only shadow book")
    p_create.add_argument("--book-id", required=True)
    p_create.add_argument("--starting-capital", type=float, default=100_000.0)
    p_create.add_argument("--strategy-id", action="append", default=[])
    p_create.add_argument("--weight", action="append", default=[])
    p_create.add_argument("--overwrite", action="store_true")
    p_create.add_argument("--json", action="store_true")

    p_alloc = sub.add_parser("apply-allocation", help="Apply allocation artifact to a shadow book")
    p_alloc.add_argument("--book-id", required=True)
    p_alloc.add_argument("--from-allocation", required=True)
    p_alloc.add_argument("--json", action="store_true")

    p_sim = sub.add_parser("simulate-day", help="Simulate paper fills and mark-to-market")
    p_sim.add_argument("--book-id", required=True)
    p_sim.add_argument("--date", required=True)
    p_sim.add_argument("--price-fixture", default="")
    p_sim.add_argument("--json", action="store_true")

    p_risk = sub.add_parser("risk", help="Show latest read-plane risk summary")
    p_risk.add_argument("--book-id", default="")
    p_risk.add_argument("--json", action="store_true")

    p_freeze = sub.add_parser("freeze", help="Freeze book by operator/risk rule")
    p_freeze.add_argument("--book-id", required=True)
    p_freeze.add_argument("--reason", required=True)
    p_freeze.add_argument("--json", action="store_true")

    p_latest = sub.add_parser("latest", help="Show UI latest payload")
    p_latest.add_argument("--json", action="store_true")

    ns = parser.parse_args(argv)
    try:
        if ns.cmd == "create":
            weights = [float(x) for x in ns.weight]
            allocs = []
            for i, sid in enumerate(ns.strategy_id):
                w = weights[i] if i < len(weights) else 0.0
                allocs.append(ShadowBookAllocation(strategy_id=sid, target_weight=w, notional=w * ns.starting_capital))
            book = create_shadow_book(book_id=ns.book_id, starting_capital=ns.starting_capital, allocations=allocs, overwrite=ns.overwrite)
            _emit({"ok": True, "book": book.model_dump(mode="json"), "no_live_trading": True, "no_broker_orders": True}, as_json=ns.json)
            return 0
        if ns.cmd == "apply-allocation":
            book = apply_allocation_result(ns.book_id, Path(ns.from_allocation))
            _emit({"ok": True, "book": book.model_dump(mode="json")}, as_json=ns.json)
            return 0
        if ns.cmd == "simulate-day":
            day = _parse_date(ns.date)
            pf = Path(ns.price_fixture) if ns.price_fixture else None
            fills = simulate_daily_fills(ns.book_id, as_of_date=day, price_fixture=pf)
            snap = mark_to_market(ns.book_id, as_of_date=day, price_fixture=pf)
            _emit({"ok": True, "fill_count": len(fills), "snapshot": snap.model_dump(mode="json"), "no_broker_orders": True}, as_json=ns.json)
            return 0
        if ns.cmd == "risk":
            _emit(build_ui_shadow_book_latest_payload(), as_json=ns.json)
            return 0
        if ns.cmd == "freeze":
            book = freeze_shadow_book(ns.book_id, reason=ns.reason)
            _emit({"ok": True, "book": book.model_dump(mode="json")}, as_json=ns.json)
            return 0
        if ns.cmd == "latest":
            _emit(build_ui_shadow_book_latest_payload(), as_json=ns.json)
            return 0
    except Exception as e:  # pragma: no cover
        _emit({"ok": False, "error": f"{type(e).__name__}: {e}"}, as_json=getattr(ns, "json", False))
        return 1
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
