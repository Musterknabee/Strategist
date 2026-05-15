#!/usr/bin/env python3
"""Oracle research cycle: backtest evidence → advisory briefing → theses → optional next batch."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _artifact_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    for candidate in (
        os.environ.get("STRATEGY_VALIDATOR_ARTIFACT_ROOT", ""),
        r"C:\var\lib\strategy-validator\artifacts",
        str(_REPO / "artifacts"),
    ):
        if candidate:
            p = Path(candidate).resolve()
            p.mkdir(parents=True, exist_ok=True)
            return p
    return (_REPO / "artifacts").resolve()


def _maybe_fetch_news(repo: Path, *, allow_network: bool) -> None:
    samples = repo / "artifacts" / "provider_samples"
    samples.mkdir(parents=True, exist_ok=True)
    if (samples / "newsapi").is_dir() and any((samples / "newsapi").glob("*.json")):
        print("news: using existing provider_samples/newsapi", flush=True)
        return
    if not allow_network:
        print("news: skipped (no samples; pass --allow-network to fetch NewsAPI)", flush=True)
        return
    cmd = [
        sys.executable,
        str(repo / "scripts" / "retrieve_provider_samples.py"),
        "--providers",
        "newsapi",
        "--output-dir",
        str(samples),
        "--manifest-json",
    ]
    print("news: fetching NewsAPI sample...", flush=True)
    proc = subprocess.run(cmd, cwd=repo, env=os.environ.copy())
    if proc.returncode != 0:
        print("news: fetch failed; Oracle will use batch-derived semantic sensors", flush=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifact-root", default=None)
    p.add_argument("--batch-summary", default=None, help="batch_summary.json (default: newest under artifact root)")
    p.add_argument("--allow-network", action="store_true", help="Fetch NewsAPI sample if missing")
    p.add_argument("--skip-thesis", action="store_true")
    p.add_argument("--run-next-batch", action="store_true", help="Run research_os next_batch_spec_proposed.json if present")
    p.add_argument("--json", action="store_true")
    ns = p.parse_args(argv)

    art = _artifact_root(ns.artifact_root)
    os.environ["STRATEGY_VALIDATOR_ARTIFACT_ROOT"] = str(art)
    os.environ["STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT"] = str(art / "strategy_runs")

    _maybe_fetch_news(_REPO, allow_network=ns.allow_network)

    from strategy_validator.application.oracle_evidence_bridge import (
        discover_latest_batch_summary,
        run_oracle_advisory_from_batch,
    )
    from strategy_validator.application.strategy_batch_loader import load_strategy_batch_spec
    from strategy_validator.contracts.strategy_batch import StrategyBatchRunSummary
    from strategy_validator.research.strategy_batch_runner import run_strategy_batch
    from strategy_validator.research.strategy_thesis_generator import generate_from_paths

    summary_path = Path(ns.batch_summary).resolve() if ns.batch_summary else discover_latest_batch_summary(art)
    summary = StrategyBatchRunSummary.model_validate(json.loads(summary_path.read_text(encoding="utf-8")))

    oracle_payload = run_oracle_advisory_from_batch(
        summary,
        artifact_root=art,
        repo_root=_REPO,
        provider_samples_dir=_REPO / "artifacts" / "provider_samples",
    )

    thesis_report = None
    if not ns.skip_thesis:
        thesis_report = generate_from_paths(strategy_run=summary_path, output_root=None)
        oracle_payload["thesis_generation"] = thesis_report.model_dump(mode="json")

    next_batch = art / "research_os_runtime" / "next_batch_spec_proposed.json"
    if ns.run_next_batch and next_batch.is_file():
        spec = load_strategy_batch_spec(next_batch)
        spec = spec.model_copy(update={"output_root": str(art / "strategy_runs")})
        next_summary = run_strategy_batch(
            spec,
            allow_synthetic=True,
            fail_fast=False,
            run_id="oracle-next-batch",
            overwrite=True,
        )
        oracle_payload["next_batch_run"] = {
            "batch_id": next_summary.batch_id,
            "run_id": next_summary.run_id,
            "passed_count": next_summary.passed_count,
            "strategy_count": next_summary.strategy_count,
            "output_dir": next_summary.output_dir,
        }

    try:
        from strategy_validator.application.operator_evidence_wiring import wire_all_operator_evidence_modules

        oracle_payload["satellite_wiring"] = wire_all_operator_evidence_modules(
            artifact_root=art,
            repo_root=_REPO,
            run_id="oracle-cycle",
            overwrite=True,
        )
    except Exception as exc:
        oracle_payload["satellite_wiring"] = {"ok": False, "error": str(exc)}

    manifest_path = art / "oracle_cycle" / "latest" / "oracle_research_cycle_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(oracle_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if ns.json:
        print(json.dumps(oracle_payload, indent=2, sort_keys=True), flush=True)
    else:
        print(f"Oracle cycle OK batch={summary.batch_id} run={summary.run_id}", flush=True)
        print(f"  fusion posture: {oracle_payload.get('fusion_posture')}", flush=True)
        print(f"  news source: {oracle_payload.get('news_semantic_source')}", flush=True)
        print(f"  manifest: {manifest_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
