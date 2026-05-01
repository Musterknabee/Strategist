#!/usr/bin/env python3
"""End-to-end local research OS demo: gauntlet → paper → lifecycle → packet → daily → allocation (no network).

Uses example_gauntlet_batch.json and repo-local CSV fixtures. Optional GPU benchmark can be skipped.
Does not submit broker orders or call live providers.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-root", type=Path, default=Path("artifacts/research_os_demo"))
    p.add_argument("--run-id", default="research-os-demo")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--skip-benchmark", action="store_true", help="Skip process-pool benchmark (faster CI/demos).")
    p.add_argument("--skip-portfolio", action="store_true")
    p.add_argument("--json", action="store_true")
    ns = p.parse_args(argv)

    demo_root = ns.output_root
    if not demo_root.is_absolute():
        demo_root = (_REPO_ROOT / demo_root).resolve()
    latest_dir = demo_root / "latest"
    paper_root = demo_root / "paper_tracking"
    strategy_runs = demo_root / "strategy_runs"
    batch_spec_path = _REPO_ROOT / "configs" / "strategy_batches" / "example_gauntlet_batch.json"

    if not batch_spec_path.is_file():
        err = {"ok": False, "error": "MISSING_BATCH_SPEC", "path": str(batch_spec_path)}
        sys.stdout.write(json.dumps(err, indent=2) + "\n")
        return 2

    preserved = {
        "STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT": os.environ.get("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT"),
        "STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT": os.environ.get("STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT"),
        "STRATEGY_VALIDATOR_TEST_PAPER_CLOCK_DATE": os.environ.get("STRATEGY_VALIDATOR_TEST_PAPER_CLOCK_DATE"),
        "STRATEGY_VALIDATOR_ARTIFACT_ROOT": os.environ.get("STRATEGY_VALIDATOR_ARTIFACT_ROOT"),
    }
    os.environ["STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT"] = str(paper_root)
    os.environ["STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT"] = str(strategy_runs)
    os.environ["STRATEGY_VALIDATOR_TEST_PAPER_CLOCK_DATE"] = "2026-05-01"
    os.environ["STRATEGY_VALIDATOR_ARTIFACT_ROOT"] = str(demo_root / "internal_artifacts")

    manifest: dict[str, object] = {
        "schema_version": "research_os_demo_manifest/v1",
        "run_id": ns.run_id,
        "demo_started_at_utc": datetime.now(timezone.utc).isoformat(),
        "demo_root": str(demo_root),
        "steps": [],
        "warnings": [],
        "ok": True,
    }

    try:
        os.chdir(_REPO_ROOT)
        from strategy_validator.application.strategy_batch_loader import load_strategy_batch_spec
        from strategy_validator.application.promotion_review_ops import build_promotion_review_packet
        from strategy_validator.application.paper_tracking_ops import (
            append_daily_snapshot,
            assess_paper_tracking,
            enroll_strategies_from_batch_run,
            evaluate_paper_tracking,
            run_paper_tracking_daily,
        )
        from strategy_validator.contracts.portfolio_allocation import (
            AllocationMethod,
            PortfolioAllocationRequest,
        )
        from strategy_validator.research.portfolio_allocation import simulate_portfolio_allocation
        from strategy_validator.research.strategy_batch_runner import run_strategy_batch
        from strategy_validator.contracts.strategy_batch import StrategyBatchRunSummary

        spec = load_strategy_batch_spec(str(batch_spec_path))
        spec = spec.model_copy(update={"output_root": str(strategy_runs)})

        summary = run_strategy_batch(
            spec,
            allow_synthetic=True,
            fail_fast=False,
            adjudication_hook=None,
            run_id=ns.run_id.strip(),
            overwrite=ns.overwrite,
        )
        run_dir = Path(summary.output_dir)
        manifest["steps"].append(
            {
                "name": "gauntlet_batch",
                "ok": summary.ok,
                "batch_id": summary.batch_id,
                "run_id": summary.run_id,
                "output_dir": str(run_dir),
                "summary_path": str(run_dir / "batch_summary.json"),
            }
        )
        if not (run_dir / "batch_summary.json").is_file():
            manifest["ok"] = False
            manifest["warnings"].append("MISSING_BATCH_SUMMARY")

        manifests = enroll_strategies_from_batch_run(
            run_dir,
            allow_synthetic_demo=True,
            repo_root=_REPO_ROOT,
        )
        tids = [m.tracking_id for m in manifests]
        manifest["steps"].append(
            {"name": "paper_enroll", "ok": bool(tids), "tracking_ids": tids, "count": len(tids)}
        )
        if not tids:
            manifest["warnings"].append("NO_TRACKING_IDS_ENROLLED")

        obs = date(2026, 5, 1)
        for tid in tids:
            try:
                append_daily_snapshot(tid, observation_date=obs, repo_root=_REPO_ROOT)
                evaluate_paper_tracking(tid, repo_root=_REPO_ROOT)
                assess_paper_tracking(tid, repo_root=_REPO_ROOT)
                build_promotion_review_packet(tid, repo_root=_REPO_ROOT)
            except Exception as exc:
                manifest["warnings"].append(f"TRACKING_STEP:{tid}:{exc!s}")
        manifest["steps"].append({"name": "snapshot_evaluate_assess_packet", "tracking_ids": tids})

        daily_payload = run_paper_tracking_daily(
            date(2026, 5, 2),
            repo_root=_REPO_ROOT,
            tracking_root=paper_root,
        )
        manifest["steps"].append({"name": "paper_daily", "payload_paths": str(paper_root / "daily_runs")})

        if not ns.skip_portfolio:
            raw = json.loads((run_dir / "batch_summary.json").read_text(encoding="utf-8"))
            summ = StrategyBatchRunSummary.model_validate(raw)
            req = PortfolioAllocationRequest(
                batch_run_id=summ.run_id,
                capital=100_000.0,
                method=AllocationMethod.equal_weight,
            )
            alloc = simulate_portfolio_allocation(summ, run_dir=run_dir, request=req)
            out_alloc = run_dir / "portfolio_allocation_result.json"
            _write_json(out_alloc, alloc.model_dump(mode="json"))
            manifest["steps"].append(
                {"name": "portfolio_allocation", "artifact": str(out_alloc), "gate": alloc.allocation_gate_status.value}
            )
        else:
            manifest["steps"].append({"name": "portfolio_allocation", "skipped": True})

        from strategy_validator.research_compute.gpu_probe import probe_gpu_capability

        probe = probe_gpu_capability()
        manifest["steps"].append({"name": "gpu_probe", "gpu_available": probe.get("gpu_available")})

        if not ns.skip_benchmark:
            try:
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(_REPO_ROOT / "scripts" / "benchmark_research_compute.py"),
                        "--iterations",
                        "8000",
                        "--chunks",
                        "2",
                        "--json",
                    ],
                    cwd=str(_REPO_ROOT),
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )
                if completed.returncode != 0:
                    manifest["warnings"].append(f"BENCHMARK_EXIT_{completed.returncode}")
                manifest["steps"].append(
                    {"name": "compute_benchmark", "ok": completed.returncode == 0}
                )
            except Exception as exc:
                manifest["warnings"].append(f"BENCHMARK:{exc!s}")
                manifest["steps"].append({"name": "compute_benchmark", "ok": False})
        else:
            manifest["steps"].append({"name": "compute_benchmark", "skipped": True})

    except Exception as exc:
        manifest["ok"] = False
        manifest["warnings"].append(f"FATAL:{type(exc).__name__}:{exc}")
    finally:
        for k, v in preserved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    manifest["demo_completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    out_manifest = latest_dir / "demo_manifest.json"
    _write_json(out_manifest, manifest)

    payload = {"ok": bool(manifest.get("ok")), "manifest_path": str(out_manifest), "manifest": manifest}
    if ns.json:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(f"wrote {out_manifest}\n")
    return 0 if manifest.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
