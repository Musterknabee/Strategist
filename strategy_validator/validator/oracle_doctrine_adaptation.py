from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from strategy_validator.contracts.oracle_core import OracleAdvisoryInput
from strategy_validator.contracts.oracle_strategic_memory import (
    OracleDoctrineAdaptationItem,
    OracleDoctrineAdaptationReport,
    OracleResearchExecutionMemoryReport,
    OracleThesisMemoryReport,
)
from strategy_validator.contracts.oracle_strategic_fusion import (
    OracleRegimeTransitionSignalReport,
    OracleStrategicFusionReport,
    StrategyHealthPosteriorReport,
)
from strategy_validator.contracts.oracle_strategic_programs import (
    OracleScenarioLabReport,
    OracleStrategyCohortReport,
)
from strategy_validator.validator.oracle_regime_transition import compare_strategic_fusion_reports
from strategy_validator.validator.oracle_scenario_lab import build_oracle_scenario_lab_report
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report
from strategy_validator.validator.oracle_strategy_cohort import build_oracle_strategy_cohort_report
from strategy_validator.validator.oracle_thesis_memory import build_oracle_thesis_memory_report
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.strategy_health_posterior import build_strategy_health_posterior_report
from strategy_validator.validator.oracle_run_identity import assert_matching_strategic_epoch
from strategy_validator.validator.oracle_history_integrity import history_integrity_status, sealed_history_observation_count, unsealed_history_excluded_count, preferred_strategic_backing_source, preferred_strategic_backing_classification


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _unique(items: list[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if normalized and normalized not in output:
            output.append(normalized)
    return output


def _transition_pressure(transition: OracleRegimeTransitionSignalReport | None) -> tuple[float, list[str]]:
    if transition is None:
        return 0.18, []
    score = {
        "STABLE_REGIME": 0.12,
        "DRIFTING": 0.30,
        "TRANSITIONING": 0.52,
        "HIGH_UNCERTAINTY": 0.72,
        "STRUCTURAL_BREAK_CANDIDATE": 0.90,
    }.get(transition.transition_classification, 0.35)
    return round(score, 6), transition.drivers[:3]


def _scenario_pressure(scenario_lab: OracleScenarioLabReport | None) -> tuple[float, list[str]]:
    if scenario_lab is None or not scenario_lab.scenarios:
        return 0.20, []
    downside = next((item for item in scenario_lab.scenarios if item.scenario_id == scenario_lab.highest_downside_scenario_id), None)
    if downside is None:
        downside = max(scenario_lab.scenarios, key=lambda item: (item.caution_delta + item.doctrine_stress_delta - item.opportunity_delta, item.average_posterior_delta))
    score = _clamp(0.50 + 0.45 * max(downside.caution_delta, 0.0) + 0.35 * max(downside.doctrine_stress_delta, 0.0) + 0.20 * max(-downside.average_posterior_delta, 0.0))
    evidence = _unique([
        f"downside_scenario={downside.scenario_id}",
        f"transition_classification={downside.transition_classification}",
        f"caution_delta={downside.caution_delta:+.2f}",
        f"doctrine_stress_delta={downside.doctrine_stress_delta:+.2f}",
        f"average_posterior_delta={downside.average_posterior_delta:+.2f}",
    ])
    return round(score, 6), evidence


def _doctrine_thesis_pressure(thesis_memory: OracleThesisMemoryReport | None) -> tuple[float, list[str]]:
    if thesis_memory is None:
        return 0.24, []
    item = next((item for item in thesis_memory.items if item.thesis_id == "doctrine:coherence"), None)
    if item is None:
        return 0.24, []
    pressure = {
        "SUPPORTIVE": 0.12,
        "NEUTRAL": 0.32,
        "CAUTIONARY": 0.56,
        "AT_RISK": 0.80,
        "BROKEN": 0.94,
    }.get(item.current_state, 0.40)
    if item.evolution_state in {"WEAKENING", "REVERSING"}:
        pressure = min(1.0, pressure + 0.08)
    elif item.evolution_state in {"STRENGTHENING", "EMERGING"}:
        pressure = max(0.0, pressure - 0.05)
    evidence = _unique([
        f"doctrine_thesis_state={item.current_state}",
        f"doctrine_thesis_evolution={item.evolution_state}",
        *item.evidence_against[:2],
        *item.evidence_for[:1],
    ])
    return round(pressure, 6), evidence


def _cohort_pressure(strategy_cohort: OracleStrategyCohortReport | None) -> tuple[float, list[str]]:
    if strategy_cohort is None or not strategy_cohort.items:
        return 0.22, []
    pressured = sum(1 for item in strategy_cohort.items if item.cohort_bucket in {"PRESSURED", "RESEARCH_ONLY"})
    ratio = pressured / max(len(strategy_cohort.items), 1)
    evidence = [
        f"lead_strategy_ids={','.join(strategy_cohort.lead_strategy_ids) if strategy_cohort.lead_strategy_ids else 'none'}",
        f"pressured_ratio={ratio:.2f}",
    ]
    return round(_clamp(0.15 + 0.80 * ratio), 6), evidence


def _state_from_stress(stress_score: float) -> str:
    if stress_score >= 0.86:
        return "FREEZE"
    if stress_score >= 0.64:
        return "ADAPT"
    if stress_score >= 0.40:
        return "REVIEW"
    return "MONITOR"


def _adaptation_action(clause_label: str, state: str) -> str:
    if state == "FREEZE":
        return f"Freeze doctrine changes touching {clause_label.lower()} until the current stress drivers and thesis contradictions are resolved."
    if state == "ADAPT":
        return f"Adapt {clause_label.lower()} now by tightening its assumptions and refreshing supporting evidence before broad reuse."
    if state == "REVIEW":
        return f"Review {clause_label.lower()} on the next research cadence and test whether the current assumptions still match the observed regime."
    return f"Monitor {clause_label.lower()} and keep collecting confirming evidence before changing doctrine."


def _make_item(clause_id: str, clause_label: str, stress_score: float, review_priority_score: float, weakening_assumptions: list[str], pressure_sources: list[str]) -> OracleDoctrineAdaptationItem:
    state = _state_from_stress(stress_score)
    return OracleDoctrineAdaptationItem(
        clause_id=clause_id,
        clause_label=clause_label,
        adaptation_state=state,
        stress_score=round(_clamp(stress_score), 6),
        review_priority_score=round(_clamp(review_priority_score), 6),
        exact_evidence_support_score=0.0,
        weakening_assumptions=_unique(weakening_assumptions)[:5],
        pressure_sources=_unique(pressure_sources)[:6],
        recommended_adaptation=_adaptation_action(clause_label, state),
        summary_line=f"{clause_label} is in {state.lower()} mode with stress {stress_score:.2f} and review priority {review_priority_score:.2f}.",
    )



def _apply_execution_memory_to_items(items: list[OracleDoctrineAdaptationItem], execution_memory_report: OracleResearchExecutionMemoryReport | None) -> list[OracleDoctrineAdaptationItem]:
    if execution_memory_report is None:
        return items
    adjusted: list[OracleDoctrineAdaptationItem] = []
    for item in items:
        relevant = [outcome for outcome in execution_memory_report.items if item.clause_id in outcome.doctrine_clause_ids]
        if not relevant:
            adjusted.append(item)
            continue
        stress = item.stress_score
        priority = item.review_priority_score
        sources = list(item.pressure_sources)
        weakening = list(item.weakening_assumptions)
        action = item.recommended_adaptation
        exact_support = 0.0
        for outcome in relevant:
            support = float(getattr(outcome, 'exact_evidence_support_score', 0.0) or 0.0)
            exact_support = max(exact_support, support)
            weighted_support = 0.35 + 0.65 * support
            stress += outcome.confidence_impact * (0.08 + 0.04 * weighted_support)
            priority += outcome.urgency_impact * (0.12 + 0.05 * weighted_support)
            if outcome.doctrine_effect == 'PRESSURES':
                stress += 0.08 + 0.06 * weighted_support
                priority += 0.06 + 0.06 * weighted_support
            elif outcome.doctrine_effect == 'FREEZE_CANDIDATE':
                stress += 0.12 + 0.12 * weighted_support
                priority += 0.08 + 0.10 * weighted_support
            elif outcome.doctrine_effect == 'RELIEVES':
                stress -= 0.08 + 0.10 * weighted_support
                priority -= 0.06 + 0.08 * weighted_support
            sources.append(f"investigation:{outcome.priority_id}:{outcome.doctrine_effect}:{outcome.execution_state}")
            if support > 0.0:
                sources.append(f"exact_execution_support={support:.2f}")
            weakening.append(outcome.finding_summary)
            action = outcome.next_action
        stress = _clamp(stress)
        priority = _clamp(priority)
        state = _state_from_stress(stress)
        adjusted.append(item.model_copy(update={
            'adaptation_state': state,
            'stress_score': round(stress, 6),
            'review_priority_score': round(priority, 6),
            'exact_evidence_support_score': round(exact_support, 6),
            'pressure_sources': _unique(sources)[:8],
            'weakening_assumptions': _unique(weakening)[:6],
            'recommended_adaptation': action,
            'summary_line': f"{item.clause_label} is in {state.lower()} mode with stress {stress:.2f} after {len(relevant)} investigation outcome(s) and exact execution support {exact_support:.2f}.",
        }))
    return adjusted

def build_oracle_doctrine_adaptation_report(
    payload: OracleAdvisoryInput,
    fusion_report: OracleStrategicFusionReport | None = None,
    posterior_report: StrategyHealthPosteriorReport | None = None,
    transition_report: OracleRegimeTransitionSignalReport | None = None,
    previous_fusion_report: OracleStrategicFusionReport | None = None,
    thesis_memory_report: OracleThesisMemoryReport | None = None,
    scenario_lab_report: OracleScenarioLabReport | None = None,
    strategy_cohort_report: OracleStrategyCohortReport | None = None,
    execution_memory_report: OracleResearchExecutionMemoryReport | None = None,
    strategic_memory_horizon_report=None,
    now_utc: datetime | None = None,
) -> OracleDoctrineAdaptationReport:
    issued_at = now_utc or _utc_now()
    fusion = fusion_report or build_oracle_strategic_fusion_report(payload, now_utc=issued_at)
    posterior = posterior_report or build_strategy_health_posterior_report(payload, fusion, now_utc=issued_at)
    transition = transition_report
    if transition is None and previous_fusion_report is not None:
        transition = compare_strategic_fusion_reports(previous_fusion_report, fusion, now_utc=issued_at)
    thesis = thesis_memory_report or build_oracle_thesis_memory_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        now_utc=issued_at,
    )
    scenario_lab = scenario_lab_report or build_oracle_scenario_lab_report(payload, baseline_fusion_report=fusion, now_utc=issued_at)
    cohorts = strategy_cohort_report or build_oracle_strategy_cohort_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        thesis_memory_report=thesis,
        now_utc=issued_at,
    )

    oracle_run_id, input_timestamp_utc, _ = assert_matching_strategic_epoch(fusion, posterior, transition, thesis, scenario_lab, cohorts, execution_memory_report)

    transition_pressure, transition_evidence = _transition_pressure(transition)
    scenario_pressure, scenario_evidence = _scenario_pressure(scenario_lab)
    thesis_pressure, thesis_evidence = _doctrine_thesis_pressure(thesis)
    cohort_pressure, cohort_evidence = _cohort_pressure(cohorts)
    pressured_ids = cohorts.pressured_strategy_ids[:3]
    degraded_ids = posterior.degraded_strategy_ids[:3]
    leading_downside = next((item for item in scenario_lab.scenarios if item.scenario_id == scenario_lab.highest_downside_scenario_id), None)
    downside_kind = leading_downside.leading_queue_kind if leading_downside is not None else None

    items = [
        _make_item(
            "doctrine:regime-assumptions",
            "Regime assumptions",
            0.42 * fusion.doctrine_stress_score + 0.24 * transition_pressure + 0.18 * thesis_pressure + 0.16 * scenario_pressure,
            0.48 * fusion.doctrine_stress_score + 0.26 * transition_pressure + 0.16 * scenario_pressure + 0.10 * fusion.caution_score,
            [
                f"dominant_regime={fusion.dominant_regime}",
                f"regime_confidence={fusion.regime_confidence:.2f}",
                *( [f"transition={transition.transition_classification}"] if transition is not None else []),
            ],
            fusion.doctrine_pressure_points[:3] + transition_evidence + scenario_evidence[:2],
        ),
        _make_item(
            "doctrine:liquidity-tolerance",
            "Liquidity tolerance",
            0.38 * payload.sensors.microstructure.liquidity_thinning_score + 0.20 * fusion.caution_score + 0.18 * scenario_pressure + 0.14 * transition_pressure + 0.10 * cohort_pressure,
            0.36 * fusion.caution_score + 0.24 * scenario_pressure + 0.20 * payload.sensors.microstructure.liquidity_thinning_score + 0.20 * max(payload.sensors.microstructure.spread_variance_zscore, 0.0) / 3.0,
            [
                f"liquidity_thinning_score={payload.sensors.microstructure.liquidity_thinning_score:.2f}",
                f"vpin={payload.sensors.microstructure.vpin:.2f}",
                f"spread_variance_zscore={payload.sensors.microstructure.spread_variance_zscore:.2f}",
            ],
            scenario_evidence + [*fusion.caution_factors[:2], *cohort_evidence[:1]],
        ),
        _make_item(
            "doctrine:strategy-alignment",
            "Strategy alignment",
            0.28 * fusion.strategy_pressure_score + 0.22 * cohort_pressure + 0.20 * transition_pressure + 0.15 * thesis_pressure + 0.15 * scenario_pressure,
            0.32 * fusion.strategy_pressure_score + 0.24 * cohort_pressure + 0.22 * scenario_pressure + 0.12 * transition_pressure + 0.10 * (1.0 - posterior.average_posterior_edge_confidence),
            [
                f"average_posterior_edge_confidence={posterior.average_posterior_edge_confidence:.2f}",
                f"degraded_strategy_ids={','.join(degraded_ids) if degraded_ids else 'none'}",
                f"pressured_strategy_ids={','.join(pressured_ids) if pressured_ids else 'none'}",
            ],
            cohort_evidence + [f"strategy_pressure_score={fusion.strategy_pressure_score:.2f}"] + thesis_evidence[:2],
        ),
        _make_item(
            "doctrine:research-expansion",
            "Research expansion",
            0.30 * fusion.caution_score + 0.24 * thesis_pressure + 0.18 * scenario_pressure + 0.16 * transition_pressure + 0.12 * fusion.doctrine_stress_score,
            0.30 * fusion.caution_score + 0.22 * scenario_pressure + 0.18 * thesis_pressure + 0.16 * transition_pressure + 0.14 * fusion.doctrine_stress_score,
            [
                f"strategic_posture={fusion.strategic_posture}",
                f"opportunity_score={fusion.opportunity_score:.2f}",
                f"caution_score={fusion.caution_score:.2f}",
                *( [f"downside_queue_kind={downside_kind}"] if downside_kind else []),
            ],
            thesis_evidence + scenario_evidence + [f"doctrine_stress_score={fusion.doctrine_stress_score:.2f}"],
        ),
    ]
    items = _apply_execution_memory_to_items(items, execution_memory_report)
    integrity_status = history_integrity_status(strategic_memory_horizon_report)
    preferred_backing_source = preferred_strategic_backing_source(strategic_memory_horizon_report)
    preferred_backing_classification = preferred_strategic_backing_classification(strategic_memory_horizon_report)
    items.sort(key=lambda item: (-item.review_priority_score, -item.stress_score, item.clause_id))
    top_review_clause_ids = [item.clause_id for item in items if item.adaptation_state in {"FREEZE", "ADAPT", "REVIEW"}][:4]
    freeze_recommended = any(item.adaptation_state == "FREEZE" for item in items)
    exact_evidence_support_score = round(max((item.exact_evidence_support_score for item in items), default=0.0), 6)
    relieving_exact = [item for item in execution_memory_report.items if item.doctrine_effect == "RELIEVES" and item.exact_evidence_support_score >= 0.85] if execution_memory_report is not None else []
    pressuring_exact = [item for item in execution_memory_report.items if item.doctrine_effect in {"PRESSURES", "FREEZE_CANDIDATE"} and item.exact_evidence_support_score >= 0.85] if execution_memory_report is not None else []
    cadence_feedback: list[str] = []
    if pressuring_exact:
        cadence_feedback.append("Increase doctrine review cadence because exact sealed execution outcomes are confirming live pressure on the affected clauses.")
    elif relieving_exact and not freeze_recommended:
        cadence_feedback.append("Keep doctrine review active but allow the exact sealed relieving outcomes to slightly relax freeze pressure for the directly supported clauses.")
    elif exact_evidence_support_score >= 0.85:
        cadence_feedback.append("Maintain doctrine review cadence around the exact sealed execution subjects and avoid generalizing beyond the supported clause scope.")
    operator_actions = _unique(cadence_feedback + [item.recommended_adaptation for item in items] + thesis.operator_actions + cohorts.operator_actions + scenario_lab.operator_actions)[:8]
    return OracleDoctrineAdaptationReport(
        generated_at_utc=issued_at,
        universe_label=payload.universe_label,
        oracle_run_id=oracle_run_id,
        input_timestamp_utc=input_timestamp_utc,
        dominant_regime=fusion.dominant_regime,
        strategic_posture=fusion.strategic_posture,
        transition_classification=(transition.transition_classification if transition else None),
        history_integrity_status=integrity_status,
        sealed_history_observation_count=sealed_history_observation_count(strategic_memory_horizon_report),
        unsealed_history_excluded_count=unsealed_history_excluded_count(strategic_memory_horizon_report),
        preferred_strategic_backing_source=preferred_backing_source,
        preferred_strategic_backing_classification=preferred_backing_classification,
        exact_evidence_support_score=exact_evidence_support_score,
        summary_line=(
            f"Doctrine adaptation advisory for {payload.universe_label}: top_review={top_review_clause_ids[0] if top_review_clause_ids else 'none'}, "
            f"freeze_recommended={'yes' if freeze_recommended else 'no'}, doctrine_stress={fusion.doctrine_stress_score:.2f}, "
            f"caution_score={fusion.caution_score:.2f}, exact_execution_support={exact_evidence_support_score:.2f}."
        ),
        top_review_clause_ids=top_review_clause_ids,
        freeze_recommended=freeze_recommended,
        items=items,
        operator_actions=operator_actions,
    )


