"""Execution constraint gate evaluation for the adjudication orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from strategy_validator.contracts.experiments import GateResult
from strategy_validator.core.enums import BANK_STATE_RANKING, PromotionState


@dataclass(frozen=True)
class ExecutionConstraintGateOutcome:
    """State, gates, and summary notes from execution-constraint evaluation."""

    state: PromotionState
    gates: tuple[GateResult, ...]
    summary_notes: tuple[str, ...]


def evaluate_execution_constraint_gates(
    execution_report: Any,
    *,
    state: PromotionState,
) -> ExecutionConstraintGateOutcome:
    """Evaluate execution realism, stress, borrow, capacity, and midpoint gates.

    The orchestrator owns sequencing, experiment mutation, and ledger commits.
    This helper only translates an already-built execution realism report into
    gate results plus the most restrictive lawful state.
    """
    gates: list[GateResult] = [
        GateResult(
            gate_name="ExecutionRealism",
            passed=execution_report.passed,
            reason=execution_report.failure_reason,
        )
    ]
    summary_notes: list[str] = []

    if not execution_report.passed:
        state = _reconcile_states(state, PromotionState.REJECTED)

    stress_report = execution_report.stress_report
    if stress_report is not None:
        gates.append(
            GateResult(
                gate_name="ExecutionStressResilience",
                passed=stress_report.passed,
                reason=stress_report.failure_reason,
            )
        )
        if not stress_report.passed:
            stress_state = (
                PromotionState.INVALID
                if stress_report.failure_reason == "CRITICAL_LIQUIDITY_FAILURE"
                else PromotionState.REJECTED
            )
            state = _reconcile_states(state, stress_state)

    gates.append(
        GateResult(
            gate_name="ShortabilityBorrow",
            passed=execution_report.shortability_passed,
            reason=execution_report.borrow_constraint_note,
        )
    )
    if not execution_report.shortability_passed:
        state = _reconcile_states(state, PromotionState.REJECTED)

    gates.append(
        GateResult(
            gate_name="CapacityLimit",
            passed=execution_report.capacity.capacity_limit_passed,
            reason=execution_report.capacity.degradation_reason,
            metric_value=execution_report.capacity.estimated_participation_rate,
        )
    )
    if not execution_report.capacity.capacity_limit_passed:
        state = _reconcile_states(state, PromotionState.REJECTED)

    if execution_report.midpoint_only_flag:
        state = _reconcile_states(state, PromotionState.QUARANTINED)
        summary_notes.append("Advisory: Midpoint-only economics detected.")

    return ExecutionConstraintGateOutcome(
        state=state,
        gates=tuple(gates),
        summary_notes=tuple(summary_notes),
    )


def _reconcile_states(current_state: PromotionState, new_restriction: PromotionState) -> PromotionState:
    if BANK_STATE_RANKING[new_restriction] > BANK_STATE_RANKING[current_state]:
        return new_restriction
    return current_state
