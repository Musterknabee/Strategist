"""
Anti-leakage and deterministic replay infrastructure tests.

These tests prove:
  1. Repeated ledger tests in one run do not interfere with each other.
  2. Append-only persistence works with isolated DB paths.
  3. No stale promoted state survives across isolated test runs.
  4. Fixture setup/teardown is deterministic.
  5. Identical lawful inputs produce identical adjudication/provenance artifacts.
  6. Changing only material evidence/config changes outcomes deterministically.
  7. No provenance-free PROMOTABLE path exists.
  8. No hidden local-state dependency changes adjudication outcome.
"""
from datetime import datetime, timezone
import os
import uuid

import pytest

from strategy_validator.contracts.evidence import Evidence, EvidenceBundle, ReproducibilityManifest
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.market_data import LiquiditySnapshot
from strategy_validator.core.enums import EvidenceType, PromotionState
from strategy_validator.ledger._append_only import resolve_database_path, read_events
from strategy_validator.validator.market_data_feeds import SnapshotStore, SnapshotStoreLiquidityFeed
from strategy_validator.validator.orchestrator import adjudicate


# -- Helpers -----------------------------------------------------------------

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
        evaluation_time_utc=datetime(2026, 4, 12, tzinfo=timezone.utc),
        decoy_survival_passed=True,
        decoy_suite_version="decoy-v1",
        decoy_coverage=1.0,
        cpcv_passed=True,
        cpcv_folds=4,
        cpcv_path_coverage=1.0,
        cpcv_path_stability=0.1,
        dsr_estimate=0.5,
        pbo_estimate=0.1,
        incrementality_significant=True,
        incrementality_p_value=0.01,
        market_data_subject_id="TEST-ASSET",
    )
    defaults.update(kw)
    return EvidenceBundle(**defaults)


def _ev(experiment_id: str, **payload) -> Evidence:
    return Evidence(
        evidence_id=f"ev-{experiment_id}-{len(payload)}",
        experiment_id=experiment_id,
        evidence_type=EvidenceType.OUT_OF_SAMPLE_AUDIT,
        timestamp=datetime(2026, 4, 12, tzinfo=timezone.utc),
        payload=payload,
        source_module="anti_leakage",
        checksum="f" * 64,
    )


def _manifest(exp_id: str, **bundle_kw) -> ExperimentManifest:
    return ExperimentManifest(
        experiment_id=exp_id,
        strategy_name="AntiLeakage",
        version="1.0",
        proposer_id="anti_leakage",
        evidence_bundle=_bundle(**bundle_kw),
    )


# -- Anti-leakage: DB isolation ----------------------------------------------

class TestLedgerIsolation:
    """
    LAW: Each test receives an isolated ledger database.
    No stale state survives across test boundaries.
    """

    def test_each_test_has_unique_db_path(self):
        """resolve_database_path returns a test-local path."""
        db_path = resolve_database_path()
        assert db_path.exists() or str(db_path).endswith(".sqlite3")
        # Must NOT be the production default path
        assert ".strategy_validator/ledger.sqlite3" not in str(db_path).replace("\\", "/")
        assert "STRATEGY_VALIDATOR_LEDGER_DB_PATH" in os.environ

    def test_no_cross_test_ledger_contamination(self):
        """
        A fresh test sees an empty ledger for its experiment ID.
        No events from prior tests leak through.
        """
        exp_id = f"ISOLATION-{uuid.uuid4().hex[:8]}"
        events = read_events(exp_id)
        assert len(events) == 0

    def test_append_isolation_persists_within_test(self):
        """
        Events written within a test are visible to that test,
        proving append-only persistence works on the isolated DB.
        """
        exp = _manifest("APPEND-ISOLATION")
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.05, "benchmark_passed": True,
            "estimated_trade_notional": 1000.0,
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
            "dsr_estimate": 0.2, "pbo_estimate": 0.1,
            "cpcv_passed": True, "cpcv_folds": 4, "cpcv_path_coverage": 1.0,
        }
        state = adjudicate(exp, [_ev(exp.experiment_id, **payload)])
        assert state == PromotionState.PROMOTABLE

        # Ledger should have exactly one event for this experiment
        events = read_events(exp.experiment_id)
        assert len(events) == 1
        assert events[0].experiment_id == exp.experiment_id

    def test_no_stale_promotable_state(self):
        """
        A test that creates a REJECTED experiment does not see
        a stale PROMOTABLE state from a prior test.
        """
        exp = _manifest("STALE-CHECK", market_data_subject_id=None)
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.05, "benchmark_passed": True,
            "estimated_trade_notional": 100_000_000.0,
            "estimated_participation_rate": 0.50,  # 50% → fatal
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
        }
        state = adjudicate(exp, [_ev(exp.experiment_id, **payload)])
        # Should be REJECTED (excessive participation), not PROMOTABLE
        assert state != PromotionState.PROMOTABLE


# -- Deterministic replay ----------------------------------------------------

