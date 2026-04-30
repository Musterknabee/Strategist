"""
Two-phase pilot burn-in: real HTTP (staging) first, then Alpaca-backed liquidity.

Operator supplies credentials and URLs via the **parent** process environment
(plus promotion_gates.yaml defaults). This script only pins provider order per
phase and runs ``pilot probe --resolution`` + ``pilot analyze``.

Phase 1 child env: Alpaca disabled, HTTP connector unchanged from parent.
Phase 2 child env: HTTP disabled, Alpaca enabled from parent.

Captures (via NDJSON + ``pilot analyze``): latency distribution, freshness
counts, provider status / vendor event taxonomies, fallback_applied, and
auth/rate-limit proxies from aggregates.

Optional: ``PILOT_SNAPSHOT_FALLBACK=1`` in the child (set here for both phases
when the parent exports it) exercises snapshot fallback **only if**
``STRATEGY_VALIDATOR_ALLOW_MARKET_DATA_FALLBACK`` is true in policy — this
driver does not change freshness thresholds.

Usage (repo root, after exporting staging HTTP + Alpaca env vars):

  python scripts/pilot_staging_alpaca_burnin_driver.py [ROUNDS]

RC2: decide only after reviewing both phase artifacts; this script does not tag.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _run_probe(env: dict[str, str], rounds: int, out: Path) -> None:
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
        os.environ.get("PILOT_PROBE_SYMBOL", "SPY"),
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


def main() -> int:
    rounds = 60
    if len(sys.argv) >= 2:
        rounds = int(sys.argv[1])
    if not (30 <= rounds <= 100):
        print("usage: python scripts/pilot_staging_alpaca_burnin_driver.py [ROUNDS]  # 30..100", file=sys.stderr)
        return 2

    base = os.environ.copy()
    # Pass through PILOT_SNAPSHOT_FALLBACK / PILOT_PROBE_SYMBOL / strategy_validator env from parent.
    http_env = base.copy()
    http_env["STRATEGY_VALIDATOR_ALPACA_MARKET_DATA_ENABLED"] = "false"

    alpaca_env = base.copy()
    alpaca_env["STRATEGY_VALIDATOR_HTTP_MARKET_DATA_ENABLED"] = "false"
    alpaca_env["STRATEGY_VALIDATOR_ALPACA_MARKET_DATA_ENABLED"] = "true"

    root = Path(__file__).resolve().parents[1]
    http_jsonl = root / "pilot_burnin_round_http_staging.jsonl"
    http_analyze = root / "pilot_burnin_round_http_staging_analyze.txt"
    alp_jsonl = root / "pilot_burnin_round_alpaca.jsonl"
    alp_analyze = root / "pilot_burnin_round_alpaca_analyze.txt"

    for p in (http_jsonl, http_analyze, alp_jsonl, alp_analyze):
        if p.exists():
            p.unlink()

    try:
        _run_probe(http_env, rounds, http_jsonl)
    except subprocess.CalledProcessError:
        print(
            "Phase 1 (HTTP-only) failed. The parent shell must already enable the HTTP JSON "
            "connector (e.g. STRATEGY_VALIDATOR_HTTP_MARKET_DATA_ENABLED=true and "
            "STRATEGY_VALIDATOR_HTTP_MARKET_DATA_LIQUIDITY_URL_TEMPLATE=…). "
            "Alpaca is forced off for this phase only.",
            file=sys.stderr,
        )
        return 3
    _run_analyze(base, http_jsonl, http_analyze)

    try:
        _run_probe(alpaca_env, rounds, alp_jsonl)
    except subprocess.CalledProcessError:
        print(
            "Phase 2 (Alpaca-only) failed. Enable Alpaca in config or parent env "
            "(STRATEGY_VALIDATOR_ALPACA_MARKET_DATA_ENABLED=true, data base URL, and key id/secret "
            "via the env var names in promotion_gates.yaml). HTTP is forced off for this phase only.",
            file=sys.stderr,
        )
        return 4
    _run_analyze(base, alp_jsonl, alp_analyze)

    print(f"wrote {http_jsonl.name}, {http_analyze.name}, {alp_jsonl.name}, {alp_analyze.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
