"""
Anti-regression invariant tests — CI-grade constitutional law enforcement.

This module encodes the most load-bearing laws as fast, deterministic tests.
If any of these regress, the system's constitutional guarantees are broken.

These are NOT mutation tests.  They are targeted invariant tests that would
fail if someone weakens:
  - State severity ordering
  - PIT available_at legality
  - Benchmark invalid-context → INVALID
  - Midpoint-only rejection
  - Capacity hard cap
  - Borrow-required rejection
  - Mandatory PROMOTABLE metadata
  - Provided-vs-recomputed provenance law
  - Market-data provenance sealing
  - Ledger append-only integrity
  - No silent overwrite of PROVIDED evidence

Run as a fast CI gate:
    pytest tests/constitutional/test_anti_regression_invariants.py -v
Or select by marker:
    pytest -m invariant -v
"""
from datetime import datetime, timezone

import pytest

from strategy_validator.contracts.evidence import Evidence, EvidenceBundle, ReproducibilityManifest
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.market_data import LiquiditySnapshot, BorrowSnapshot
from strategy_validator.core.enums import EvidenceType, PromotionState, BANK_STATE_RANKING, MetricSourceMode
from strategy_validator.validator.market_data_feeds import SnapshotStore, SnapshotStoreLiquidityFeed, SnapshotStoreBorrowFeed
from strategy_validator.validator.orchestrator import adjudicate
from strategy_validator.validator.robustness.engine import RobustnessEngine


# -- Canonical fixtures ------------------------------------------------------

_EVAL_TIME = datetime(2026, 4, 12, tzinfo=timezone.utc)

def _repro() -> ReproducibilityManifest:
    return ReproducibilityManifest(
        code_hash="a" * 64, data_snapshot_hash="b" * 64,
        universe_hash="c" * 64, feature_graph_hash="d" * 64,
        parameter_manifest_hash="e" * 64, benchmark_version="bench-v1",
        cost_model_version="cost-v1", calendar_version="cal-v1",
    )

def _bundle(**kw) -> EvidenceBundle:
    d = dict(
        reproducibility=_repro(), benchmark_rung="L1", search_breadth=3,
        evaluation_time_utc=_EVAL_TIME,
        decoy_survival_passed=True, decoy_suite_version="decoy-v1", decoy_coverage=1.0,
        cpcv_passed=True, cpcv_folds=4, cpcv_path_coverage=1.0, cpcv_path_stability=0.1,
        incrementality_significant=True, incrementality_p_value=0.01,
        dsr_estimate=0.5, pbo_estimate=0.1,
        market_data_subject_id="INV-ASSET",
    )
    d.update(kw)
    return EvidenceBundle(**d)

def _ev(eid: str, **payload) -> Evidence:
    return Evidence(
        evidence_id=f"inv-{eid}-{len(payload)}", experiment_id=eid,
        evidence_type=EvidenceType.OUT_OF_SAMPLE_AUDIT,
        timestamp=_EVAL_TIME, payload=payload,
        source_module="anti_regression", checksum="f" * 64,
    )

def _manifest(eid: str, **bk) -> ExperimentManifest:
    return ExperimentManifest(
        experiment_id=eid, strategy_name="Invariant", version="1.0",
        proposer_id="invariant", evidence_bundle=_bundle(**bk),
    )

# ---------------------------------------------------------------------------
# LAW: State severity ordering is monotonic and immutable
# ---------------------------------------------------------------------------

@pytest.mark.invariant
class TestStateSeverityOrdering:
    """INVALID > REJECTED > QUARANTINED > CONDITIONAL > CANARY_ONLY > PROMOTABLE"""

    def test_invalid_is_worst(self):
        assert BANK_STATE_RANKING[PromotionState.INVALID] > BANK_STATE_RANKING[PromotionState.REJECTED]

    def test_rejected_worse_than_quarantined(self):
        assert BANK_STATE_RANKING[PromotionState.REJECTED] > BANK_STATE_RANKING[PromotionState.QUARANTINED]

    def test_quarantined_worse_than_conditional(self):
        assert BANK_STATE_RANKING[PromotionState.QUARANTINED] > BANK_STATE_RANKING[PromotionState.CONDITIONAL]

    def test_conditional_worse_than_canary(self):
        assert BANK_STATE_RANKING[PromotionState.CONDITIONAL] > BANK_STATE_RANKING[PromotionState.CANARY_ONLY]

    def test_canary_worse_than_promotable(self):
        assert BANK_STATE_RANKING[PromotionState.CANARY_ONLY] > BANK_STATE_RANKING[PromotionState.PROMOTABLE]