def render_oracle_doctrine_adaptation_markdown(report: OracleDoctrineAdaptationReport) -> str:
    blocks: list[str] = []
    for item in report.items:
        weakening = "\n".join(f"- {entry}" for entry in item.weakening_assumptions) or "- none"
        pressure = "\n".join(f"- {entry}" for entry in item.pressure_sources) or "- none"
        blocks.append(
            f"## {item.clause_label}\n\n"
            f"- Adaptation state: {item.adaptation_state}\n"
            f"- Stress score: {item.stress_score:.2f}\n"
            f"- Review priority score: {item.review_priority_score:.2f}\n"
            f"- Summary: {item.summary_line}\n"
            f"- Recommended adaptation: {item.recommended_adaptation}\n\n"
            f"### Weakening assumptions\n\n{weakening}\n\n"
            f"### Pressure sources\n\n{pressure}"
        )
    actions = "\n".join(f"- {entry}" for entry in report.operator_actions) or "- none"
    block_lines = "\n\n".join(blocks)
    return f"""# ORACLE DOCTRINE ADAPTATION REPORT

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Universe: {report.universe_label}
- Dominant regime: {report.dominant_regime}
- Strategic posture: {report.strategic_posture}
- Transition classification: {report.transition_classification or 'N/A'}
- Freeze recommended: {report.freeze_recommended}
- History integrity: {report.history_integrity_status}
- Preferred strategic backing source: {report.preferred_strategic_backing_source or 'none'}
- Preferred strategic backing classification: {report.preferred_strategic_backing_classification or 'none'}
- Exact evidence support score: {report.exact_evidence_support_score:.2f}

## Summary

{report.summary_line}

{block_lines}

## Recommended operator actions

{actions}
"""


def load_doctrine_adaptation_report(path: Path) -> OracleDoctrineAdaptationReport:
    return OracleDoctrineAdaptationReport.model_validate(json.loads(path.read_text(encoding="utf-8")))
