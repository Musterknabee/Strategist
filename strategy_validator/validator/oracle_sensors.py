from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from strategy_validator.contracts.oracle import (
    MacroRegimeSensorSnapshot,
    MicrostructureSensorSnapshot,
    OracleAdvisoryInput,
    OracleSensorIngestionInput,
    OracleSensorIngestionReport,
    OracleSensorMatrix,
    SemanticSensorSnapshot,
)
from strategy_validator.validator.oracle_transition_common import _utc_now


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def load_sensor_ingestion_input(path: Path) -> OracleSensorIngestionInput:
    return OracleSensorIngestionInput.model_validate(json.loads(path.read_text(encoding="utf-8")))


def normalize_sensor_input(payload: OracleSensorIngestionInput) -> OracleSensorIngestionReport:
    notes: list[str] = []

    semantic = SemanticSensorSnapshot(
        inflation_hawkishness_score=round((payload.semantic_raw.hawkish_document_ratio - payload.semantic_raw.dovish_document_ratio) * 2.0, 6),
        geopolitical_risk_index=round(payload.semantic_raw.geopolitical_headline_share, 6),
        narrative_contradiction_count=payload.semantic_raw.contradiction_count,
        tribunal_belief_conflict=round(payload.semantic_raw.belief_conflict_score, 6),
    )
    notes.append("semantic snapshot normalized from hawkish/dovish ratio spread, headline-share risk, and contradiction pressure")

    total_volume = payload.microstructure_raw.buy_volume + payload.microstructure_raw.sell_volume
    if total_volume <= 0.0:
        order_flow_imbalance = 0.0
        notes.append("microstructure buy/sell volume was flat, so order flow imbalance was set to 0.0")
    else:
        order_flow_imbalance = (payload.microstructure_raw.buy_volume - payload.microstructure_raw.sell_volume) / total_volume

    spread_ratio = payload.microstructure_raw.median_spread_bps / payload.microstructure_raw.baseline_spread_bps
    spread_variance_zscore = (spread_ratio - 1.0) * 3.0
    depth_ratio = payload.microstructure_raw.top_book_depth_usd / payload.microstructure_raw.baseline_top_book_depth_usd
    liquidity_thinning = _clamp(1.0 - depth_ratio, 0.0, 1.0)
    micro = MicrostructureSensorSnapshot(
        vpin=round(payload.microstructure_raw.toxic_flow_ratio, 6),
        order_flow_imbalance=round(_clamp(order_flow_imbalance, -1.0, 1.0), 6),
        spread_variance_zscore=round(spread_variance_zscore, 6),
        liquidity_thinning_score=round(liquidity_thinning, 6),
    )
    notes.append("microstructure snapshot normalized from toxic-flow proxy, spread expansion, and top-of-book depth thinning")

    base_vol = max(payload.macro_raw.realized_volatility_252d, 1e-6)
    realized_volatility_zscore = (payload.macro_raw.realized_volatility_20d - payload.macro_raw.realized_volatility_252d) / base_vol
    cross_asset_stress = _clamp((payload.macro_raw.cross_asset_correlation_20d + 1.0) / 2.0, 0.0, 1.0)
    macro = MacroRegimeSensorSnapshot(
        yield_curve_slope_bps=payload.macro_raw.yield_curve_slope_bps,
        high_yield_credit_spread_bps=payload.macro_raw.high_yield_credit_spread_bps,
        equity_bond_correlation=payload.macro_raw.equity_bond_correlation_20d,
        cross_asset_correlation_stress=round(cross_asset_stress, 6),
        realized_volatility_zscore=round(realized_volatility_zscore, 6),
    )
    notes.append("macro snapshot normalized from realized-vol regime shift and cross-asset correlation stress")

    advisory_input = OracleAdvisoryInput(
        generated_for_utc=payload.generated_for_utc,
        universe_label=payload.universe_label,
        sensors=OracleSensorMatrix(semantic=semantic, microstructure=micro, macro=macro),
        strategies=payload.strategies,
    )

    quality_score = 1.0
    if payload.macro_raw.realized_volatility_20d <= 0.0:
        quality_score -= 0.10
        notes.append("realized_volatility_20d was non-positive, which weakens macro signal reliability")
    if payload.microstructure_raw.baseline_top_book_depth_usd <= payload.microstructure_raw.top_book_depth_usd:
        notes.append("top-of-book depth is at or above baseline, reducing liquidity-stress concern")
    if payload.semantic_raw.contradiction_count == 0:
        notes.append("semantic contradiction pressure is absent in this ingestion window")
    quality_score = _clamp(quality_score, 0.0, 1.0)

    return OracleSensorIngestionReport(
        generated_at_utc=_utc_now(),
        universe_label=payload.universe_label,
        advisory_input=advisory_input,
        quality_score=round(quality_score, 6),
        normalization_notes=notes,
        summary_line=(
            f"Normalized raw macro/semantic/microstructure inputs into oracle advisory sensors for {payload.universe_label} "
            f"with ingestion quality {quality_score:.2f}."
        ),
    )


def render_sensor_ingestion_markdown(report: OracleSensorIngestionReport) -> str:
    sensors = report.advisory_input.sensors
    notes = "\n".join(f"- {item}" for item in report.normalization_notes) or "- none"
    return f"""# ORACLE SENSOR INGESTION REPORT

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Universe: {report.universe_label}
- Quality score: {report.quality_score:.2f}

## Summary

{report.summary_line}

## Macro snapshot

- yield_curve_slope_bps={sensors.macro.yield_curve_slope_bps:.1f}
- high_yield_credit_spread_bps={sensors.macro.high_yield_credit_spread_bps:.1f}
- equity_bond_correlation={sensors.macro.equity_bond_correlation:.2f}
- cross_asset_correlation_stress={sensors.macro.cross_asset_correlation_stress:.2f}
- realized_volatility_zscore={sensors.macro.realized_volatility_zscore:.2f}

## Semantic snapshot

- inflation_hawkishness_score={sensors.semantic.inflation_hawkishness_score:.2f}
- geopolitical_risk_index={sensors.semantic.geopolitical_risk_index:.2f}
- narrative_contradiction_count={sensors.semantic.narrative_contradiction_count}
- tribunal_belief_conflict={sensors.semantic.tribunal_belief_conflict:.2f}

## Microstructure snapshot

- vpin={sensors.microstructure.vpin:.2f}
- order_flow_imbalance={sensors.microstructure.order_flow_imbalance:.2f}
- spread_variance_zscore={sensors.microstructure.spread_variance_zscore:.2f}
- liquidity_thinning_score={sensors.microstructure.liquidity_thinning_score:.2f}

## Normalization notes

{notes}
"""
