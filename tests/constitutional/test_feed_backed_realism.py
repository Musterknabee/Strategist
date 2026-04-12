"""
Constitutional tests for feed-backed market-data snapshot realism.

These tests prove:
  1. PIT liquidity lookup uses decision/evaluation timestamp, not wall-clock now().
  2. PIT borrow lookup uses decision/evaluation timestamp, not wall-clock now().
  3. Changing decision timestamp changes selected snapshot lawfully.
  4. Changing subject/asset identity changes selected snapshot lawfully.
  5. No hardcoded "portfolio" dependency remains in adjudication path.
  6. PROVISIONAL payload values cannot masquerade as SNAPSHOT/LIVE.
  7. Short-required strategy using only PROVISIONAL borrow input degrades honestly.
  8. Promotion-grade decision preserves typed liquidity and borrow source provenance.
  9. Identical snapshots produce identical provenance fingerprints.
 10. Provided robustness evidence is not silently overwritten.
 11. Explicit recomputation persists typed provenance correctly.
 12. Promotion-grade decision preserves typed market-data timestamp and subject provenance.
"""
from datetime import datetime, timezone, timedelta

import pytest

from strategy_validator.contracts.evidence import Evidence, EvidenceBundle, ReproducibilityManifest, MetricProvenance
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.market_data import LiquiditySnapshot, BorrowSnapshot, SourceMode
from strategy_validator.contracts.execution import CapacityEvidence, BorrowEvidence, MarketDataProvenance
from strategy_validator.core.enums import EvidenceType, PromotionState, MetricSourceMode
from strategy_validator.validator.market_data_feeds import (
    SnapshotStore,
    SnapshotStoreLiquidityFeed,
    SnapshotStoreBorrowFeed,
    ProvisionalLiquidityFeed,
    ProvisionalBorrowFeed,
)
from strategy_validator.validator.orchestrator import adjudicate, _evaluate_execution_realism
from strategy_validator.validator.robustness.engine import RobustnessEngine


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
        search_breadth=3,
        decoy_survival_passed=True,
        decoy_suite_version="decoy-v1",
        decoy_coverage=1.0,
        cpcv_path_stability=0.1,
        dsr_estimate=0.5,
        pbo_estimate=0.1,
        market_data_subject_id="portfolio",
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
        strategy_name="FeedBackedRealism",
        version="1.0",
        proposer_id="constitutional",
        evidence_bundle=_bundle(**bundle_kw),
    )


# -- PIT liquidity lookup tests ---------------------------------------------

class TestPITLiquidityLookup:
    """
    LAW: PIT liquidity lookup returns the most recent snapshot at or
    before the decision time.
    """

    def test_pit_liquidity_returns_lawful_snapshot(self):
        """The feed returns the snapshot at or before the lookup time."""
        now = datetime.now(timezone.utc)
        t1 = now - timedelta(hours=2)
        t2 = now - timedelta(hours=1)
        t3 = now + timedelta(hours=1)  # future — should not be returned

        snaps = [
            LiquiditySnapshot(
                asset_id="portfolio", snapshot_time=t1,
                adv_notional=50_000_000, spread_bps=10.0,
                source_id="mock_adv_feed", source_mode="SNAPSHOT",
            ),
            LiquiditySnapshot(
                asset_id="portfolio", snapshot_time=t2,
                adv_notional=100_000_000, spread_bps=8.0,
                source_id="mock_adv_feed", source_mode="SNAPSHOT",
            ),
            LiquiditySnapshot(
                asset_id="portfolio", snapshot_time=t3,
                adv_notional=1_000_000, spread_bps=50.0,
                source_id="mock_adv_feed", source_mode="SNAPSHOT",
            ),
        ]
        store = SnapshotStore(liquidity=snaps)
        feed = SnapshotStoreLiquidityFeed(store)

        # Lookup at "now" should return t2 (most recent <= now)
        result = feed.lookup("portfolio", now)
        assert result is not None
        assert result.snapshot_time == t2
        assert result.adv_notional == 100_000_000
        assert result.source_mode == "SNAPSHOT"

    def test_pit_liquidity_no_future_snapshot(self):
        """A future-only snapshot is never returned for a past lookup time."""
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        snap = LiquiditySnapshot(
            asset_id="portfolio", snapshot_time=future,
            adv_notional=10_000_000,
            source_id="future_feed", source_mode="SNAPSHOT",
        )
        store = SnapshotStore(liquidity=[snap])
        feed = SnapshotStoreLiquidityFeed(store)
        result = feed.lookup("portfolio", datetime.now(timezone.utc))
        assert result is None


