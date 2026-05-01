"""CLI: Alpaca paper broker evidence (optional keys; no browser orders)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from strategy_validator.brokers.alpaca_paper import (
    dry_run_paper_order,
    evaluate_alpaca_paper_policy,
    get_alpaca_paper_account,
    list_alpaca_paper_positions,
    submit_paper_order,
)
from strategy_validator.cli.deployment_env_check import parse_env_file
from strategy_validator.contracts.paper_broker import PaperBrokerOrderIntent
def _paper_broker_artifact_root() -> Path:
    return (Path.cwd() / "artifacts" / "paper_broker").resolve()


def _merge_env(env_file: Path | None) -> dict[str, str]:
    base = {k: str(v) for k, v in os.environ.items()}
    if env_file is None:
        return base
    vals, _ = parse_env_file(env_file)
    return {**base, **vals}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Paper-only Alpaca broker evidence CLI.")
    sub = p.add_subparsers(dest="cmd", required=True)

    s_status = sub.add_parser("status", help="Account snapshot (paper endpoint only).")
    s_status.add_argument("--env-file", default="", type=Path)

    s_pos = sub.add_parser("positions", help="List paper positions.")
    s_pos.add_argument("--env-file", default="", type=Path)

    s_dry = sub.add_parser("dry-run-order", help="Validate intent without submitting.")
    s_dry.add_argument("--tracking-id", required=True)
    s_dry.add_argument("--symbol", default="SPY")
    s_dry.add_argument("--qty", type=float, default=1.0)
    s_dry.add_argument("--side", default="buy", choices=["buy", "sell"])
    s_dry.add_argument("--env-file", default="", type=Path)

    s_sub = sub.add_parser("submit-paper-order", help="Submit order to paper API (CLI only).")
    s_sub.add_argument("--tracking-id", required=True)
    s_sub.add_argument("--symbol", default="SPY")
    s_sub.add_argument("--qty", type=float, default=1.0)
    s_sub.add_argument("--side", default="buy", choices=["buy", "sell"])
    s_sub.add_argument("--confirm-paper", action="store_true", required=True)
    s_sub.add_argument("--env-file", default="", type=Path)

    ns = p.parse_args(argv)
    raw_ef = str(getattr(ns, "env_file", "") or "").strip()
    env = _merge_env(Path(raw_ef) if raw_ef else None)

    if ns.cmd == "status":
        acct = get_alpaca_paper_account(env)
        sys.stdout.write(json.dumps({"ok": True, "account": acct.model_dump(mode="json")}, indent=2) + "\n")
        return 0
    if ns.cmd == "positions":
        pol, rows, notes = list_alpaca_paper_positions(env)
        sys.stdout.write(
            json.dumps(
                {"ok": True, "policy": pol.value, "positions": [r.model_dump(mode="json") for r in rows], "notes": notes},
                indent=2,
            )
            + "\n"
        )
        return 0
    if ns.cmd == "dry-run-order":
        intent = PaperBrokerOrderIntent(
            tracking_id=ns.tracking_id,
            symbol=ns.symbol,
            side=ns.side,
            qty=float(ns.qty),
        )
        res = dry_run_paper_order(intent, env)
        sys.stdout.write(json.dumps({"ok": res.ok, "result": res.model_dump(mode="json")}, indent=2) + "\n")
        return 0
    if ns.cmd == "submit-paper-order":
        pol, _, blocks = evaluate_alpaca_paper_policy(env)
        if pol.value != "PAPER_READY":
            sys.stdout.write(json.dumps({"ok": False, "blocked": blocks}, indent=2) + "\n")
            return 2
        intent = PaperBrokerOrderIntent(
            tracking_id=ns.tracking_id,
            symbol=ns.symbol,
            side=ns.side,
            qty=float(ns.qty),
        )
        res = submit_paper_order(intent, env)
        tdir = _paper_broker_artifact_root() / ns.tracking_id
        tdir.mkdir(parents=True, exist_ok=True)
        art = tdir / "paper_order_submission.json"
        redacted = res.model_dump(mode="json")
        art.write_text(json.dumps(redacted, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        sys.stdout.write(json.dumps({"ok": res.ok, "result": redacted, "artifact": str(art)}, indent=2) + "\n")
        return 0 if res.ok else 3
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
