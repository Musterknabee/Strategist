"""CLI: thesis to mutation proposals to next batch spec (read-plane artifacts)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategy_validator.research.thesis_mutation_batch_loop import run_thesis_mutation_batch_cycle


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--batch-summary", type=Path, required=True, help="Path to batch_summary.json from a completed run")
    p.add_argument(
        "--next-batch-spec-output",
        type=Path,
        required=True,
        help="Where to write the proposed StrategyBatchSpec JSON for a follow-on run",
    )
    p.add_argument("--loop-report-output", type=Path, default=None, help="Optional path for loop report JSON")
    p.add_argument("--json", action="store_true")
    ns = p.parse_args(argv)
    report = run_thesis_mutation_batch_cycle(
        batch_summary_path=ns.batch_summary.resolve(),
        next_batch_spec_output=ns.next_batch_spec_output.resolve(),
        loop_report_output=ns.loop_report_output.resolve() if ns.loop_report_output else None,
    )
    if ns.json:
        sys.stdout.write(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    else:
        sys.stdout.write(f"ok={report.get('ok')} next_spec={report.get('next_batch_spec_output')}\n")
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