# -- PIT borrow lookup tests ------------------------------------------------

class TestPITBorrowLookup:
    """
    LAW: PIT borrow lookup returns the most recent snapshot at or before
    the decision time.
    """

    def test_pit_borrow_returns_lawful_snapshot(self):
        now = datetime.now(timezone.utc)
        t1 = now - timedelta(hours=3)
        t2 = now - timedelta(hours=1)

        snaps = [
            BorrowSnapshot(
                asset_id="portfolio", snapshot_time=t1,
                borrow_available=True, borrow_cost_bps=100.0,
                source_id="mock_borrow_feed", source_mode="SNAPSHOT",
            ),
            BorrowSnapshot(
                asset_id="portfolio", snapshot_time=t2,
                borrow_available=False, borrow_cost_bps=800.0,
                locate_required=True,
                source_id="mock_borrow_feed", source_mode="SNAPSHOT",
            ),
        ]
        store = SnapshotStore(borrow=snaps)
        feed = SnapshotStoreBorrowFeed(store)

        result = feed.lookup("portfolio", now)
        assert result is not None
        assert result.snapshot_time == t2
        assert result.borrow_available is False
        assert result.borrow_cost_bps == 800.0
        assert result.source_mode == "SNAPSHOT"


# -- Snapshot-driven adjudication determinism --------------------------------

class TestSnapshotDrivenAdjudication:
    """
    LAW: Changing snapshot inputs changes adjudication deterministically.
    """

    def test_feed_liquidity_overrides_payload(self):
        """
        Feed-backed ADV overrides payload-asserted participation rate.
        Strategy that would pass with low payload participation fails
        when feed-backed ADV reveals higher true participation.
        """
        exp = _manifest("EXP-FEED-LIQ-OVERRIDE")
        # Payload claims $1M trade notional at 1% participation (100M ADV implied)
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.10, "benchmark_passed": True,
            "estimated_trade_notional": 1_000_000.0,
            "estimated_participation_rate": 0.01,  # 1% -> ~60bps impact, passes
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
        }

        # Feed says ADV is only $2M → true participation = 50% → fatal
        now = datetime.now(timezone.utc)
        liq_snap = LiquiditySnapshot(
            asset_id="portfolio", snapshot_time=now,
            adv_notional=2_000_000.0,
            source_id="truth_feed", source_mode="SNAPSHOT",
        )
        liq_feed = SnapshotStoreLiquidityFeed(SnapshotStore(liquidity=[liq_snap]))

        adjudicate(exp, [_ev(exp.experiment_id, **payload)], liquidity_feed=liq_feed)
        assert exp.state == PromotionState.REJECTED
        decision = exp.promotion_history[-1]
        # Feed overrode participation to 50% (1M/2M), capped at 10% → hard cap
        assert decision.execution_report.capacity.capacity_limit_passed is False

    def test_feed_borrow_overrides_payload(self):
        """
        Feed-backed borrow data overrides optimistic payload assertions.
        """
        exp = _manifest("EXP-FEED-BRW-OVERRIDE")
        # Payload claims borrow is available at low cost
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.10, "benchmark_passed": True,
            "requires_shorting": True,
            "borrow_available": True,
            "borrow_cost_bps": 50.0,  # optimistic
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
        }

        # Feed truth: borrow is unavailable
        now = datetime.now(timezone.utc)
        brw_snap = BorrowSnapshot(
            asset_id="portfolio", snapshot_time=now,
            borrow_available=False, borrow_cost_bps=999.0,
            source_id="truth_borrow_feed", source_mode="SNAPSHOT",
        )
        brw_feed = SnapshotStoreBorrowFeed(SnapshotStore(borrow=[brw_snap]))

        adjudicate(exp, [_ev(exp.experiment_id, **payload)], borrow_feed=brw_feed)
        assert exp.state == PromotionState.REJECTED
        decision = exp.promotion_history[-1]
        assert decision.execution_report.borrow.shortability_passed is False
        assert "BORROW_UNAVAILABLE" in (decision.execution_report.borrow_constraint_note or "")


