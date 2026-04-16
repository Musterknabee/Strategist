"""Single controlled adjudication path and sole production entry to ledger writes."""

from __future__ import annotations

import logging
import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Iterable, List, Literal, Tuple, Optional, cast

from strategy_validator.contracts.evidence import Evidence, SemanticArtifact
from strategy_validator.contracts.experiments import AdjudicationDecision, ExperimentManifest, AdjudicationEvent, GateResult, compute_config_hash
from strategy_validator.contracts.benchmarks import BENCHMARK_RUNG_REGISTRY, validate_benchmark_observation, BenchmarkResult
from strategy_validator.contracts.execution import (
    ExecutionRealismResult, ExecutionStressResult,
    CapacityEvidence, BorrowEvidence, MarketDataProvenance,
)
from strategy_validator.contracts.market_data import (
    LiquiditySnapshot, BorrowSnapshot,
    LiquidityFeed, BorrowFeed,
    FreshnessResult, ProviderLookupMetadata,
)
from strategy_validator.core.config import load_config, AppConfig, RuntimePolicy
from strategy_validator.core.enums import EvidenceType, PromotionState, BANK_STATE_RANKING, MetricSourceMode, RuntimeMode
from strategy_validator.core.exceptions import AdjudicationError, ConstitutionalViolation
from strategy_validator.validator.readiness import perform_readiness_check
from strategy_validator.ledger._append_only import get_schema_version_info
from strategy_validator.ledger.writer import commit_state_transition, issue_write_authority
from strategy_validator.validator.robustness import RobustnessEngine
from strategy_validator.validator.cost_engine import evidence_uses_midpoint_only_economics
from strategy_validator.validator.decoys.battery import evaluate_decoy_survival_hook
from strategy_validator.contracts.vendor_runtime import (
    VendorFailureDomain,
    VendorFailureEvent,
    classify_vendor_failure_detail,
)
from strategy_validator.validator.calibration_curve import interpolate_impact_bps
from strategy_validator.validator.calibration_loader import load_calibration_artifact_from_path
from strategy_validator.validator.market_hours import us_equities_regular_session_open
from strategy_validator.validator.metrics_sinks import emit_runtime_metrics

logger = logging.getLogger(__name__)

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

_LEDGER_WRITE_AUTHORITY = issue_write_authority()

def _reconcile_states(current_state: PromotionState, new_restriction: PromotionState) -> PromotionState:
    """Ensure the most restrictive state (maximal ranking) is enforced."""
    if BANK_STATE_RANKING[new_restriction] > BANK_STATE_RANKING[current_state]:
        return new_restriction
    return current_state


def adjudicate(
    experiment: ExperimentManifest,
    new_evidence: List[Evidence],
    *,
    liquidity_feed: Optional[LiquidityFeed] = None,
    borrow_feed: Optional[BorrowFeed] = None,
    liquidity_fallback_feed: Optional[LiquidityFeed] = None,
    borrow_fallback_feed: Optional[BorrowFeed] = None,
) -> PromotionState:
    """
    Apply constitutional gates, update promotion state, append ledger row with decision history.

    Optional market-data feeds provide lawful, PIT-aware liquidity and borrow
    snapshots.  When absent, execution realism degrades to PROVISIONAL payload
    assertions.
    """
    # 0. Readiness Check
    report = perform_readiness_check()
    if report.status == "BLOCKED":
        blocker_msg = "; ".join(f"{b.code}: {b.message}" for b in report.blockers)
        raise ConstitutionalViolation(f"PRODUCTION_READINESS_BLOCKED: {blocker_msg}")

    for ev in new_evidence:
        if ev.experiment_id != experiment.experiment_id:
            raise AdjudicationError(
                f"Evidence {ev.evidence_id} experiment_id mismatch ({ev.experiment_id} vs {experiment.experiment_id})"
            )

    merged = list(experiment.evidence_bundle.evidence_items) + list(new_evidence)
    experiment.evidence_bundle.evidence_items.clear()
    experiment.evidence_bundle.evidence_items.extend(merged)
    
    # 1. Select new state and build decision provenance
    previous_state = experiment.state
    new_state, decision = _select_promotion_state_with_provenance(
        experiment, previous_state,
        liquidity_feed=liquidity_feed,
        borrow_feed=borrow_feed,
        liquidity_fallback_feed=liquidity_fallback_feed,
        borrow_fallback_feed=borrow_fallback_feed,
    )
    
    experiment.state = new_state
    experiment.promotion_history.append(decision)
    
    # 3. Emit structured telemetry (Task 3: Observability Hardening)
    try:
        from strategy_validator.validator.observability import generate_decision_telemetry
        from strategy_validator.validator.telemetry_sinks import emit_decision_telemetry_sinks

        telemetry = generate_decision_telemetry(decision, experiment.experiment_id)
        logger.info(f"ADJUDICATION_TELEMETRY: {telemetry.model_dump_json()}")
        emit_decision_telemetry_sinks(telemetry.model_dump(mode="json"))
    except Exception as e:
        logger.warning(f"TELEMETRY_EMISSION_FAILED: {e}")

    try:
        rr = perform_readiness_check()
        cur_v, exp_v = get_schema_version_info()
        emit_runtime_metrics(
            readiness_status=rr.status,
            blocker_count=len(rr.blockers),
            schema_ok=cur_v >= exp_v,
        )
    except Exception as e:
        logger.warning(f"RUNTIME_METRICS_EMISSION_FAILED: {e}")

    # 4. Commit snapshot
    commit_state_transition(experiment, _LEDGER_WRITE_AUTHORITY, created_at=decision.decided_at)
    return experiment.state


