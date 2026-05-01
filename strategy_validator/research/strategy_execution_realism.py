"""Conservative execution realism estimates from local bars (research only; not broker-grade)."""
from __future__ import annotations

from strategy_validator.contracts.strategy_batch import StrategyBatchSpec, StrategyCandidateSpec
from strategy_validator.contracts.strategy_data_snapshot import StrategyBar as Bar
from strategy_validator.contracts.strategy_execution_realism import (
    MODEL_LABEL,
    CapacityEstimate,
    ExecutionRealismGateStatus,
    ExecutionRealismResult,
    FeeModelResult,
    LiquidityCheckResult,
    SlippageModelResult,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def evaluate_execution_realism(
    *,
    candidate: StrategyCandidateSpec,
    batch: StrategyBatchSpec,
    run_id: str,
    metrics: dict[str, float],
    bars: list[Bar] | None,
    synthetic: bool,
) -> ExecutionRealismResult:
    """Return execution realism evidence; gate PROVEN only when conservative checks pass."""

    base = ExecutionRealismResult(
        strategy_id=candidate.strategy_id,
        batch_id=batch.batch_id,
        run_id=run_id,
        model_label=MODEL_LABEL,
        market_data_freshness_status="LOCAL_SNAPSHOT_STATIC",
    )

    if synthetic:
        return base.model_copy(
            update={
                "gate_status": ExecutionRealismGateStatus.NOT_APPLICABLE,
                "blockers": ["EXECUTION_REALISM_CANNOT_PROVE_ON_SYNTHETIC"],
                "liquidity_status": "NOT_APPLICABLE_SYNTHETIC",
                "borrow_status": "NOT_APPLICABLE_SYNTHETIC",
                "evidence_digest": canonical_json_sha256(
                    {"gate": "NOT_APPLICABLE", "synthetic": True, "strategy_id": candidate.strategy_id}
                ),
            }
        )

    if bars is None or len(bars) == 0:
        return base.model_copy(
            update={
                "gate_status": ExecutionRealismGateStatus.BLOCKED,
                "blockers": ["NO_BARS_FOR_EXECUTION_REALISM"],
                "liquidity_status": "BLOCKED_NO_BARS",
                "evidence_digest": canonical_json_sha256({"gate": "BLOCKED", "reason": "no_bars"}),
            }
        )

    assum = candidate.execution_realism_assumptions
    if assum is None:
        return base.model_copy(
            update={
                "gate_status": ExecutionRealismGateStatus.BLOCKED,
                "blockers": ["MISSING_EXECUTION_REALISM_ASSUMPTIONS"],
                "liquidity_status": "BLOCKED_MISSING_ASSUMPTIONS",
                "warnings": ["DECLARE_STARTING_CAPITAL_PARTICIPATION_FEES_IN_EXECUTION_ASSUMPTIONS"],
                "evidence_digest": canonical_json_sha256({"gate": "BLOCKED", "reason": "no_assumptions"}),
            }
        )

    base = base.model_copy(update={"assumptions": assum})

    dollar_vols = [float(b.volume) * float(b.close) for b in bars]
    if not dollar_vols or all(dv <= 0 for dv in dollar_vols):
        return base.model_copy(
            update={
                "gate_status": ExecutionRealismGateStatus.BLOCKED,
                "blockers": ["MISSING_OR_ZERO_VOLUME_FOR_LIQUIDITY"],
                "liquidity_status": "BLOCKED_NO_VOLUME",
                "warnings": ["LOCAL_BARS_NEED_POSITIVE_VOLUME_FOR_PARTICIPATION_MODEL"],
                "evidence_digest": canonical_json_sha256({"gate": "BLOCKED", "reason": "volume"}),
            }
        )

    avg_dd_vol = sum(dollar_vols) / float(len(dollar_vols))
    n = len(bars)
    trade_count = float(metrics.get("trade_count", 0.0))
    turnover_estimate = min(1.0, max(1e-8, (trade_count + 0.5) / float(max(n, 1))))
    notional_daily = float(assum.starting_capital) * turnover_estimate
    participation = notional_daily / avg_dd_vol if avg_dd_vol > 0 else float("inf")

    fee_bps = float(assum.fee_bps)
    slip_bps = float(assum.slippage_bps)
    fee_drag_usd = notional_daily * (fee_bps / 10_000.0)
    slip_drag_usd = notional_daily * (slip_bps / 10_000.0)
    cap_notional = max(0.0, avg_dd_vol * float(assum.max_participation_rate))
    headroom = cap_notional - notional_daily

    liquidity = LiquidityCheckResult(
        status="PASS",
        average_daily_dollar_volume=avg_dd_vol,
        threshold=float(assum.min_average_daily_volume),
        detail="mean(volume*close) over filtered bars",
    )
    slip_m = SlippageModelResult(
        slippage_bps_assumed=slip_bps,
        implied_daily_drag_vs_capital=slip_drag_usd / assum.starting_capital if assum.starting_capital else 0.0,
    )
    fee_m = FeeModelResult(
        fee_bps_assumed=fee_bps,
        implied_daily_drag_vs_capital=fee_drag_usd / assum.starting_capital if assum.starting_capital else 0.0,
    )
    cap_e = CapacityEstimate(capacity_notional=cap_notional, headroom_vs_estimate=headroom)

    blockers: list[str] = []
    warnings: list[str] = []
    gate = ExecutionRealismGateStatus.PROVEN
    liq_status = "PASS"
    borrow_status = "NOT_REQUIRED"

    if assum.borrow_required:
        if not assum.borrow_liquidity_evidence_ack:
            blockers.append("BORROW_REQUIRED_WITHOUT_EVIDENCE_ACK")
            gate = ExecutionRealismGateStatus.BLOCKED
            borrow_status = "BLOCKED_NO_EVIDENCE"
        else:
            borrow_status = "ACK_ONLY_RESEARCH_NOT_BROKER_VERIFIED"
    if not assum.allow_short and metrics.get("total_return", 0.0) < -0.5:
        warnings.append("LARGE_DRAWDOWN_CHECK_SHORT_CONSTRAINT_NOT_MODELED")

    if avg_dd_vol < float(assum.min_average_daily_volume):
        blockers.append("AVERAGE_DOLLAR_VOLUME_BELOW_OPERATOR_THRESHOLD")
        liquidity = liquidity.model_copy(update={"status": "BLOCK"})
        gate = ExecutionRealismGateStatus.BLOCKED
        liq_status = "BLOCKED_BELOW_MIN_AVG_VOLUME"

    if participation > float(assum.max_participation_rate) + 1e-12:
        blockers.append(
            f"ESTIMATED_PARTICIPATION_{participation:.6f}_EXCEEDS_MAX_{assum.max_participation_rate:.6f}"
        )
        gate = ExecutionRealismGateStatus.BLOCKED
        liq_status = "BLOCKED_PARTICIPATION"

    warn_threshold = 0.85 * float(assum.max_participation_rate)
    if gate == ExecutionRealismGateStatus.PROVEN and participation > warn_threshold:
        warnings.append("PARTICIPATION_NEAR_LIMIT")
        gate = ExecutionRealismGateStatus.WARNING

    if avg_dd_vol < 1.5 * float(assum.min_average_daily_volume) and gate == ExecutionRealismGateStatus.PROVEN:
        warnings.append("LIQUIDITY_ONLY_MARGINALLY_ABOVE_THRESHOLD")
        gate = ExecutionRealismGateStatus.WARNING

    result = ExecutionRealismResult(
        strategy_id=candidate.strategy_id,
        batch_id=batch.batch_id,
        run_id=run_id,
        model_label=MODEL_LABEL,
        assumptions=assum,
        average_daily_volume=sum(float(b.volume) for b in bars) / float(len(bars)),
        average_daily_dollar_volume=avg_dd_vol,
        estimated_participation_rate=participation,
        turnover_estimate=turnover_estimate,
        estimated_slippage_bps=slip_bps,
        estimated_fees_bps=fee_bps,
        slippage_drag_daily_usd=slip_drag_usd,
        fee_drag_daily_usd=fee_drag_usd,
        liquidity=liquidity,
        slippage_model=slip_m,
        fee_model=fee_m,
        capacity=cap_e,
        liquidity_status=liq_status,
        borrow_status=borrow_status,
        market_data_freshness_status="LOCAL_SNAPSHOT_STATIC",
        gate_status=gate,
        blockers=blockers,
        warnings=warnings,
    )
    digest = canonical_json_sha256(result.model_dump(mode="json"))
    return result.model_copy(update={"evidence_digest": digest})


__all__ = ["evaluate_execution_realism"]
