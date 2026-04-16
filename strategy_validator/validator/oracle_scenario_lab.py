from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

from strategy_validator.contracts.oracle import (
    MacroRegimeSensorSnapshot,
    MicrostructureSensorSnapshot,
    OracleAdvisoryInput,
    OracleScenarioLabReport,
    OracleScenarioOutcome,
    OracleScenarioPlanInput,
    OracleScenarioShock,
    OracleSensorMatrix,
    OracleStrategicFusionReport,
    SemanticSensorSnapshot,
    StrategyHealthSnapshot,
)
from strategy_validator.validator.oracle_opportunity_queue import build_oracle_opportunity_queue_report
from strategy_validator.validator.oracle_regime_transition import compare_strategic_fusion_reports
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.strategy_health_posterior import build_strategy_health_posterior_report
from strategy_validator.validator.oracle_run_identity import assert_matching_strategic_epoch
from strategy_validator.validator.oracle_history_integrity import preferred_strategic_backing_classification, preferred_strategic_backing_source
from strategy_validator.validator.oracle_strategic_artifact_evidence import discover_preferred_strategic_artifact_evidence, preferred_artifact_evidence_fact, strategic_artifact_evidence_support_score


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _unique(items: Iterable[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if normalized and normalized not in output:
            output.append(normalized)
    return output


def load_scenario_plan_input(path: Path) -> OracleScenarioPlanInput:
    return OracleScenarioPlanInput.model_validate(json.loads(path.read_text(encoding="utf-8")))


def default_scenario_plan(payload: OracleAdvisoryInput) -> OracleScenarioPlanInput:
    return OracleScenarioPlanInput(
        generated_for_utc=payload.generated_for_utc,
        universe_label=payload.universe_label,
        scenarios=[
            OracleScenarioShock(
                scenario_id="macro_stress_spike",
                title="Macro stress spike",
                scenario_kind="DOWNSIDE",
                summary="Credit spreads widen, volatility jumps, and cross-asset stress compresses risk appetite.",
                inflation_hawkishness_shift=0.35,
                geopolitical_risk_shift=0.20,
                narrative_contradiction_delta=2,
                doctrine_conflict_shift=0.18,
                vpin_shift=0.18,
                order_flow_shift=-0.22,
                spread_variance_shift=0.90,
                liquidity_thinning_shift=0.22,
                yield_curve_slope_shift_bps=-55.0,
                high_yield_credit_spread_shift_bps=95.0,
                equity_bond_correlation_shift=0.45,
                cross_asset_stress_shift=0.32,
                realized_volatility_zscore_shift=1.10,
                realized_live_sharpe_shift=-0.25,
                recent_win_rate_shift=-0.08,
                drawdown_fraction_shift=0.06,
            ),
            OracleScenarioShock(
                scenario_id="liquidity_air_pocket",
                title="Liquidity air pocket",
                scenario_kind="DOWNSIDE",
                summary="Order flow turns toxic and top-of-book depth disappears faster than macro headlines can explain.",
                geopolitical_risk_shift=0.08,
                narrative_contradiction_delta=1,
                doctrine_conflict_shift=0.10,
                vpin_shift=0.26,
                order_flow_shift=-0.30,
                spread_variance_shift=1.20,
                liquidity_thinning_shift=0.38,
                cross_asset_stress_shift=0.12,
                realized_volatility_zscore_shift=0.55,
                realized_live_sharpe_shift=-0.18,
                recent_win_rate_shift=-0.05,
                drawdown_fraction_shift=0.04,
            ),
            OracleScenarioShock(
                scenario_id="doctrine_conflict_escalation",
                title="Doctrine conflict escalation",
                scenario_kind="RESEARCH_REVIEW",
                summary="Narrative contradictions and tribunal disagreement rise enough to pressure current research doctrine.",
                inflation_hawkishness_shift=0.20,
                geopolitical_risk_shift=0.10,
                narrative_contradiction_delta=3,
                doctrine_conflict_shift=0.35,
                spread_variance_shift=0.25,
                liquidity_thinning_shift=0.10,
                cross_asset_stress_shift=0.18,
                realized_volatility_zscore_shift=0.35,
                realized_live_sharpe_shift=-0.08,
                recent_win_rate_shift=-0.03,
                drawdown_fraction_shift=0.02,
            ),
            OracleScenarioShock(
                scenario_id="supportive_recovery_window",
                title="Supportive recovery window",
                scenario_kind="UPSIDE",
                summary="Liquidity improves, contradiction pressure fades, and strategies recover into a friendlier opportunity window.",
                inflation_hawkishness_shift=-0.18,
                geopolitical_risk_shift=-0.10,
                narrative_contradiction_delta=-1,
                doctrine_conflict_shift=-0.12,
                vpin_shift=-0.10,
                order_flow_shift=0.18,
                spread_variance_shift=-0.45,
                liquidity_thinning_shift=-0.16,
                yield_curve_slope_shift_bps=20.0,
                high_yield_credit_spread_shift_bps=-55.0,
                equity_bond_correlation_shift=-0.18,
                cross_asset_stress_shift=-0.16,
                realized_volatility_zscore_shift=-0.55,
                realized_live_sharpe_shift=0.18,
                recent_win_rate_shift=0.05,
                drawdown_fraction_shift=-0.03,
            ),
        ],
    )


def apply_scenario_shock_to_input(payload: OracleAdvisoryInput, shock: OracleScenarioShock) -> OracleAdvisoryInput:
    semantic = payload.sensors.semantic
    micro = payload.sensors.microstructure
    macro = payload.sensors.macro

    shocked_semantic = SemanticSensorSnapshot(
        inflation_hawkishness_score=round(semantic.inflation_hawkishness_score + shock.inflation_hawkishness_shift, 6),
        geopolitical_risk_index=round(_clamp(semantic.geopolitical_risk_index + shock.geopolitical_risk_shift, 0.0, 1.0), 6),
        narrative_contradiction_count=max(0, semantic.narrative_contradiction_count + shock.narrative_contradiction_delta),
        tribunal_belief_conflict=round(_clamp(semantic.tribunal_belief_conflict + shock.doctrine_conflict_shift, 0.0, 1.0), 6),
    )
    shocked_micro = MicrostructureSensorSnapshot(
        vpin=round(_clamp(micro.vpin + shock.vpin_shift, 0.0, 1.0), 6),
        order_flow_imbalance=round(_clamp(micro.order_flow_imbalance + shock.order_flow_shift, -1.0, 1.0), 6),
        spread_variance_zscore=round(micro.spread_variance_zscore + shock.spread_variance_shift, 6),
        liquidity_thinning_score=round(_clamp(micro.liquidity_thinning_score + shock.liquidity_thinning_shift, 0.0, 1.0), 6),
    )
    shocked_macro = MacroRegimeSensorSnapshot(
        yield_curve_slope_bps=round(macro.yield_curve_slope_bps + shock.yield_curve_slope_shift_bps, 6),
        high_yield_credit_spread_bps=round(max(0.0, macro.high_yield_credit_spread_bps + shock.high_yield_credit_spread_shift_bps), 6),
        equity_bond_correlation=round(_clamp(macro.equity_bond_correlation + shock.equity_bond_correlation_shift, -1.0, 1.0), 6),
        cross_asset_correlation_stress=round(_clamp(macro.cross_asset_correlation_stress + shock.cross_asset_stress_shift, 0.0, 1.0), 6),
        realized_volatility_zscore=round(macro.realized_volatility_zscore + shock.realized_volatility_zscore_shift, 6),
    )

    shocked_strategies = [
        StrategyHealthSnapshot(
            strategy_id=strategy.strategy_id,
            strategy_type=strategy.strategy_type,
            prior_edge_confidence=strategy.prior_edge_confidence,
            deflated_sharpe_ratio=strategy.deflated_sharpe_ratio,
            cpcv_lower_bound=strategy.cpcv_lower_bound,
            realized_live_sharpe=round(strategy.realized_live_sharpe + shock.realized_live_sharpe_shift, 6),
            recent_win_rate=round(_clamp(strategy.recent_win_rate + shock.recent_win_rate_shift, 0.0, 1.0), 6),
            drawdown_fraction=round(_clamp(strategy.drawdown_fraction + shock.drawdown_fraction_shift, 0.0, 1.0), 6),
            expected_regimes=list(strategy.expected_regimes),
        )
        for strategy in payload.strategies
    ]

    return OracleAdvisoryInput(
        generated_for_utc=payload.generated_for_utc,
        universe_label=payload.universe_label,
        sensors=OracleSensorMatrix(semantic=shocked_semantic, microstructure=shocked_micro, macro=shocked_macro),
        strategies=shocked_strategies,
    )


def _scenario_outcome(
    payload: OracleAdvisoryInput,
    baseline_fusion: OracleStrategicFusionReport,
    baseline_avg_posterior: float,
    shock: OracleScenarioShock,
    *,
    exact_evidence_support_score: float = 0.0,
    exact_evidence_facts: list[str] | None = None,
    now_utc: datetime,
) -> OracleScenarioOutcome:
    simulated_input = apply_scenario_shock_to_input(payload, shock)
    fusion = build_oracle_strategic_fusion_report(simulated_input, now_utc=now_utc)
    posterior = build_strategy_health_posterior_report(simulated_input, fusion, now_utc=now_utc)
    transition = compare_strategic_fusion_reports(baseline_fusion, fusion, now_utc=now_utc)
    queue = build_oracle_opportunity_queue_report(simulated_input, fusion, posterior, transition_report=transition, now_utc=now_utc)
    top_item = queue.items[0] if queue.items else None
    return OracleScenarioOutcome(
        scenario_id=shock.scenario_id,
        title=shock.title,
        scenario_kind=shock.scenario_kind,
        exact_evidence_support_score=round(exact_evidence_support_score, 6),
        resulting_dominant_regime=fusion.dominant_regime,
        resulting_strategic_posture=fusion.strategic_posture,
        transition_classification=transition.transition_classification,
        doctrine_stress_delta=round(fusion.doctrine_stress_score - baseline_fusion.doctrine_stress_score, 6),
        caution_delta=round(fusion.caution_score - baseline_fusion.caution_score, 6),
        opportunity_delta=round(fusion.opportunity_score - baseline_fusion.opportunity_score, 6),
        average_posterior_delta=round(posterior.average_posterior_edge_confidence - baseline_avg_posterior, 6),
        leading_queue_item_title=(top_item.title if top_item is not None else None),
        leading_queue_kind=(top_item.queue_kind if top_item is not None else None),
        summary_line=(
            f"{shock.title} would move posture toward {fusion.strategic_posture} under {fusion.dominant_regime}; "
            f"caution delta {fusion.caution_score - baseline_fusion.caution_score:+.2f}, opportunity delta {fusion.opportunity_score - baseline_fusion.opportunity_score:+.2f}."
        ),
        operator_action=(
            (top_item.operator_action if top_item is not None else "Refresh strategic evidence before changing doctrine confidence.")
            if exact_evidence_support_score < 0.99 else
            (top_item.operator_action if top_item is not None else "Advance this scenario review with the exact sealed supporting subject while keeping execution authority advisory-only.")
        ),
        evidence=_unique([
            shock.summary,
            f"transition={transition.transition_classification}",
            f"doctrine_stress_delta={fusion.doctrine_stress_score - baseline_fusion.doctrine_stress_score:+.2f}",
            f"caution_delta={fusion.caution_score - baseline_fusion.caution_score:+.2f}",
            f"opportunity_delta={fusion.opportunity_score - baseline_fusion.opportunity_score:+.2f}",
            f"avg_posterior_delta={posterior.average_posterior_edge_confidence - baseline_avg_posterior:+.2f}",
            *fusion.doctrine_pressure_points[:2],
            *(top_item.evidence[:3] if top_item is not None else []),
            *((exact_evidence_facts or [])[:4]),
        ]),
    )


def build_oracle_scenario_lab_report(
    payload: OracleAdvisoryInput,
    *,
    plan: OracleScenarioPlanInput | None = None,
    baseline_fusion_report: OracleStrategicFusionReport | None = None,
    doctrine_adaptation_report=None,
    research_priority_report=None,
    doctrine_adaptation_report_path: Path | None = None,
    research_priority_report_path: Path | None = None,
    repo_root: Path | None = None,
    search_root: Path | None = None,
    now_utc: datetime | None = None,
) -> OracleScenarioLabReport:
    issued_at = now_utc or _utc_now()
    baseline_fusion = baseline_fusion_report or build_oracle_strategic_fusion_report(payload, now_utc=issued_at)
    baseline_posterior = build_strategy_health_posterior_report(payload, baseline_fusion, now_utc=issued_at)
    baseline_avg = baseline_posterior.average_posterior_edge_confidence
    doctrine = doctrine_adaptation_report
    priorities = research_priority_report
    oracle_run_id, input_timestamp_utc, _ = assert_matching_strategic_epoch(baseline_fusion, baseline_posterior)
    resolved_repo_root = repo_root.resolve() if repo_root is not None else None
    resolved_search_root = search_root.resolve() if search_root is not None else resolved_repo_root
    doctrine_artifact_evidence = discover_preferred_strategic_artifact_evidence(report_path=Path(doctrine_adaptation_report_path), repo_root=resolved_repo_root, search_root=resolved_search_root) if doctrine_adaptation_report_path is not None and Path(doctrine_adaptation_report_path).exists() and resolved_repo_root is not None else None
    research_artifact_evidence = discover_preferred_strategic_artifact_evidence(report_path=Path(research_priority_report_path), repo_root=resolved_repo_root, search_root=resolved_search_root) if research_priority_report_path is not None and Path(research_priority_report_path).exists() and resolved_repo_root is not None else None
    exact_evidence_support = round(max(strategic_artifact_evidence_support_score(doctrine_artifact_evidence), strategic_artifact_evidence_support_score(research_artifact_evidence)), 6)
    exact_evidence_facts = preferred_artifact_evidence_fact("scenario_support", research_artifact_evidence or doctrine_artifact_evidence)
    scenario_plan = plan or default_scenario_plan(payload)
    scenarios = [
        _scenario_outcome(payload, baseline_fusion, baseline_avg, shock, exact_evidence_support_score=exact_evidence_support, exact_evidence_facts=exact_evidence_facts, now_utc=issued_at)
        for shock in scenario_plan.scenarios
    ]
    downside = max(
        (item for item in scenarios if item.scenario_kind == "DOWNSIDE"),
        key=lambda item: (item.caution_delta - item.opportunity_delta, item.doctrine_stress_delta),
        default=None,
    )
    upside = max(
        (item for item in scenarios if item.scenario_kind == "UPSIDE"),
        key=lambda item: (item.opportunity_delta - item.caution_delta, item.average_posterior_delta),
        default=None,
    )
    operator_actions = _unique([
        (downside.operator_action if downside is not None else "Stress test downside assumptions before increasing conviction."),
        (upside.operator_action if upside is not None else "Keep one upside recovery scenario active so opportunity drift is not missed."),
        "Treat scenario outputs as advisory-only research futures, never as execution authority.",
    ])[:6]
    return OracleScenarioLabReport(
        generated_at_utc=issued_at,
        universe_label=payload.universe_label,
        oracle_run_id=oracle_run_id,
        input_timestamp_utc=input_timestamp_utc,
        baseline_dominant_regime=baseline_fusion.dominant_regime,
        baseline_strategic_posture=baseline_fusion.strategic_posture,
        preferred_strategic_backing_source=getattr(doctrine, "preferred_strategic_backing_source", None) or getattr(priorities, "preferred_strategic_backing_source", None) or preferred_strategic_backing_source(getattr(doctrine, 'strategic_memory_horizon_report', None) if hasattr(doctrine, 'strategic_memory_horizon_report') else None),
        preferred_strategic_backing_classification=getattr(doctrine, "preferred_strategic_backing_classification", None) or getattr(priorities, "preferred_strategic_backing_classification", None) or preferred_strategic_backing_classification(getattr(doctrine, 'strategic_memory_horizon_report', None) if hasattr(doctrine, 'strategic_memory_horizon_report') else None),
        exact_evidence_support_score=exact_evidence_support,
        baseline_average_posterior_edge_confidence=baseline_avg,
        summary_line=(
            f"Scenario lab evaluated {len(scenarios)} futures from baseline posture {baseline_fusion.strategic_posture}; "
            f"highest downside={downside.scenario_id if downside is not None else 'none'}, "
            f"highest upside={upside.scenario_id if upside is not None else 'none'}."
        ),
        scenarios=scenarios,
        highest_downside_scenario_id=(downside.scenario_id if downside is not None else None),
        highest_upside_scenario_id=(upside.scenario_id if upside is not None else None),
        operator_actions=operator_actions,
    )


def render_oracle_scenario_lab_markdown(report: OracleScenarioLabReport) -> str:
    blocks: list[str] = []
    for scenario in report.scenarios:
        evidence = "\n".join(f"- {item}" for item in scenario.evidence) or "- none"
        blocks.append(
            f"## {scenario.title}\n\n"
            f"- Kind: {scenario.scenario_kind}\n"
            f"- Resulting regime: {scenario.resulting_dominant_regime}\n"
            f"- Resulting posture: {scenario.resulting_strategic_posture}\n"
            f"- Transition classification: {scenario.transition_classification}\n"
            f"- Summary: {scenario.summary_line}\n\n"
            f"### Effects\n\n"
            f"- doctrine_stress_delta={scenario.doctrine_stress_delta:+.2f}\n"
            f"- caution_delta={scenario.caution_delta:+.2f}\n"
            f"- opportunity_delta={scenario.opportunity_delta:+.2f}\n"
            f"- average_posterior_delta={scenario.average_posterior_delta:+.2f}\n"
            f"- leading_queue_item={scenario.leading_queue_item_title or 'none'}\n"
            f"- leading_queue_kind={scenario.leading_queue_kind or 'none'}\n\n"
            f"### Evidence\n\n{evidence}\n\n"
            f"### Operator action\n\n- {scenario.operator_action}"
        )
    actions = "\n".join(f"- {item}" for item in report.operator_actions) or "- none"
    return f"""# ORACLE SCENARIO LAB REPORT

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Universe: {report.universe_label}
- Baseline regime: {report.baseline_dominant_regime}
- Baseline posture: {report.baseline_strategic_posture}
- Preferred backing source: {report.preferred_strategic_backing_source or 'none'}
- Preferred backing classification: {report.preferred_strategic_backing_classification or 'none'}
- Exact evidence support score: {report.exact_evidence_support_score:.2f}
- Baseline average posterior edge confidence: {report.baseline_average_posterior_edge_confidence:.2f}
- Highest downside scenario: {report.highest_downside_scenario_id or 'none'}
- Highest upside scenario: {report.highest_upside_scenario_id or 'none'}

## Summary

{report.summary_line}

{"\n\n".join(blocks) if blocks else 'No scenarios were evaluated.'}

## Operator actions

{actions}
"""
