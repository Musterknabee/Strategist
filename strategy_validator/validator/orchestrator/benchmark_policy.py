"""Benchmark-performance gate evaluation for the adjudication orchestrator."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from strategy_validator.contracts.benchmarks import BENCHMARK_RUNG_REGISTRY
from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.experiments import ExperimentManifest, GateResult
from strategy_validator.core.enums import BANK_STATE_RANKING, PromotionState
from strategy_validator.validator.orchestrator.execution_realism import _benchmark_evidence_performance_typed


@dataclass(frozen=True)
class BenchmarkPerformanceGateOutcome:
    """State, gate, and typed report from benchmark-performance evaluation."""

    state: PromotionState
    gate: GateResult
    benchmark_report: Any | None


def evaluate_benchmark_performance_gate(
    experiment: ExperimentManifest,
    evidence: Iterable[Evidence],
    *,
    context_passed: bool,
    total_post_cost_bps: float,
    state: PromotionState,
) -> BenchmarkPerformanceGateOutcome:
    """Evaluate benchmark performance without mutating experiment state."""
    if not context_passed:
        return BenchmarkPerformanceGateOutcome(
            state=state,
            gate=GateResult(gate_name="BenchmarkSuccess", passed=False, reason="INVALID_CONTEXT"),
            benchmark_report=None,
        )

    report = _benchmark_evidence_performance_typed(experiment, evidence, total_post_cost_bps)
    gate = GateResult(
        gate_name="BenchmarkSuccess",
        passed=report.passed,
        metric_value=report.post_cost_excess_metric,
        threshold_value=BENCHMARK_RUNG_REGISTRY[experiment.evidence_bundle.benchmark_rung].minimum_delta,
    )
    if not report.passed:
        state = _reconcile_states(state, PromotionState.REJECTED)

    return BenchmarkPerformanceGateOutcome(state=state, gate=gate, benchmark_report=report)


def _reconcile_states(current_state: PromotionState, new_restriction: PromotionState) -> PromotionState:
    if BANK_STATE_RANKING[new_restriction] > BANK_STATE_RANKING[current_state]:
        return new_restriction
    return current_state
