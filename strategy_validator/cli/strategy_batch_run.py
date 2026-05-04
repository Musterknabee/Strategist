"""CLI: run governed multi-strategy batch (research/paper; artifacts only)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategy_validator.application.strategy_batch_loader import load_strategy_batch_spec
from strategy_validator.research.strategy_batch_adjudication import build_adjudication_hook
from strategy_validator.research.strategy_batch_runner import run_strategy_batch


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", required=True, help="Path to JSON/YAML StrategyBatchSpec")
    parser.add_argument("--output-root", default="", help="Override spec output_root")
    parser.add_argument("--max-workers", type=int, default=0, help="Override spec max_workers (0=use spec)")
    parser.add_argument("--mode", default="", choices=["", "research", "paper"], help="Override spec mode")
    parser.add_argument("--adjudicate", action="store_true", help="Optional orchestrator adjudication (commit=False)")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary on stdout")
    parser.add_argument("--fail-fast", action="store_true", help="Stop after first strategy failure")
    parser.add_argument("--dry-run", action="store_true", help="Validate spec only; do not execute")
    parser.add_argument("--no-synthetic", action="store_true", help="Disallow synthetic demo data path")
    parser.add_argument(
        "--run-id",
        default="",
        help="Explicit run directory name under output_root/batch_id (default: content hash)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Remove existing output_root/batch_id/run_id before running (never outside output root)",
    )
    parser.add_argument(
        "--worker-model",
        default="",
        choices=["", "thread_pool", "process_pool"],
        help="Override spec worker_model (process_pool disables in-process adjudication hook)",
    )
    ns = parser.parse_args(argv)

    spec = load_strategy_batch_spec(ns.batch)
    if ns.output_root:
        spec = spec.model_copy(update={"output_root": ns.output_root})
    if ns.max_workers > 0:
        spec = spec.model_copy(update={"max_workers": ns.max_workers})
    if ns.mode:
        spec = spec.model_copy(update={"mode": ns.mode})  # type: ignore[arg-type]
    if ns.worker_model:
        spec = spec.model_copy(update={"worker_model": ns.worker_model})  # type: ignore[arg-type]

    if ns.dry_run:
        payload = {
            "ok": True,
            "dry_run": True,
            "batch_id": spec.batch_id,
            "strategy_count": len(spec.strategies),
            "output_root": spec.output_root,
        }
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
        return 0

    hook = build_adjudication_hook() if ns.adjudicate else None
    try:
        summary = run_strategy_batch(
            spec,
            allow_synthetic=not ns.no_synthetic,
            fail_fast=ns.fail_fast,
            adjudication_hook=hook,
            run_id=ns.run_id.strip() or None,
            overwrite=ns.overwrite,
        )
    except FileExistsError as exc:
        msg = str(exc)
        path = msg.split(":", 1)[1].strip() if msg.startswith("RUN_DIRECTORY_EXISTS:") else msg
        err_obj = {"ok": False, "error": "RUN_DIRECTORY_EXISTS", "path": path}
        if ns.json:
            sys.stdout.write(json.dumps(err_obj, sort_keys=True) + "\n")
        else:
            sys.stderr.write(f"{msg}\n")
        return 2

    passed = summary.passed_count
    blocked = summary.blocked_count
    paper_only = summary.paper_only_count
    failed = summary.failed_count

    payload = {
        "ok": summary.ok,
        "batch_id": summary.batch_id,
        "run_id": summary.run_id,
        "output_dir": summary.output_dir,
        "strategy_count": summary.strategy_count,
        "passed_count": passed,
        "blocked_count": blocked,
        "paper_only_count": paper_only,
        "failed_count": failed,
        "summary_path": str(Path(summary.output_dir) / "batch_summary.json"),
        "blockers": summary.blockers,
        "warnings": [w for s in summary.strategies for w in s.warnings][:200],
    }

    if ns.json:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(
            f"strategy batch complete batch_id={summary.batch_id} run_id={summary.run_id}\n"
            f"output_dir={summary.output_dir}\n"
            f"paper_only={paper_only} failed={failed} blocked={blocked}\n"
        )
    return 0 if summary.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