# -- PROVISIONAL cannot masquerade ------------------------------------------

class TestProvisionalHonesty:
    """
    LAW: PROVISIONAL payload values cannot masquerade as SNAPSHOT/LIVE.
    """

    def test_provisional_liquidity_labeled_honestly(self):
        """Provisional feed returns PROVISIONAL source_mode."""
        feed = ProvisionalLiquidityFeed()
        snap = feed.lookup("portfolio", datetime.now(timezone.utc))
        assert snap is not None
        assert snap.source_mode == "PROVISIONAL"
        assert snap.source_id == "provisional_payload"

    def test_provisional_borrow_labeled_honestly(self):
        feed = ProvisionalBorrowFeed()
        snap = feed.lookup("portfolio", datetime.now(timezone.utc))
        assert snap is not None
        assert snap.source_mode == "PROVISIONAL"
        assert snap.source_id == "provisional_payload"

    def test_short_required_provisional_borrow_degrades_honestly(self):
        """
        Short-required strategy with only PROVISIONAL borrow input
        degrades honestly (borrow evidence missing).
        """
        exp = _manifest("EXP-PROV-BRW-DEGRADE")
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.10, "benchmark_passed": True,
            "requires_shorting": True,
            # No borrow_available, no borrow_cost_bps → missing evidence
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
        }
        adjudicate(exp, [_ev(exp.experiment_id, **payload)])
        assert exp.state == PromotionState.REJECTED
        decision = exp.promotion_history[-1]
        assert decision.execution_report.borrow.shortability_passed is False
        # Honest label present
        assert decision.execution_report.borrow.degradation_reason is not None


# -- Provenance preservation ------------------------------------------------

class TestProvenancePreservation:
    """
    LAW: Promotion-grade decision preserves typed liquidity and borrow
    source provenance.
    """

    def test_feed_backed_provenance_in_decision(self):
        """
        When feed-backed snapshots are used, the execution report
        preserves the source_mode and fingerprint.
        """
        exp = _manifest("EXP-PROV-FEED")
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.05, "benchmark_passed": True,
            "estimated_trade_notional": 500_000.0,
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
            "dsr_estimate": 0.2, "pbo_estimate": 0.1,
            "cpcv_passed": True, "cpcv_folds": 4, "cpcv_path_coverage": 1.0,
        }

        now = datetime.now(timezone.utc)
        liq_snap = LiquiditySnapshot(
            asset_id="portfolio", snapshot_time=now,
            adv_notional=100_000_000.0, spread_bps=5.0,
            source_id="feed_A", source_mode="SNAPSHOT",
        )
        liq_feed = SnapshotStoreLiquidityFeed(SnapshotStore(liquidity=[liq_snap]))

        adjudicate(exp, [_ev(exp.experiment_id, **payload)], liquidity_feed=liq_feed)

        decision = exp.promotion_history[-1]
        cap = decision.execution_report.capacity
        assert isinstance(cap, CapacityEvidence)
        # Feed-backed participation rate was computed: 500k/100M = 0.005
        assert cap.estimated_participation_rate == pytest.approx(0.005, abs=1e-6)
        assert cap.adv_notional_proxy == pytest.approx(100_000_000.0)

    def test_identical_snapshots_produce_identical_fingerprints(self):
        """
        Two identical LiquiditySnapshot instances produce identical
        fingerprints.
        """
        t = datetime(2025, 1, 1, tzinfo=timezone.utc)
        s1 = LiquiditySnapshot(
            asset_id="X", snapshot_time=t, adv_notional=1e8,
            spread_bps=5.0, source_id="f", source_mode="SNAPSHOT",
        )
        s2 = LiquiditySnapshot(
            asset_id="X", snapshot_time=t, adv_notional=1e8,
            spread_bps=5.0, source_id="f", source_mode="SNAPSHOT",
        )
        assert s1.snapshot_hash == s2.snapshot_hash
        assert s1.compute_fingerprint() == s2.compute_fingerprint()

    def test_different_snapshots_produce_different_fingerprints(self):
        t = datetime(2025, 1, 1, tzinfo=timezone.utc)
        s1 = LiquiditySnapshot(
            asset_id="X", snapshot_time=t, adv_notional=1e8,
            spread_bps=5.0, source_id="f", source_mode="SNAPSHOT",
        )
        s2 = LiquiditySnapshot(
            asset_id="X", snapshot_time=t, adv_notional=2e8,  # different ADV
            spread_bps=5.0, source_id="f", source_mode="SNAPSHOT",
        )
        assert s1.snapshot_hash != s2.snapshot_hash


