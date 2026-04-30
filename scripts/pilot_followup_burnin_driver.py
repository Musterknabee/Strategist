"""
Follow-up Alpaca-only pilot burn-ins (after an initial staging + Alpaca pass).

Runs three operator-triggered scenarios for evidence on freshness law and vendor
behavior:

  long        Longer Alpaca-only ``pilot probe --resolution`` + analyze.
  off-hours   Same probe shape; run this mode during weekend or outside US RTH
              so policy/market-hours law matches your question (script prints
              current UTC and a simple NY-schedule RTH hint).
  symbol      Repeat on a second symbol (e.g. QQQ) with the same child env.

Parent shell must already configure Alpaca (keys via APCA_* or project env
overrides). HTTP is forced off in the child so only Alpaca backs the probe.

Usage (repo root):

  python scripts/pilot_followup_burnin_driver.py long [ROUNDS]        # default 180
  python scripts/pilot_followup_burnin_driver.py off-hours [ROUNDS]   # default 60
  python scripts/pilot_followup_burnin_driver.py symbol QQQ [ROUNDS] # default 60

ROUNDS are clamped to pilot CLI limits (1..500); long/off-hours/symbol use
sensible floors so ``long`` stays meaningfully longer than a 60-round pass.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.validator.market_hours import us_equities_regular_session_open


def _alpaca_only_env(base: dict[str, str]) -> dict[str, str]:
    e = base.copy()
    e["STRATEGY_VALIDATOR_HTTP_MARKET_DATA_ENABLED"] = "false"
    e["STRATEGY_VALIDATOR_ALPACA_MARKET_DATA_ENABLED"] = "true"
    return e


def _run_probe(env: dict[str, str], rounds: int, out: Path, symbol: str) -> None:
    root = Path(__file__).resolve().parents[1]
    cmd = [
        sys.executable,
        "-m",
        "strategy_validator.cli.pilot",
        "probe",
        "--resolution",
        "--rounds",
        str(rounds),
        "--symbol",
        symbol,
        "--output",
        str(out),
    ]
    subprocess.run(cmd, cwd=root, env=env, check=True)


def _run_analyze(env: dict[str, str], probe_file: Path, analysis_out: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, "-m", "strategy_validator.cli.pilot", "analyze", str(probe_file)]
    p = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stderr or p.stdout or "(no output)", file=sys.stderr)
        raise subprocess.CalledProcessError(p.returncode, cmd, p.stdout, p.stderr)
    analysis_out.write_text(p.stdout, encoding="utf-8")


def _clamp_rounds(n: int, *, lo: int, hi: int = 500) -> int:
    return max(lo, min(hi, n))


def cmd_long(ns: argparse.Namespace) -> int:
    rounds = _clamp_rounds(ns.rounds, lo=90)
    return _run_one(
        stem="pilot_followup_alpaca_long",
        rounds=rounds,
        symbol=os.environ.get("PILOT_PROBE_SYMBOL", "SPY"),
        banner=None,
    )


def cmd_off_hours(ns: argparse.Namespace) -> int:
    rounds = _clamp_rounds(ns.rounds, lo=30)
    now = datetime.now(timezone.utc)
    rth = us_equities_regular_session_open(now)
    banner = (
        f"Now (UTC): {now.isoformat()} | us_equities_regular_session_open={rth}. "
        "For off-hours / weekend law, prefer running when this is false (weekend or outside NY 09:30-16:00)."
    )
    return _run_one(
        stem="pilot_followup_alpaca_off_hours",
        rounds=rounds,
        symbol=os.environ.get("PILOT_PROBE_SYMBOL", "SPY"),
        banner=banner,
    )


def cmd_symbol(ns: argparse.Namespace) -> int:
    sym = ns.ticker.strip().upper()
    if not sym:
        print("symbol: ticker required", file=sys.stderr)
        return 2
    rounds = _clamp_rounds(ns.rounds, lo=30)
    return _run_one(
        stem=f"pilot_followup_alpaca_sym_{sym}",
        rounds=rounds,
        symbol=sym,
        banner=f"Second-symbol pass: {sym}",
    )


def _run_one(*, stem: str, rounds: int, symbol: str, banner: str | None) -> int:
    root = Path(__file__).resolve().parents[1]
    jsonl = root / f"{stem}.jsonl"
    txt = root / f"{stem}_analyze.txt"
    for p in (jsonl, txt):
        if p.exists():
            p.unlink()

    base = os.environ.copy()
    env = _alpaca_only_env(base)
    if banner:
        print(banner, file=sys.stderr)

    try:
        _run_probe(env, rounds, jsonl, symbol)
    except subprocess.CalledProcessError:
        print(
            "Probe failed. Ensure Alpaca is enabled in parent env and HTTP is not the only provider "
            "(this script forces HTTP off).",
            file=sys.stderr,
        )
        return 3

    try:
        _run_analyze(base, jsonl, txt)
    except subprocess.CalledProcessError:
        return 4

    print(f"wrote {jsonl.name}, {txt.name}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Alpaca-only follow-up pilot burn-ins")
    sub = parser.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("long", help="Longer Alpaca-only run (default 180 rounds)")
    pl.add_argument("rounds", nargs="?", type=int, default=180, help="Probe rounds (90..500)")
    pl.set_defaults(_run=cmd_long)

    po = sub.add_parser(
        "off-hours",
        help="Alpaca run for weekend / outside-RTH behavior (schedule manually; prints RTH hint)",
    )
    po.add_argument("rounds", nargs="?", type=int, default=60, help="Probe rounds (30..500)")
    po.set_defaults(_run=cmd_off_hours)

    ps = sub.add_parser("symbol", help="Alpaca-only run on a second symbol")
    ps.add_argument("ticker", help="Symbol, e.g. QQQ")
    ps.add_argument("rounds", nargs="?", type=int, default=60, help="Probe rounds (30..500)")
    ps.set_defaults(_run=cmd_symbol)

    ns = parser.parse_args()
    return int(ns._run(ns))


if __name__ == "__main__":
    raise SystemExit(main())
