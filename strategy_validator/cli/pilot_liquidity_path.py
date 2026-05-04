"""
Lawful liquidity primary + optional snapshot fallback for pilot NDJSON.

Mirrors ``orchestrator._evaluate_execution_realism`` liquidity block (no borrow,
no evidence). Importing this module loads ``validator.orchestrator`` once for
shared helpers; behavior is intended to stay aligned with adjudication.
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Optional

from strategy_validator.contracts.execution import MarketDataProvenance
from strategy_validator.contracts.market_data import FreshnessResult, LiquidityFeed, LiquiditySnapshot
from strategy_validator.contracts.vendor_runtime import VendorFailureEvent
from strategy_validator.core.config import RuntimePolicy
from strategy_validator.validator import orchestrator as _orch


def run_liquidity_resolution_probe_round(
    *,
    liquidity_feed: LiquidityFeed,
    liquidity_fallback_feed: Optional[LiquidityFeed],
    symbol: str,
    evaluation_time_utc: datetime,
    policy: RuntimePolicy,
    round_index: int,
    interface_freeze: str,
    primary_provider_id: str,
) -> dict[str, Any]:
    prov = MarketDataProvenance(
        evaluation_time_utc=evaluation_time_utc,
        market_data_subject_id=symbol,
    )
    t_wall0 = time.perf_counter()
    primary_dt_ms = 0.0
    fallback_dt_ms = 0.0

    prov.liquidity_provider_status = "NOT_CONFIGURED"
    prov.liquidity_freshness_status = "MISSING"

    primary_snap: Optional[LiquiditySnapshot] = None
    primary_freshness = _orch._evaluate_snapshot_freshness(None, evaluation_time_utc, policy)
    try:
        t0 = time.perf_counter()
        primary_snap = liquidity_feed.lookup(symbol, evaluation_time_utc)
        primary_dt_ms = (time.perf_counter() - t0) * 1000.0
        meta = _orch._get_feed_lookup_metadata(liquidity_feed)
        if meta is not None:
            prov.liquidity_retry_count = meta.retry_count
            prov.liquidity_circuit_state = meta.circuit_state
            prov.liquidity_provider_status = meta.status
            if meta.error_summary:
                line = f"LIQUIDITY_LOOKUP_ERROR: {meta.error_summary}"
                prov.provider_errors.append(line)
                if meta.failure_domain and meta.failure_code:
                    prov.vendor_failure_events.append(
                        VendorFailureEvent(
                            domain=_orch._as_vendor_domain(meta.failure_domain),
                            code=meta.failure_code or "UNSPECIFIED",
                            detail=meta.error_summary[:2048],
                            feed_kind="liquidity",
                            provider_id=meta.provider_id or "unknown",
                        )
                    )
                else:
                    prov.vendor_failure_events.append(
                        _orch.classify_vendor_failure_detail(
                            meta.error_summary,
                            feed_kind="liquidity",
                            provider_id=meta.provider_id or "unknown",
                        )
                    )
        primary_freshness = _orch._evaluate_snapshot_freshness(primary_snap, evaluation_time_utc, policy)
        if meta is None:
            if primary_snap is None:
                prov.liquidity_provider_status = "MISSING"
            elif primary_freshness.status == "STALE":
                prov.liquidity_provider_status = "STALE"
            else:
                prov.liquidity_provider_status = "SUCCESS"
        elif primary_snap is not None and primary_freshness.status == "STALE" and prov.liquidity_provider_status == "SUCCESS":
            prov.liquidity_provider_status = "STALE"
        elif primary_snap is None and prov.liquidity_provider_status == "SUCCESS":
            prov.liquidity_provider_status = "MISSING"
    except Exception as e:
        _orch._append_lookup_exception(
            prov,
            prefix="LIQUIDITY_LOOKUP_ERROR",
            feed_kind="liquidity",
            provider_id=_orch._feed_provider_id(liquidity_feed),
            exc=e,
        )
        prov.liquidity_provider_status = "ERROR"
        thr, law = _orch._live_freshness_threshold_seconds(policy, evaluation_time_utc)
        primary_freshness = FreshnessResult(
            status="ERROR",
            threshold_seconds=thr,
            applied_threshold_seconds=thr,
            market_hours_law=law,
            as_of_utc=evaluation_time_utc,
        )

    effective_snap: Optional[LiquiditySnapshot] = None
    effective_freshness = primary_freshness
    if primary_snap is not None and primary_freshness.is_acceptable():
        effective_snap = primary_snap
    elif policy.allow_market_data_fallback:
        fallback_reason = {
            "ERROR": "LIQUIDITY_ERROR_FALLBACK",
            "TIMEOUT": "LIQUIDITY_TIMEOUT_FALLBACK",
            "CIRCUIT_OPEN": "LIQUIDITY_CIRCUIT_OPEN_FALLBACK",
            "STALE": "LIQUIDITY_STALE_FALLBACK",
            "MISSING": "LIQUIDITY_MISSING_FALLBACK",
            "UNKNOWN": "LIQUIDITY_UNKNOWN_FALLBACK",
        }.get(prov.liquidity_provider_status or primary_freshness.status, "LIQUIDITY_POLICY_ALLOWED_FALLBACK")
        t1 = time.perf_counter()
        fallback_snap = _orch._try_market_data_fallback(
            fallback_feed=liquidity_fallback_feed,
            asset_id=symbol,
            evaluation_time_utc=evaluation_time_utc,
            policy=policy,
            kind="liquidity",
            provenance=prov,
            fallback_reason=fallback_reason,
        )
        fallback_dt_ms = (time.perf_counter() - t1) * 1000.0
        if fallback_snap is not None:
            effective_snap = fallback_snap
            effective_freshness = _orch._evaluate_snapshot_freshness(fallback_snap, evaluation_time_utc, policy)

    if effective_snap is not None:
        _orch._record_effective_snapshot(
            prov, kind="liquidity", snapshot=effective_snap, freshness_status=effective_freshness.status
        )
    else:
        _orch._record_effective_snapshot(
            prov, kind="liquidity", snapshot=primary_snap, freshness_status=primary_freshness.status
        )

    if effective_freshness.market_hours_law:
        prov.liquidity_market_hours_law = effective_freshness.market_hours_law

    wall_ms = (time.perf_counter() - t_wall0) * 1000.0
    age_s = None
    if effective_snap is not None:
        age_s = (evaluation_time_utc - effective_snap.snapshot_time).total_seconds()

    meta = _orch._get_feed_lookup_metadata(liquidity_feed)
    vfe_json = [e.model_dump(mode="json") for e in prov.vendor_failure_events]

    return {
        "pilot_schema": "2",
        "interface_freeze": interface_freeze,
        "round": round_index,
        "symbol": symbol,
        "evaluated_at_utc": evaluation_time_utc.isoformat(),
        "primary_provider_id": primary_provider_id,
        "latency_ms": round(wall_ms, 3),
        "primary_latency_ms": round(primary_dt_ms, 3),
        "fallback_latency_ms": round(fallback_dt_ms, 3),
        "snapshot_present": effective_snap is not None,
        "effective_source_mode": getattr(effective_snap, "source_mode", None) if effective_snap else None,
        "primary_freshness_status": primary_freshness.status,
        "effective_freshness_status": effective_freshness.status,
        "freshness_threshold_seconds": primary_freshness.applied_threshold_seconds,
        "market_hours_law": primary_freshness.market_hours_law,
        "liquidity_market_hours_law": prov.liquidity_market_hours_law,
        "provider_status": prov.liquidity_provider_status,
        "circuit_state": prov.liquidity_circuit_state,
        "retry_count": prov.liquidity_retry_count,
        "error_summary": getattr(meta, "error_summary", None) if meta is not None else None,
        "failure_domain": getattr(meta, "failure_domain", None) if meta is not None else None,
        "failure_code": getattr(meta, "failure_code", None) if meta is not None else None,
        "snapshot_age_s": age_s,
        "fallback_applied": prov.fallback_applied,
        "fallback_reason": prov.fallback_reason,
        "provider_errors": list(prov.provider_errors),
        "vendor_failure_events": vfe_json,
    }