# -- PIT timestamp enforcement ----------------------------------------------

class TestPITTimestampEnforcement:
    """
    LAW: Snapshot lookup uses the lawful evaluation/decision timestamp,
    never wall-clock now().
    """

    def test_liquidity_lookup_uses_evaluation_time_not_wall_clock(self):
        """
        Two snapshots exist: one at t1 (low ADV) and one at t2 (high ADV).
        Setting evaluation_time_utc to t1 returns the t1 snapshot;
        wall-clock now() would return t2.  This proves the lookup uses
        the bundle's evaluation_time_utc, not datetime.now().
        """
        # Fixed timestamps — no wall-clock dependency
        t1 = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        t2 = datetime(2025, 6, 1, 18, 0, 0, tzinfo=timezone.utc)

        snaps = [
            LiquiditySnapshot(
                asset_id="AAPL", snapshot_time=t1,
                adv_notional=10_000_000, spread_bps=10.0,
                source_id="feed", source_mode="SNAPSHOT",
            ),
            LiquiditySnapshot(
                asset_id="AAPL", snapshot_time=t2,
                adv_notional=100_000_000, spread_bps=5.0,
                source_id="feed", source_mode="SNAPSHOT",
            ),
        ]
        feed = SnapshotStoreLiquidityFeed(SnapshotStore(liquidity=snaps))

        # Evaluate at t1 — should return the t1 snapshot (10M ADV)
        result_t1 = feed.lookup("AAPL", t1)
        assert result_t1 is not None
        assert result_t1.adv_notional == 10_000_000
        assert result_t1.snapshot_time == t1

        # Evaluate at t2 — should return the t2 snapshot (100M ADV)
        result_t2 = feed.lookup("AAPL", t2)
        assert result_t2 is not None
        assert result_t2.adv_notional == 100_000_000
        assert result_t2.snapshot_time == t2

    def test_adjudication_decision_carries_evaluation_time_provenance(self):
        """
        The AdjudicationDecision record preserves the exact
        evaluation_time_utc used for market-data lookups.
        """
        eval_time = datetime(2025, 3, 15, 14, 30, 0, tzinfo=timezone.utc)
        exp = _manifest(
            "EXP-PIT-TIME-PROV",
            evaluation_time_utc=eval_time,
            market_data_subject_id="AAPL",
        )
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.05, "benchmark_passed": True,
            "estimated_trade_notional": 500_000.0,
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
            "dsr_estimate": 0.2, "pbo_estimate": 0.1,
            "cpcv_passed": True, "cpcv_folds": 4, "cpcv_path_coverage": 1.0,
        }

        liq_snap = LiquiditySnapshot(
            asset_id="AAPL", snapshot_time=eval_time,
            adv_notional=100_000_000.0, spread_bps=5.0,
            source_id="pit_feed", source_mode="SNAPSHOT",
        )
        liq_feed = SnapshotStoreLiquidityFeed(SnapshotStore(liquidity=[liq_snap]))

        adjudicate(exp, [_ev(exp.experiment_id, **payload)], liquidity_feed=liq_feed)

        decision = exp.promotion_history[-1]
        # Direct field on decision
        assert decision.evaluation_time_utc == eval_time
        assert decision.market_data_subject_id == "AAPL"
        # Transitively in execution report provenance
        mdp = decision.execution_report.market_data_provenance
        assert isinstance(mdp, MarketDataProvenance)
        assert mdp.evaluation_time_utc == eval_time
        assert mdp.market_data_subject_id == "AAPL"
        assert mdp.liquidity_snapshot_hash == liq_snap.snapshot_hash
        assert mdp.liquidity_source_mode == "SNAPSHOT"