# ---------------------------------------------------------------------------
# LAW: PIT available_at legality — no future data inclusion
# ---------------------------------------------------------------------------

@pytest.mark.invariant
class TestPITAvailableAtLegality:
    """Future snapshots must never be selected for past evaluation times."""

    def test_future_liquidity_never_selected(self):
        future = datetime(2030, 1, 1, tzinfo=timezone.utc)
        past = datetime(2025, 1, 1, tzinfo=timezone.utc)
        snaps = [
            LiquiditySnapshot(
                asset_id="X", snapshot_time=future, adv_notional=1e8,
                source_id="future", source_mode="SNAPSHOT",
            ),
        ]
        feed = SnapshotStoreLiquidityFeed(SnapshotStore(liquidity=snaps))
        assert feed.lookup("X", past) is None

    def test_future_borrow_never_selected(self):
        future = datetime(2030, 1, 1, tzinfo=timezone.utc)
        past = datetime(2025, 1, 1, tzinfo=timezone.utc)
        snaps = [
            BorrowSnapshot(
                asset_id="X", snapshot_time=future,
                borrow_available=True, borrow_cost_bps=10.0,
                source_id="future", source_mode="SNAPSHOT",
            ),
        ]
        feed = SnapshotStoreBorrowFeed(SnapshotStore(borrow=snaps))
        assert feed.lookup("X", past) is None

    def test_most_recent_past_selected(self):
        t1 = datetime(2025, 1, 1, tzinfo=timezone.utc)
        t2 = datetime(2025, 6, 1, tzinfo=timezone.utc)
        t3 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        snaps = [
            LiquiditySnapshot(
                asset_id="X", snapshot_time=t1, adv_notional=1e7,
                source_id="feed", source_mode="SNAPSHOT",
            ),
            LiquiditySnapshot(
                asset_id="X", snapshot_time=t2, adv_notional=5e7,
                source_id="feed", source_mode="SNAPSHOT",
            ),
            LiquiditySnapshot(
                asset_id="X", snapshot_time=t3, adv_notional=1e9,
                source_id="feed", source_mode="SNAPSHOT",
            ),
        ]
        feed = SnapshotStoreLiquidityFeed(SnapshotStore(liquidity=snaps))
        # Lookup at t2.5 → should return t2 (most recent ≤ t2.5)
        mid = datetime(2025, 9, 1, tzinfo=timezone.utc)
        result = feed.lookup("X", mid)
        assert result is not None
        assert result.snapshot_time == t2
        assert result.adv_notional == 5e7


# ---------------------------------------------------------------------------
# LAW: Benchmark invalid-context → INVALID
# ---------------------------------------------------------------------------

@pytest.mark.invariant
class TestBenchmarkInvalidContext:
    """Unknown benchmark rung must force INVALID, not soft fallback."""

    def test_unknown_rung_forces_invalid(self):
        exp = _manifest("BAD-RUNG", benchmark_rung="NONEXISTENT-RUNG")
        state = adjudicate(exp, [_ev("BAD-RUNG", pit_integrity_ok=True)])
        assert state == PromotionState.INVALID


# ---------------------------------------------------------------------------
# LAW: Midpoint-only economics → never PROMOTABLE
# ---------------------------------------------------------------------------

