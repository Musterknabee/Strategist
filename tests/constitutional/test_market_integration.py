import pytest
from datetime import datetime, timezone
from typing import Optional
from strategy_validator.core.enums import RuntimeMode, PromotionState, EvidenceType
from strategy_validator.contracts.market_data import LiquiditySnapshot, BorrowSnapshot, MarketDataProvider
from strategy_validator.validator.market_data_feeds import (
    ProviderBackedLiquidityFeed,
    ProviderBackedBorrowFeed,
    SnapshotStore,
    SnapshotStoreLiquidityFeed,
    LiveConnectorProvider
)
from strategy_validator.validator.orchestrator import adjudicate
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.evidence import EvidenceBundle, ReproducibilityManifest

class MockLiveProvider(MarketDataProvider):
    """Honest mock for a live provider seam."""
    def __init__(self, provider_id: str):
        self.provider_id = provider_id

    def provide_liquidity(self, asset_id: str, timestamp: datetime) -> Optional[LiquiditySnapshot]:
        return LiquiditySnapshot(
            asset_id=asset_id,
            snapshot_time=timestamp,
            adv_notional=1000000.0,
            spread_bps=5.0,
            source_id=self.provider_id,
            source_mode="LIVE"
        )

    def provide_borrow(self, asset_id: str, timestamp: datetime) -> Optional[BorrowSnapshot]:
        return BorrowSnapshot(
            asset_id=asset_id,
            snapshot_time=timestamp,
            borrow_available=True,
            borrow_cost_bps=10.0,
            source_id=self.provider_id,
            source_mode="LIVE"
        )

def _repro() -> ReproducibilityManifest:
    return ReproducibilityManifest(
        code_hash="a"*64, data_snapshot_hash="b"*64, universe_hash="c"*64,
        feature_graph_hash="d"*64, parameter_manifest_hash="e"*64,
        benchmark_version="v1", cost_model_version="v1", calendar_version="v1"
    )

def _exp(eid: str) -> ExperimentManifest:
    bundle = EvidenceBundle(
        reproducibility=_repro(),
        benchmark_rung="L1",
        search_breadth=1,
        evaluation_time_utc=datetime(2026, 4, 12, tzinfo=timezone.utc),
        market_data_subject_id="AAPL"
    )
    return ExperimentManifest(
        experiment_id=eid, strategy_name="strat", version="1", proposer_id="p1",
        evidence_bundle=bundle, state=PromotionState.QUARANTINED
    )

@pytest.mark.constitutional
class TestMarketIntegration:
    def test_live_provider_seam_preserves_mode(self):
        provider = MockLiveProvider("LIVE_FEED_01")
        liq_feed = ProviderBackedLiquidityFeed(provider)
        
        snap = liq_feed.lookup("AAPL", datetime.now(timezone.utc))
        assert snap.source_mode == "LIVE"
        assert snap.source_id == "LIVE_FEED_01"

    def test_production_policy_blocks_snapshot_when_disallowed(self, monkeypatch, tmp_path):
        # Setup PRODUCTION mode with explicit SNAPSHOT disallowed
        monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
        # SnapshotStore produces SNAPSHOT mode
        store = SnapshotStore(
            liquidity=[LiquiditySnapshot(
                asset_id="AAPL", snapshot_time=datetime(2026,4,12, tzinfo=timezone.utc),
                adv_notional=1e6, source_id="ARCHIVE", source_mode="SNAPSHOT"
            )]
        )
        liq_feed = SnapshotStoreLiquidityFeed(store)
        
        exp = _exp("EXP-SNAP-BLOCK")
        payload = {"estimated_trade_notional": 1000.0}
        from strategy_validator.contracts.evidence import Evidence
        evidence = [Evidence(
            evidence_id="EV-SNAP-1",
            experiment_id="EXP-SNAP-BLOCK", 
            evidence_type=EvidenceType.EXECUTION_LOG, 
            timestamp=datetime(2026,4,12, tzinfo=timezone.utc), 
            payload=payload,
            source_module="TEST",
            checksum="a"*64
        )]
        
        # Use a real absolute path for promotion readiness
        db_path = tmp_path / "prod_ledger.sqlite3"
        monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(db_path.absolute()))

        # Adjudicate should cap at REJECTED or INVALID due to production policy
        state = adjudicate(exp, evidence, liquidity_feed=liq_feed)

        assert state in (PromotionState.REJECTED, PromotionState.INVALID, PromotionState.CONDITIONAL)
        last_dec = exp.promotion_history[-1]
        assert any("STRICT_PRODUCTION_BLOCKER" in n for n in last_dec.summary_notes)

    def test_production_policy_permits_live_data(self, monkeypatch, tmp_path):
        monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
        provider = MockLiveProvider("LIVE_REALTIME")
        liq_feed = ProviderBackedLiquidityFeed(provider)
        
        # provide enough metadata to pass other gates
        payload = {"estimated_trade_notional": 1000.0}
        from strategy_validator.contracts.evidence import Evidence
        evidence = [Evidence(
            evidence_id="EV-LIVE-1",
            experiment_id="EXP-LIVE", 
            evidence_type=EvidenceType.EXECUTION_LOG, 
            timestamp=datetime(2026,4,12, tzinfo=timezone.utc), 
            payload=payload,
            source_module="TEST",
            checksum="a"*64
        )]
        
        db_path = tmp_path / "prod_ledger_live.sqlite3"
        monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(db_path.absolute()))

        exp = _exp("EXP-LIVE")
        brw_feed = ProviderBackedBorrowFeed(provider)
        state = adjudicate(exp, evidence, liquidity_feed=liq_feed, borrow_feed=brw_feed)
        last_dec = exp.promotion_history[-1]
        
        # Should NOT be blocked by source policy because it's LIVE
        # (Might be rejected/quarantined for other reasons, but not STRICT_PRODUCTION_BLOCKER regarding source)
        if any("STRICT_PRODUCTION_BLOCKER" in n for n in last_dec.summary_notes):
            pytest.fail(f"Unexpected source blocker: {last_dec.summary_notes}")
        assert last_dec.execution_report.market_data_provenance.liquidity_source_mode == "LIVE"

    def test_provider_backed_lookup_is_pit_aware(self):
        class PITProvider(MarketDataProvider):
            provider_id = "PIT"
            def provide_liquidity(self, asset_id: str, timestamp: datetime) -> Optional[LiquiditySnapshot]:
                # Return snapshot timestamped AT the requested time to prove awareness
                return LiquiditySnapshot(
                    asset_id=asset_id, snapshot_time=timestamp, 
                    adv_notional=1e6, source_id=self.provider_id, source_mode="SNAPSHOT"
                )
            def provide_borrow(self, asset_id, timestamp): return None

        provider = PITProvider()
        liq_feed = ProviderBackedLiquidityFeed(provider)
        
        req_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
        snap = liq_feed.lookup("AAPL", req_time)
        assert snap.snapshot_time == req_time
