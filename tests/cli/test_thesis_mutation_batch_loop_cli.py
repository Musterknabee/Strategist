from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.cli.thesis_mutation_batch_loop import main
from strategy_validator.contracts.strategy_batch import (
    StrategyBatchRunManifest,
    StrategyBatchRunSummary,
    StrategyCandidateSpec,
    StrategyGateSummary,
    StrategyRunResult,
    StrategyRunStatus,
)


def _write_run_tree(run: Path) -> Path:
    run.mkdir(parents=True)
    strat = "demo-momentum-1"
    (run / "strategies" / strat).mkdir(parents=True)
    cand = StrategyCandidateSpec(
        strategy_id=strat,
        strategy_type="momentum",
        universe="SYNTHETIC_DEMO_UNIVERSE",
        timeframe="1d",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        lookback_days=120,
        params={"signal_window": 20},
    )
    spec_body = cand.model_dump(mode="json")
    (run / "strategies" / strat / "input_manifest.json").write_text(
        json.dumps({"spec": spec_body, "input_spec_sha256": "a" * 64}, indent=2),
        encoding="utf-8",
    )
    manifest = StrategyBatchRunManifest(
        batch_id="batch-cli-loop",
        run_id="run-cli-loop",
        spec_sha256="b" * 64,
        mode="paper",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        created_at_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        output_dir=str(run.resolve()),
        strategy_count=1,
        max_workers=1,
    )
    (run / "batch_manifest.json").write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")

    result = StrategyRunResult(
        strategy_id=strat,
        strategy_type="momentum",
        status=StrategyRunStatus.PASSED,
        data_plane="LOCAL_BARS",
        total_return=0.08,
        max_drawdown=-0.03,
        sharpe_like=0.9,
        bars_row_count=80,
        evidence_manifest_path="evidence_manifest.json",
        evidence_manifest_sha256="e" * 64,
        robustness_evidence_sha256="r" * 64,
        execution_realism_digest="x" * 64,
        strategy_scorecard_path="scorecard.json",
        robustness_gate_status="PROVEN",
        market_data_integrity_gate_status="PROVEN",
        gate_summary=StrategyGateSummary(
            pit_gate="PIT_VERIFIED",
            data_gate="LOCAL_BARS",
            robustness_gate="PROVEN",
            execution_realism_gate="PROVEN",
            promotion_eligible=True,
        ),
    )
    summary = StrategyBatchRunSummary(
        ok=True,
        batch_id="batch-cli-loop",
        run_id="run-cli-loop",
        output_dir=str(run.resolve()),
        strategy_count=1,
        passed_count=1,
        strategies=[result],
        manifest=manifest,
    )
    summary_path = run.parent / "batch_summary.json"
    summary_path.write_text(json.dumps(summary.model_dump(mode="json"), indent=2), encoding="utf-8")
    return summary_path


def test_thesis_mutation_batch_loop_cli_writes_next_spec(tmp_path: Path) -> None:
    run = tmp_path / "run_dir"
    summary_path = _write_run_tree(run)
    next_spec = tmp_path / "next_batch.json"
    report_path = tmp_path / "loop_report.json"
    rc = main(
        [
            "--batch-summary",
            str(summary_path),
            "--next-batch-spec-output",
            str(next_spec),
            "--loop-report-output",
            str(report_path),
            "--json",
        ]
    )
    assert rc == 0
    assert next_spec.is_file()
    body = json.loads(next_spec.read_text(encoding="utf-8"))
    assert body["batch_id"].endswith("_mutation_next")
    assert report_path.is_file()