# -- Subject identity enforcement --------------------------------------------

class TestSubjectIdentityEnforcement:
    """
    LAW: Changing subject/asset identity changes selected snapshot lawfully.
    No hardcoded "portfolio" dependency in adjudication path.
    """

    def test_different_subject_id_selects_different_snapshot(self):
        """
        Snapshots exist for two different assets.  Changing the
        market_data_subject_id selects the correct asset's snapshot.
        """
        t = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        snaps = [
            LiquiditySnapshot(
                asset_id="AAPL", snapshot_time=t,
                adv_notional=50_000_000, spread_bps=5.0,
                source_id="feed", source_mode="SNAPSHOT",
            ),
            LiquiditySnapshot(
                asset_id="TSLA", snapshot_time=t,
                adv_notional=20_000_000, spread_bps=12.0,
                source_id="feed", source_mode="SNAPSHOT",
            ),
        ]
        feed = SnapshotStoreLiquidityFeed(SnapshotStore(liquidity=snaps))

        # AAPL lookup returns AAPL snapshot
        aapl = feed.lookup("AAPL", t)
        assert aapl is not None
        assert aapl.adv_notional == 50_000_000

        # TSLA lookup returns TSLA snapshot
        tsla = feed.lookup("TSLA", t)
        assert tsla is not None
        assert tsla.adv_notional == 20_000_000

    def test_adjudication_uses_typed_subject_id_not_hardcoded(self):
        """
        Adjudication uses the bundle's market_data_subject_id for
        lookups, not a hardcoded string.  Setting subject to "TSLA"
        selects the TSLA snapshot, not a "portfolio" snapshot.
        """
        t = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        # Only TSLA snapshot exists — no "portfolio" snapshot
        liq_snap = LiquiditySnapshot(
            asset_id="TSLA", snapshot_time=t,
            adv_notional=20_000_000.0, spread_bps=12.0,
            source_id="tsla_feed", source_mode="SNAPSHOT",
        )
        liq_feed = SnapshotStoreLiquidityFeed(SnapshotStore(liquidity=[liq_snap]))

        exp = _manifest(
            "EXP-SUBJECT-TSLA",
            market_data_subject_id="TSLA",
            evaluation_time_utc=t,
        )
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.05, "benchmark_passed": True,
            "estimated_trade_notional": 500_000.0,
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
            "dsr_estimate": 0.2, "pbo_estimate": 0.1,
            "cpcv_passed": True, "cpcv_folds": 4, "cpcv_path_coverage": 1.0,
        }

        adjudicate(exp, [_ev(exp.experiment_id, **payload)], liquidity_feed=liq_feed)

        decision = exp.promotion_history[-1]
        mdp = decision.execution_report.market_data_provenance
        # TSLA snapshot was found — proves subject_id is typed, not hardcoded
        assert mdp.liquidity_snapshot_hash == liq_snap.snapshot_hash
        assert mdp.market_data_subject_id == "TSLA"
        # Participation rate computed from TSLA ADV: 500k/20M = 0.025
        assert decision.execution_report.capacity.estimated_participation_rate == pytest.approx(0.025, abs=1e-6)

    def test_no_hardcoded_portfolio_in_borrow_lookup(self):
        """
        Borrow lookup uses market_data_subject_id, not hardcoded "portfolio".
        When subject is "AAPL" and only AAPL borrow snapshot exists,
        the borrow lookup finds it.
        """
        t = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        brw_snap = BorrowSnapshot(
            asset_id="AAPL", snapshot_time=t,
            borrow_available=True, borrow_cost_bps=50.0,
            source_id="aapl_borrow", source_mode="SNAPSHOT",
        )
        brw_feed = SnapshotStoreBorrowFeed(SnapshotStore(borrow=[brw_snap]))

        exp = _manifest(
            "EXP-BRW-SUBJECT-AAPL",
            market_data_subject_id="AAPL",
            evaluation_time_utc=t,
        )
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.10, "benchmark_passed": True,
            "requires_shorting": True,
            "borrow_available": False,  # pessimistic payload
            "borrow_cost_bps": 999.0,
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
        }

        adjudicate(exp, [_ev(exp.experiment_id, **payload)], borrow_feed=brw_feed)

        decision = exp.promotion_history[-1]
        mdp = decision.execution_report.market_data_provenance
        # AAPL borrow snapshot was found
        assert mdp.borrow_snapshot_hash == brw_snap.snapshot_hash
        assert mdp.market_data_subject_id == "AAPL"
        # Feed-backed borrow data overrode pessimistic payload
        assert decision.execution_report.borrow.borrow_available is True
        assert decision.execution_report.borrow.borrow_cost_bps == 50.0

    def test_missing_subject_id_honestly_degrades(self):
        """
        When market_data_subject_id is None, feed lookups are skipped
        and the system degrades honestly with a recorded reason.
        """
        exp = _manifest("EXP-NO-SUBJECT", market_data_subject_id=None)
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.10, "benchmark_passed": True,
            "requires_shorting": True,
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
        }

        # Provide a borrow feed but no subject identity
        t = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        brw_snap = BorrowSnapshot(
            asset_id="AAPL", snapshot_time=t,
            borrow_available=True, borrow_cost_bps=50.0,
            source_id="feed", source_mode="SNAPSHOT",
        )
        brw_feed = SnapshotStoreBorrowFeed(SnapshotStore(borrow=[brw_snap]))

        adjudicate(exp, [_ev(exp.experiment_id, **payload)], borrow_feed=brw_feed)

        decision = exp.promotion_history[-1]
        mdp = decision.execution_report.market_data_provenance
        # No subject identity recorded
        assert mdp.market_data_subject_id is None
        assert mdp.borrow_source_mode == "NONE"
        # Honest degradation note present
        assert "BORROW_LOOKUP_SKIPPED" in (decision.execution_report.borrow_constraint_note or "")


