"""Provider lookup metadata surfaces as typed vendor_failure_events on execution realism."""
from __future__ import annotations

from datetime import datetime, timezone

from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.market_data import LiquiditySnapshot, ProviderLookupMetadata
from strategy_validator.core.config import RuntimePolicy
from strategy_validator.core.enums import EvidenceType
from strategy_validator.validator.orchestrator import _evaluate_execution_realism


class _LiquidityFeedWithMeta:
    provider_id = "test_vendor"

    def __init__(self) -> None:
        self.last_lookup_metadata = ProviderLookupMetadata(
            provider_id="test_vendor",
            feed_kind="liquidity",
            status="ERROR",
            error_summary="alpaca_http_429 rate limited",
            failure_domain="RATE_LIMIT",
            failure_code="HTTP_429",
        )

    def lookup(self, asset_id: str, timestamp: datetime) -> LiquiditySnapshot:
        return LiquiditySnapshot(
            asset_id=asset_id,
            snapshot_time=timestamp,
            adv_notional=2e9,
            spread_bps=2.0,
            source_id="test_vendor",
            source_mode="LIVE",
        )


def test_liquidity_meta_error_emits_vendor_failure_event():
    t = datetime(2024, 6, 3, 14, 30, 0, tzinfo=timezone.utc)
    ev = Evidence(
        evidence_id="ev-1",
        experiment_id="exp-vendor",
        evidence_type=EvidenceType.OUT_OF_SAMPLE_AUDIT,
        timestamp=t,
        payload={
            "estimated_trade_notional": 1_000_000.0,
            "estimated_participation_rate": 0.01,
        },
        source_module="test",
        checksum="f" * 64,
    )
    policy = RuntimePolicy()
    res = _evaluate_execution_realism(
        [ev],
        1.0,
        evaluation_time_utc=t,
        market_data_subject_id="SPY",
        liquidity_feed=_LiquidityFeedWithMeta(),
        policy=policy,
    )
    mdp = res.market_data_provenance
    assert mdp is not None
    assert mdp.vendor_failure_events
    assert mdp.vendor_failure_events[0].domain == "RATE_LIMIT"
    assert mdp.vendor_failure_events[0].feed_kind == "liquidity"
    assert mdp.vendor_failure_events[0].provider_id == "test_vendor"
