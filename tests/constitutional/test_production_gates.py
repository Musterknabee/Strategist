import pytest
import os
from datetime import datetime, timezone
from typing import Optional
from strategy_validator.core.enums import RuntimeMode, PromotionState, EvidenceType
from strategy_validator.core.config import load_config
from strategy_validator.validator.readiness import perform_readiness_check
from strategy_validator.validator.orchestrator import adjudicate
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.evidence import EvidenceBundle, Evidence, ReproducibilityManifest
from strategy_validator.core.exceptions import AdjudicationError, ConstitutionalViolation
from strategy_validator.contracts.market_data import LiquidityFeed, BorrowFeed, SourceMode
from strategy_validator.contracts.execution import MarketDataProvenance

@pytest.fixture
def prod_env(monkeypatch):
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
    # Force absolute safe path for readiness
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", "c:/absolute/production/ledger.sqlite3")

def _repro() -> ReproducibilityManifest:
    return ReproducibilityManifest(
        code_hash="a" * 64, data_snapshot_hash="b" * 64, universe_hash="c" * 64,
        feature_graph_hash="d" * 64, parameter_manifest_hash="e" * 64,
        benchmark_version="bench-v1", cost_model_version="v1", calendar_version="v1"
    )

def _ev(eid: str, **payload) -> Evidence:
    return Evidence(
        experiment_id=eid,
        evidence_id=f"ev_{eid}",
        evidence_type=EvidenceType.COST_SUMMARY,
        timestamp=datetime(2026, 4, 1, tzinfo=timezone.utc),
        payload=payload,
        source_module="test",
        checksum="abc"
    )

def _bundle(**kw) -> EvidenceBundle:
    defaults = dict(
        reproducibility=_repro(),
        benchmark_rung="L1",
        search_breadth=3,
        evaluation_time_utc=datetime(2026, 4, 12, tzinfo=timezone.utc),
        market_data_subject_id="portfolio"
    )
    defaults.update(kw)
    return EvidenceBundle(**defaults)

def _exp(eid: str, bundle: EvidenceBundle) -> ExperimentManifest:
    return ExperimentManifest(
        experiment_id=eid,
        strategy_name="test_strat",
        version="1.0",
        proposer_id="user_1",
        evidence_bundle=bundle,
        state=PromotionState.QUARANTINED # Start at restricted state
    )

@pytest.mark.constitutional
class TestProductionReadiness:
    def test_production_mode_blocks_relative_ledger_path(self, monkeypatch):
        monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
        monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", "relative/path/ledger.sqlite3")
        
        report = perform_readiness_check()
        assert report.status == "BLOCKED"
        assert any(b.code in ("UNSAFE_LEDGER_PATH", "LEDGER_ACCESS_FAILED") for b in report.blockers)

    def test_production_mode_blocks_default_ledger_path(self, monkeypatch):
        monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
        if "STRATEGY_VALIDATOR_LEDGER_DB_PATH" in os.environ:
            monkeypatch.delenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH")
        
        report = perform_readiness_check()
        assert report.status == "BLOCKED"
        assert any(b.code in ("DEFAULT_LEDGER_PATH_FORBIDDEN", "LEDGER_ACCESS_FAILED") for b in report.blockers)

    def test_dev_mode_permits_local_ledger(self, monkeypatch):
        monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
        report = perform_readiness_check()
        assert report.status == "READY"

@pytest.mark.constitutional
class TestProductionOrchestratorGates:
    def test_production_mode_rejects_provisional_market_data(self, monkeypatch, prod_env):
        import uuid
        eid = f"PROD-PROV-{uuid.uuid4().hex[:8]}"
        # Provide all metadata to avoid other gate failures
        bundle = _bundle(
            decoy_survival_passed=True,
            decoy_suite_version="v1",
            decoy_coverage=1.0,
            cpcv_passed=True,
            cpcv_folds=5,
            cpcv_path_coverage=1.0,
            cpcv_path_stability=0.1,
            incrementality_significant=True,
            dsr_estimate=0.5,
            pbo_estimate=0.1
        )
        exp = _exp(eid, bundle)
        
        # Evidence payload
        payload = {
            "benchmark_delta": 0.5, 
            "benchmark_passed": True, 
            "benchmark_id": "L1_BMK", 
            "benchmark_version": "bench-v1",
            "strategy_return": 0.05,
            "benchmark_return": 0.02,
            "horizon": "1y",
            "estimated_trade_notional": 1000.0,
            "estimated_participation_rate": 0.01
        }
        evidence = [_ev(eid, **payload)]
        
        # Mandatory provisional feed to trigger the production gate
        class MockFeed:
            def lookup(self, asset_id, timestamp):
                return None # The realism engine will handle None as provisional if it falls back

        # Adjudicate should cap at CONDITIONAL due to production policy
        # But wait! I want to trigger the source policy violation.
        # If I want it to be PROVISIONAL, I need get_snapshot to return a snapshot with source_mode="PROVISIONAL".
        
        from strategy_validator.contracts.market_data import LiquiditySnapshot
        class ProvisionalFeed:
            def lookup(self, asset_id, timestamp):
                return LiquiditySnapshot(
                    asset_id=asset_id,
                    snapshot_time=timestamp,
                    source_mode="PROVISIONAL"
                )

        # Adjudicate should cap at INVALID due to strict production policy
        state = adjudicate(exp, evidence, liquidity_feed=ProvisionalFeed())
        decision = exp.promotion_history[-1]
        
        assert state == PromotionState.INVALID
        assert any("STRICT_PRODUCTION_BLOCKER" in n for n in decision.summary_notes)

    def test_production_mode_fails_on_missing_context(self, monkeypatch, prod_env):
        eid = "PROD-MISSING-CONTEXT"
        bundle = _bundle(evaluation_time_utc=None)
        exp = _exp(eid, bundle)

        with pytest.raises(AdjudicationError, match="STRICT_CONTEXT_VIOLATION"):
            adjudicate(exp, [])

    def test_production_mode_rejects_missing_subject_id(self, monkeypatch, prod_env):
        """
        LAW: In strict production mode, missing market_data_subject_id fails closed.
        """
        eid = "PROD-MISSING-SUBJECT"
        bundle = _bundle(market_data_subject_id=None)
        exp = _exp(eid, bundle)

        with pytest.raises(AdjudicationError, match="STRICT_CONTEXT_VIOLATION"):
            adjudicate(exp, [])

@pytest.mark.constitutional
class TestProvenanceFingerprinting:
    def test_readiness_report_contains_fingerprint(self):
        report = perform_readiness_check()
        assert report.config_fingerprint is not None
        assert len(report.config_fingerprint) == 12

    def test_strict_production_mode_changes_readiness(self, monkeypatch, tmp_path):
        """
        LAW: Changing strict_production_mode changes readiness outcome deterministically.
        """
        # Use a real absolute path that SQLite can create
        db_path = tmp_path / "prod_ledger.sqlite3"

        # DEV mode — READY
        monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
        monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(db_path))
        report_dev = perform_readiness_check()
        assert report_dev.status == "READY"
        assert report_dev.run_mode == RuntimeMode.DEV

        # PRODUCTION mode — should be READY (PRODUCTION defaults are safe
        # and the absolute path is valid)
        monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
        monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(db_path.absolute()))
        report_prod = perform_readiness_check()
        assert report_prod.status == "READY"
        assert report_prod.run_mode == RuntimeMode.PRODUCTION