@pytest.mark.invariant
class TestMidpointOnlyRejection:
    """Midpoint-only economics must be REJECTED or QUARANTINED, never PROMOTABLE."""

    def test_midpoint_only_not_promotable(self):
        exp = _manifest("MID-ONLY")
        state = adjudicate(exp, [_ev("MID-ONLY",
            economics_model="midpoint_only",
            benchmark_id="SPY", benchmark_version="bench-v1",
            benchmark_delta=0.10, benchmark_passed=True,
            pit_integrity_ok=True,
        )])
        assert state != PromotionState.PROMOTABLE
        dec = exp.promotion_history[-1]
        assert dec.execution_report.midpoint_only_flag is True


# ---------------------------------------------------------------------------
# LAW: Capacity hard cap — participation > 10% is fatal
# ---------------------------------------------------------------------------

@pytest.mark.invariant
class TestCapacityHardCap:
    """Participation rate above 10% must fail the capacity gate."""

    def test_excessive_participation_fails_capacity(self):
        exp = _manifest("CAP-FAIL")
        state = adjudicate(exp, [_ev("CAP-FAIL",
            benchmark_id="SPY", benchmark_version="bench-v1",
            benchmark_delta=0.10, benchmark_passed=True,
            estimated_participation_rate=0.50,
            pit_integrity_ok=True,
        )])
        assert state != PromotionState.PROMOTABLE
        dec = exp.promotion_history[-1]
        cap_gate = next(g for g in dec.gate_results if g.gate_name == "CapacityLimit")
        assert cap_gate.passed is False


# ---------------------------------------------------------------------------
# LAW: Borrow-required + unavailable → REJECTED
# ---------------------------------------------------------------------------

@pytest.mark.invariant
class TestBorrowRequiredRejection:
    """Short-required strategy with unavailable borrow must be REJECTED."""

    def test_short_required_unavailable_borrow_rejected(self):
        exp = _manifest("BRW-FAIL")
        state = adjudicate(exp, [_ev("BRW-FAIL",
            benchmark_id="SPY", benchmark_version="bench-v1",
            benchmark_delta=0.10, benchmark_passed=True,
            requires_shorting=True,
            borrow_available=False,
            pit_integrity_ok=True,
        )])
        assert state != PromotionState.PROMOTABLE
        dec = exp.promotion_history[-1]
        assert dec.execution_report.borrow.shortability_passed is False


# ---------------------------------------------------------------------------
# LAW: Mandatory PROMOTABLE metadata — no provenance-free promotion
# ---------------------------------------------------------------------------

@pytest.mark.invariant
class TestPromotableMetadataRequired:
    """Every PROMOTABLE decision carries market-data provenance."""

    def test_promotable_has_market_data_provenance(self):
        exp = _manifest("PROV-REQ")
        state = adjudicate(exp, [_ev("PROV-REQ",
            benchmark_id="SPY", benchmark_version="bench-v1",
            benchmark_delta=0.05, benchmark_passed=True,
            estimated_trade_notional=1000.0,
            pit_integrity_ok=True,
        )])
        assert state == PromotionState.PROMOTABLE
        dec = exp.promotion_history[-1]
        mdp = dec.execution_report.market_data_provenance
        assert mdp is not None
        assert mdp.evaluation_time_utc is not None
        assert mdp.liquidity_source_mode is not None
        assert mdp.borrow_source_mode is not None

    def test_promotable_has_decision_eval_time(self):
        exp = _manifest("PROV-TIME")
        adjudicate(exp, [_ev("PROV-TIME",
            benchmark_id="SPY", benchmark_version="bench-v1",
            benchmark_delta=0.05, benchmark_passed=True,
            estimated_trade_notional=1000.0,
            pit_integrity_ok=True,
        )])
        dec = exp.promotion_history[-1]
        assert dec.evaluation_time_utc is not None
        assert dec.market_data_subject_id is not None


# ---------------------------------------------------------------------------
# LAW: Provided-vs-recomputed provenance — no silent overwrite
# ---------------------------------------------------------------------------

