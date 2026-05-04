"""CLI for market-data integrity checks on governed local bar CSV/JSON snapshots."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.contracts.strategy_data_snapshot import StrategyBar
from strategy_validator.research.market_data_integrity import evaluate_market_data_integrity


def _parse_ts(raw: str) -> datetime:
    s = raw.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _load_csv(path: Path) -> list[StrategyBar]:
    out: list[StrategyBar] = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            out.append(
                StrategyBar(
                    symbol=str(row.get("symbol") or "SPY"),
                    timestamp_utc=_parse_ts(str(row["timestamp_utc"])),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row.get("volume") or 0.0),
                )
            )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evaluate", nargs="?")
    parser.add_argument("--bars", required=True)
    parser.add_argument("--strategy-id", default="manual-market-data-integrity")
    parser.add_argument("--batch-id", default="manual")
    parser.add_argument("--run-id", default="manual")
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--provider-id", default="local_file")
    parser.add_argument("--license-scope", default="local_unverified")
    parser.add_argument("--trust-level", default="local_unverified")
    parser.add_argument("--output", default="")
    parser.add_argument("--json", action="store_true")
    ns = parser.parse_args(argv)
    bars = _load_csv(Path(ns.bars))
    res = evaluate_market_data_integrity(
        strategy_id=ns.strategy_id,
        batch_id=ns.batch_id,
        run_id=ns.run_id,
        bars=bars,
        as_of_utc=_parse_ts(ns.as_of),
        snapshot=None,
        provider_id=ns.provider_id,
        license_scope=ns.license_scope,
        trust_level=ns.trust_level,
    )
    payload = {"ok": res.gate_status.value != "BLOCKED", "result": res.model_dump(mode="json")}
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if ns.output:
        Path(ns.output).parent.mkdir(parents=True, exist_ok=True)
        Path(ns.output).write_text(text, encoding="utf-8")
    sys.stdout.write(text if ns.json else json.dumps(payload, sort_keys=True) + "\n")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
