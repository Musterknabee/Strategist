from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from strategy_validator.contracts.evidence import Evidence, EvidenceBundle, MetricProvenance
from strategy_validator.core.enums import PromotionState, BANK_STATE_RANKING, MetricSourceMode
from strategy_validator.core.config import TribunalThresholds
from strategy_validator.validator.robustness.cpcv import evaluate_cpcv_hook
from strategy_validator.validator.robustness.incrementality import IncrementalityResult
from strategy_validator.validator.robustness.statistics import estimate_dsr, estimate_pbo


@dataclass(frozen=True)
class RobustnessReport:
    """Consolidated robustness verification contract."""
    passed: bool
    folds: int | None
    path_coverage: float | None
    path_stability: float | None
    incrementality_p_value: float | None
    incrementality_coefficient: float | None
    incrementality_significant: bool | None
    dsr_estimate: float | None
    pbo_estimate: float | None
    provenance: List[MetricProvenance]
    evaluation_notes: List[str]
    suggested_state: PromotionState


class RobustnessEngine:
    """
    Orchestrates the Falsification Kernel and enforces constitutional 
    robustness gates.
    """
    def __init__(self, thresholds: TribunalThresholds | None = None):
        self.thresholds = thresholds or TribunalThresholds()

    def _get_worse_state(self, s1: PromotionState, s2: PromotionState) -> PromotionState:
        if BANK_STATE_RANKING[s1] >= BANK_STATE_RANKING[s2]:
            return s1
        return s2

    def evaluate(
        self, 
        evidence: Iterable[Evidence], 
        bundle: EvidenceBundle | None = None,
        search_breadth: int = 1,
        recompute_requested: bool = False
    ) -> RobustnessReport:
        notes: List[str] = []
        provenance: List[MetricProvenance] = []
        th = self.thresholds
        
        # 1. CPCV Evaluation
        cpcv_folds = None
        cpcv_passed = None
        cpcv_path_coverage = None
        cpcv_path_stability = None

        if bundle and bundle.cpcv_passed is not None and not recompute_requested:
            cpcv_folds = bundle.cpcv_folds
            cpcv_passed = bundle.cpcv_passed
            cpcv_path_coverage = bundle.cpcv_path_coverage
            cpcv_path_stability = bundle.cpcv_path_stability
            provenance.append(MetricProvenance(
                metric_name="cpcv_passed",
                source_mode=MetricSourceMode.PROVIDED,
                upstream_claim_present=True,
                provided_value=float(cpcv_passed),
                source_of_truth_used=MetricSourceMode.PROVIDED
            ))
        else:
            cpcv = evaluate_cpcv_hook(evidence)
            cpcv_folds = cpcv.folds
            cpcv_passed = cpcv.passed
            cpcv_path_coverage = cpcv.path_coverage
            cpcv_path_stability = cpcv.path_stability
            
            recompute_reason = "RECOMPUTE_REQUESTED" if recompute_requested else "MISSING_IN_BUNDLE"
            provenance.append(MetricProvenance(
                metric_name="cpcv_passed",
                source_mode=MetricSourceMode.RECOMPUTED,
                upstream_claim_present=bundle.cpcv_passed is not None if bundle else False,
                provided_value=float(bundle.cpcv_passed) if bundle and bundle.cpcv_passed is not None else None,
                recomputed_value=float(cpcv_passed) if cpcv_passed is not None else None,
                source_of_truth_used=MetricSourceMode.RECOMPUTED,
                recomputed_reason=recompute_reason
            ))

        coverage = cpcv_path_coverage if cpcv_path_coverage is not None else 0.0
        stability = cpcv_path_stability if cpcv_path_stability is not None else float('inf')
        
        # 2. Extract Incrementality
        inc_p_val, inc_coeff = None, None
        if bundle and bundle.incrementality_significant is not None and not recompute_requested:
            inc_p_val = bundle.incrementality_p_value
            inc_coeff = bundle.incrementality_coefficient
            provenance.append(MetricProvenance(
                metric_name="incrementality",
                source_mode=MetricSourceMode.PROVIDED,
                upstream_claim_present=True,
                provided_value=inc_p_val,
                source_of_truth_used=MetricSourceMode.PROVIDED
            ))
        else:
            for ev in evidence:
                if "incrementality_p_value" in ev.payload:
                    inc_p_val = float(ev.payload["incrementality_p_value"])
                    inc_coeff = float(ev.payload.get("incrementality_coefficient", 0.0))
                    break
            provenance.append(MetricProvenance(
                metric_name="incrementality",
                source_mode=MetricSourceMode.RECOMPUTED,
                upstream_claim_present=bundle.incrementality_significant is not None if bundle else False,
                provided_value=bundle.incrementality_p_value if bundle else None,
                recomputed_value=inc_p_val,
                source_of_truth_used=MetricSourceMode.RECOMPUTED,
                recomputed_reason="REFRESH_FROM_EVIDENCE"
            ))

        # 3. Dynamic Multiple Testing Adjustment (DSR/PBO)
        dsr_val, pbo_val = None, None
        
        # Task 2: Mutation-Law Stringency
        # If the strategy asserts success but omits supporting metadata, it is INVALID.
        
        # DSR Selection
        if bundle and bundle.dsr_estimate is not None and not recompute_requested:
            dsr_val = bundle.dsr_estimate
            provenance.append(MetricProvenance(
                metric_name="dsr_estimate",
                source_mode=MetricSourceMode.PROVIDED,
                upstream_claim_present=True,
                provided_value=dsr_val,
                source_of_truth_used=MetricSourceMode.PROVIDED
            ))
        else:
            observed_sharpe, sample_size = None, None
            for ev in evidence:
                if "observed_sharpe" in ev.payload: observed_sharpe = float(ev.payload["observed_sharpe"])
                if "sample_size" in ev.payload: sample_size = int(ev.payload["sample_size"])
                if "dsr_estimate" in ev.payload: dsr_val = float(ev.payload["dsr_estimate"])
            
            if dsr_val is None and observed_sharpe is not None and sample_size is not None:
                dsr_val = estimate_dsr(observed_sharpe=observed_sharpe, num_trials=search_breadth, sample_size=sample_size)
            
            provenance.append(MetricProvenance(
                metric_name="dsr_estimate",
                source_mode=MetricSourceMode.RECOMPUTED,
                upstream_claim_present=bundle.dsr_estimate is not None if bundle else False,
                provided_value=bundle.dsr_estimate if bundle else None,
                recomputed_value=dsr_val,
                source_of_truth_used=MetricSourceMode.RECOMPUTED,
                recomputed_reason="RECOMPUTE_FROM_TRIALS"
            ))

        # PBO Selection
        if bundle and bundle.pbo_estimate is not None and not recompute_requested:
            pbo_val = bundle.pbo_estimate
            provenance.append(MetricProvenance(
                metric_name="pbo_estimate",
                source_mode=MetricSourceMode.PROVIDED,
                upstream_claim_present=True,
                provided_value=pbo_val,
                source_of_truth_used=MetricSourceMode.PROVIDED
            ))
        else:
            train_sharpes, test_sharpes = None, None
            for ev in evidence:
                if "train_sharpes" in ev.payload: train_sharpes = [float(x) for x in ev.payload["train_sharpes"]]
                if "test_sharpes" in ev.payload: test_sharpes = [float(x) for x in ev.payload["test_sharpes"]]
                if "pbo_estimate" in ev.payload: pbo_val = float(ev.payload["pbo_estimate"])
            if train_sharpes and test_sharpes:
                pbo_val = estimate_pbo(train_sharpes=train_sharpes, test_sharpes=test_sharpes)
            
            provenance.append(MetricProvenance(
                metric_name="pbo_estimate",
                source_mode=MetricSourceMode.RECOMPUTED,
                upstream_claim_present=bundle.pbo_estimate is not None if bundle else False,
                provided_value=bundle.pbo_estimate if bundle else None,
                recomputed_value=pbo_val,
                source_of_truth_used=MetricSourceMode.RECOMPUTED,
                recomputed_reason="RECOMPUTE_FROM_FOLDS"
            ))

        # 4. Gating logic
        passed = True
        state = PromotionState.PROMOTABLE

        # Task 2: Mutation-Law Stringency
        # If the strategy asserts success but omits supporting metadata, it is INVALID.
        
        # CPCV Mutation Law
        if cpcv_passed is True:
            if cpcv_folds is None or coverage is None:
                notes.append("INVALID_CPCV_CLAIM: Success asserted without supporting folds/coverage.")
                state = self._get_worse_state(state, PromotionState.INVALID)
                passed = False
            elif cpcv_folds < 2:
                notes.append("INVALID_CPCV_CLAIM: CPCV requires at least 2 folds.")
                state = self._get_worse_state(state, PromotionState.INVALID)
                passed = False
        
        # Decoy Mutation Law (if we had decoy passed in this engine, but it's handled in orchestrator)
        # However, the engine should handle what it knows.
        
        # Standard Gating
        if cpcv_passed is False or (coverage is not None and coverage < th.min_path_coverage):
            passed = False
            notes.append(f"INSUFFICIENT_PATH_COVERAGE: {coverage:.2f} < {th.min_path_coverage}")
            state = self._get_worse_state(state, PromotionState.REJECTED)

        if stability > th.max_path_stability:
            passed = False
            notes.append(f"UNSTABLE_FOLD_OUTCOMES: Stability {stability:.2f} > {th.max_path_stability}")
            state = self._get_worse_state(state, PromotionState.QUARANTINED)

        inc_significant = None
        if inc_p_val is not None:
            inc_significant = inc_p_val <= th.max_nuisance_p_value
            if not inc_significant:
                passed = False
                notes.append(f"LACKS_ORTHOGONAL_INCREMENTALITY: p={inc_p_val:.4f} > {th.max_nuisance_p_value}")
                state = self._get_worse_state(state, PromotionState.REJECTED)
        else:
            notes.append("INCREMENTALITY_NOT_TESTED: No orthogonality evidence found.")
            state = self._get_worse_state(state, PromotionState.CANARY_ONLY)

        if dsr_val is not None:
            if dsr_val < th.min_deflated_sharpe_ratio:
                passed = False
                notes.append(f"INSUFFICIENT_DEFLATED_SHARPE: {dsr_val:.2f} < {th.min_deflated_sharpe_ratio}")
                state = self._get_worse_state(state, PromotionState.QUARANTINED)
        else:
            notes.append("MISSING_DSR: Robustness requires Deflated Sharpe Ratio.")
            state = self._get_worse_state(state, PromotionState.CONDITIONAL)
        
        if pbo_val is not None:
            if pbo_val > th.max_prob_overfit:
                passed = False
                notes.append(f"EXCESSIVE_OVERFIT_PROBABILITY: {pbo_val:.2f} > {th.max_prob_overfit}")
                state = self._get_worse_state(state, PromotionState.QUARANTINED)
        else:
            notes.append("MISSING_PBO: Robustness requires Probability of Overfitting.")
            state = self._get_worse_state(state, PromotionState.CONDITIONAL)

        if not cpcv_folds or cpcv_folds < 2:
            notes.append("INSUFFICIENT_FOLDS: Robustness claims require multi-fold validation.")
            state = self._get_worse_state(state, PromotionState.CONDITIONAL)

        return RobustnessReport(
            passed=passed,
            folds=cpcv_folds,
            path_coverage=coverage,
            path_stability=stability,
            incrementality_p_value=inc_p_val,
            incrementality_coefficient=inc_coeff,
            incrementality_significant=inc_significant,
            dsr_estimate=dsr_val,
            pbo_estimate=pbo_val,
            provenance=provenance,
            evaluation_notes=notes,
            suggested_state=state
        )
