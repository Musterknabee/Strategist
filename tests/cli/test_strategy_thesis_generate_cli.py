from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.cli.strategy_thesis import main
from strategy_validator.contracts.strategy_batch import (
    StrategyBatchRunManifest,
    StrategyBatchRunSummary,
    StrategyGateSummary,
    StrategyRunResult,
    StrategyRunStatus,
)


def _write_summary(path: Path) -> None:
    result = StrategyRunResult(
        strategy_id="ma-trend",
        strategy_type="moving_average_trend",
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
        batch_id="batch-cli",
        run_id="run-cli",
        output_dir="runs/run-cli",
        strategy_count=1,
        passed_count=1,
        strategies=[result],
        manifest=StrategyBatchRunManifest(
            batch_id="batch-cli",
            run_id="run-cli",
            spec_sha256="s" * 64,
            mode="paper",
            as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
            created_at_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
            output_dir="runs/run-cli",
            strategy_count=1,
            max_workers=1,
        ),
    )
    path.write_text(json.dumps(summary.model_dump(mode="json")), encoding="utf-8")


def test_strategy_thesis_generate_from_batch_cli(tmp_path: Path, capsys) -> None:
    summary_path = tmp_path / "batch_summary.json"
    _write_summary(summary_path)
    out = tmp_path / "theses"

    code = main([
        "generate-from-batch",
        "--strategy-run",
        str(summary_path),
        "--output-root",
        str(out),
        "--json",
    ])

    captured = json.loads(capsys.readouterr().out)
    assert code == 0
    assert captured["ok"] is True
    assert captured["no_live_trading"] is True
    assert captured["generation_report"]["generated_count"] == 1
    assert captured["generation_report"]["generated_theses"][0]["strategy_id"] == "ma-trend"
    assert (out / "generated" / "run-cli" / "ma-trend" / "thesis.json").is_file()
