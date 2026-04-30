"""Robustness gate evaluation for the adjudication orchestrator."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.experiments import ExperimentManifest, GateResult
from strategy_validator.core.enums import BANK_STATE_RANKING, MetricSourceMode, PromotionState


@dataclass(frozen=True)
class RobustnessGateOutcome:
    """State, gate, and summary-note output from robustness evaluation."""

    state: PromotionState
    gate: GateResult
    summary_notes: tuple[str, ...]


def evaluate_robustness_gate(
    experiment: ExperimentManifest,
    evidence: Iterable[Evidence],
    *,
    thresholds: object,
    state: PromotionState,
) -> RobustnessGateOutcome:
    """Evaluate robustness evidence and sync recomputed metrics only when explicit."""
    # Deliberately lazy: importing the robustness package pulls statsmodels/scipy.
    # Keep orchestrator import/startup light; pay this cost only when adjudication
    # actually evaluates robustness gates.
    from strategy_validator.validator.robustness import RobustnessEngine

    engine = RobustnessEngine(thresholds=thresholds)
    report = engine.evaluate(
        evidence,
        bundle=experiment.evidence_bundle,
        search_breadth=experiment.evidence_bundle.search_breadth,
        recompute_requested=False,
    )

    experiment.evidence_bundle.robustness_provenance = report.provenance
    for provenance in report.provenance:
        if provenance.source_of_truth_used != MetricSourceMode.RECOMPUTED:
            continue
        if provenance.metric_name == "cpcv_passed":
            experiment.evidence_bundle.cpcv_folds = report.folds
            experiment.evidence_bundle.cpcv_passed = report.passed if report.folds is not None else None
            experiment.evidence_bundle.cpcv_path_coverage = report.path_coverage
            experiment.evidence_bundle.cpcv_path_stability = report.path_stability
        elif provenance.metric_name == "incrementality":
            experiment.evidence_bundle.incrementality_significant = report.incrementality_significant
            experiment.evidence_bundle.incrementality_p_value = report.incrementality_p_value
        elif provenance.metric_name == "dsr_estimate":
            if report.dsr_estimate is not None:
                experiment.evidence_bundle.dsr_estimate = report.dsr_estimate
        elif provenance.metric_name == "pbo_estimate":
            if report.pbo_estimate is not None:
                experiment.evidence_bundle.pbo_estimate = report.pbo_estimate

    gate = GateResult(
        gate_name="RobustnessAudit",
        passed=report.passed,
        note="; ".join(report.evaluation_notes),
    )
    return RobustnessGateOutcome(
        state=_reconcile_states(state, report.suggested_state),
        gate=gate,
        summary_notes=tuple(report.evaluation_notes),
    )


def _reconcile_states(current_state: PromotionState, new_restriction: PromotionState) -> PromotionState:
    if BANK_STATE_RANKING[new_restriction] > BANK_STATE_RANKING[current_state]:
        return new_restriction
    return current_state
