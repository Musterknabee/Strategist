"""Fixture-first provider-backed paper research loop (evidence only; no live trading)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.promotion_review_ops import build_promotion_review_packet
from strategy_validator.application.paper_research_replay import (
    build_replay_manifest,
    config_fingerprint_from_env,
    redact_command_args,
    verify_replay_manifest,
)
from strategy_validator.application.research_os_paths import artifact_root_directory
from strategy_validator.application.strategy_batch_loader import load_strategy_batch_spec
from strategy_validator.application.paper_tracking_ops import (
    append_daily_snapshot,
    assess_paper_tracking,
    enroll_strategies_from_batch_run,
    evaluate_paper_tracking,
    run_paper_tracking_daily,
)
from strategy_validator.application.ui_paper_tracking import discover_latest_paper_tracking
from strategy_validator.brokers.paper_broker_status_builder import (
    build_paper_broker_status_artifact,
    write_paper_broker_status_artifact,
)
from strategy_validator.cli.deployment_env_check import parse_env_file
from strategy_validator.contracts.provider_historical_snapshot import ProviderPaperLoopManifest
from strategy_validator.contracts.portfolio_allocation import AllocationMethod, PortfolioAllocationRequest
from strategy_validator.contracts.strategy_batch import StrategyBatchRunSummary
from strategy_validator.research.portfolio_allocation import simulate_portfolio_allocation
from strategy_validator.research.provider_historical_snapshot_ingest import run_provider_historical_ingest
from strategy_validator.research.strategy_batch_runner import run_strategy_batch


def _write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _digest_obj(obj: object) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def _merge_env(env_file: Path | None) -> dict[str, str]:
    base = {k: str(v) for k, v in os.environ.items()}
    if env_file is None:
        return base
    vals, _ = parse_env_file(env_file)
    return {**base, **vals}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifact-root", type=Path, default=None)
    p.add_argument("--run-id", default="provider-paper-demo")
    p.add_argument("--batch-spec", type=Path, default=None)
    p.add_argument("--fixture-provider-snapshot", type=Path, default=None)
    p.add_argument("--env-file", type=Path, default=None)
    p.add_argument("--provider", default="demo_provider")
    p.add_argument("--symbols", default="SPY,QQQ")
    p.add_argument("--timeframe", default="1d")
    p.add_argument("--start", default="2026-01-02")
    p.add_argument("--end", default="2026-02-15")
    p.add_argument("--as-of", default="2026-02-15T12:00:00Z")
    p.add_argument("--allow-network", action="store_true")
    p.add_argument("--allow-broker-network", action="store_true")
    p.add_argument("--skip-portfolio", action="store_true")
    p.add_argument("--overwrite", action="store_true")
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
    os.environ["STRATEGY_VALIDATOR_TEST_PAPER_CLOCK_DATE"] = "2026-02-15"

    env = _merge_env(ns.env_file)
    fixture = ns.fixture_provider_snapshot
    if fixture is None:
        fixture = repo_root / "tests" / "fixtures" / "provider_snapshots" / "demo_provider_bars_manifest.json"
    fixture = fixture.resolve()
    if not fixture.is_file():
        err = {"ok": False, "error": "MISSING_FIXTURE_MANIFEST", "path": str(fixture)}
        sys.stdout.write(json.dumps(err, indent=2) + "\n")
        return 2

    snap_root = art / "provider_historical_snapshots"
    sym_list = [s.strip() for s in ns.symbols.split(",") if s.strip()]
    run_ingest = run_provider_historical_ingest(
        provider_id=ns.provider,
        symbols=sym_list,
        timeframe=ns.timeframe,
        start_day=ns.start,
        end_day=ns.end,
        as_of_raw=ns.as_of,
        output_root=snap_root,
        env=env,
        no_network=not ns.allow_network,
        allow_network=bool(ns.allow_network),
        fixture_manifest=fixture,
        allow_best_effort_as_of=False,
    )

    batch_path = ns.batch_spec.resolve() if ns.batch_spec else (
        repo_root / "configs" / "strategy_batches" / "example_provider_snapshot_batch.json"
    ).resolve()
    if not batch_path.is_file():
        err = {"ok": False, "error": "MISSING_BATCH_SPEC", "path": str(batch_path)}
        sys.stdout.write(json.dumps(err, indent=2) + "\n")
        return 2

    manifest: dict[str, Any] = {
        "schema_version": "provider_paper_loop_manifest/v1",
        "ok": True,
        "run_id": ns.run_id.strip(),
        "generated_at_utc": datetime.now(timezone.utc),
        "artifact_root": str(art),
        "provider_snapshot": run_ingest.model_dump(mode="json"),
        "gauntlet_run": None,
        "paper_tracking": None,
        "lifecycle": None,
        "promotion_packet": None,
        "paper_broker": None,
        "daily_tracking": None,
        "portfolio": None,
        "artifact_descriptor": None,
        "replay_manifest_path": None,
        "replayable_offline": True,
        "paper_only": True,
        "live_trading_blocked": True,
        "warnings": [],
        "blockers": [],
        "digests": {},
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
        }
        manifest["digests"]["batch_summary_sha256"] = _digest_obj(
            json.loads((run_dir / "batch_summary.json").read_text(encoding="utf-8"))
        )

        enrolled = enroll_strategies_from_batch_run(
            run_dir,
            allow_synthetic_demo=True,
            repo_root=repo_root,
        )
        tids = [m.tracking_id for m in enrolled]
        manifest["paper_tracking"] = {"tracking_ids": tids, "count": len(tids)}

        obs = date(2026, 2, 15)
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
            manifest["promotion_packet"] = (
                (bundle or {}).get("promotion_review_packet_summary") if bundle else None
            )
            manifest["lifecycle"] = {
                "state": (bundle or {}).get("lifecycle_state"),
                "promotion_review_ready": (bundle or {}).get("promotion_review_ready"),
            }

        manifest["daily_tracking"] = run_paper_tracking_daily(
            date(2026, 2, 16),
            repo_root=repo_root,
            tracking_root=art / "paper_tracking",
        )

        broker_root = art / "paper_broker"
        b_art = build_paper_broker_status_artifact(env, allow_network=bool(ns.allow_broker_network))
        broker_path = write_paper_broker_status_artifact(broker_root, b_art)
        manifest["paper_broker"] = {"artifact_path": str(broker_path), "policy_status": b_art.policy_status}

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
            manifest["portfolio"] = {
                "artifact": str(out_alloc),
                "allocation_gate_status": alloc.allocation_gate_status.value,
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

    digest_body = json.loads(json.dumps(manifest, default=str))
    digest_body.pop("digests", None)
    manifest["digests"]["full_manifest_sha256"] = _digest_obj(digest_body)
    out_path = (art / "provider_paper_loop" / "latest" / "provider_paper_loop_manifest.json").resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(out_path, json.loads(json.dumps(manifest, default=str)))

    provider_mode = "SYNTHETIC" if not bool(ns.allow_network) else "KEYED"
    provider_name = ns.provider.strip() or "UNKNOWN"
    input_paths: list[tuple[str, Path]] = [
        ("batch_spec", batch_path),
        ("fixture_provider_snapshot", fixture),
    ]
    sample_manifest_env = env.get("STRATEGY_VALIDATOR_PROVIDER_SAMPLES_MANIFEST", "").strip()
    if sample_manifest_env:
        sample_path = Path(sample_manifest_env)
        if not sample_path.is_absolute():
            sample_path = (repo_root / sample_path).resolve()
        input_paths.append(("provider_samples_manifest", sample_path))
    run_dir = Path((manifest.get("gauntlet_run") or {}).get("output_dir", "")) if manifest.get("gauntlet_run") else None
    output_paths: list[tuple[str, Path]] = []
    if run_dir and run_dir.is_dir():
        output_paths.append(("batch_summary", run_dir / "batch_summary.json"))
        output_paths.append(("portfolio_allocation", run_dir / "portfolio_allocation_result.json"))
    if manifest.get("paper_broker"):
        output_paths.append(("paper_broker_status", Path(str(manifest["paper_broker"]["artifact_path"]))))
    replay_path = (art / "provider_paper_loop" / "latest" / "replay_manifest.json").resolve()
    replay_model = build_replay_manifest(
        repo_root=repo_root,
        artifact_id=ns.run_id.strip(),
        command="strategy-validator-provider-paper-loop",
        command_args_redacted=redact_command_args(argv or []),
        provider_id=provider_name,
        provider_name=provider_name,
        provider_mode=provider_mode,
        provider_key_required=bool(ns.allow_network),
        provider_key_present=bool(ns.allow_network),
        trust_banner="SYNTHETIC_FIXTURE_RESEARCH_ONLY" if provider_mode == "SYNTHETIC" else "UNKNOWN",
        license_usage_caveat="fixture_research_only" if provider_mode == "SYNTHETIC" else "provider_license_required",
        source_label="tests/fixtures/provider_snapshots",
        config_fingerprint=config_fingerprint_from_env(env),
        input_paths=input_paths,
        output_paths=output_paths,
        warnings=manifest.get("warnings", ()),
        blockers=manifest.get("blockers", ()),
    )
    _write_json(replay_path, json.loads(replay_model.model_dump_json()))
    replay_verify = verify_replay_manifest(replay_path, repo_root=repo_root).model_dump(mode="json")
    manifest["artifact_descriptor"] = {
        "schema_version": "paper_research_artifact_descriptor/v1",
        "artifact_id": ns.run_id.strip(),
        "artifact_kind": "provider_paper_loop",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": "strategy-validator-provider-paper-loop",
        "command_args_redacted": list(redact_command_args(argv or [])),
        "code_fingerprint": replay_model.code_fingerprint,
        "git_commit": replay_model.git_commit,
        "config_fingerprint": replay_model.config_fingerprint,
        "provider_id": replay_model.provider_id,
        "provider_name": replay_model.provider_name,
        "provider_mode": replay_model.provider_mode,
        "provider_key_required": replay_model.provider_key_required,
        "provider_key_present": replay_model.provider_key_present,
        "trust_banner": replay_model.trust_banner,
        "license_usage_caveat": replay_model.license_usage_caveat,
        "source_label": replay_model.source_label,
        "input_artifact_count": len(replay_model.input_artifacts),
        "output_artifact_count": len(replay_model.output_artifacts),
        "paper_only": True,
        "live_trading_blocked": True,
        "replayable_offline": True,
        "replay_manifest_path": str(replay_path),
        "replay_verification": replay_verify,
    }
    manifest["replay_manifest_path"] = str(replay_path)
    manifest["digests"]["replay_manifest_sha256"] = _digest_obj(json.loads(replay_model.model_dump_json()))
    digest_body = json.loads(json.dumps(manifest, default=str))
    digest_body.pop("digests", None)
    manifest["digests"]["full_manifest_sha256"] = _digest_obj(digest_body)
    try:
        loop = ProviderPaperLoopManifest.model_validate(manifest)
        _write_json(out_path, json.loads(loop.model_dump_json()))
    except Exception as exc:
        manifest["warnings"].append(f"LOOP_MANIFEST_VALIDATE:{type(exc).__name__}")
        _write_json(out_path, json.loads(json.dumps(manifest, default=str)))

    payload = {"ok": bool(manifest.get("ok")), "manifest_path": str(out_path), "manifest": manifest}
    if ns.json:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    else:
        sys.stdout.write(f"wrote {out_path}\n")
    return 0 if manifest.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
