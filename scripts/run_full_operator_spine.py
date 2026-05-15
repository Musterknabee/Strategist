#!/usr/bin/env python3
"""Run all example strategy batches + provider loop + runtime demo + operator run (host / venv)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_BATCH_DIR = _REPO / "configs" / "strategy_batches"
_BATCHES = [
    "example_batch.json",
    "example_gauntlet_batch.json",
    "example_local_bars_batch.json",
    "example_mean_reversion_batch.json",
    "example_market_structure_batch.json",
    "example_candlestick_volume_batch.json",
    "example_price_volume_batch.json",
    "example_chart_pattern_batch.json",
    "example_advanced_technical_batch.json",
    "example_provider_snapshot_batch.json",
]


def _artifact_root() -> Path:
    for candidate in (
        Path(os.environ.get("STRATEGY_VALIDATOR_ARTIFACT_ROOT", "")),
        Path(r"C:\var\lib\strategy-validator\artifacts"),
        _REPO / "artifacts",
    ):
        if str(candidate) and candidate.is_absolute():
            root = candidate.resolve()
            if root.exists() or candidate == _REPO / "artifacts":
                root.mkdir(parents=True, exist_ok=True)
                return root
    root = (_REPO / "artifacts").resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _run(label: str, args: list[str]) -> int:
    print(f"\n=== {label} ===", flush=True)
    env = os.environ.copy()
    art = _artifact_root()
    env["STRATEGY_VALIDATOR_ARTIFACT_ROOT"] = str(art)
    env["STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT"] = str(art / "strategy_runs")
    env["STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT"] = str(art / "paper_tracking")
    cmd = [sys.executable, "-m", f"strategy_validator.cli.{args[0]}", *args[1:]]
    proc = subprocess.run(cmd, cwd=_REPO, env=env)
    if proc.returncode != 0:
        print(f"WARN: {label} exited {proc.returncode}", flush=True)
    return proc.returncode


def main() -> int:
    os.chdir(_REPO)
    art = _artifact_root()
    print(f"artifact_root={art}", flush=True)
    failures: list[str] = []

    for name in _BATCHES:
        run_id = "full-" + name.replace("example_", "").replace(".json", "")
        code = _run(
            f"batch {name}",
            [
                "strategy_batch_run",
                "--batch",
                str(_BATCH_DIR / name),
                "--output-root",
                str(art / "strategy_runs"),
                "--run-id",
                run_id,
                "--overwrite",
                "--json",
            ],
        )
        if code != 0:
            failures.append(f"batch:{name}")

    fixture = _REPO / "tests" / "fixtures" / "provider_snapshots" / "demo_provider_bars_manifest.json"
    code = _run(
        "provider paper loop",
        [
            "provider_paper_loop",
            "--artifact-root",
            str(art),
            "--run-id",
            "full-provider-paper",
            "--fixture-provider-snapshot",
            str(fixture),
            "--batch-spec",
            str(_BATCH_DIR / "example_provider_snapshot_batch.json"),
            "--allow-network",
            "--allow-broker-network",
            "--overwrite",
            "--json",
        ],
    )
    if code != 0:
        failures.append("provider-paper-loop")

    _run(
        "paper broker",
        [
            "paper_broker",
            "status",
            "--output-root",
            str(art / "paper_broker"),
            "--allow-network",
            "--json",
        ],
    )

    code = _run(
        "runtime demo",
        [
            "research_os_runtime_demo",
            "--artifact-root",
            str(art),
            "--run-id",
            "full-runtime",
            "--batch-spec",
            str(_BATCH_DIR / "example_gauntlet_batch.json"),
            "--full-research-os-cycle",
            "--allow-synthetic-demo",
            "--overwrite",
            "--skip-benchmark",
            "--json",
        ],
    )
    if code != 0:
        failures.append("runtime-demo")

    print("\n=== wire satellite evidence modules ===", flush=True)
    try:
        from strategy_validator.application.operator_evidence_wiring import wire_all_operator_evidence_modules

        wire_report = wire_all_operator_evidence_modules(
            artifact_root=art,
            repo_root=_REPO,
            run_id="full-operator",
            overwrite=True,
        )
        if wire_report.get("warnings"):
            print(f"  warnings: {len(wire_report['warnings'])}", flush=True)
        if not wire_report.get("ok", True):
            failures.append("operator-evidence-wiring")
    except Exception as exc:
        print(f"WARN: operator evidence wiring: {exc}", flush=True)
        failures.append("operator-evidence-wiring")

    print("\n=== oracle research cycle ===", flush=True)
    oc_env = os.environ.copy()
    oc_env["STRATEGY_VALIDATOR_ARTIFACT_ROOT"] = str(art)
    oc_env["STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT"] = str(art / "strategy_runs")
    try:
        oc = subprocess.run(
            [sys.executable, str(_REPO / "scripts" / "run_oracle_research_cycle.py"), "--run-next-batch", "--json"],
            cwd=_REPO,
            env=oc_env,
        )
        if oc.returncode != 0:
            failures.append("oracle-cycle")
    except Exception as exc:
        print(f"WARN: oracle cycle: {exc}", flush=True)
        failures.append("oracle-cycle")

    code = _run(
        "operator run",
        [
            "research_os_operator_run",
            "run",
            "--artifact-root",
            str(art),
            "--repo-root",
            str(_REPO),
            "--run-id",
            "full-operator",
            "--overwrite",
            "--json",
        ],
    )
    if code != 0:
        failures.append("operator-run")

    summary = {"artifact_root": str(art), "failures": failures}
    print(json.dumps(summary, indent=2), flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
