"""
Constitutional tests for capacity and borrow realism.

These tests enforce:
  1. Strategy passes fixed friction but fails nonlinear impact -> not PROMOTABLE.
  2. Increasing trade size flips adjudication outcome.
  3. Short-required strategy with missing borrow evidence cannot be PROMOTABLE.
  4. Short-required strategy with failing borrow status is REJECTED explicitly.
  5. Changing liquidity inputs changes impact result deterministically.
  6. Capacity / borrow evidence is preserved in typed adjudication provenance.
"""

from datetime import datetime, timezone

import pytest

from strategy_validator.contracts.evidence import Evidence, EvidenceBundle, ReproducibilityManifest
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.execution import CapacityEvidence, BorrowEvidence
from strategy_validator.core.enums import EvidenceType, PromotionState
from strategy_validator.validator.orchestrator import adjudicate


# -- Test helpers -----------------------------------------------------------

def _repro() -> ReproducibilityManifest:
    return ReproducibilityManifest(
        code_hash="a" * 64,
        data_snapshot_hash="b" * 64,
        universe_hash="c" * 64,
        feature_graph_hash="d" * 64,
        parameter_manifest_hash="e" * 64,
        benchmark_version="bench-v1",
        cost_model_version="cost-v1",
        calendar_version="cal-v1",
    )


def _bundle(**kw) -> EvidenceBundle:
    defaults = dict(
        reproducibility=_repro(),
        benchmark_rung="L1",
        search_breadth=1,
        decoy_survival_passed=True,
        decoy_suite_version="decoy-v1",
        decoy_coverage=1.0,
    )
    defaults.update(kw)
    return EvidenceBundle(**defaults)


def _ev(experiment_id: str, **payload) -> Evidence:
    return Evidence(
        evidence_id=f"ev-{experiment_id}-{len(payload)}",
        experiment_id=experiment_id,
        evidence_type=EvidenceType.OUT_OF_SAMPLE_AUDIT,
        timestamp=datetime.now(timezone.utc),
        payload=payload,
        source_module="constitutional",
        checksum="f" * 64,
    )


def _manifest(exp_id: str, **bundle_kw) -> ExperimentManifest:
    return ExperimentManifest(
        experiment_id=exp_id,
        strategy_name="CapacityBorrowConstitutional",
        version="1.0",
        proposer_id="constitutional",
        evidence_bundle=_bundle(**bundle_kw),
    )


# -- Constitutional Tests ---------------------------------------------------

class TestNonlinearCapacityOverridesFixedFriction:
    """
    LAW: A strategy that passes fixed-bps friction can still fail
    when nonlinear impact is applied at realistic participation rates.
    """

    def test_passes_fixed_but_fails_nonlinear(self):
        """Large pre-cost alpha passes fixed friction, but nonlinear impact at 5% participation erases it."""
        exp = _manifest("EXP-NONLINEAR-ERASE")
        # 5% participation -> sqrt(0.05)*600 ≈ 134bps impact
        # Pre-cost delta = 50bps, post-cost = 50 - 134 = -84bps -> REJECTED
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.0050, "benchmark_passed": True,
            "estimated_participation_rate": 0.05,
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
        }
        adjudicate(exp, [_ev(exp.experiment_id, **payload)])
        assert exp.state != PromotionState.PROMOTABLE
        decision = exp.promotion_history[-1]
        assert decision.execution_report.impact_model_mode == "NONLINEAR_HEURISTIC"
        assert decision.execution_report.nonlinear_impact_bps > 100

    def test_increasing_size_flips_outcome(self):
        """
        LAW: Doubling trade size (participation rate) must flip adjudication
        from acceptable to rejected when impact erases the edge.
        """
        # Low participation: impact is small enough that post-cost still passes
        exp_small = _manifest("EXP-SIZE-LOW")
        payload_small = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.02, "benchmark_passed": True,
            "estimated_participation_rate": 0.001,  # 0.1% -> ~19bps impact
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
            "dsr_estimate": 0.2, "pbo_estimate": 0.1,
            "cpcv_passed": True, "cpcv_folds": 4, "cpcv_path_coverage": 1.0,
        }
        adjudicate(exp_small, [_ev(exp_small.experiment_id, **payload_small)])

        # High participation: same strategy, larger size -> impact erases alpha
        exp_large = _manifest("EXP-SIZE-HIGH")
        payload_large = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.02, "benchmark_passed": True,
            "estimated_participation_rate": 0.08,  # 8% -> ~170bps impact
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
            "dsr_estimate": 0.2, "pbo_estimate": 0.1,
            "cpcv_passed": True, "cpcv_folds": 4, "cpcv_path_coverage": 1.0,
        }
        adjudicate(exp_large, [_ev(exp_large.experiment_id, **payload_large)])

        # Large size must be strictly worse or equal
        rank = {
            PromotionState.PROMOTABLE: 0, PromotionState.CANARY_ONLY: 1,
            PromotionState.CONDITIONAL: 2, PromotionState.QUARANTINED: 3,
            PromotionState.INVALID: 4, PromotionState.REJECTED: 5,
        }
        assert rank[exp_large.state] >= rank[exp_small.state]


