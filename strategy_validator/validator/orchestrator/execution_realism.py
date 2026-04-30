"""Execution realism and benchmark helpers for the adjudication orchestrator."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Iterable, Literal, Optional, cast

from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.benchmarks import BENCHMARK_RUNG_REGISTRY, BenchmarkResult
from strategy_validator.contracts.execution import (
    ExecutionRealismResult,
    ExecutionStressResult,
    CapacityEvidence,
    BorrowEvidence,
    MarketDataProvenance,
)
from strategy_validator.contracts.market_data import (
    BorrowFeed,
    BorrowSnapshot,
    FreshnessResult,
    LiquidityFeed,
    LiquiditySnapshot,
    ProviderLookupMetadata,
)
from strategy_validator.contracts.vendor_runtime import (
    VendorFailureDomain,
    VendorFailureEvent,
    classify_vendor_failure_detail,
)
from strategy_validator.core.config import RuntimePolicy
from strategy_validator.core.enums import EvidenceType
from strategy_validator.validator.calibration_curve import interpolate_impact_bps
from strategy_validator.validator.calibration_loader import load_calibration_artifact_from_path
from strategy_validator.validator.cost_engine import evidence_uses_midpoint_only_economics
from strategy_validator.validator.market_hours import us_equities_regular_session_open

_VENDOR_DOMAINS: frozenset[str] = frozenset(
    {
        "NETWORK",
        "AUTH",
        "RATE_LIMIT",
        "VENDOR_4XX",
        "VENDOR_5XX",
        "TIMEOUT",
        "CIRCUIT",
        "SCHEMA",
        "MISSING",
        "UNKNOWN",
    }
)

def _live_freshness_threshold_seconds(policy: RuntimePolicy, as_of: datetime) -> tuple[float, str]:
    """Return (threshold_seconds, market_hours_law_label) for LIVE age evaluation."""
    base = float(policy.live_market_data_freshness_threshold_seconds)
    if policy.live_freshness_market_hours_profile != "US_EQUITIES_RTH":
        return base, "DISABLED"
    if us_equities_regular_session_open(as_of):
        return base, "US_RTH_OPEN"
    return float(policy.live_market_data_freshness_off_hours_threshold_seconds), "US_RTH_CLOSED"


def _append_lookup_exception(
    prov: MarketDataProvenance,
    *,
    prefix: str,
    feed_kind: Literal["liquidity", "borrow"],
    provider_id: str,
    exc: BaseException,
) -> None:
    human = f"{prefix}: {str(exc)}"
    prov.provider_errors.append(human)
    prov.vendor_failure_events.append(
        classify_vendor_failure_detail(str(exc), feed_kind=feed_kind, provider_id=provider_id)
    )


def _evaluate_snapshot_freshness(
    snapshot: Optional[LiquiditySnapshot | BorrowSnapshot],
    as_of: Optional[datetime],
    policy: RuntimePolicy,
) -> FreshnessResult:
    """
    Lawfully evaluate the freshness of a market-data snapshot (LIVE age law + optional market-hours).
    """
    effective_as_of = as_of
    if effective_as_of is None and snapshot is not None:
        effective_as_of = snapshot.snapshot_time
    if effective_as_of is None:
        effective_as_of = datetime(1970, 1, 1, tzinfo=timezone.utc)
    threshold, session_law = _live_freshness_threshold_seconds(policy, effective_as_of)
    if snapshot is None:
        return FreshnessResult(
            status="MISSING",
            threshold_seconds=threshold,
            applied_threshold_seconds=threshold,
            market_hours_law=session_law,
            as_of_utc=effective_as_of,
        )

    # PROVISIONAL and SNAPSHOT are exempt from 'live' freshness law (they are by definition non-live)
    if snapshot.source_mode != "LIVE":
        return FreshnessResult(
            status="FRESH",
            age_seconds=0.0,
            threshold_seconds=threshold,
            applied_threshold_seconds=threshold,
            market_hours_law=session_law,
            as_of_utc=effective_as_of,
        )

    age = (effective_as_of - snapshot.snapshot_time).total_seconds()
    status = "FRESH" if age <= threshold else "STALE"

    return FreshnessResult(
        status=status,
        age_seconds=age,
        threshold_seconds=threshold,
        applied_threshold_seconds=threshold,
        market_hours_law=session_law,
        as_of_utc=effective_as_of,
    )


def _as_vendor_domain(s: Optional[str]) -> VendorFailureDomain:
    if s in _VENDOR_DOMAINS:
        return cast(VendorFailureDomain, s)
    return "UNKNOWN"


def _feed_provider_id(feed: object) -> str:
    lm = getattr(feed, "last_lookup_metadata", None)
    if isinstance(lm, ProviderLookupMetadata):
        return lm.provider_id or "unknown"
    pid = getattr(feed, "provider_id", None)
    if isinstance(pid, str) and pid:
        return pid
    return "unknown"


def _coerce_as_of(evaluation_time_utc: Optional[datetime]) -> datetime:
    return evaluation_time_utc or datetime(1970, 1, 1, tzinfo=timezone.utc)


def _get_feed_lookup_metadata(feed: Optional[LiquidityFeed | BorrowFeed]) -> Optional[ProviderLookupMetadata]:
    meta = getattr(feed, "last_lookup_metadata", None)
    return meta if isinstance(meta, ProviderLookupMetadata) else None
def _record_effective_snapshot(
    provenance: MarketDataProvenance,
    *,
    kind: str,
    snapshot: Optional[LiquiditySnapshot | BorrowSnapshot],
    freshness_status: str,
) -> None:
    if kind == "liquidity":
        provenance.liquidity_freshness_status = freshness_status
        provenance.liquidity_source_mode = snapshot.source_mode if snapshot is not None else "NONE"
        provenance.liquidity_snapshot_hash = snapshot.snapshot_hash if snapshot is not None else None
        provenance.liquidity_source_id = snapshot.source_id if snapshot is not None else None
    else:
        provenance.borrow_freshness_status = freshness_status
        provenance.borrow_source_mode = snapshot.source_mode if snapshot is not None else "NONE"
        provenance.borrow_snapshot_hash = snapshot.snapshot_hash if snapshot is not None else None
        provenance.borrow_source_id = snapshot.source_id if snapshot is not None else None


def _try_market_data_fallback(
    *,
    fallback_feed: Optional[LiquidityFeed | BorrowFeed],
    asset_id: Optional[str],
    evaluation_time_utc: datetime,
    policy: RuntimePolicy,
    kind: str,
    provenance: MarketDataProvenance,
    fallback_reason: str,
) -> Optional[LiquiditySnapshot | BorrowSnapshot]:
    if fallback_feed is None or asset_id is None:
        return None
    fk_fb: Literal["fallback_liquidity", "fallback_borrow"] = (
        "fallback_liquidity" if kind == "liquidity" else "fallback_borrow"
    )
    try:
        snap = fallback_feed.lookup(asset_id, evaluation_time_utc)
    except Exception as e:
        line = f"{kind.upper()}_FALLBACK_LOOKUP_ERROR: {str(e)}"
        provenance.provider_errors.append(line)
        provenance.vendor_failure_events.append(
            classify_vendor_failure_detail(str(e), feed_kind=fk_fb, provider_id="fallback_feed")
        )
        return None
    meta = _get_feed_lookup_metadata(fallback_feed)
    if meta is not None:
        if kind == "liquidity":
            provenance.liquidity_retry_count = meta.retry_count
            provenance.liquidity_circuit_state = meta.circuit_state
        else:
            provenance.borrow_retry_count = meta.retry_count
            provenance.borrow_circuit_state = meta.circuit_state
        if meta.error_summary:
            line = f"{kind.upper()}_FALLBACK_PROVIDER: {meta.error_summary}"
            if line not in provenance.provider_errors:
                provenance.provider_errors.append(line)
            if meta.failure_domain and meta.failure_code:
                provenance.vendor_failure_events.append(
                    VendorFailureEvent(
                        domain=_as_vendor_domain(meta.failure_domain),
                        code=meta.failure_code or "UNSPECIFIED",
                        detail=meta.error_summary[:2048],
                        feed_kind=fk_fb,
                        provider_id=meta.provider_id or "unknown",
                    )
                )
            else:
                provenance.vendor_failure_events.append(
                    classify_vendor_failure_detail(
                        meta.error_summary,
                        feed_kind=fk_fb,
                        provider_id=meta.provider_id or "unknown",
                    )
                )
    freshness = _evaluate_snapshot_freshness(snap, evaluation_time_utc, policy)
    if snap is None or freshness.status in {"MISSING", "ERROR", "UNKNOWN"}:
        return None
    provenance.fallback_applied = True
    provenance.fallback_reason = fallback_reason
    _record_effective_snapshot(provenance, kind=kind, snapshot=snap, freshness_status=freshness.status)
    return snap


def _evaluate_execution_realism(
    evidence: Iterable[Evidence],
    multiplier: float,
    *,
    evaluation_time_utc: datetime,
    market_data_subject_id: Optional[str] = None,
    liquidity_feed: Optional[LiquidityFeed] = None,
    borrow_feed: Optional[BorrowFeed] = None,
    liquidity_fallback_feed: Optional[LiquidityFeed] = None,
    borrow_fallback_feed: Optional[BorrowFeed] = None,
    policy: Optional[RuntimePolicy] = None,
) -> ExecutionRealismResult:
    """
    Hardened execution-realism evaluator with lawful feed-backed snapshots.
    """
    res = ExecutionRealismResult()
    policy = policy or RuntimePolicy()
    calibration_failures: list[str] = []
    midpoint_only = evidence_uses_midpoint_only_economics(evidence)
    res.midpoint_only_flag = midpoint_only

    half_life, latency = None, None
    borrow_instability = False

    # -- Collect raw evidence into typed sub-objects ---------------------------
    cap = CapacityEvidence()
    brw = BorrowEvidence()

    effective_evaluation_time = evaluation_time_utc
    if effective_evaluation_time is None:
        timestamps = [ev.timestamp for ev in evidence if getattr(ev, "timestamp", None) is not None]
        effective_evaluation_time = max(timestamps) if timestamps else _coerce_as_of(None)

    # Provenance tracking
    prov = MarketDataProvenance(
        evaluation_time_utc=effective_evaluation_time,
        market_data_subject_id=market_data_subject_id
    )

    liquidity_source: Optional[LiquiditySnapshot] = None
    borrow_source: Optional[BorrowSnapshot] = None
    borrow_reasons: list[str] = []

    for ev in evidence:
        payload = ev.payload
        if "alpha_half_life_minutes" in payload:
            half_life = float(payload["alpha_half_life_minutes"])
        if "expected_latency_minutes" in payload:
            latency = float(payload["expected_latency_minutes"])
        if "spread_bps" in payload:
            res.spread_bps = float(payload["spread_bps"])
        if "slippage_bps" in payload:
            res.slippage_bps = float(payload["slippage_bps"])
        if "fees_bps" in payload:
            res.fees_bps = float(payload["fees_bps"])

        if "estimated_trade_notional" in payload:
            val = float(payload["estimated_trade_notional"])
            res.estimated_trade_notional = val
            cap.estimated_trade_notional = val
        if "estimated_participation_rate" in payload:
            val = float(payload["estimated_participation_rate"])
            res.estimated_participation_rate = val
            cap.estimated_participation_rate = val
        if "adv_notional_proxy" in payload:
            cap.adv_notional_proxy = float(payload["adv_notional_proxy"])

        if "requires_shorting" in payload:
            val = bool(payload["requires_shorting"])
            res.requires_shorting = val
            brw.requires_shorting = val
        if "borrow_available" in payload:
            val = bool(payload["borrow_available"])
            res.borrow_available = val
            brw.borrow_available = val
        if "borrow_cost_bps" in payload:
            val = float(payload["borrow_cost_bps"])
            res.borrow_cost_bps = val
            brw.borrow_cost_bps = val
        if "locate_required" in payload:
            val = bool(payload["locate_required"])
            res.locate_required = val
            brw.locate_required = val
        if "borrow_recall_risk" in payload:
            borrow_instability = bool(payload["borrow_recall_risk"])

    res.half_life_minutes = half_life
    res.latency_minutes = latency or 0.0

    # -- Liquidity Feed Resilience ---------------------------------------------
    if liquidity_feed is not None and cap.estimated_trade_notional > 0:
        prov.liquidity_provider_status = "NOT_CONFIGURED" if market_data_subject_id is None else None
        if market_data_subject_id is None:
            prov.liquidity_freshness_status = "MISSING"
        else:
            primary_snap: Optional[LiquiditySnapshot] = None
            primary_freshness = _evaluate_snapshot_freshness(None, effective_evaluation_time, policy)
            try:
                primary_snap = liquidity_feed.lookup(market_data_subject_id, effective_evaluation_time)
                meta = _get_feed_lookup_metadata(liquidity_feed)
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
                                    domain=_as_vendor_domain(meta.failure_domain),
                                    code=meta.failure_code or "UNSPECIFIED",
                                    detail=meta.error_summary[:2048],
                                    feed_kind="liquidity",
                                    provider_id=meta.provider_id or "unknown",
                                )
                            )
                        else:
                            prov.vendor_failure_events.append(
                                classify_vendor_failure_detail(
                                    meta.error_summary,
                                    feed_kind="liquidity",
                                    provider_id=meta.provider_id or "unknown",
                                )
                            )
                primary_freshness = _evaluate_snapshot_freshness(primary_snap, effective_evaluation_time, policy)
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
                _append_lookup_exception(
                    prov,
                    prefix="LIQUIDITY_LOOKUP_ERROR",
                    feed_kind="liquidity",
                    provider_id=_feed_provider_id(liquidity_feed),
                    exc=e,
                )
                prov.liquidity_provider_status = "ERROR"
                effective_as_of = _coerce_as_of(effective_evaluation_time)
                thr, law = _live_freshness_threshold_seconds(policy, effective_as_of)
                primary_freshness = FreshnessResult(
                    status="ERROR",
                    threshold_seconds=thr,
                    applied_threshold_seconds=thr,
                    market_hours_law=law,
                    as_of_utc=effective_as_of,
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
                fallback_snap = _try_market_data_fallback(
                    fallback_feed=liquidity_fallback_feed,
                    asset_id=market_data_subject_id,
                    evaluation_time_utc=effective_evaluation_time,
                    policy=policy,
                    kind="liquidity",
                    provenance=prov,
                    fallback_reason=fallback_reason,
                )
                if fallback_snap is not None:
                    effective_snap = fallback_snap
                    effective_freshness = _evaluate_snapshot_freshness(fallback_snap, effective_evaluation_time, policy)

            if effective_snap is not None:
                liquidity_source = effective_snap
                _record_effective_snapshot(prov, kind="liquidity", snapshot=effective_snap, freshness_status=effective_freshness.status)
                if effective_snap.adv_notional > 0:
                    cap.adv_notional_proxy = effective_snap.adv_notional
                if effective_snap.spread_bps > 0:
                    res.spread_bps = effective_snap.spread_bps
                if effective_snap.adv_notional > 0:
                    computed_rate = min(cap.estimated_trade_notional / effective_snap.adv_notional, 1.0)
                    cap.estimated_participation_rate = computed_rate
                    res.estimated_participation_rate = computed_rate
            else:
                _record_effective_snapshot(prov, kind="liquidity", snapshot=primary_snap, freshness_status=primary_freshness.status)

            if effective_freshness.market_hours_law:
                prov.liquidity_market_hours_law = effective_freshness.market_hours_law

    # -- Borrow Feed Resilience ------------------------------------------------
    if borrow_feed is not None and brw.requires_shorting:
        if market_data_subject_id is None:
            borrow_reasons.append("BORROW_LOOKUP_SKIPPED: market_data_subject_id missing")
            prov.borrow_provider_status = "MISSING"
            prov.borrow_freshness_status = "MISSING"
        else:
            primary_snap: Optional[BorrowSnapshot] = None
            primary_freshness = _evaluate_snapshot_freshness(None, effective_evaluation_time, policy)
            try:
                primary_snap = borrow_feed.lookup(market_data_subject_id, effective_evaluation_time)
                meta = _get_feed_lookup_metadata(borrow_feed)
                if meta is not None:
                    prov.borrow_retry_count = meta.retry_count
                    prov.borrow_circuit_state = meta.circuit_state
                    prov.borrow_provider_status = meta.status
                    if meta.error_summary:
                        line = f"BORROW_LOOKUP_ERROR: {meta.error_summary}"
                        prov.provider_errors.append(line)
                        if meta.failure_domain and meta.failure_code:
                            prov.vendor_failure_events.append(
                                VendorFailureEvent(
                                    domain=_as_vendor_domain(meta.failure_domain),
                                    code=meta.failure_code or "UNSPECIFIED",
                                    detail=meta.error_summary[:2048],
                                    feed_kind="borrow",
                                    provider_id=meta.provider_id or "unknown",
                                )
                            )
                        else:
                            prov.vendor_failure_events.append(
                                classify_vendor_failure_detail(
                                    meta.error_summary,
                                    feed_kind="borrow",
                                    provider_id=meta.provider_id or "unknown",
                                )
                            )
                primary_freshness = _evaluate_snapshot_freshness(primary_snap, effective_evaluation_time, policy)
                if meta is None:
                    if primary_snap is None:
                        prov.borrow_provider_status = "MISSING"
                    elif primary_freshness.status == "STALE":
                        prov.borrow_provider_status = "STALE"
                    else:
                        prov.borrow_provider_status = "SUCCESS"
                elif primary_snap is not None and primary_freshness.status == "STALE" and prov.borrow_provider_status == "SUCCESS":
                    prov.borrow_provider_status = "STALE"
                elif primary_snap is None and prov.borrow_provider_status == "SUCCESS":
                    prov.borrow_provider_status = "MISSING"
            except Exception as e:
                _append_lookup_exception(
                    prov,
                    prefix="BORROW_LOOKUP_ERROR",
                    feed_kind="borrow",
                    provider_id=_feed_provider_id(borrow_feed),
                    exc=e,
                )
                prov.borrow_provider_status = "ERROR"
                effective_as_of = _coerce_as_of(effective_evaluation_time)
                thr, law = _live_freshness_threshold_seconds(policy, effective_as_of)
                primary_freshness = FreshnessResult(
                    status="ERROR",
                    threshold_seconds=thr,
                    applied_threshold_seconds=thr,
                    market_hours_law=law,
                    as_of_utc=effective_as_of,
                )

            effective_snap: Optional[BorrowSnapshot] = None
            effective_freshness = primary_freshness
            if primary_snap is not None and primary_freshness.is_acceptable():
                effective_snap = primary_snap
            elif policy.allow_market_data_fallback:
                fallback_reason = {
                    "ERROR": "BORROW_ERROR_FALLBACK",
                    "TIMEOUT": "BORROW_TIMEOUT_FALLBACK",
                    "CIRCUIT_OPEN": "BORROW_CIRCUIT_OPEN_FALLBACK",
                    "STALE": "BORROW_STALE_FALLBACK",
                    "MISSING": "BORROW_MISSING_FALLBACK",
                    "UNKNOWN": "BORROW_UNKNOWN_FALLBACK",
                }.get(prov.borrow_provider_status or primary_freshness.status, "BORROW_POLICY_ALLOWED_FALLBACK")
                fallback_snap = _try_market_data_fallback(
                    fallback_feed=borrow_fallback_feed,
                    asset_id=market_data_subject_id,
                    evaluation_time_utc=effective_evaluation_time,
                    policy=policy,
                    kind="borrow",
                    provenance=prov,
                    fallback_reason=fallback_reason,
                )
                if fallback_snap is not None:
                    effective_snap = fallback_snap
                    effective_freshness = _evaluate_snapshot_freshness(fallback_snap, effective_evaluation_time, policy)

            if effective_snap is not None:
                borrow_source = effective_snap
                _record_effective_snapshot(prov, kind="borrow", snapshot=effective_snap, freshness_status=effective_freshness.status)
                brw.borrow_available = effective_snap.borrow_available
                res.borrow_available = effective_snap.borrow_available
                brw.borrow_cost_bps = effective_snap.borrow_cost_bps
                res.borrow_cost_bps = effective_snap.borrow_cost_bps
                if effective_snap.locate_required is not None:
                    brw.locate_required = effective_snap.locate_required
                    res.locate_required = effective_snap.locate_required
            else:
                _record_effective_snapshot(prov, kind="borrow", snapshot=primary_snap, freshness_status=primary_freshness.status)

            if effective_freshness.market_hours_law:
                prov.borrow_market_hours_law = effective_freshness.market_hours_law

    res.market_data_provenance = prov
    prov.liquidity_source_mode = prov.liquidity_source_mode or (liquidity_source.source_mode if liquidity_source else "NONE")
    prov.borrow_source_mode = prov.borrow_source_mode or (borrow_source.source_mode if borrow_source else "NONE")

    # -- Nonlinear impact model (heuristic vs calibrated; never silent downgrade)
    if cap.estimated_participation_rate > 0:
        sqrt_part = math.sqrt(cap.estimated_participation_rate)
        if policy.capacity_impact_model == "CALIBRATED":
            cal_path = policy.calibration_artifact_path
            if not cal_path:
                res.impact_model_mode = "PROVISIONAL"
                res.nonlinear_impact_bps = 0.0
                calibration_failures.append("CALIBRATION_ARTIFACT_PATH_MISSING")
            else:
                art = load_calibration_artifact_from_path(cal_path)
                if art is None:
                    res.impact_model_mode = "PROVISIONAL"
                    res.nonlinear_impact_bps = 0.0
                    calibration_failures.append("CALIBRATION_ARTIFACT_INVALID_OR_UNREADABLE")
                else:
                    meta = art.to_metadata()
                    res.impact_model_mode = "EMPIRICAL_CALIBRATED"
                    res.impact_calibration_metadata = meta
                    if art.empirical_participation_curve:
                        res.nonlinear_impact_bps = interpolate_impact_bps(
                            cap.estimated_participation_rate,
                            art.empirical_participation_curve,
                        )
                    else:
                        res.nonlinear_impact_bps = sqrt_part * art.nonlinear_sqrt_multiplier
        else:
            res.impact_model_mode = "NONLINEAR_HEURISTIC"
            res.nonlinear_impact_bps = sqrt_part * 600.0
        cap.nonlinear_impact_bps = res.nonlinear_impact_bps
    elif res.spread_bps > 0 or res.slippage_bps > 0 or res.fees_bps > 0:
        res.impact_model_mode = "FIXED_BPS"
    else:
        res.impact_model_mode = "PROVISIONAL"

    # Total post-cost = spread + slippage + fees + nonlinear impact + borrow cost
    res.total_post_cost_bps = (
        res.spread_bps + res.slippage_bps + res.fees_bps
        + res.nonlinear_impact_bps + res.borrow_cost_bps
    )

    # -- Sync typed sub-objects with flat fields (backward compat) -------------
    cap.capacity_limit_passed = True
    brw.shortability_passed = True

    # -- Stress scenarios (deterministically derived from baseline) ------------
    stress = ExecutionStressResult(
        baseline_impact_bps=res.nonlinear_impact_bps,
        stressed_impact_bps=res.nonlinear_impact_bps * 2.5,
        baseline_borrow_cost_bps=res.borrow_cost_bps,
        stressed_borrow_cost_bps=res.borrow_cost_bps * 4.0,
        borrow_recall_risk_flag=borrow_instability,
    )

    stress_passed = True
    if borrow_instability and res.requires_shorting:
        stress_passed = False
        stress.failure_reason = "RECALL_RISK: Substantial borrow instability detected."
    elif (stress.stressed_impact_bps + stress.stressed_borrow_cost_bps) > 1000:
        stress_passed = False
        stress.failure_reason = "ADVERSE_LIQUIDITY: Stress costs exceed 1000bps threshold."
    stress.passed = stress_passed
    res.stress_report = stress

    # -- Binding gate evaluation -----------------------------------------------
    passed = True
    reasons: list[str] = []
    reasons.extend(calibration_failures)
    capacity_reasons: list[str] = []

    # Gate A: Midpoint-only economics are inadmissible
    if midpoint_only:
        passed = False
        reasons.append("MIDPOINT_OPTIMISM: Midpoint-only economics restricted.")

    # Gate B: Alpha decay vs latency
    if half_life is not None and latency is not None:
        if half_life < (latency * multiplier):
            passed = False
            reasons.append(f"ALPHA_DECAY: Half-life ({half_life}m) < {multiplier}x Latency ({latency}m)")

    # Gate C: Capacity limits (participation hard cap + nonlinear degradation)
    if cap.estimated_participation_rate > 0.1:
        passed = False
        cap.capacity_limit_passed = False
        cap.degradation_reason = f"EXCESSIVE_PARTICIPATION: {cap.estimated_participation_rate:.2%} > 10% cap"
        capacity_reasons.append(cap.degradation_reason)
        res.capacity_note = "NONLINEAR_IMPACT_FATAL"
    elif cap.estimated_participation_rate > 0:
        if res.nonlinear_impact_bps > 0:
            src_label = "feed-backed" if liquidity_source is not None else "payload-asserted"
            capacity_reasons.append(
                f"NONLINEAR_IMPACT_APPLIED: {res.nonlinear_impact_bps:.1f}bps at {cap.estimated_participation_rate:.2%} participation ({src_label})"
            )

    # Gate D: Borrow / shortability (binding)
    if brw.requires_shorting:
        if not brw.borrow_available:
            brw.shortability_passed = False
            brw.degradation_reason = "BORROW_UNAVAILABLE"
            borrow_reasons.append(brw.degradation_reason)
        elif brw.borrow_cost_bps > 500:
            brw.shortability_passed = False
            brw.degradation_reason = "PROHIBITIVE_BORROW_COST"
            borrow_reasons.append(brw.degradation_reason)
    else:
        brw.shortability_passed = True

    # Gate E: Honest degradation for missing borrow evidence
    if brw.requires_shorting and brw.borrow_available and brw.borrow_cost_bps == 0.0:
        brw.shortability_passed = False
        brw.degradation_reason = "BORROW_EVIDENCE_MISSING: Shorting required but no borrow cost data provided"
        borrow_reasons.append(brw.degradation_reason)

    # Gate F: PROVISIONAL borrow for short-required strategies degrades honesty
    if (
        brw.requires_shorting
        and borrow_source is not None
        and borrow_source.source_mode == "PROVISIONAL"
    ):
        borrow_reasons.append(
            f"PROVISIONAL_BORROW_SOURCE: Borrow data from {borrow_source.source_id}, not feed-backed"
        )

    # Gate G: PROVISIONAL liquidity for capacity-sensitive strategies
    if (
        cap.estimated_participation_rate > 0
        and liquidity_source is not None
        and liquidity_source.source_mode == "PROVISIONAL"
    ):
        capacity_reasons.append(
            f"PROVISIONAL_LIQUIDITY_SOURCE: ADV from {liquidity_source.source_id}, not feed-backed"
        )

    if prov.liquidity_freshness_status == "STALE" and not policy.allow_market_data_fallback:
        reasons.append("stale market data")
    if prov.borrow_freshness_status == "STALE" and brw.requires_shorting and not policy.allow_market_data_fallback:
        reasons.append("stale market data")
    if prov.liquidity_provider_status in {"ERROR", "TIMEOUT", "CIRCUIT_OPEN"} or prov.borrow_provider_status in {"ERROR", "TIMEOUT", "CIRCUIT_OPEN"}:
        reasons.append("market-data provider failure")
    elif prov.provider_errors:
        reasons.append("market-data provider failure")
    if prov.fallback_applied and not prov.fallback_reason:
        prov.fallback_reason = "POLICY_ALLOWED_FALLBACK"

    # Sync typed sub-objects back to result
    res.capacity = cap
    res.borrow = brw
    res.shortability_passed = brw.shortability_passed
    res.borrow_constraint_note = "; ".join(borrow_reasons) if borrow_reasons else None

    # -- Seal market-data provenance -------------------------------------------
    # Record the exact lookup parameters and snapshot fingerprints used.
    # No promotion-grade decision may be time-ambiguous or identity-ambiguous.
    prov.liquidity_snapshot_hash = prov.liquidity_snapshot_hash or (liquidity_source.snapshot_hash if liquidity_source else None)
    prov.borrow_snapshot_hash = prov.borrow_snapshot_hash or (borrow_source.snapshot_hash if borrow_source else None)
    prov.liquidity_source_mode = prov.liquidity_source_mode or (liquidity_source.source_mode if liquidity_source else "NONE")
    prov.borrow_source_mode = prov.borrow_source_mode or (borrow_source.source_mode if borrow_source else "NONE")
    res.market_data_provenance = prov

    # Compile failure reasons
    all_reasons = reasons + capacity_reasons + borrow_reasons
    if not stress_passed:
        all_reasons.append(f"STRESS: {stress.failure_reason}")

    passed = (not reasons) and cap.capacity_limit_passed and brw.shortability_passed
    if not passed:
        res.passed = False
        if not res.failure_reason:
            res.failure_reason = "; ".join(all_reasons) if all_reasons else "EXECUTION_REALISM_FAILED"
    else:
        res.passed = True

    return res





def _benchmark_evidence_performance_typed(
    experiment: ExperimentManifest, 
    evidence: Iterable[Evidence],
    external_cost_bps: float = 0.0
) -> BenchmarkResult:
    rep = BenchmarkResult(
        benchmark_id="unknown",
        experiment_id=experiment.experiment_id,
        rung_id="unknown",
        raw_strategy_metric=0.0,
        benchmark_metric=0.0,
        excess_metric=0.0,
        passed=False,
        evaluation_horizon="unknown"
    )
    rung_id = experiment.evidence_bundle.benchmark_rung
    if rung_id not in BENCHMARK_RUNG_REGISTRY:
        rep.failure_reason = "UNKNOWN_BENCHMARK_RUNG"
        return rep
        
    rung = BENCHMARK_RUNG_REGISTRY[rung_id]
    rep.benchmark_id = rung.benchmark_id
    rep.rung_id = rung.rung_id
    
    saw_delta = False
    
    for ev in evidence:
        if ev.evidence_type == EvidenceType.COST_SUMMARY and ev.payload.get("passed") is False:
            rep.passed = False
            rep.failure_reason = "COST_ENGINE_REJECTION"
            return rep
            
        if "benchmark_id" in ev.payload:
            if ev.payload.get("benchmark_passed") is False:
                rep.passed = False
                rep.failure_reason = "BENCHMARK_PROPOSER_REJECTION"
                return rep
                
            try:
                rep.raw_strategy_metric = float(ev.payload.get("strategy_return", 0.0))
                rep.benchmark_metric = float(ev.payload.get("benchmark_return", 0.0))
                rep.excess_metric = float(ev.payload.get("benchmark_delta", 0.0))
                
                # Apply externally calculated realism costs
                post_cost = rep.excess_metric - (external_cost_bps / 10000.0)
                rep.post_cost_excess_metric = post_cost
                
                if post_cost < rung.minimum_delta:
                    rep.passed = False
                    rep.failure_reason = f"INSUFFICIENT_POST_COST_DELTA: {post_cost:.4f} < {rung.minimum_delta}"
                    return rep
                
                saw_delta = True
                rep.evaluation_horizon = str(ev.payload.get("horizon", "unknown"))
            except (KeyError, ValueError, TypeError):
                rep.passed = False
                rep.failure_reason = "MALFORMED_BENCHMARK_EVIDENCE"
                return rep

    if not saw_delta:
        rep.passed = False
        rep.failure_reason = "MISSING_BENCHMARK_EVIDENCE"
    else:
        rep.passed = True
        
    return rep


