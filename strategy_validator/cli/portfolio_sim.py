"""CLI: portfolio allocation simulation over a strategy batch run directory."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategy_validator.contracts.portfolio_allocation import (
    AllocationMethod,
    PortfolioAllocationRequest,
)
from strategy_validator.contracts.strategy_batch import StrategyBatchRunSummary
from strategy_validator.research.portfolio_allocation import simulate_portfolio_allocation


def _resolve_run_dir(arg: Path) -> tuple[Path, StrategyBatchRunSummary]:
    p = arg.resolve()
    if (p / "batch_summary.json").is_file():
        run_dir = p
    elif p.is_file() and p.name == "batch_summary.json":
        run_dir = p.parent
    else:
        raise FileNotFoundError(f"batch_summary.json not under {p}")
    raw = json.loads((run_dir / "batch_summary.json").read_text(encoding="utf-8"))
    summary = StrategyBatchRunSummary.model_validate(raw)
    return run_dir, summary


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Simulate portfolio weights from a batch run (research only).")
    p.add_argument("--batch-run", required=True, type=Path, help="Run directory containing batch_summary.json")
    p.add_argument("--capital", type=float, default=100_000.0)
    p.add_argument("--method", default="capped_score_weight", choices=[m.value for m in AllocationMethod])
    p.add_argument("--max-weight", type=float, default=0.35)
    p.add_argument("--json", action="store_true")
    ns = p.parse_args(argv)

    run_dir, summary = _resolve_run_dir(ns.batch_run)
    req = PortfolioAllocationRequest(
        batch_run_id=summary.run_id,
        capital=float(ns.capital),
        method=AllocationMethod(ns.method),
        max_weight=float(ns.max_weight),
    )
    result = simulate_portfolio_allocation(summary, run_dir=run_dir, request=req)
    out_path = run_dir / "portfolio_allocation_result.json"
    body = result.model_dump(mode="json")
    out_path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload = {
        "ok": True,
        "artifact": str(out_path),
        "evidence_digest": result.evidence_digest,
        "allocation_gate_status": result.allocation_gate_status.value,
    }
    if ns.json:
        payload["result"] = body
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
