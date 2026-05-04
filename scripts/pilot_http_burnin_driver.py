"""
Controlled local HTTP JSON burn-in: ephemeral server + pilot probe subprocesses.

Run from repo root:
  python scripts/pilot_http_burnin_driver.py

Requires no Alpaca keys; uses STRATEGY_VALIDATOR_HTTP_* env overrides only in child processes.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


class _EchoLiquidityHandler(BaseHTTPRequestHandler):
    def log_message(self, *args: object) -> None:  # noqa: ARG002
        return

    def do_GET(self) -> None:  # noqa: N802
        if "/liq/" not in self.path:
            self.send_error(404)
            return
        ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        body = json.dumps(
            {
                "adv_notional": 500_000_000.0,
                "spread_bps": 4.25,
                "snapshot_time": ts,
            }
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _child_env(port: int) -> dict[str, str]:
    e = os.environ.copy()
    e["STRATEGY_VALIDATOR_HTTP_MARKET_DATA_ENABLED"] = "True"
    e["STRATEGY_VALIDATOR_HTTP_MARKET_DATA_PROVIDER_ID"] = "pilot_local_echo"
    e["STRATEGY_VALIDATOR_HTTP_MARKET_DATA_LIQUIDITY_URL_TEMPLATE"] = (
        f"http://127.0.0.1:{port}/liq/{{asset_id}}"
    )
    e["STRATEGY_VALIDATOR_HTTP_MARKET_DATA_TIMEOUT_SECONDS"] = "5"
    return e


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
        "SPY",
        "--output",
        str(out),
    ]
    subprocess.run(cmd, cwd=root, env=env, check=True)


def _run_analyze(env: dict[str, str], probe_file: Path, analysis_out: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, "-m", "strategy_validator.cli.pilot", "analyze", str(probe_file)]
    p = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True, check=True)
    analysis_out.write_text(p.stdout, encoding="utf-8")


def main() -> int:
    rounds = 60
    if len(sys.argv) >= 2:
        rounds = int(sys.argv[1])
    if not (30 <= rounds <= 100):
        print("usage: python scripts/pilot_http_burnin_driver.py [ROUNDS]  # 30..100", file=sys.stderr)
        return 2

    srv = HTTPServer(("127.0.0.1", 0), _EchoLiquidityHandler)
    port = srv.server_address[1]
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    env = _child_env(port)
    root = Path(__file__).resolve().parents[1]
    r1 = root / "pilot_burnin_round1.jsonl"
    r2 = root / "pilot_burnin_round2.jsonl"
    a1 = root / "pilot_burnin_round1_analyze.txt"
    a2 = root / "pilot_burnin_round2_analyze.txt"
    try:
        for p in (r1, r2, a1, a2):
            if p.exists():
                p.unlink()
        _run_probe(env, rounds, r1)
        _run_analyze(env, r1, a1)
        _run_probe(env, rounds, r2)
        _run_analyze(env, r2, a2)
    finally:
        srv.shutdown()
        srv.server_close()
    print(f"wrote {r1.name}, {a1.name}, {r2.name}, {a2.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
