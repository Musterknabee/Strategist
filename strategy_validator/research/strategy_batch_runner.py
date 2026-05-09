"""Concurrent strategy batch runner public facade.

The heavy data-loading, single-strategy execution, and batch orchestration logic
lives in phase modules. This facade preserves the historic import and monkeypatch
surface used by CLIs, tests, and downstream operator scripts.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.contracts.strategy_batch import (
    StrategyBatchRunSummary,
    StrategyBatchSpec,
    StrategyCandidateSpec,
    StrategyRunResult,
)
from strategy_validator.research.strategy_batch_evaluators import deterministic_prices
from strategy_validator.research.strategy_batch_runner_batch import run_strategy_batch_impl
from strategy_validator.research.strategy_batch_runner_single import run_single_strategy_impl


def run_single_strategy(
    *,
    candidate: StrategyCandidateSpec,
    batch: StrategyBatchSpec,
    run_id: str,
    run_dir: Path,
    allow_synthetic: bool,
    adjudication_hook: Any | None = None,
) -> StrategyRunResult:
    """Execute one strategy while preserving the legacy monkeypatch seam."""

    return run_single_strategy_impl(
        candidate=candidate,
        batch=batch,
        run_id=run_id,
        run_dir=run_dir,
        allow_synthetic=allow_synthetic,
        adjudication_hook=adjudication_hook,
        deterministic_prices_fn=deterministic_prices,
    )


def run_strategy_batch(
    spec: StrategyBatchSpec,
    *,
    allow_synthetic: bool = True,
    fail_fast: bool = False,
    adjudication_hook: Any | None = None,
    run_id: str | None = None,
    overwrite: bool = False,
) -> StrategyBatchRunSummary:
    """Run all strategies in *spec* concurrently; write manifests under output_root."""

    return run_strategy_batch_impl(
        spec,
        allow_synthetic=allow_synthetic,
        fail_fast=fail_fast,
        adjudication_hook=adjudication_hook,
        run_id=run_id,
        overwrite=overwrite,
        run_single_strategy_fn=run_single_strategy,
    )


__all__ = ["run_single_strategy", "run_strategy_batch", "deterministic_prices"]