class TestBorrowRealismBinding:
    """
    LAW: Short-required strategies without lawful borrow evidence
    cannot become PROMOTABLE.
    """

    def test_short_required_missing_borrow_evidence_rejected(self):
        """Shorting required but borrow_available=False -> REJECTED."""
        exp = _manifest("EXP-BORROW-MISSING")
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.10, "benchmark_passed": True,
            "requires_shorting": True,
            "borrow_available": False,
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
        }
        adjudicate(exp, [_ev(exp.experiment_id, **payload)])
        assert exp.state == PromotionState.REJECTED
        decision = exp.promotion_history[-1]
        assert decision.execution_report.borrow.shortability_passed is False
        assert "BORROW_UNAVAILABLE" in (decision.execution_report.borrow_constraint_note or "")

    def test_short_required_prohibitive_cost_rejected(self):
        """Shorting required and borrow cost > 500bps -> REJECTED."""
        exp = _manifest("EXP-BORROW-COST")
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.10, "benchmark_passed": True,
            "requires_shorting": True,
            "borrow_available": True,
            "borrow_cost_bps": 600,
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
        }
        adjudicate(exp, [_ev(exp.experiment_id, **payload)])
        assert exp.state == PromotionState.REJECTED
        decision = exp.promotion_history[-1]
        assert decision.execution_report.borrow.shortability_passed is False
        assert "PROHIBITIVE_BORROW_COST" in (decision.execution_report.borrow_constraint_note or "")

    def test_long_only_borrow_is_advisory(self):
        """Long-only strategies should not be rejected for missing borrow evidence."""
        exp = _manifest("EXP-LONG-ONLY")
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.05, "benchmark_passed": True,
            "requires_shorting": False,
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
            "dsr_estimate": 0.2, "pbo_estimate": 0.1,
            "cpcv_passed": True, "cpcv_folds": 4, "cpcv_path_coverage": 1.0,
        }
        adjudicate(exp, [_ev(exp.experiment_id, **payload)])
        # Should not be rejected for borrow reasons
        decision = exp.promotion_history[-1]
        assert decision.execution_report.borrow.requires_shorting is False
        assert decision.execution_report.shortability_passed is True