# -- Source-of-truth: evidence not silently overwritten ---------------------

class TestSourceOfTruthSemantics:
    """
    LAW: Provided evidence is authoritative by default.  Recomputation
    happens only when explicitly requested.  No silent overwrites.
    """

    def test_provided_cpcv_not_overwritten(self):
        """
        When the bundle already has CPCV evidence, the engine uses it
        as the source of truth and does not recompute.
        """
        bundle = EvidenceBundle(
            reproducibility=_repro(),
            benchmark_rung="L1",
            search_breadth=3,
            cpcv_passed=True,
            cpcv_folds=4,
            cpcv_path_coverage=0.95,
            cpcv_path_stability=0.1,
        )
        engine = RobustnessEngine()
        report = engine.evaluate(
            [], bundle=bundle, search_breadth=3, recompute_requested=False
        )
        # Provenance says PROVIDED
        cpcv_prov = [p for p in report.provenance if p.metric_name == "cpcv_passed"]
        assert len(cpcv_prov) == 1
        assert cpcv_prov[0].source_mode == MetricSourceMode.PROVIDED
        assert cpcv_prov[0].source_of_truth_used == MetricSourceMode.PROVIDED
        # Provided value preserved
        assert cpcv_prov[0].provided_value == 1.0
        assert cpcv_prov[0].recomputed_value is None

    def test_recompute_requested_persists_provenance(self):
        """
        When recomputation is explicitly requested, provenance records
        both the provided and recomputed values with the reason.
        """
        bundle = EvidenceBundle(
            reproducibility=_repro(),
            benchmark_rung="L1",
            search_breadth=3,
            cpcv_passed=True,
            cpcv_folds=4,
            cpcv_path_coverage=0.95,
            cpcv_path_stability=0.1,
        )
        engine = RobustnessEngine()
        report = engine.evaluate(
            [], bundle=bundle, search_breadth=3, recompute_requested=True
        )
        cpcv_prov = [p for p in report.provenance if p.metric_name == "cpcv_passed"]
        assert len(cpcv_prov) == 1
        assert cpcv_prov[0].source_mode == MetricSourceMode.RECOMPUTED
        assert cpcv_prov[0].source_of_truth_used == MetricSourceMode.RECOMPUTED
        assert cpcv_prov[0].provided_value == 1.0
        assert cpcv_prov[0].recomputed_reason == "RECOMPUTE_REQUESTED"

    def test_adjudication_preserves_provided_dsr_pbo(self):
        """
        When the bundle has DSR/PBO estimates, adjudication does not
        overwrite them; provenance records PROVIDED as source of truth.
        """
        exp = _manifest(
            "EXP-PROVIDED-DSR-PBO",
            dsr_estimate=0.8,
            pbo_estimate=0.05,
            cpcv_passed=True,
            cpcv_folds=4,
            cpcv_path_coverage=0.95,
            cpcv_path_stability=0.1,
            decoy_survival_passed=True,
            decoy_suite_version="decoy-v1",
            decoy_coverage=1.0,
        )
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.05, "benchmark_passed": True,
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
        }

        adjudicate(exp, [_ev(exp.experiment_id, **payload)])

        # Bundle values preserved
        assert exp.evidence_bundle.dsr_estimate == 0.8
        assert exp.evidence_bundle.pbo_estimate == 0.05
        # Provenance records PROVIDED
        dsr_prov = [p for p in exp.evidence_bundle.robustness_provenance if p.metric_name == "dsr_estimate"]
        pbo_prov = [p for p in exp.evidence_bundle.robustness_provenance if p.metric_name == "pbo_estimate"]
        assert len(dsr_prov) == 1
        assert dsr_prov[0].source_of_truth_used == MetricSourceMode.PROVIDED
        assert len(pbo_prov) == 1
        assert pbo_prov[0].source_of_truth_used == MetricSourceMode.PROVIDED


