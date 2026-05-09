from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.application.backtest_forensics_projection import (
    build_ui_backtest_forensics_detail_payload,
    build_ui_backtest_forensics_latest_payload,
)
from strategy_validator.contracts.strategy_batch import (
    StrategyBatchRunSummary,
    StrategyGateSummary,
    StrategyRunResult,
    StrategyRunStatus,
)


def _write_summary(root: Path) -> None:
    run_dir = root / "run-forensics"
    run_dir.mkdir(parents=True)
    summary = StrategyBatchRunSummary(
        ok=False,
        batch_id="batch-forensics",
        run_id="run-forensics",
        output_dir=str(run_dir),
        generated_at_utc=datetime(2026, 5, 5, tzinfo=timezone.utc),
        strategy_count=2,
        passed_count=1,
        paper_only_count=1,
        strategies=[
            StrategyRunResult(
                strategy_id="review-ready-provider",
                status=StrategyRunStatus.PASSED,
                data_plane="PROVIDER_SNAPSHOT",
                pit_status="OK",
                data_status="OK",
                evidence_manifest_path="evidence/review-ready.json",
                evidence_manifest_sha256="a" * 64,
                robustness_gate_status="PASS",
                cpcv_robustness_gate_status="PASS",
                execution_realism_gate="PASS",
                total_return=0.2,
                max_drawdown=-0.05,
                gate_summary=StrategyGateSummary(
                    pit_gate="PASS",
                    data_gate="PASS",
                    robustness_gate="PASS",
                    cpcv_robustness_gate="PASS",
                    execution_realism_gate="PASS",
                    promotion_eligible=True,
                ),
            ),
            StrategyRunResult(
                strategy_id="paper-only-synthetic",
                status=StrategyRunStatus.PAPER_ONLY,
                data_plane="SYNTHETIC",
                blockers=["MISSING_PROVIDER_SNAPSHOT"],
                warnings=["SYNTHETIC_DEMO_DATA"],
                gate_summary=StrategyGateSummary(
                    promotion_eligible=False,
                    promotion_blocked_reasons=["ROBUSTNESS_NOT_PROVEN"],
                ),
            ),
        ],
    )
    (run_dir / "batch_summary.json").write_text(json.dumps(summary.model_dump(mode="json"), indent=2), encoding="utf-8")


def test_backtest_forensics_projection_filters_by_review_posture(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = tmp_path / "strategy_runs"
    _write_summary(root)
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT", str(root))

    payload = build_ui_backtest_forensics_latest_payload(review_posture=("REVIEW_READY",), limit=10)

    assert payload["schema_version"] == "ui_backtest_forensics/v1"
    assert payload["read_plane_only"] is True
    assert payload["no_live_trading"] is True
    assert payload["total_strategy_count"] == 2
    assert payload["filtered_strategy_count"] == 1
    assert payload["returned_strategy_count"] == 1
    assert payload["strategies"][0]["strategy_id"] == "review-ready-provider"
    assert payload["filtered_summary"]["review_ready_count"] == 1
    assert payload["summary"]["paper_only_count"] == 1
    assert payload["filters"]["review_posture"] == ["REVIEW_READY"]
    assert "No strategy promotion" in " ".join(payload["guardrails"])


def test_backtest_forensics_projection_filters_by_risk_status_and_detail(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = tmp_path / "strategy_runs"
    _write_summary(root)
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT", str(root))

    risk_payload = build_ui_backtest_forensics_latest_payload(
        status=("PAPER_ONLY",),
        data_plane=("SYNTHETIC",),
        risk_flag=("SYNTHETIC_DATA_PAPER_ONLY",),
        blocker_contains="provider",
        limit=1,
    )
    detail_payload = build_ui_backtest_forensics_detail_payload("run-forensics", promotion_eligible=True)

    assert risk_payload["filtered_strategy_count"] == 1
    assert risk_payload["returned_strategy_count"] == 1
    assert risk_payload["strategies"][0]["strategy_id"] == "paper-only-synthetic"
    assert "SYNTHETIC_DATA_PAPER_ONLY" in risk_payload["strategies"][0]["risk_flags"]
    assert detail_payload["filtered_strategy_count"] == 1
    assert detail_payload["strategies"][0]["promotion_eligible"] is True
