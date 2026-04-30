import pytest
from datetime import datetime, timezone, timedelta
from typing import Optional
from strategy_validator.core.enums import RuntimeMode, PromotionState, EvidenceType
from strategy_validator.contracts.market_data import LiquiditySnapshot, BorrowSnapshot, MarketDataProvider, ProviderResiliencePolicy
from strategy_validator.validator.market_data_feeds import (
    ProviderBackedLiquidityFeed,
    ProviderBackedBorrowFeed,
    SnapshotStore,
    SnapshotStoreLiquidityFeed,
    SnapshotStoreBorrowFeed,
)
from strategy_validator.validator.orchestrator import adjudicate
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.evidence import EvidenceBundle, ReproducibilityManifest, Evidence

class ResilientMockProvider(MarketDataProvider):
    """Mock provider with controllable staleness and errors."""
    def __init__(self, provider_id: str, staleness_delta: Optional[timedelta] = None, raise_error: bool = False):
        self.provider_id = provider_id
        self.staleness_delta = staleness_delta
        self.raise_error = raise_error

    def provide_liquidity(self, asset_id: str, timestamp: datetime) -> Optional[LiquiditySnapshot]:
        if self.raise_error:
            raise RuntimeError("PROVIDER_CRASHED")
        
        snap_time = timestamp
        if self.staleness_delta:
            snap_time = timestamp - self.staleness_delta
            
        return LiquiditySnapshot(
            asset_id=asset_id,
            snapshot_time=snap_time,
            adv_notional=1000000.0,
            spread_bps=5.0,
            source_id=self.provider_id,
            source_mode="LIVE"
        )

    def provide_borrow(self, asset_id: str, timestamp: datetime) -> Optional[BorrowSnapshot]:
        if self.raise_error:
            raise RuntimeError("PROVIDER_CRASHED")
        snap_time = timestamp
        if self.staleness_delta:
            snap_time = timestamp - self.staleness_delta
        return BorrowSnapshot(
            asset_id=asset_id,
            snapshot_time=snap_time,
            borrow_available=True,
            source_id=self.provider_id,
            source_mode="LIVE"
        )



class Vendor503Provider(MarketDataProvider):
    """Always fails liquidity with an Alpaca-style 5xx token (circuit-burn-in tests)."""

    def __init__(self, provider_id: str = "v503") -> None:
        self.provider_id = provider_id

    def provide_liquidity(self, asset_id: str, timestamp: datetime) -> Optional[LiquiditySnapshot]:
        raise RuntimeError("ALPACA_HTTP_503")

    def provide_borrow(self, asset_id: str, timestamp: datetime) -> Optional[BorrowSnapshot]:
        return None


class FlakyTimeoutProvider(MarketDataProvider):
    def __init__(self, provider_id: str, *, fail_count: int = 1, borrow_fail_count: int = 0):
        self.provider_id = provider_id
        self.fail_count = fail_count
        self.borrow_fail_count = borrow_fail_count
        self.liquidity_calls = 0
        self.borrow_calls = 0

    def provide_liquidity(self, asset_id: str, timestamp: datetime) -> Optional[LiquiditySnapshot]:
        self.liquidity_calls += 1
        if self.liquidity_calls <= self.fail_count:
            raise TimeoutError("LIQUIDITY_TIMEOUT")
        return LiquiditySnapshot(
            asset_id=asset_id,
            snapshot_time=timestamp,
            adv_notional=1_000_000.0,
            spread_bps=5.0,
            source_id=self.provider_id,
            source_mode="LIVE",
        )

    def provide_borrow(self, asset_id: str, timestamp: datetime) -> Optional[BorrowSnapshot]:
        self.borrow_calls += 1
        if self.borrow_calls <= self.borrow_fail_count:
            raise TimeoutError("BORROW_TIMEOUT")
        return BorrowSnapshot(
            asset_id=asset_id,
            snapshot_time=timestamp,
            borrow_available=True,
            borrow_cost_bps=50.0,
            source_id=self.provider_id,
            source_mode="LIVE",
        )

