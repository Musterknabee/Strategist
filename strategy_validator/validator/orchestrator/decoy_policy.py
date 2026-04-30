"""Decoy-survival gate evaluation for the adjudication orchestrator."""

from __future__ import annotations

from dataclasses import dataclass

from strategy_validator.contracts.experiments import ExperimentManifest, GateResult
from strategy_validator.core.enums import BANK_STATE_RANKING, PromotionState


@dataclass(frozen=True)
class DecoyGateOutcome:
    """State, gate, and summary-note output from decoy survival evaluation."""

    state: PromotionState
    gate: GateResult
    summary_notes: tuple[str, ...]


def evaluate_decoy_survival_gate(
    experiment: ExperimentManifest,
    *,
    min_decoy_coverage: float,
    state: PromotionState,
) -> DecoyGateOutcome:
    """Evaluate decoy-survival bundle claims without mutating proposal state."""
    decoy_pass_claim = experiment.evidence_bundle.decoy_survival_passed
    decoy_cov = experiment.evidence_bundle.decoy_coverage
    summary_notes: list[str] = []

    if decoy_pass_claim is True:
        if decoy_cov is None:
            summary_notes.append("INVALID_DECOY_CLAIM: Decoy success asserted without supporting coverage.")
            return DecoyGateOutcome(
                state=_reconcile_states(state, PromotionState.INVALID),
                gate=GateResult(gate_name="DecoySurvival", passed=False, reason="INVALID_DECOY_CLAIM"),
                summary_notes=tuple(summary_notes),
            )
        if decoy_cov < min_decoy_coverage:
            return DecoyGateOutcome(
                state=_reconcile_states(state, PromotionState.REJECTED),
                gate=GateResult(gate_name="DecoySurvival", passed=False, reason="LOW_COVERAGE"),
                summary_notes=(),
            )
        return DecoyGateOutcome(
            state=state,
            gate=GateResult(gate_name="DecoySurvival", passed=True),
            summary_notes=(),
        )

    if decoy_pass_claim is False:
        return DecoyGateOutcome(
            state=_reconcile_states(state, PromotionState.REJECTED),
            gate=GateResult(gate_name="DecoySurvival", passed=False, reason="DECOY_FAILURE"),
            summary_notes=(),
        )

    return DecoyGateOutcome(
        state=_reconcile_states(state, PromotionState.CONDITIONAL),
        gate=GateResult(gate_name="DecoySurvival", passed=False, reason="DECOY_NOT_TESTED"),
        summary_notes=(),
    )


def _reconcile_states(current_state: PromotionState, new_restriction: PromotionState) -> PromotionState:
    if BANK_STATE_RANKING[new_restriction] > BANK_STATE_RANKING[current_state]:
        return new_restriction
    return current_state
