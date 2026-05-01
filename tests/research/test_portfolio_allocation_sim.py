from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.contracts.portfolio_allocation import (
    AllocationGateStatus,
    AllocationMethod,
    PortfolioAllocationRequest,
)
from strategy_validator.contracts.strategy_batch import (
    StrategyBatchRunSummary,
    StrategyGateSummary,
    StrategyRunResult,
    StrategyRunStatus,
)
from strategy_validator.research.portfolio_allocation import simulate_portfolio_allocation


def _minimal_summary(run_dir: Path) -> StrategyBatchRunSummary:
    strat_dir = run_dir / "strategies" / "a1"
    strat_dir.mkdir(parents=True)
    sc = {
        "schema_version": "strategy_scorecard/v2",
        "strategy_id": "a1",
        "batch_id": "b",
        "run_id": "r1",
        "volatility": 0.2,
        "max_drawdown": 0.1,
        "score": 0.5,
        "pit_status": "PIT_VERIFIED",
    }
    (strat_dir / "strategy_scorecard.json").write_text(json.dumps(sc), encoding="utf-8")
    row = StrategyRunResult(
        strategy_id="a1",
        status=StrategyRunStatus.PASSED,
        gate_summary=StrategyGateSummary(data_gate="LOCAL_BARS"),
    )
    return StrategyBatchRunSummary(
        ok=True,
        batch_id="b",
        run_id="r1",
        output_dir=str(run_dir),
        strategy_count=1,
        strategies=[row],
    )


def test_equal_weight_deterministic(tmp_path: Path) -> None:
    run_dir = tmp_path / "out"
    run_dir.mkdir()
    summary = _minimal_summary(run_dir)
    req = PortfolioAllocationRequest(batch_run_id="r1", capital=100_000, method=AllocationMethod.equal_weight)
    a = simulate_portfolio_allocation(summary, run_dir=run_dir, request=req)
    b = simulate_portfolio_allocation(summary, run_dir=run_dir, request=req)
    assert a.allocations[0].weight == pytest.approx(1.0)
    assert a.evidence_digest == b.evidence_digest
    assert a.allocation_gate_status == AllocationGateStatus.ALLOCATABLE


def test_synthetic_excluded(tmp_path: Path) -> None:
    run_dir = tmp_path / "out"
    run_dir.mkdir()
    strat_dir = run_dir / "strategies" / "syn"
    strat_dir.mkdir(parents=True)
    sc = {
        "schema_version": "strategy_scorecard/v2",
        "strategy_id": "syn",
        "pit_status": "SYNTHETIC_DEMO",
        "volatility": 0.1,
        "score": 1.0,
    }
    (strat_dir / "strategy_scorecard.json").write_text(json.dumps(sc), encoding="utf-8")
    summary = StrategyBatchRunSummary(
        ok=True,
        batch_id="b",
        run_id="r1",
        output_dir=str(run_dir),
        strategy_count=1,
        strategies=[
            StrategyRunResult(strategy_id="syn", status=StrategyRunStatus.PASSED, gate_summary=StrategyGateSummary())
        ],
    )
    req = PortfolioAllocationRequest(batch_run_id="r1", capital=1.0, method=AllocationMethod.equal_weight)
    res = simulate_portfolio_allocation(summary, run_dir=run_dir, request=req)
    assert res.allocation_gate_status == AllocationGateStatus.NOT_APPLICABLE