def _repro() -> ReproducibilityManifest:
    return ReproducibilityManifest(
        code_hash="a"*64, data_snapshot_hash="b"*64, universe_hash="c"*64,
        feature_graph_hash="d"*64, parameter_manifest_hash="e"*64,
        benchmark_version="bench-v1", cost_model_version="v1", calendar_version="v1"
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

def _setup_production_safe_env(monkeypatch, tmp_path):
    db_path = tmp_path / "prod_resilience.sqlite3"
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(db_path.absolute()))

@pytest.mark.constitutional
class TestMarketDataResilience:
    def test_stale_live_data_blocks_promotion(self, monkeypatch, tmp_path):
        """LAW: Stale live data must block PROMOTABLE in strict production."""
        _setup_production_safe_env(monkeypatch, tmp_path)
        
        # Data is 70 seconds old (threshold is 60s)
        provider = ResilientMockProvider("STALE_FEED", staleness_delta=timedelta(seconds=70))
        liq_feed = ProviderBackedLiquidityFeed(provider)
        
        exp = _exp("EXP-STALE")
        evidence = [Evidence(
            evidence_id="EV-1", experiment_id="EXP-STALE", 
            evidence_type=EvidenceType.EXECUTION_LOG, 
            timestamp=exp.evidence_bundle.evaluation_time_utc,
            payload={"estimated_trade_notional": 1000.0},
            source_module="TEST", checksum="a"*64
        )]
        
        state = adjudicate(exp, evidence, liquidity_feed=liq_feed)
        
        # Should be REJECTED due to freshness law violation
        if state != PromotionState.REJECTED:
             pytest.fail(f"Expected REJECTED, got {state}. Notes: {exp.promotion_history[-1].summary_notes}")
        assert state == PromotionState.REJECTED
        last_dec = exp.promotion_history[-1]
        assert any("stale market data" in n for n in last_dec.summary_notes)
        assert last_dec.execution_report.market_data_provenance.liquidity_freshness_status == "STALE"

    def test_provider_error_blocks_promotion(self, monkeypatch, tmp_path):
        """LAW: Provider exceptions must block PROMOTABLE in strict production."""
        _setup_production_safe_env(monkeypatch, tmp_path)
        
        provider = ResilientMockProvider("CRASHED_FEED", raise_error=True)
        liq_feed = ProviderBackedLiquidityFeed(provider)
        
        exp = _exp("EXP-CRASH")
        evidence = [Evidence(
            evidence_id="EV-1", experiment_id="EXP-CRASH", 
            evidence_type=EvidenceType.EXECUTION_LOG, 
            timestamp=exp.evidence_bundle.evaluation_time_utc,
            payload={"estimated_trade_notional": 1000.0},
            source_module="TEST", checksum="a"*64
        )]
        
        state = adjudicate(exp, evidence, liquidity_feed=liq_feed)
        
        assert state == PromotionState.REJECTED
        last_dec = exp.promotion_history[-1]
        assert any("market-data provider failure" in n for n in last_dec.summary_notes)
        assert any("PROVIDER_CRASHED" in e for e in last_dec.execution_report.market_data_provenance.provider_errors)

    def test_provenance_seals_freshness_status(self, monkeypatch, tmp_path):
        """LAW: Freshness results must be forensically sealed in decision provenance."""
        _setup_production_safe_env(monkeypatch, tmp_path)
        
        # Fresh data (0s age)
        provider = ResilientMockProvider("FRESH_FEED", staleness_delta=timedelta(seconds=0))
        liq_feed = ProviderBackedLiquidityFeed(provider)
        
        exp = _exp("EXP-FRESH")
        evidence = [Evidence(
            evidence_id="EV-1", experiment_id="EXP-FRESH", 
            evidence_type=EvidenceType.EXECUTION_LOG, 
            timestamp=exp.evidence_bundle.evaluation_time_utc,
            payload={"estimated_trade_notional": 1000.0},
            source_module="TEST", checksum="a"*64
        )]
        
        adjudicate(exp, evidence, liquidity_feed=liq_feed)
        
        last_dec = exp.promotion_history[-1]
        prov = last_dec.execution_report.market_data_provenance
        assert prov.liquidity_freshness_status == "FRESH"
        assert prov.liquidity_source_mode == "LIVE"
        assert not prov.fallback_applied

    def test_fallback_permitted_policy(self, monkeypatch, tmp_path):
        """LAW: Stale data is accepted ONLY if policy explicitly allow_market_data_fallback."""
        _setup_production_safe_env(monkeypatch, tmp_path)
        # Override policy to allow fallback
        monkeypatch.setenv("STRATEGY_VALIDATOR_ALLOW_MARKET_DATA_FALLBACK", "True")
        
        provider = ResilientMockProvider("STALE_FEED", staleness_delta=timedelta(seconds=300))
        liq_feed = ProviderBackedLiquidityFeed(provider)
        
        exp = _exp("EXP-FALLBACK")
        evidence = [Evidence(
            evidence_id="EV-1", experiment_id="EXP-FALLBACK", 
            evidence_type=EvidenceType.EXECUTION_LOG, 
            timestamp=exp.evidence_bundle.evaluation_time_utc,
            payload={"estimated_trade_notional": 1000.0},
            source_module="TEST", checksum="a"*64
        )]
        
        state = adjudicate(exp, evidence, liquidity_feed=liq_feed)
        
        # Should NOT be blocked because fallback is allowed by policy.
        # Without an explicit secondary feed, the decision remains honest about stale LIVE data.
        last_dec = exp.promotion_history[-1]
        assert not any("stale market data" in n for n in last_dec.summary_notes)
        assert last_dec.execution_report.market_data_provenance.liquidity_freshness_status == "STALE"
        assert last_dec.execution_report.market_data_provenance.fallback_applied is False


    def test_stale_live_data_falls_back_to_snapshot_when_allowed(self, monkeypatch, tmp_path):
        """LAW: stale LIVE data may fall back to SNAPSHOT only when policy explicitly allows it."""
        _setup_production_safe_env(monkeypatch, tmp_path)
        monkeypatch.setenv("STRATEGY_VALIDATOR_ALLOW_MARKET_DATA_FALLBACK", "True")
        monkeypatch.setenv("STRATEGY_VALIDATOR_ALLOW_SNAPSHOT_MARKET_DATA", "True")

        provider = ResilientMockProvider("STALE_FEED", staleness_delta=timedelta(seconds=300))
        liq_feed = ProviderBackedLiquidityFeed(provider)
        fallback_store = SnapshotStore(liquidity=[
            LiquiditySnapshot(
                asset_id="AAPL",
                snapshot_time=datetime(2026, 4, 12, tzinfo=timezone.utc),
                adv_notional=2_000_000.0,
                spread_bps=3.0,
                source_id="ARCHIVE_FALLBACK",
                source_mode="SNAPSHOT",
            )
        ])
        fallback_feed = SnapshotStoreLiquidityFeed(fallback_store)

        exp = _exp("EXP-FALLBACK-LIQ")
        evidence = [Evidence(
            evidence_id="EV-1", experiment_id="EXP-FALLBACK-LIQ",
            evidence_type=EvidenceType.EXECUTION_LOG,
            timestamp=exp.evidence_bundle.evaluation_time_utc,
            payload={"estimated_trade_notional": 1000.0},
            source_module="TEST", checksum="a"*64
        )]

        adjudicate(exp, evidence, liquidity_feed=liq_feed, liquidity_fallback_feed=fallback_feed)
        last_dec = exp.promotion_history[-1]
        prov = last_dec.execution_report.market_data_provenance
        assert prov.fallback_applied is True
        assert prov.fallback_reason == "LIQUIDITY_STALE_FALLBACK"
        assert prov.liquidity_source_mode == "SNAPSHOT"
        assert prov.liquidity_source_id == "ARCHIVE_FALLBACK"
        assert prov.liquidity_provider_status == "STALE"
        assert prov.liquidity_freshness_status == "FRESH"

    def test_provider_error_falls_back_to_snapshot_when_allowed(self, monkeypatch, tmp_path):
        """LAW: provider failures may fall back only when policy explicitly allows it and provenance must remain explicit."""
        _setup_production_safe_env(monkeypatch, tmp_path)
        monkeypatch.setenv("STRATEGY_VALIDATOR_ALLOW_MARKET_DATA_FALLBACK", "True")
        monkeypatch.setenv("STRATEGY_VALIDATOR_ALLOW_SNAPSHOT_MARKET_DATA", "True")

        provider = ResilientMockProvider("CRASHED_FEED", raise_error=True)
        liq_feed = ProviderBackedLiquidityFeed(provider)
        fallback_store = SnapshotStore(liquidity=[
            LiquiditySnapshot(
                asset_id="AAPL",
                snapshot_time=datetime(2026, 4, 12, tzinfo=timezone.utc),
                adv_notional=1_500_000.0,
                spread_bps=4.0,
                source_id="ARCHIVE_FALLBACK",
                source_mode="SNAPSHOT",
            )
        ])
        fallback_feed = SnapshotStoreLiquidityFeed(fallback_store)

        exp = _exp("EXP-FALLBACK-ERR")
        evidence = [Evidence(
            evidence_id="EV-1", experiment_id="EXP-FALLBACK-ERR",
            evidence_type=EvidenceType.EXECUTION_LOG,
            timestamp=exp.evidence_bundle.evaluation_time_utc,
            payload={"estimated_trade_notional": 1000.0},
            source_module="TEST", checksum="a"*64
        )]

        adjudicate(exp, evidence, liquidity_feed=liq_feed, liquidity_fallback_feed=fallback_feed)
        last_dec = exp.promotion_history[-1]
        prov = last_dec.execution_report.market_data_provenance
        assert prov.fallback_applied is True
        assert prov.fallback_reason == "LIQUIDITY_ERROR_FALLBACK"
        assert prov.liquidity_source_mode == "SNAPSHOT"
        assert any("PROVIDER_CRASHED" in e for e in prov.provider_errors)
        assert prov.liquidity_provider_status == "ERROR"

    def test_borrow_fallback_applies_only_when_shorting_required(self, monkeypatch, tmp_path):
        """LAW: borrow fallback is only material for short-required strategies and remains explicit in provenance."""
        _setup_production_safe_env(monkeypatch, tmp_path)
        monkeypatch.setenv("STRATEGY_VALIDATOR_ALLOW_MARKET_DATA_FALLBACK", "True")
        monkeypatch.setenv("STRATEGY_VALIDATOR_ALLOW_SNAPSHOT_MARKET_DATA", "True")

        provider = ResilientMockProvider("CRASHED_BORROW", raise_error=True)
        brw_feed = ProviderBackedBorrowFeed(provider)
        fallback_store = SnapshotStore(borrow=[
            BorrowSnapshot(
                asset_id="AAPL",
                snapshot_time=datetime(2026, 4, 12, tzinfo=timezone.utc),
                borrow_available=True,
                borrow_cost_bps=25.0,
                source_id="BORROW_ARCHIVE",
                source_mode="SNAPSHOT",
            )
        ])
        fallback_feed = SnapshotStoreBorrowFeed(fallback_store)

        exp = _exp("EXP-BORROW-FALLBACK")
        evidence = [Evidence(
            evidence_id="EV-1", experiment_id="EXP-BORROW-FALLBACK",
            evidence_type=EvidenceType.EXECUTION_LOG,
            timestamp=exp.evidence_bundle.evaluation_time_utc,
            payload={"estimated_trade_notional": 1000.0, "requires_shorting": True},
            source_module="TEST", checksum="a"*64
        )]

        adjudicate(exp, evidence, borrow_feed=brw_feed, borrow_fallback_feed=fallback_feed)
        last_dec = exp.promotion_history[-1]
        prov = last_dec.execution_report.market_data_provenance
        assert prov.fallback_applied is True
        assert prov.fallback_reason == "BORROW_ERROR_FALLBACK"
        assert prov.borrow_source_mode == "SNAPSHOT"
        assert prov.borrow_source_id == "BORROW_ARCHIVE"
        assert prov.borrow_provider_status == "ERROR"


    def test_provider_retry_recovers_before_blocking(self, monkeypatch, tmp_path):
        """LAW: provider retries may recover, but retry provenance must be sealed."""
        _setup_production_safe_env(monkeypatch, tmp_path)
        provider = FlakyTimeoutProvider("FLAKY_FEED", fail_count=1)
        liq_feed = ProviderBackedLiquidityFeed(provider, policy=ProviderResiliencePolicy(max_retries=1, circuit_breaker_threshold=2, circuit_cooldown_seconds=120))

        exp = _exp("EXP-RETRY-RECOVER")
        evidence = [Evidence(
            evidence_id="EV-1", experiment_id="EXP-RETRY-RECOVER",
            evidence_type=EvidenceType.EXECUTION_LOG,
            timestamp=exp.evidence_bundle.evaluation_time_utc,
            payload={"estimated_trade_notional": 1000.0},
            source_module="TEST", checksum="a"*64
        )]

        adjudicate(exp, evidence, liquidity_feed=liq_feed)
        prov = exp.promotion_history[-1].execution_report.market_data_provenance
        assert prov.liquidity_provider_status == "SUCCESS"
        assert prov.liquidity_retry_count == 1
        assert prov.liquidity_circuit_state == "CLOSED"
        assert prov.liquidity_source_mode == "LIVE"

    def test_provider_timeout_trips_circuit_and_blocks(self, monkeypatch, tmp_path):
        """LAW: repeated provider timeouts must trip the circuit and subsequent lookups must surface CIRCUIT_OPEN."""
        _setup_production_safe_env(monkeypatch, tmp_path)
        provider = FlakyTimeoutProvider("BROKEN_FEED", fail_count=10)
        liq_feed = ProviderBackedLiquidityFeed(provider, policy=ProviderResiliencePolicy(max_retries=0, circuit_breaker_threshold=2, circuit_cooldown_seconds=300))

        exp1 = _exp("EXP-CIRCUIT-1")
        exp2 = _exp("EXP-CIRCUIT-2")
        exp3 = _exp("EXP-CIRCUIT-3")
        evidence = [Evidence(
            evidence_id="EV-1", experiment_id="EXP-CIRCUIT-1",
            evidence_type=EvidenceType.EXECUTION_LOG,
            timestamp=exp1.evidence_bundle.evaluation_time_utc,
            payload={"estimated_trade_notional": 1000.0},
            source_module="TEST", checksum="a"*64
        )]
        adjudicate(exp1, evidence, liquidity_feed=liq_feed)

        evidence2 = [Evidence(
            evidence_id="EV-2", experiment_id="EXP-CIRCUIT-2",
            evidence_type=EvidenceType.EXECUTION_LOG,
            timestamp=exp2.evidence_bundle.evaluation_time_utc,
            payload={"estimated_trade_notional": 1000.0},
            source_module="TEST", checksum="b"*64
        )]
        state2 = adjudicate(exp2, evidence2, liquidity_feed=liq_feed)
        prov2 = exp2.promotion_history[-1].execution_report.market_data_provenance
        assert state2 == PromotionState.REJECTED
        assert prov2.liquidity_provider_status == "TIMEOUT"
        assert prov2.liquidity_circuit_state == "OPEN"

        evidence3 = [Evidence(
            evidence_id="EV-3", experiment_id="EXP-CIRCUIT-3",
            evidence_type=EvidenceType.EXECUTION_LOG,
            timestamp=exp3.evidence_bundle.evaluation_time_utc,
            payload={"estimated_trade_notional": 1000.0},
            source_module="TEST", checksum="c"*64
        )]
        state3 = adjudicate(exp3, evidence3, liquidity_feed=liq_feed)
        prov3 = exp3.promotion_history[-1].execution_report.market_data_provenance
        assert state3 == PromotionState.REJECTED
        assert prov3.liquidity_provider_status == "CIRCUIT_OPEN"
        assert prov3.liquidity_circuit_state == "OPEN"
        assert any("CIRCUIT_OPEN" in e for e in prov3.provider_errors)

    def test_timeout_falls_back_to_snapshot_when_allowed(self, monkeypatch, tmp_path):
        """LAW: timeout fallback must be explicit and never misreported as LIVE."""
        _setup_production_safe_env(monkeypatch, tmp_path)
        monkeypatch.setenv("STRATEGY_VALIDATOR_ALLOW_MARKET_DATA_FALLBACK", "True")
        monkeypatch.setenv("STRATEGY_VALIDATOR_ALLOW_SNAPSHOT_MARKET_DATA", "True")

        provider = FlakyTimeoutProvider("TIMEOUT_FEED", fail_count=10)
        liq_feed = ProviderBackedLiquidityFeed(provider, policy=ProviderResiliencePolicy(max_retries=1, circuit_breaker_threshold=3, circuit_cooldown_seconds=120))
        fallback_store = SnapshotStore(liquidity=[
            LiquiditySnapshot(
                asset_id="AAPL",
                snapshot_time=datetime(2026, 4, 12, tzinfo=timezone.utc),
                adv_notional=3_000_000.0,
                spread_bps=2.0,
                source_id="ARCHIVE_TIMEOUT",
                source_mode="SNAPSHOT",
            )
        ])
        fallback_feed = SnapshotStoreLiquidityFeed(fallback_store)

        exp = _exp("EXP-TIMEOUT-FALLBACK")
        evidence = [Evidence(
            evidence_id="EV-1", experiment_id="EXP-TIMEOUT-FALLBACK",
            evidence_type=EvidenceType.EXECUTION_LOG,
            timestamp=exp.evidence_bundle.evaluation_time_utc,
            payload={"estimated_trade_notional": 1000.0},
            source_module="TEST", checksum="a"*64
        )]

        adjudicate(exp, evidence, liquidity_feed=liq_feed, liquidity_fallback_feed=fallback_feed)
        prov = exp.promotion_history[-1].execution_report.market_data_provenance
        assert prov.fallback_applied is True
        assert prov.fallback_reason == "LIQUIDITY_TIMEOUT_FALLBACK"
        assert prov.liquidity_source_mode == "SNAPSHOT"
        assert prov.liquidity_provider_status == "TIMEOUT"
        assert prov.liquidity_retry_count == 1
        assert any("LIQUIDITY_TIMEOUT" in e for e in prov.provider_errors)


