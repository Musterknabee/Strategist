"""Freshness law: borrow and liquidity fail independently."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from strategy_validator.contracts.evidence import Evidence, EvidenceBundle, ReproducibilityManifest
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.market_data import BorrowSnapshot, LiquiditySnapshot, ProviderResiliencePolicy
from strategy_validator.core.enums import EvidenceType, PromotionState
from strategy_validator.validator.market_data_feeds import (
    ProviderBackedBorrowFeed,
    ProviderBackedLiquidityFeed,
    SnapshotStore,
    SnapshotStoreBorrowFeed,
    SnapshotStoreLiquidityFeed,
)
from strategy_validator.validator.orchestrator import adjudicate
from tests.constitutional.test_market_data_resilience import ResilientMockProvider


def _repro() -> ReproducibilityManifest:
    return ReproducibilityManifest(
        code_hash="a" * 64,
        data_snapshot_hash="b" * 64,
        universe_hash="c" * 64,
        feature_graph_hash="d" * 64,
        parameter_manifest_hash="e" * 64,
        benchmark_version="bench-v1",
        cost_model_version="v1",
        calendar_version="v1",
    )


def _exp(eid: str) -> ExperimentManifest:
    bundle = EvidenceBundle(
        reproducibility=_repro(),
        benchmark_rung="L1",
        search_breadth=3,
        evaluation_time_utc=datetime(2026, 4, 12, tzinfo=timezone.utc),
        market_data_subject_id="AAPL",
        decoy_survival_passed=True,
        decoy_suite_version="v1",
        decoy_coverage=1.0,
        cpcv_passed=True,
        cpcv_folds=5,
        cpcv_path_coverage=1.0,
        cpcv_path_stability=0.1,
        incrementality_significant=True,
        dsr_estimate=0.5,
        pbo_estimate=0.1,
    )
    return ExperimentManifest(
        experiment_id=eid,
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=bundle,
        state=PromotionState.QUARANTINED,
    )


def _setup_production_safe_env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    db_path = tmp_path / "fresh_borrow.sqlite3"
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(db_path.absolute()))


@pytest.mark.constitutional
def test_fresh_liquidity_stale_borrow_blocks_independently(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """LAW: borrow can be STALE while liquidity is FRESH; strict production fails closed on borrow staleness."""
    _setup_production_safe_env(monkeypatch, tmp_path)

    liq = ProviderBackedLiquidityFeed(ResilientMockProvider("FRESH_LIQ", staleness_delta=timedelta(seconds=0)))
    brw = ProviderBackedBorrowFeed(ResilientMockProvider("STALE_BRW", staleness_delta=timedelta(seconds=120)))

    exp = _exp("FB-1")
    evidence = [
        Evidence(
            evidence_id="e1",
            experiment_id="FB-1",
            evidence_type=EvidenceType.COST_SUMMARY,
            timestamp=datetime(2026, 4, 1, tzinfo=timezone.utc),
            payload={
                "benchmark_delta": 0.5,
                "benchmark_passed": True,
                "benchmark_id": "L1_BMK",
                "benchmark_version": "bench-v1",
                "strategy_return": 0.05,
                "benchmark_return": 0.02,
                "horizon": "1y",
                "estimated_trade_notional": 1000.0,
                "estimated_participation_rate": 0.01,
                "requires_shorting": True,
            },
            source_module="t",
            checksum="abc",
        )
    ]
    adjudicate(exp, evidence, liquidity_feed=liq, borrow_feed=brw)
    prov = exp.promotion_history[-1].execution_report.market_data_provenance
    assert prov.liquidity_freshness_status == "FRESH"
    assert prov.borrow_freshness_status == "STALE"
    notes = exp.promotion_history[-1].summary_notes
    assert any("stale market data" in n for n in notes) or any("STRICT_PRODUCTION_BLOCKER" in n for n in notes)
    assert exp.promotion_history[-1].new_state in (
        PromotionState.REJECTED,
        PromotionState.INVALID,
    )


@pytest.mark.constitutional
def test_borrow_fallback_when_liquidity_stale_only(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """LAW: explicit borrow fallback does not mask independent liquidity staleness."""
    _setup_production_safe_env(monkeypatch, tmp_path)
    monkeypatch.setenv("STRATEGY_VALIDATOR_ALLOW_MARKET_DATA_FALLBACK", "True")
    monkeypatch.setenv("STRATEGY_VALIDATOR_ALLOW_SNAPSHOT_MARKET_DATA", "True")

    liq = ProviderBackedLiquidityFeed(ResilientMockProvider("STALE_LIQ", staleness_delta=timedelta(seconds=300)))
    brw = ProviderBackedBorrowFeed(ResilientMockProvider("STALE_BRW", staleness_delta=timedelta(seconds=300)))

    fb_liq = SnapshotStoreLiquidityFeed(
        SnapshotStore(
            liquidity=[
                LiquiditySnapshot(
                    asset_id="AAPL",
                    snapshot_time=datetime(2026, 4, 12, tzinfo=timezone.utc),
                    adv_notional=2_000_000.0,
                    spread_bps=2.0,
                    source_id="snap_liq",
                    source_mode="SNAPSHOT",
                )
            ]
        )
    )
    fb_brw = SnapshotStoreBorrowFeed(
        SnapshotStore(
            borrow=[
                BorrowSnapshot(
                    asset_id="AAPL",
                    snapshot_time=datetime(2026, 4, 12, tzinfo=timezone.utc),
                    borrow_available=True,
                    borrow_cost_bps=30.0,
                    source_id="snap_brw",
                    source_mode="SNAPSHOT",
                )
            ]
        )
    )

    exp = _exp("FB-2")
    evidence = [
        Evidence(
            evidence_id="e1",
            experiment_id="FB-2",
            evidence_type=EvidenceType.COST_SUMMARY,
            timestamp=datetime(2026, 4, 1, tzinfo=timezone.utc),
            payload={
                "benchmark_delta": 0.5,
                "benchmark_passed": True,
                "benchmark_id": "L1_BMK",
                "benchmark_version": "bench-v1",
                "strategy_return": 0.05,
                "benchmark_return": 0.02,
                "horizon": "1y",
                "estimated_trade_notional": 1000.0,
                "estimated_participation_rate": 0.01,
                "requires_shorting": True,
            },
            source_module="t",
            checksum="abc",
        )
    ]
    adjudicate(
        exp,
        evidence,
        liquidity_feed=liq,
        borrow_feed=brw,
        liquidity_fallback_feed=fb_liq,
        borrow_fallback_feed=fb_brw,
    )
    prov = exp.promotion_history[-1].execution_report.market_data_provenance
    assert prov.fallback_applied is True
    assert prov.liquidity_source_mode == "SNAPSHOT"
    assert prov.borrow_source_mode == "SNAPSHOT"
    assert prov.liquidity_freshness_status == "FRESH"
    assert prov.borrow_freshness_status == "FRESH"


@pytest.mark.constitutional
def test_provider_retry_backoff_invoked(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    from tests.constitutional.test_market_data_resilience import FlakyTimeoutProvider

    _setup_production_safe_env(monkeypatch, tmp_path)
    sleeps: list[float] = []

    def fake_sleep(sec: float) -> None:
        sleeps.append(sec)

    monkeypatch.setattr("strategy_validator.validator.market_data_feeds.time.sleep", fake_sleep)

    provider = FlakyTimeoutProvider("FLAKY", fail_count=2)
    liq = ProviderBackedLiquidityFeed(
        provider,
        policy=ProviderResiliencePolicy(max_retries=2, retry_backoff_ms=100, circuit_breaker_threshold=5, circuit_cooldown_seconds=60),
    )
    exp = _exp("BK-1")
    evidence = [
        Evidence(
            evidence_id="e1",
            experiment_id="BK-1",
            evidence_type=EvidenceType.EXECUTION_LOG,
            timestamp=exp.evidence_bundle.evaluation_time_utc,
            payload={"estimated_trade_notional": 1000.0},
            source_module="TEST",
            checksum="a" * 64,
        )
    ]
    adjudicate(exp, evidence, liquidity_feed=liq)
    assert len(sleeps) >= 2
    assert all(s == 0.1 for s in sleeps)
