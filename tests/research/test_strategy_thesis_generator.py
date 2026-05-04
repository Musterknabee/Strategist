from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.contracts.strategy_batch import (
    StrategyBatchRunManifest,
    StrategyBatchRunSummary,
    StrategyGateSummary,
    StrategyRunResult,
    StrategyRunStatus,
)
from strategy_validator.research.strategy_thesis_generator import (
    build_strategy_thesis_from_result,
    build_ui_strategy_thesis_generation_latest_payload,
    generate_strategy_theses,
)


def _summary() -> StrategyBatchRunSummary:
    result = StrategyRunResult(
        strategy_id="pv-breakout",
        strategy_type="trendline_volume_breakout",
        status=StrategyRunStatus.PASSED,
        data_plane="LOCAL_BARS",
        total_return=0.14,
        max_drawdown=-0.04,
        sharpe_like=1.2,
        bars_row_count=90,
        evidence_manifest_path="artifacts/strategy_runs/r1/pv/evidence_manifest.json",
        evidence_manifest_sha256="e" * 64,
        data_snapshot_manifest_path="artifacts/strategy_runs/r1/pv/data_snapshot_manifest.json",
        data_snapshot_manifest_sha256="d" * 64,
        robustness_evidence_sha256="r" * 64,
        execution_realism_digest="x" * 64,
        strategy_scorecard_path="artifacts/strategy_runs/r1/pv/scorecard.json",
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
    return StrategyBatchRunSummary(
        ok=True,
        batch_id="batch-1",
        run_id="run-1",
        output_dir="artifacts/strategy_runs/run-1",
        strategy_count=1,
        passed_count=1,
        strategies=[result],
        manifest=StrategyBatchRunManifest(
            batch_id="batch-1",
            run_id="run-1",
            spec_sha256="s" * 64,
            mode="paper",
            as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
            created_at_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
            output_dir="artifacts/strategy_runs/run-1",
            strategy_count=1,
            max_workers=1,
        ),
    )


def test_oracle_generator_builds_falsification_first_thesis() -> None:
    summary = _summary()
    thesis = build_strategy_thesis_from_result(
        result=summary.strategies[0],
        batch_summary=summary,
        now_utc=datetime(2026, 5, 2, tzinfo=timezone.utc),
    )

    assert thesis.author == "oracle_deterministic_thesis_generator"
    assert thesis.thesis_id == "oracle-generated:run-1:pv-breakout"
    assert "PIT" in thesis.hypothesis or "point-in-time" in thesis.hypothesis
    assert thesis.required_evidence
    assert any(c.criterion_id == "KILL_PROMOTION_INELIGIBLE" for c in thesis.falsification_criteria)
    assert thesis.thesis_sha256
    assert thesis.disclaimer.startswith("Research thesis only")


def test_oracle_generator_writes_generation_report_and_evaluations(tmp_path: Path) -> None:
    summary = _summary()
    report = generate_strategy_theses(
        batch_summary=summary,
        source_batch_summary_path=tmp_path / "batch_summary.json",
        output_root=tmp_path / "theses",
        evaluate=True,
        now_utc=datetime(2026, 5, 2, tzinfo=timezone.utc),
    )

    assert report.no_live_trading is True
    assert report.read_plane_only is True
    assert report.generated_count == 1
    assert report.evaluated_count == 1
    assert report.generated_theses[0].support_status.value == "SUPPORTED"
    assert report.generated_theses[0].candidate_mutations
    assert report.report_sha256
    assert (tmp_path / "theses" / "generated" / "run-1" / "pv-breakout" / "thesis.json").is_file()
    assert (tmp_path / "theses" / "latest" / "thesis_generation_report.json").is_file()


def test_ui_strategy_thesis_generation_latest_payload_reads_latest(tmp_path: Path, monkeypatch) -> None:
    summary = _summary()
    generate_strategy_theses(
        batch_summary=summary,
        source_batch_summary_path=tmp_path / "batch_summary.json",
        output_root=tmp_path / "theses",
        evaluate=False,
        now_utc=datetime(2026, 5, 2, tzinfo=timezone.utc),
    )
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_THESIS_ROOT", str(tmp_path / "theses"))

    payload = build_ui_strategy_thesis_generation_latest_payload()

    assert payload["schema_version"] == "ui_strategy_thesis_generation/v1"
    assert payload["read_plane_only"] is True
    assert payload["no_live_trading"] is True
    assert payload["degraded"] == []
    assert payload["latest_generation"]["generated_count"] == 1