@pytest.mark.invariant
class TestProvidedVsRecomputedLaw:
    """Provided evidence is authoritative by default. Recomputation only when explicit."""

    def test_provided_evidence_not_recomputed_by_default(self):
        bundle = _bundle(cpcv_passed=True, cpcv_folds=4, cpcv_path_coverage=0.95)
        engine = RobustnessEngine()
        report = engine.evaluate([], bundle=bundle, search_breadth=3, recompute_requested=False)
        cpcv_prov = [p for p in report.provenance if p.metric_name == "cpcv_passed"]
        assert len(cpcv_prov) == 1
        assert cpcv_prov[0].source_of_truth_used == MetricSourceMode.PROVIDED
        assert cpcv_prov[0].recomputed_value is None

    def test_recompute_requested_records_both_values(self):
        bundle = _bundle(cpcv_passed=True, cpcv_folds=4, cpcv_path_coverage=0.95)
        engine = RobustnessEngine()
        report = engine.evaluate([], bundle=bundle, search_breadth=3, recompute_requested=True)
        cpcv_prov = [p for p in report.provenance if p.metric_name == "cpcv_passed"]
        assert len(cpcv_prov) == 1
        assert cpcv_prov[0].source_of_truth_used == MetricSourceMode.RECOMPUTED
        assert cpcv_prov[0].recomputed_reason is not None


# ---------------------------------------------------------------------------
# LAW: Market-data provenance sealing
# ---------------------------------------------------------------------------

@pytest.mark.invariant
class TestMarketDataProvenanceSealing:
    """Every execution report seals market-data lookup provenance."""

    def test_execution_report_seals_snapshot_hashes(self):
        t = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        liq_snap = LiquiditySnapshot(
            asset_id="MSFT", snapshot_time=t, adv_notional=8e7, spread_bps=6.0,
            source_id="feed", source_mode="SNAPSHOT",
        )
        liq_feed = SnapshotStoreLiquidityFeed(SnapshotStore(liquidity=[liq_snap]))
        exp = _manifest("MD-SEAL", evaluation_time_utc=t, market_data_subject_id="MSFT")
        adjudicate(exp, [_ev("MD-SEAL",
            benchmark_id="SPY", benchmark_version="bench-v1",
            benchmark_delta=0.05, benchmark_passed=True,
            estimated_trade_notional=4e5,
            pit_integrity_ok=True,
        )], liquidity_feed=liq_feed)
        dec = exp.promotion_history[-1]
        mdp = dec.execution_report.market_data_provenance
        assert mdp.liquidity_snapshot_hash == liq_snap.snapshot_hash
        assert mdp.liquidity_source_mode == "SNAPSHOT"
        assert mdp.market_data_subject_id == "MSFT"
        assert mdp.evaluation_time_utc == t


# ---------------------------------------------------------------------------
# LAW: CPCV/decoy required metadata — asserted success without data → INVALID
# ---------------------------------------------------------------------------

@pytest.mark.invariant
class TestMetadataRequiredForClaims:
    """Asserted CPCV/decoy success without supporting metadata is INVALID."""

    def test_cpcv_pass_without_metadata_is_invalid(self):
        bundle = _bundle(cpcv_passed=True, cpcv_folds=None, cpcv_path_coverage=None)
        exp = _manifest("CPCV-INV", cpcv_passed=True, cpcv_folds=None, cpcv_path_coverage=None)
        state = adjudicate(exp, [_ev("CPCV-INV",
            benchmark_id="SPY", benchmark_version="bench-v1",
            benchmark_delta=0.05, benchmark_passed=True,
            pit_integrity_ok=True,
        )])
        assert state == PromotionState.INVALID

    def test_decoy_pass_without_suite_version_is_invalid(self):
        """Decoy success claim without suite_version is caught by ledger validation."""
        from strategy_validator.core.exceptions import LedgerPayloadViolation
        exp = _manifest("DECOY-INV", decoy_survival_passed=True, decoy_suite_version=None, decoy_coverage=1.0)
        with pytest.raises(LedgerPayloadViolation, match="PROMOTABLE writes require decoy_suite_version"):
            adjudicate(exp, [_ev("DECOY-INV",
                benchmark_id="SPY", benchmark_version="bench-v1",
                benchmark_delta=0.05, benchmark_passed=True,
                pit_integrity_ok=True,
            )])