# -- Decision-level market-data provenance -----------------------------------

class TestDecisionMarketDataProvenance:
    """
    LAW: Promotion-grade decision preserves typed market-data timestamp
    and subject provenance at the decision record level.
    """

    def test_decision_records_evaluation_time_and_subject(self):
        """
        The AdjudicationDecision directly carries evaluation_time_utc
        and market_data_subject_id.
        """
        eval_time = datetime(2025, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
        exp = _manifest(
            "EXP-DECISION-PROV",
            evaluation_time_utc=eval_time,
            market_data_subject_id="MSFT",
        )
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.05, "benchmark_passed": True,
            "estimated_trade_notional": 1_000_000.0,
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
            "dsr_estimate": 0.2, "pbo_estimate": 0.1,
            "cpcv_passed": True, "cpcv_folds": 4, "cpcv_path_coverage": 1.0,
        }

        adjudicate(exp, [_ev(exp.experiment_id, **payload)])

        decision = exp.promotion_history[-1]
        assert decision.evaluation_time_utc == eval_time
        assert decision.market_data_subject_id == "MSFT"

    def test_execution_report_market_data_provenance(self):
        """
        The execution report's market_data_provenance sub-object records
        the lookup timestamp, subject, and snapshot hashes.
        """
        t = datetime(2025, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
        liq_snap = LiquiditySnapshot(
            asset_id="MSFT", snapshot_time=t,
            adv_notional=80_000_000.0, spread_bps=6.0,
            source_id="msft_feed", source_mode="SNAPSHOT",
        )
        liq_feed = SnapshotStoreLiquidityFeed(SnapshotStore(liquidity=[liq_snap]))

        exp = _manifest(
            "EXP-EXEC-MDP",
            evaluation_time_utc=t,
            market_data_subject_id="MSFT",
        )
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.05, "benchmark_passed": True,
            "estimated_trade_notional": 400_000.0,
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
            "dsr_estimate": 0.2, "pbo_estimate": 0.1,
            "cpcv_passed": True, "cpcv_folds": 4, "cpcv_path_coverage": 1.0,
        }

        adjudicate(exp, [_ev(exp.experiment_id, **payload)], liquidity_feed=liq_feed)

        decision = exp.promotion_history[-1]
        mdp = decision.execution_report.market_data_provenance
        assert mdp.evaluation_time_utc == t
        assert mdp.market_data_subject_id == "MSFT"
        assert mdp.liquidity_snapshot_hash == liq_snap.snapshot_hash
        assert mdp.liquidity_source_mode == "SNAPSHOT"
        # No borrow feed was provided
        assert mdp.borrow_snapshot_hash is None
        assert mdp.borrow_source_mode == "NONE"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