def _select_promotion_state_with_provenance(
    experiment: ExperimentManifest,
    previous_state: PromotionState,
    *,
    liquidity_feed: Optional[LiquidityFeed] = None,
    borrow_feed: Optional[BorrowFeed] = None,
    liquidity_fallback_feed: Optional[LiquidityFeed] = None,
    borrow_fallback_feed: Optional[BorrowFeed] = None,
) -> Tuple[PromotionState, AdjudicationDecision]:
    evidence = experiment.evidence_bundle.evidence_items
    bundle = experiment.evidence_bundle
    config = load_config()
    policy = config.runtime_policy
    th = config.tribunal_thresholds
    cfg_hash = compute_config_hash(config.model_dump(mode="json"))

    gates: List[GateResult] = []
    summary_notes: List[str] = []

    # -- Lawful PIT evaluation context ---------------------------------------
    eval_time = bundle.evaluation_time_utc
    if eval_time is None:
        if config.runtime_policy.require_explicit_evaluation_time:
            raise AdjudicationError(
                "STRICT_CONTEXT_VIOLATION: evaluation_time_utc is mandatory in PRODUCTION mode."
            )
        # Fallback: latest evidence timestamp. Still point-in-time lawful,
        # just not an explicit decision time.
        evidence_times = [
            ev.timestamp for ev in evidence
            if ev.timestamp is not None
        ]
        if not evidence_times:
            raise AdjudicationError(
                "Missing lawful evaluation context: evaluation_time_utc not provided "
                "and no evidence timestamps found. Cannot adjudicate without deterministic PIT."
            )
        eval_time = max(evidence_times)

    # Subject identity for market-data lookups.
    subject_id = bundle.market_data_subject_id
    if subject_id is None and config.runtime_policy.require_explicit_market_data_subject_id:
        # If any realistic gate is sensitive to subject ID, we must fail closed in production
        raise AdjudicationError(
            "STRICT_CONTEXT_VIOLATION: market_data_subject_id is mandatory in PRODUCTION mode."
        )

    # Materialize Decorators
    _materialize_decoy_hook(experiment, evidence)

    state = PromotionState.PROMOTABLE

    # 1. Integrity Gates
    leakage = _evidence_indicates_future_leakage(evidence)
    pit_ok = _pit_integrity_ok(evidence)
    gates.append(GateResult(gate_name="FutureLeakage", passed=not leakage))
    gates.append(GateResult(gate_name="PointInTimeIntegrity", passed=pit_ok))
    if leakage:
        state = _reconcile_states(state, PromotionState.INVALID)
    if not pit_ok:
        state = _reconcile_states(state, PromotionState.REJECTED)
    
    # 2. Benchmark Context Check
    bench_ctxt = _evaluate_benchmark_context(experiment, evidence)
    gates.append(bench_ctxt)
    if not bench_ctxt.passed:
        state = _reconcile_states(state, PromotionState.INVALID)

    # 3. Execution Realism (Harden Capacity + Borrow + Stress)
    exec_report = _evaluate_execution_realism(
        evidence, th.phantom_edge_buffer_multiplier,
        evaluation_time_utc=eval_time,
        market_data_subject_id=subject_id,
        liquidity_feed=liquidity_feed,
        borrow_feed=borrow_feed,
        liquidity_fallback_feed=liquidity_fallback_feed,
        borrow_fallback_feed=borrow_fallback_feed,
        policy=policy,
    )
    gates.append(GateResult(
        gate_name="ExecutionRealism", 
        passed=exec_report.passed, 
        reason=exec_report.failure_reason
    ))
    if not exec_report.passed:
        state = _reconcile_states(state, PromotionState.REJECTED)
    
    # Execution Stress Gate
    stress_rep = exec_report.stress_report
    if stress_rep:
        gates.append(GateResult(
            gate_name="ExecutionStressResilience",
            passed=stress_rep.passed,
            reason=stress_rep.failure_reason
        ))
        if not stress_rep.passed:
            state = _reconcile_states(state, PromotionState.INVALID if stress_rep.failure_reason == "CRITICAL_LIQUIDITY_FAILURE" else PromotionState.REJECTED)

    # Explicit Borrow Gate
    gates.append(GateResult(
        gate_name="ShortabilityBorrow",
        passed=exec_report.shortability_passed,
        reason=exec_report.borrow_constraint_note
    ))
    if not exec_report.shortability_passed:
        state = _reconcile_states(state, PromotionState.REJECTED)

    # Explicit Capacity Gate
    gates.append(GateResult(
        gate_name="CapacityLimit",
        passed=exec_report.capacity.capacity_limit_passed,
        reason=exec_report.capacity.degradation_reason,
        metric_value=exec_report.capacity.estimated_participation_rate,
    ))
    if not exec_report.capacity.capacity_limit_passed:
        state = _reconcile_states(state, PromotionState.REJECTED)

    if exec_report.midpoint_only_flag:
        state = _reconcile_states(state, PromotionState.QUARANTINED)
        summary_notes.append("Advisory: Midpoint-only economics detected.")
    
    # 3.2 Production Source Policy Check
    prov = exec_report.market_data_provenance
    if policy.strict_production_mode:
        # Strict production: any non-compliant source mode blocks PROMOTABLE entirely.
        source_violation = False
        reason = ""
        
        # Check PROVISIONAL (Always blocked in strict production)
        if any(m == "PROVISIONAL" for m in (prov.liquidity_source_mode, prov.borrow_source_mode)):
            source_violation = True
            reason = "provisional data usage"
        
        # 1. Check FRESHNESS / ERRORS (highest priority for operational diagnostics)
        elif prov.liquidity_freshness_status == "STALE" or prov.borrow_freshness_status == "STALE":
            if not policy.allow_market_data_fallback:
                source_violation = True
                reason = "stale market data (freshness law violation)"
        
        elif prov.provider_errors:
            source_violation = True
            reason = "market-data provider failure"

        # 2. Check NONE (Blocked if data was needed and no error/staleness was already reported)
        # Liquidity is ALWAYS needed for realistic adjudication.
        elif prov.liquidity_source_mode == "NONE":
            source_violation = True
            reason = "missing liquidity feed"
            
        elif prov.borrow_source_mode == "NONE" and exec_report.requires_shorting:
            source_violation = True
            reason = "missing borrow feed (required for short strategy)"
            
        # 3. Check SNAPSHOT (if explicitly disallowed in production)
        elif not policy.allow_snapshot_market_data:
            used_snapshot = (prov.liquidity_source_mode == "SNAPSHOT") or (
                prov.borrow_source_mode == "SNAPSHOT" and exec_report.requires_shorting
            )
            if used_snapshot:
                source_violation = True
                reason = "SNAPSHOT-level data (LIVE required by policy)"

        if source_violation:
            state = _reconcile_states(state, PromotionState.REJECTED)
            summary_notes.append(f"STRICT_PRODUCTION_BLOCKER: PROMOTABLE rejected due to {reason}.")
            
    elif not policy.allow_provisional_market_data:
        # Non-strict but no-provisional: downgrade to CONDITIONAL.
        if any(m in ("PROVISIONAL", "NONE") for m in (prov.liquidity_source_mode, prov.borrow_source_mode)):
            state = _reconcile_states(state, PromotionState.CONDITIONAL)
            summary_notes.append(
                "PRODUCTION_POLICY_VIOLATION: PROMOTABLE state blocked due to "
                "provisional/unverified market-data usage."
            )
        elif not policy.allow_snapshot_market_data and any(m == "SNAPSHOT" for m in (prov.liquidity_source_mode, prov.borrow_source_mode)):
             state = _reconcile_states(state, PromotionState.CONDITIONAL)
             summary_notes.append(
                "PRODUCTION_POLICY_VIOLATION: PROMOTABLE state blocked due to "
                "SNAPSHOT data usage (LIVE required)."
            )

    # 3.2 Snapshot Market-Data Policy
    # When allow_snapshot_market_data is False, SNAPSHOT sources alone cannot
    # support PROMOTABLE — at least one LIVE source is required.
    if not config.runtime_policy.allow_snapshot_market_data:
        modes = (prov.liquidity_source_mode, prov.borrow_source_mode)
        # If all available sources are SNAPSHOT (no LIVE), block PROMOTABLE.
        # "NONE" means no feed was used at all — already caught above.
        non_none_modes = [m for m in modes if m not in ("NONE", None)]
        if non_none_modes and all(m == "SNAPSHOT" for m in non_none_modes):
            state = _reconcile_states(state, PromotionState.CONDITIONAL)
            summary_notes.append(
                "SNAPSHOT_ONLY_POLICY: PROMOTABLE requires at least one LIVE "
                f"market-data source; got {non_none_modes}."
            )
    
    phantom_edge = _phantom_edge_detected(evidence)
    gates.append(GateResult(gate_name="PhantomEdgeDetection", passed=not phantom_edge))
    if phantom_edge:
        state = _reconcile_states(state, PromotionState.REJECTED)

    # 4. Semantic Gates
    semantic_missing = _semantic_artifacts_missing_spans(experiment.evidence_bundle.semantic_artifacts)
    gates.append(GateResult(gate_name="SemanticEvidenceSufficiency", passed=not semantic_missing))
    if semantic_missing:
        state = _reconcile_states(state, PromotionState.QUARANTINED)

    # 5. Benchmark Performance (Updated to use total_post_cost_bps)
    # Only evaluate performance if context was valid
    bench_report = None
    if bench_ctxt.passed:
        bench_report = _benchmark_evidence_performance_typed(experiment, evidence, exec_report.total_post_cost_bps)
        gates.append(GateResult(
            gate_name="BenchmarkSuccess", 
            passed=bench_report.passed, 
            metric_value=bench_report.post_cost_excess_metric,
            threshold_value=BENCHMARK_RUNG_REGISTRY[experiment.evidence_bundle.benchmark_rung].minimum_delta
        ))
        if not bench_report.passed:
            state = _reconcile_states(state, PromotionState.REJECTED)
    else:
        # If context was invalid, we don't evaluate performance, but we record the failure.
        gates.append(GateResult(gate_name="BenchmarkSuccess", passed=False, reason="INVALID_CONTEXT"))

    # 6. Robustness Engine (Consolidated)
    # Constitutional law: provided evidence is authoritative by default.
    # Recomputation happens only when explicitly requested.  The engine
    # records typed provenance for every metric.
    engine = RobustnessEngine(thresholds=th)
    report = engine.evaluate(
        evidence,
        bundle=experiment.evidence_bundle,
        search_breadth=experiment.evidence_bundle.search_breadth,
        recompute_requested=False,  # explicit; never silent
    )

    # Sync recomputed metrics — only overwrite with recomputed values.
    # Provided values remain authoritative; provenance records the distinction.
    experiment.evidence_bundle.robustness_provenance = report.provenance
    # Only write recomputed values when provenance says RECOMPUTED was used.
    for prov in report.provenance:
        if prov.source_of_truth_used == MetricSourceMode.RECOMPUTED:
            if prov.metric_name == "cpcv_passed":
                experiment.evidence_bundle.cpcv_folds = report.folds
                experiment.evidence_bundle.cpcv_passed = report.passed if report.folds is not None else None
                experiment.evidence_bundle.cpcv_path_coverage = report.path_coverage
                experiment.evidence_bundle.cpcv_path_stability = report.path_stability
            elif prov.metric_name == "incrementality":
                experiment.evidence_bundle.incrementality_significant = report.incrementality_significant
                experiment.evidence_bundle.incrementality_p_value = report.incrementality_p_value
            elif prov.metric_name == "dsr_estimate":
                if report.dsr_estimate is not None:
                    experiment.evidence_bundle.dsr_estimate = report.dsr_estimate
            elif prov.metric_name == "pbo_estimate":
                if report.pbo_estimate is not None:
                    experiment.evidence_bundle.pbo_estimate = report.pbo_estimate

    gates.append(GateResult(
        gate_name="RobustnessAudit", 
        passed=report.passed,
        note="; ".join(report.evaluation_notes)
    ))
    state = _reconcile_states(state, report.suggested_state)
    summary_notes.extend(report.evaluation_notes)

    # 7. Decoy Gates (Task 2: Mutation Law Enforcement)
    decoy_pass_claim = experiment.evidence_bundle.decoy_survival_passed
    decoy_cov = experiment.evidence_bundle.decoy_coverage
    
    decoy_gate_passed = False
    if decoy_pass_claim is True:
        if decoy_cov is None:
            # Task 2: Asserted success without mandatory metadata -> INVALID
            gates.append(GateResult(gate_name="DecoySurvival", passed=False, reason="INVALID_DECOY_CLAIM"))
            state = _reconcile_states(state, PromotionState.INVALID)
            summary_notes.append("INVALID_DECOY_CLAIM: Decoy success asserted without supporting coverage.")
        elif decoy_cov < th.min_decoy_coverage:
            gates.append(GateResult(gate_name="DecoySurvival", passed=False, reason="LOW_COVERAGE"))
            state = _reconcile_states(state, PromotionState.REJECTED)
        else:
            decoy_gate_passed = True
            gates.append(GateResult(gate_name="DecoySurvival", passed=True))
    elif decoy_pass_claim is False:
        gates.append(GateResult(gate_name="DecoySurvival", passed=False, reason="DECOY_FAILURE"))
        state = _reconcile_states(state, PromotionState.REJECTED)
    else:
        # None -> Missing/Incomplete
        gates.append(GateResult(gate_name="DecoySurvival", passed=False, reason="DECOY_NOT_TESTED"))
        state = _reconcile_states(state, PromotionState.CONDITIONAL)

    readiness = perform_readiness_check()
    decision = AdjudicationDecision(
        decided_at=eval_time,
        previous_state=previous_state,
        new_state=state,
        gate_results=gates,
        summary_notes=summary_notes,
        config_hash=cfg_hash,
        runtime_mode=config.mode,
        config_fingerprint=readiness.config_fingerprint,
        benchmark_report=bench_report,
        execution_report=exec_report,
        evaluation_time_utc=eval_time,
        market_data_subject_id=subject_id,
    )
    return state, decision


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
    as_of: datetime,
    policy: RuntimePolicy,
) -> FreshnessResult:
    """
    Lawfully evaluate the freshness of a market-data snapshot (LIVE age law + optional market-hours).
    """
    threshold, session_law = _live_freshness_threshold_seconds(policy, as_of)
    if snapshot is None:
        return FreshnessResult(
            status="MISSING",
            threshold_seconds=threshold,
            applied_threshold_seconds=threshold,
            market_hours_law=session_law,
            as_of_utc=as_of,
        )

    # PROVISIONAL and SNAPSHOT are exempt from 'live' freshness law (they are by definition non-live)
    if snapshot.source_mode != "LIVE":
        return FreshnessResult(
            status="FRESH",
            age_seconds=0.0,
            threshold_seconds=threshold,
            applied_threshold_seconds=threshold,
            market_hours_law=session_law,
            as_of_utc=as_of,
        )

    age = (as_of - snapshot.snapshot_time).total_seconds()
    status = "FRESH" if age <= threshold else "STALE"

    return FreshnessResult(
        status=status,
        age_seconds=age,
        threshold_seconds=threshold,
        applied_threshold_seconds=threshold,
        market_hours_law=session_law,
        as_of_utc=as_of,
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

    # Provenance tracking
    prov = MarketDataProvenance(
        evaluation_time_utc=evaluation_time_utc,
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
            primary_freshness = _evaluate_snapshot_freshness(None, evaluation_time_utc, policy)
            try:
                primary_snap = liquidity_feed.lookup(market_data_subject_id, evaluation_time_utc)
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
                primary_freshness = _evaluate_snapshot_freshness(primary_snap, evaluation_time_utc, policy)
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
                thr, law = _live_freshness_threshold_seconds(policy, evaluation_time_utc)
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
                fallback_snap = _try_market_data_fallback(
                    fallback_feed=liquidity_fallback_feed,
                    asset_id=market_data_subject_id,
                    evaluation_time_utc=evaluation_time_utc,
                    policy=policy,
                    kind="liquidity",
                    provenance=prov,
                    fallback_reason=fallback_reason,
                )
                if fallback_snap is not None:
                    effective_snap = fallback_snap
                    effective_freshness = _evaluate_snapshot_freshness(fallback_snap, evaluation_time_utc, policy)

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
            primary_freshness = _evaluate_snapshot_freshness(None, evaluation_time_utc, policy)
            try:
                primary_snap = borrow_feed.lookup(market_data_subject_id, evaluation_time_utc)
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
                primary_freshness = _evaluate_snapshot_freshness(primary_snap, evaluation_time_utc, policy)
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
                thr, law = _live_freshness_threshold_seconds(policy, evaluation_time_utc)
                primary_freshness = FreshnessResult(
                    status="ERROR",
                    threshold_seconds=thr,
                    applied_threshold_seconds=thr,
                    market_hours_law=law,
                    as_of_utc=evaluation_time_utc,
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
                    evaluation_time_utc=evaluation_time_utc,
                    policy=policy,
                    kind="borrow",
                    provenance=prov,
                    fallback_reason=fallback_reason,
                )
                if fallback_snap is not None:
                    effective_snap = fallback_snap
                    effective_freshness = _evaluate_snapshot_freshness(fallback_snap, evaluation_time_utc, policy)

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


def _materialize_decoy_hook(experiment: ExperimentManifest, evidence: Iterable[Evidence]) -> None:
    if experiment.evidence_bundle.decoy_survival_passed is not None: return
    decoy_eval = evaluate_decoy_survival_hook(evidence)
    experiment.evidence_bundle.decoy_survival_passed = decoy_eval.passed
    experiment.evidence_bundle.decoy_suite_version = decoy_eval.suite_version
    experiment.evidence_bundle.decoy_coverage = decoy_eval.coverage


def _evaluate_benchmark_context(manifest: ExperimentManifest, evidence: Iterable[Evidence]) -> GateResult:
    """Validates the manifest against evidence items for context alignment."""
    rung_id = manifest.evidence_bundle.benchmark_rung
    
    # 1. Basic Rung Lookup
    if rung_id not in BENCHMARK_RUNG_REGISTRY:
        return GateResult(
            gate_name="BenchmarkContext",
            passed=False,
            reason="UNKNOWN_BENCHMARK_RUNG",
            note=f"Rung '{rung_id}' not found in registry."
        )
    
    # 2. Global Manifest Validity
    if not validate_benchmark_observation(
        benchmark_rung=rung_id,
        benchmark_version=manifest.evidence_bundle.reproducibility.benchmark_version,
        observed_benchmark_id=None
    ):
        return GateResult(
            gate_name="BenchmarkContext",
            passed=False,
            reason="MANIFEST_VERSION_MISMATCH",
            note="Manifest benchmark version does not match registry for this rung."
        )

    # 3. Evidence Specific Alignment
    for ev in evidence:
        payload = ev.payload
        if "benchmark_id" in payload:
            if not validate_benchmark_observation(
                benchmark_rung=rung_id,
                benchmark_version=payload.get("benchmark_version", manifest.evidence_bundle.reproducibility.benchmark_version),
                observed_benchmark_id=payload["benchmark_id"]
            ):
                 return GateResult(
                     gate_name="BenchmarkContext",
                     passed=False,
                     reason="BENCHMARK_ID_MISMATCH",
                     note=f"Evidence benchmark {payload['benchmark_id']} (v{payload.get('benchmark_version')}) mismatches rung {rung_id}"
                 )
    
    return GateResult(gate_name="BenchmarkContext", passed=True)


def _semantic_artifacts_missing_spans(semantic_artifacts: Iterable[SemanticArtifact]) -> bool:
    for artifact in semantic_artifacts:
        if not artifact.span_citations: return True
    return False


def _evidence_indicates_future_leakage(evidence: Iterable[Evidence]) -> bool:
    for ev in evidence:
        if ev.payload.get("future_leakage_detected") is True or ev.payload.get("pit_violation") is True:
            return True
    return False


def _pit_integrity_ok(evidence: Iterable[Evidence]) -> bool:
    for ev in evidence:
        if "pit_integrity_ok" in ev.payload and ev.payload["pit_integrity_ok"] is False: return False
    return True


def _phantom_edge_detected(evidence: Iterable[Evidence]) -> bool:
    for ev in evidence:
        if ev.payload.get("phantom_edge_flag") is True: return True
        raw_edge, cost_edge = ev.payload.get("raw_edge"), ev.payload.get("cost_adjusted_edge")
        if raw_edge is not None and cost_edge is not None:
            if float(raw_edge) > 0.0 and float(cost_edge) <= 0.0: return True
    return False