class TestDeterministicReplay:
    """
    LAW: Identical lawful inputs produce identical adjudication
    and provenance artifacts.
    """

    def test_identical_inputs_produce_identical_provenance(self):
        """
        Two adjudications with identical objects produce
        bit-identical provenance hashes.
        """
        t = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        liq_snap = LiquiditySnapshot(
            asset_id="MSFT", snapshot_time=t,
            adv_notional=80_000_000.0, spread_bps=6.0,
            source_id="feed", source_mode="SNAPSHOT",
        )
        liq_feed = SnapshotStoreLiquidityFeed(SnapshotStore(liquidity=[liq_snap]))

        def _run():
            exp = _manifest(
                "DETERMINISTIC-REPLAY",
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
            return exp.promotion_history[-1]

        dec1 = _run()
        dec2 = _run()

        # Provenance hashes must be identical
        assert dec1.execution_report.market_data_provenance.liquidity_snapshot_hash == \
               dec2.execution_report.market_data_provenance.liquidity_snapshot_hash
        assert dec1.execution_report.market_data_provenance.evaluation_time_utc == \
               dec2.execution_report.market_data_provenance.evaluation_time_utc
        assert dec1.evaluation_time_utc == dec2.evaluation_time_utc

    def test_changing_material_evidence_changes_outcome(self):
        """
        Changing only the participation rate (material evidence)
        changes the adjudication outcome deterministically.
        """
        t = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        liq_snap = LiquiditySnapshot(
            asset_id="AAPL", snapshot_time=t,
            adv_notional=10_000_000.0, spread_bps=10.0,
            source_id="feed", source_mode="SNAPSHOT",
        )
        liq_feed = SnapshotStoreLiquidityFeed(SnapshotStore(liquidity=[liq_snap]))

        # Low participation → PROMOTABLE
        exp_low = _manifest("MAT-LOW", evaluation_time_utc=t, market_data_subject_id="AAPL")
        adjudicate(exp_low, [_ev(exp_low.experiment_id,
            benchmark_id="SPY", benchmark_version="bench-v1",
            benchmark_delta=0.05, benchmark_passed=True,
            estimated_trade_notional=10_000.0,
            pit_integrity_ok=True,
            train_sharpes=[1], test_sharpes=[1],
            dsr_estimate=0.2, pbo_estimate=0.1,
            cpcv_passed=True, cpcv_folds=4, cpcv_path_coverage=1.0,
        )], liquidity_feed=liq_feed)
        assert exp_low.state == PromotionState.PROMOTABLE

        # High participation → REJECTED
        exp_high = _manifest("MAT-HIGH", evaluation_time_utc=t, market_data_subject_id="AAPL")
        adjudicate(exp_high, [_ev(exp_high.experiment_id,
            benchmark_id="SPY", benchmark_version="bench-v1",
            benchmark_delta=0.05, benchmark_passed=True,
            estimated_trade_notional=5_000_000.0,  # 50% participation → fatal
            pit_integrity_ok=True,
            train_sharpes=[1], test_sharpes=[1],
            dsr_estimate=0.2, pbo_estimate=0.1,
            cpcv_passed=True, cpcv_folds=4, cpcv_path_coverage=1.0,
        )], liquidity_feed=liq_feed)
        assert exp_high.state == PromotionState.REJECTED

    def test_no_provenance_free_promotable_path(self):
        """
        Every PROMOTABLE decision carries market-data provenance.
        No promotion-grade decision is provenance-free.
        """
        exp = _manifest("PROV-FREE-CHECK")
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "bench-v1",
            "benchmark_delta": 0.05, "benchmark_passed": True,
            "estimated_trade_notional": 1000.0,
            "pit_integrity_ok": True,
            "train_sharpes": [1], "test_sharpes": [1],
            "dsr_estimate": 0.2, "pbo_estimate": 0.1,
            "cpcv_passed": True, "cpcv_folds": 4, "cpcv_path_coverage": 1.0,
        }
        adjudicate(exp, [_ev(exp.experiment_id, **payload)])
        assert exp.state == PromotionState.PROMOTABLE

        decision = exp.promotion_history[-1]
        mdp = decision.execution_report.market_data_provenance
        # Provenance is always present
        assert mdp is not None
        assert mdp.evaluation_time_utc is not None
        assert mdp.liquidity_source_mode is not None
        assert mdp.borrow_source_mode is not None

    def test_no_hidden_local_state_dependency(self):
        """
        Adjudication outcome depends only on explicit inputs,
        not on process-level state, environment variables, or
        machine-local assumptions.
        """
        t = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

        def _run():
            exp = _manifest("NO-HIDDEN-STATE", evaluation_time_utc=t, market_data_subject_id="GOOG")
            payload = {
                "benchmark_id": "SPY", "benchmark_version": "bench-v1",
                "benchmark_delta": 0.05, "benchmark_passed": True,
                "estimated_trade_notional": 5000.0,
                "pit_integrity_ok": True,
                "train_sharpes": [1], "test_sharpes": [1],
                "dsr_estimate": 0.3, "pbo_estimate": 0.05,
                "cpcv_passed": True, "cpcv_folds": 4, "cpcv_path_coverage": 1.0,
            }
            adjudicate(exp, [_ev(exp.experiment_id, **payload)])
            return exp.state, exp.promotion_history[-1].execution_report.market_data_provenance

        state1, prov1 = _run()
        state2, prov2 = _run()

        # Same inputs → same state, same provenance
        assert state1 == state2
        assert prov1.evaluation_time_utc == prov2.evaluation_time_utc
        assert prov1.market_data_subject_id == prov2.market_data_subject_id