def test_lenient_5xx_policy_does_not_trip_circuit_counter() -> None:
    t = datetime(2026, 4, 12, 12, 0, 0, tzinfo=timezone.utc)
    pol = ProviderResiliencePolicy(
        max_retries=0,
        circuit_breaker_threshold=2,
        circuit_cooldown_seconds=60,
        vendor_outage_circuit_policy="LENIENT_TRANSIENT_5XX",
    )
    feed = ProviderBackedLiquidityFeed(Vendor503Provider(), policy=pol)
    assert feed.lookup("SPY", t) is None
    assert feed.lookup("SPY", t) is None
    assert feed.last_lookup_metadata is not None
    assert feed.last_lookup_metadata.circuit_state == "CLOSED"


def test_standard_policy_5xx_advances_circuit() -> None:
    t = datetime(2026, 4, 12, 12, 0, 0, tzinfo=timezone.utc)
    pol = ProviderResiliencePolicy(
        max_retries=0,
        circuit_breaker_threshold=2,
        circuit_cooldown_seconds=60,
        vendor_outage_circuit_policy="STANDARD",
    )
    feed = ProviderBackedLiquidityFeed(Vendor503Provider(), policy=pol)
    assert feed.lookup("SPY", t) is None
    assert feed.lookup("SPY", t) is None
    assert feed.last_lookup_metadata.circuit_state == "OPEN"
