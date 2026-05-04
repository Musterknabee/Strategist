"""Populate canonical Research OS artifacts under STRATEGY_VALIDATOR_ARTIFACT_ROOT (no network; no live broker)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.promotion_review_ops import build_promotion_review_packet
from strategy_validator.application.strategy_batch_loader import load_strategy_batch_spec
from strategy_validator.application.paper_tracking_ops import (
    append_daily_snapshot,
    assess_paper_tracking,
    enroll_strategies_from_batch_run,
    evaluate_paper_tracking,
    run_paper_tracking_daily,
)
from strategy_validator.application.research_os_paths import (
    artifact_root_directory,
    research_os_runtime_manifest_path,
    strategy_data_directory,
)
from strategy_validator.application.ui_paper_tracking import discover_latest_paper_tracking
from strategy_validator.contracts.portfolio_allocation import AllocationMethod, PortfolioAllocationRequest
from strategy_validator.contracts.provider_historical_data import HistoricalDataRequest
from strategy_validator.contracts.strategy_batch import StrategyBatchRunSummary
from strategy_validator.research.portfolio_allocation import simulate_portfolio_allocation
from strategy_validator.research.provider_data_ingestion import ingest_provider_bars_to_snapshot
from strategy_validator.research.strategy_batch_runner import run_strategy_batch

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def _write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _digest_obj(obj: object) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifact-root", type=Path, default=None, help="Governed root (default: env or ./artifacts)")
    p.add_argument("--run-id", default="runtime-gauntlet-demo")
    p.add_argument("--batch-spec", type=Path, default=None, help="Batch JSON (default: packaged runtime_gauntlet_batch.json)")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument(
        "--allow-synthetic-demo",
        action="store_true",
        help="Also enroll SYNTHETIC PAPER_ONLY candidates (demo posture).",
    )
    p.add_argument("--skip-benchmark", action="store_true")
    p.add_argument("--skip-portfolio", action="store_true")
    p.add_argument("--json", action="store_true")
    ns = p.parse_args(argv)

    repo_root = Path.cwd()
    art = (ns.artifact_root.resolve() if ns.artifact_root else artifact_root_directory(repo_root)).resolve()

    preserved = {
        "STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT": os.environ.get("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT"),
        "STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT": os.environ.get("STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT"),
        "STRATEGY_VALIDATOR_TEST_PAPER_CLOCK_DATE": os.environ.get("STRATEGY_VALIDATOR_TEST_PAPER_CLOCK_DATE"),
        "STRATEGY_VALIDATOR_ARTIFACT_ROOT": os.environ.get("STRATEGY_VALIDATOR_ARTIFACT_ROOT"),
    }
    os.environ["STRATEGY_VALIDATOR_ARTIFACT_ROOT"] = str(art)
    os.environ["STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT"] = str(art / "strategy_runs")
    os.environ["STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT"] = str(art / "paper_tracking")
    os.environ["STRATEGY_VALIDATOR_TEST_PAPER_CLOCK_DATE"] = "2026-05-01"

    batch_path = ns.batch_spec.resolve() if ns.batch_spec else (_FIXTURES / "runtime_gauntlet_batch.json").resolve()
    if not batch_path.is_file():
        err = {"ok": False, "error": "MISSING_BATCH_SPEC", "path": str(batch_path)}
        sys.stdout.write(json.dumps(err, indent=2) + "\n")
        return 2

    manifest: dict[str, Any] = {
        "schema_version": "research_os_runtime_demo_manifest/v1",
        "run_id": ns.run_id.strip(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_root": str(art),
        "gauntlet_run": None,
        "paper_tracking": None,
        "lifecycle": None,
        "promotion_packet": None,
        "daily_tracking": None,
        "portfolio_allocation": None,
        "compute_probe": None,
        "compute_benchmark": None,
        "provider_ingestion": None,
        "paper_broker": {"note": "Policy is read via API env only; this CLI does not submit orders."},
        "warnings": [],
        "blockers": [],
        "digests": {},
        "ok": True,
    }

    try:
        spec = load_strategy_batch_spec(batch_path)
        spec = spec.model_copy(update={"output_root": str(art / "strategy_runs")})

        summary = run_strategy_batch(
            spec,
            allow_synthetic=True,
            fail_fast=False,
            adjudication_hook=None,
            run_id=ns.run_id.strip(),
            overwrite=ns.overwrite,
        )
        run_dir = Path(summary.output_dir)
        manifest["gauntlet_run"] = {
            "batch_id": summary.batch_id,
            "run_id": summary.run_id,
            "ok": summary.ok,
            "output_dir": str(run_dir),
            "summary_path": str(run_dir / "batch_summary.json"),
            "strategy_count": summary.strategy_count,
            "passed_count": summary.passed_count,
            "paper_only_count": summary.paper_only_count,
            "blocked_count": summary.blocked_count,
        }
        manifest["digests"]["batch_summary_sha256"] = _digest_obj(
            json.loads((run_dir / "batch_summary.json").read_text(encoding="utf-8"))
        )

        enrolled = enroll_strategies_from_batch_run(
            run_dir,
            allow_synthetic_demo=bool(ns.allow_synthetic_demo),
            repo_root=repo_root,
        )
        tids = [m.tracking_id for m in enrolled]
        manifest["paper_tracking"] = {"tracking_ids": tids, "count": len(tids)}
        if not tids:
            manifest["warnings"].append("NO_ELIGIBLE_PAPER_ENROLLMENTS_USE_ALLOW_SYNTHETIC_IF_DEMO")

        obs = date(2026, 5, 1)
        for tid in tids:
            try:
                append_daily_snapshot(tid, observation_date=obs, repo_root=repo_root)
                evaluate_paper_tracking(tid, repo_root=repo_root)
                assess_paper_tracking(tid, repo_root=repo_root)
                build_promotion_review_packet(tid, repo_root=repo_root)
            except Exception as exc:
                manifest["warnings"].append(f"TRACKING_STEP:{tid}:{exc!s}")

        if tids:
            _, bundle = discover_latest_paper_tracking(repo_root=repo_root)
            pkt_sum = (bundle or {}).get("promotion_review_packet_summary") if bundle else None
            manifest["promotion_packet"] = pkt_sum
            manifest["lifecycle"] = {
                "state": (bundle or {}).get("lifecycle_state"),
                "promotion_review_ready": (bundle or {}).get("promotion_review_ready"),
            }
        else:
            manifest["promotion_packet"] = None
            manifest["lifecycle"] = None

        daily_payload = run_paper_tracking_daily(
            date(2026, 5, 2),
            repo_root=repo_root,
            tracking_root=art / "paper_tracking",
        )
        manifest["daily_tracking"] = {
            "run_date_utc": daily_payload.get("run_date_utc"),
            "processed_count": len(daily_payload.get("processed_tracking_ids") or []),
            "failure_count": daily_payload.get("failure_count"),
        }

        if not ns.skip_portfolio:
            summ = StrategyBatchRunSummary.model_validate(
                json.loads((run_dir / "batch_summary.json").read_text(encoding="utf-8"))
            )
            req = PortfolioAllocationRequest(
                batch_run_id=summ.run_id,
                capital=100_000.0,
                method=AllocationMethod.equal_weight,
            )
            alloc = simulate_portfolio_allocation(summ, run_dir=run_dir, request=req)
            out_alloc = run_dir / "portfolio_allocation_result.json"
            _write_json(out_alloc, alloc.model_dump(mode="json"))
            manifest["portfolio_allocation"] = {
                "artifact": str(out_alloc),
                "allocation_gate_status": alloc.allocation_gate_status.value,
                "digest": _digest_obj(alloc.model_dump(mode="json")),
            }
        else:
            manifest["portfolio_allocation"] = {"skipped": True}

        sroot = strategy_data_directory(repo_root)
        req = HistoricalDataRequest(
            provider_id="runtime_demo_provider",
            symbol="DEMO",
            timeframe="1d",
            start_utc=datetime(2026, 1, 2, tzinfo=timezone.utc),
            end_utc=datetime(2026, 2, 1, tzinfo=timezone.utc),
            as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )
        prov_m = ingest_provider_bars_to_snapshot(req, {}, output_root=sroot)
        prov_paths = sorted(sroot.rglob("*_manifest.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not prov_paths:
            stub = sroot / "provider_runtime_demo_manifest.json"
            _write_json(stub, prov_m.model_dump(mode="json"))
            prov_paths = [stub]
        manifest["provider_ingestion"] = {
            "provider_status": prov_m.provider_status.value,
            "pit_status": prov_m.pit_status.value,
            "manifest_path": str(prov_paths[0]) if prov_paths else None,
            "manifest_sha256": prov_m.manifest_sha256,
        }

        from strategy_validator.research_compute.gpu_probe import probe_gpu_capability

        probe = probe_gpu_capability()
        manifest["compute_probe"] = dict(probe) if isinstance(probe, dict) else {"raw": str(probe)}

        bench_script = repo_root / "scripts" / "benchmark_research_compute.py"
        if not ns.skip_benchmark and bench_script.is_file():
            try:
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(bench_script),
                        "--iterations",
                        "4000",
                        "--chunks",
                        "2",
                        "--json",
                    ],
                    cwd=str(repo_root),
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )
                manifest["compute_benchmark"] = {"ok": completed.returncode == 0, "exit_code": completed.returncode}
                if completed.returncode != 0:
                    manifest["warnings"].append(f"BENCHMARK_EXIT_{completed.returncode}")
            except Exception as exc:
                manifest["warnings"].append(f"BENCHMARK:{exc!s}")
                manifest["compute_benchmark"] = {"ok": False}
        else:
            manifest["compute_benchmark"] = {
                "skipped": True,
                "reason": "SKIP_FLAG" if ns.skip_benchmark else "SCRIPT_ABSENT_IN_CONTAINER",
            }

    except Exception as exc:
        manifest["ok"] = False
        manifest["blockers"].append(f"FATAL:{type(exc).__name__}:{exc}")
    finally:
        for k, v in preserved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    body_wo = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    manifest["manifest_sha256"] = _digest_obj(body_wo)
    manifest["digests"]["full_manifest_sha256"] = manifest["manifest_sha256"]

    out_path = research_os_runtime_manifest_path(repo_root)
    _write_json(out_path, manifest)

    payload = {"ok": bool(manifest.get("ok")), "manifest_path": str(out_path), "manifest": manifest}
    if ns.json:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(f"wrote {out_path}\n")
    return 0 if manifest.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