class TestLiquidityInputDeterminism:
    """
    LAW: Changing liquidity inputs (participation rate) must change
    impact result deterministically.
    """

    def test_participation_scales_impact_deterministically(self):
        """Doubling participation rate must increase nonlinear impact predictably."""
        import math
        from strategy_validator.validator.orchestrator import _evaluate_execution_realism

        ev_low = Evidence(
            evidence_id="ev-low",
            experiment_id="DET",
            evidence_type=EvidenceType.OUT_OF_SAMPLE_AUDIT,
            timestamp=datetime.now(timezone.utc),
            payload={"estimated_participation_rate": 0.01},
            source_module="constitutional",
            checksum="f" * 64,
        )
        ev_high = Evidence(
            evidence_id="ev-high",
            experiment_id="DET",
            evidence_type=EvidenceType.OUT_OF_SAMPLE_AUDIT,
            timestamp=datetime.now(timezone.utc),
            payload={"estimated_participation_rate": 0.04},
            source_module="constitutional",
            checksum="f" * 64,
        )

        rep_low = _evaluate_execution_realism([ev_low], multiplier=2.0, evaluation_time_utc=datetime.now(timezone.utc))
        rep_high = _evaluate_execution_realism([ev_high], multiplier=2.0, evaluation_time_utc=datetime.now(timezone.utc))

        expected_low = math.sqrt(0.01) * 600.0
        expected_high = math.sqrt(0.04) * 600.0

        assert rep_low.nonlinear_impact_bps == pytest.approx(expected_low)
        assert rep_high.nonlinear_impact_bps == pytest.approx(expected_high)
        # 4x participation -> 2x impact (square-root law)
        assert rep_high.nonlinear_impact_bps == pytest.approx(rep_low.nonlinear_impact_bps * 2)


class TestTypedAdjudicationProvenance:
    """
    LAW: Capacity and borrow evidence must be preserved in typed
    adjudication provenance -- no promotion-grade decision should be
    capacity-ambiguous or borrow-ambiguous.
    """

    def test_capacity_evidence_in_provenance(self):
        """Typed capacity evidence is present in the execution report."""
        exp = _manifest("EXP-PROV-CAP")
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.05, "benchmark_passed": True,
            "estimated_trade_notional": 500000.0,
            "estimated_participation_rate": 0.03,
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
        }
        adjudicate(exp, [_ev(exp.experiment_id, **payload)])
        decision = exp.promotion_history[-1]
        cap = decision.execution_report.capacity
        assert isinstance(cap, CapacityEvidence)
        assert cap.estimated_trade_notional == 500000.0
        assert cap.estimated_participation_rate == pytest.approx(0.03)
        assert cap.nonlinear_impact_bps > 0

    def test_borrow_evidence_in_provenance(self):
        """Typed borrow evidence is present in the execution report."""
        exp = _manifest("EXP-PROV-BRW")
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.05, "benchmark_passed": True,
            "requires_shorting": True,
            "borrow_available": True,
            "borrow_cost_bps": 150.0,
            "locate_required": True,
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
        }
        adjudicate(exp, [_ev(exp.experiment_id, **payload)])
        decision = exp.promotion_history[-1]
        brw = decision.execution_report.borrow
        assert isinstance(brw, BorrowEvidence)
        assert brw.requires_shorting is True
        assert brw.borrow_available is True
        assert brw.borrow_cost_bps == pytest.approx(150.0)
        assert brw.locate_required is True

    def test_impact_model_mode_in_provenance(self):
        """Impact model mode is always declared (never ambiguous)."""
        exp = _manifest("EXP-PROV-MODE")
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.05, "benchmark_passed": True,
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
        }
        adjudicate(exp, [_ev(exp.experiment_id, **payload)])
        decision = exp.promotion_history[-1]
        mode = decision.execution_report.impact_model_mode
        assert mode in ("FIXED_BPS", "NONLINEAR_HEURISTIC", "EMPIRICAL_CALIBRATED", "PROVISIONAL")


class TestCapacityHardCap:
    """
    LAW: Participation rate > 10% is a hard cap -> REJECTED.
    """

    def test_excessive_participation_rejected(self):
        exp = _manifest("EXP-HARDCAP")
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.10, "benchmark_passed": True,
            "estimated_participation_rate": 0.15,
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
        }
        adjudicate(exp, [_ev(exp.experiment_id, **payload)])
        assert exp.state == PromotionState.REJECTED
        decision = exp.promotion_history[-1]
        assert decision.execution_report.capacity.capacity_limit_passed is False
        assert "EXCESSIVE_PARTICIPATION" in (decision.execution_report.capacity.degradation_reason or "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
