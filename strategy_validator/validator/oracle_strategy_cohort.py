from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from strategy_validator.contracts.oracle import (
    OracleAdvisoryInput,
    OracleOpportunityQueueReport,
    OracleRegimeTransitionSignalReport,
    OracleResearchExecutionMemoryReport,
    OracleScenarioPlanInput,
    OracleStrategicFusionReport,
    OracleStrategyCohortItem,
    OracleStrategyCohortReport,
    OracleThesisMemoryItem,
    OracleThesisMemoryReport,
    StrategyHealthPosteriorReport,
)
from strategy_validator.validator.oracle_opportunity_queue import build_oracle_opportunity_queue_report
from strategy_validator.validator.oracle_regime_transition import compare_strategic_fusion_reports
from strategy_validator.validator.oracle_scenario_lab import apply_scenario_shock_to_input, default_scenario_plan
from strategy_validator.validator.oracle_history_integrity import preferred_strategic_backing_classification, preferred_strategic_backing_source
from strategy_validator.validator.oracle_strategic_artifact_evidence import discover_preferred_strategic_artifact_evidence, preferred_artifact_evidence_fact, strategic_artifact_evidence_support_score
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report
from strategy_validator.validator.oracle_thesis_memory import build_oracle_thesis_memory_report
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.strategy_health_posterior import build_strategy_health_posterior_report
from strategy_validator.validator.oracle_run_identity import assert_matching_strategic_epoch


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _unique(items: list[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if normalized and normalized not in output:
            output.append(normalized)
    return output


def _transition_sensitivity(state_regime_fit: str, transition_report: OracleRegimeTransitionSignalReport | None) -> float:
    if transition_report is None:
        base = 0.18
    else:
        base = {
            "STABLE_REGIME": 0.12,
            "DRIFTING": 0.28,
            "TRANSITIONING": 0.48,
            "HIGH_UNCERTAINTY": 0.65,
            "STRUCTURAL_BREAK_CANDIDATE": 0.82,
        }.get(transition_report.transition_classification, 0.30)
    fit_adj = {"ALIGNED": -0.08, "NEUTRAL": 0.04, "MISMATCH": 0.15}.get(state_regime_fit, 0.0)
    return round(_clamp(base + fit_adj), 6)


def _thesis_pressure(items: list[OracleThesisMemoryItem], strategy_id: str) -> tuple[float, list[str]]:
    matching = [item for item in items if strategy_id in item.strategy_ids or item.thesis_id == f"strategy:{strategy_id}"]
    if not matching:
        return 0.25, []
    item = matching[0]
    pressure = {
        "SUPPORTIVE": 0.12,
        "NEUTRAL": 0.32,
        "CAUTIONARY": 0.55,
        "AT_RISK": 0.78,
        "BROKEN": 0.92,
    }.get(item.current_state, 0.40)
    if item.evolution_state in {"WEAKENING", "REVERSING"}:
        pressure = min(1.0, pressure + 0.12)
    elif item.evolution_state in {"STRENGTHENING", "EMERGING"}:
        pressure = max(0.0, pressure - 0.08)
    evidence = _unique([
        f"thesis_state={item.current_state}",
        f"thesis_evolution={item.evolution_state}",
        *item.evidence_for[:2],
        *item.evidence_against[:2],
    ])
    return round(_clamp(pressure), 6), evidence


def _queue_pressure(report: OracleOpportunityQueueReport, strategy_id: str) -> tuple[float, list[str]]:
    matching = [item for item in report.items if item.strategy_id == strategy_id]
    if not matching:
        return 0.30, []
    caution = sum(item.priority_score for item in matching if item.queue_kind != "OPPORTUNITY")
    opportunity = sum(item.priority_score for item in matching if item.queue_kind == "OPPORTUNITY")
    pressure = _clamp(0.50 + caution - 0.60 * opportunity)
    evidence = _unique([f"queue_item={item.queue_kind}:{item.priority_score:.2f}:{item.title}" for item in matching[:3]])
    return round(pressure, 6), evidence


def _scenario_posteriors(
    payload: OracleAdvisoryInput,
    strategy_id: str,
    scenario_plan: OracleScenarioPlanInput,
    *,
    now_utc: datetime,
) -> tuple[float, float, list[str]]:
    if not scenario_plan.scenarios:
        return 0.0, 0.0, []
    values: list[float] = []
    evidence: list[str] = []
    for shock in scenario_plan.scenarios:
        simulated_input = apply_scenario_shock_to_input(payload, shock)
        fusion = build_oracle_strategic_fusion_report(simulated_input, now_utc=now_utc)
        posterior = build_strategy_health_posterior_report(simulated_input, fusion, now_utc=now_utc)
        state = next((item for item in posterior.strategies if item.strategy_id == strategy_id), None)
        if state is None:
            continue
        values.append(state.posterior_edge_confidence)
        evidence.append(f"scenario={shock.scenario_id}:posterior={state.posterior_edge_confidence:.2f}")
    if not values:
        return 0.0, 0.0, []
    return round(sum(values) / len(values), 6), round(min(values), 6), evidence[:4]


def _operator_action(bucket: str, strategy_id: str) -> str:
    if bucket == "LEAD":
        return f"Use {strategy_id} as a lead research cohort and validate whether the current edge survives the next scenario refresh."
    if bucket == "WATCH":
        return f"Keep {strategy_id} in the active watch cohort and require one more confirming window before increasing conviction."
    if bucket == "PRESSURED":
        return f"Treat {strategy_id} as pressured until thesis drift or queue pressure eases."
    return f"Keep {strategy_id} in research-only mode until resilience and posterior evidence recover."



def _bucket_from_scores(cohort_rank: float, scenario_floor: float, thesis_pressure: float, posterior_confidence: float) -> str:
    if cohort_rank >= 0.70 and scenario_floor >= 0.42 and thesis_pressure < 0.45:
        return "LEAD"
    if cohort_rank >= 0.54 and scenario_floor >= 0.26:
        return "WATCH"
    if posterior_confidence >= 0.28 or scenario_floor >= 0.16:
        return "PRESSURED"
    return "RESEARCH_ONLY"


def _apply_execution_memory(item: OracleStrategyCohortItem, execution_memory_report: OracleResearchExecutionMemoryReport | None) -> OracleStrategyCohortItem:
    if execution_memory_report is None:
        return item
    relevant = [outcome for outcome in execution_memory_report.items if item.strategy_id in outcome.related_strategy_ids]
    if not relevant:
        return item
    delta = sum(outcome.confidence_impact for outcome in relevant) * 0.16
    rank_delta = 0.0
    evidence: list[str] = []
    action = item.operator_action
    for outcome in relevant:
        if outcome.cohort_effect == 'PROMOTES':
            rank_delta += 0.08
        elif outcome.cohort_effect == 'DEMOTES':
            rank_delta -= 0.10
        elif outcome.cohort_effect == 'WATCH':
            rank_delta -= 0.04
        evidence.append(f"investigation:{outcome.priority_id}:{outcome.cohort_effect}:{outcome.execution_state}")
        action = outcome.next_action
    resilience = _clamp(item.resilience_score + delta + 0.5 * rank_delta)
    cohort_rank = _clamp(item.cohort_rank_score + delta + rank_delta)
    bucket = _bucket_from_scores(cohort_rank, item.scenario_downside_floor, item.thesis_pressure_score, item.current_posterior_edge_confidence)
    return item.model_copy(update={
        'resilience_score': round(resilience, 6),
        'cohort_rank_score': round(cohort_rank, 6),
        'cohort_bucket': bucket,
        'summary_line': f"{item.strategy_id} ranks {bucket.lower()} with cohort score {cohort_rank:.2f} after {len(relevant)} investigation outcome(s).",
        'evidence': _unique(evidence + list(item.evidence))[:10],
        'operator_action': action,
    })

def build_oracle_strategy_cohort_report(
    payload: OracleAdvisoryInput,
    fusion_report: OracleStrategicFusionReport | None = None,
    posterior_report: StrategyHealthPosteriorReport | None = None,
    transition_report: OracleRegimeTransitionSignalReport | None = None,
    queue_report: OracleOpportunityQueueReport | None = None,
    thesis_memory_report: OracleThesisMemoryReport | None = None,
    scenario_plan: OracleScenarioPlanInput | None = None,
    previous_fusion_report: OracleStrategicFusionReport | None = None,
    execution_memory_report: OracleResearchExecutionMemoryReport | None = None,
    doctrine_adaptation_report=None,
    research_priority_report=None,
    doctrine_adaptation_report_path: Path | None = None,
    research_priority_report_path: Path | None = None,
    repo_root: Path | None = None,
    search_root: Path | None = None,
    now_utc: datetime | None = None,
) -> OracleStrategyCohortReport:
    issued_at = now_utc or _utc_now()
    fusion = fusion_report or build_oracle_strategic_fusion_report(payload, now_utc=issued_at)
    posterior = posterior_report or build_strategy_health_posterior_report(payload, fusion, now_utc=issued_at)
    transition = transition_report
    if transition is None and previous_fusion_report is not None:
        transition = compare_strategic_fusion_reports(previous_fusion_report, fusion, now_utc=issued_at)
    queue = queue_report or build_oracle_opportunity_queue_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        now_utc=issued_at,
    )
    thesis = thesis_memory_report or build_oracle_thesis_memory_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        now_utc=issued_at,
    )
    plan = scenario_plan or default_scenario_plan(payload)

    doctrine = doctrine_adaptation_report
    priorities = research_priority_report
    if doctrine is not None and priorities is not None:
        oracle_run_id, input_timestamp_utc, _ = assert_matching_strategic_epoch(fusion, posterior, transition, queue, thesis, execution_memory_report, doctrine, priorities)
    else:
        oracle_run_id, input_timestamp_utc, _ = assert_matching_strategic_epoch(fusion, posterior, transition, queue, thesis, execution_memory_report)
    resolved_repo_root = repo_root.resolve() if repo_root is not None else None
    resolved_search_root = search_root.resolve() if search_root is not None else resolved_repo_root
    doctrine_artifact_evidence = discover_preferred_strategic_artifact_evidence(report_path=Path(doctrine_adaptation_report_path), repo_root=resolved_repo_root, search_root=resolved_search_root) if doctrine_adaptation_report_path is not None and Path(doctrine_adaptation_report_path).exists() and resolved_repo_root is not None else None
    research_artifact_evidence = discover_preferred_strategic_artifact_evidence(report_path=Path(research_priority_report_path), repo_root=resolved_repo_root, search_root=resolved_search_root) if research_priority_report_path is not None and Path(research_priority_report_path).exists() and resolved_repo_root is not None else None
    doctrine_support = strategic_artifact_evidence_support_score(doctrine_artifact_evidence)
    research_support = strategic_artifact_evidence_support_score(research_artifact_evidence)
    exact_evidence_support = round(max(doctrine_support, research_support), 6)

    items: list[OracleStrategyCohortItem] = []
    for state in posterior.strategies:
        scenario_avg, scenario_floor, scenario_evidence = _scenario_posteriors(payload, state.strategy_id, plan, now_utc=issued_at)
        transition_sensitivity = _transition_sensitivity(state.regime_fit, transition)
        thesis_pressure, thesis_evidence = _thesis_pressure(thesis.items, state.strategy_id)
        queue_pressure, queue_evidence = _queue_pressure(queue, state.strategy_id)
        strategy_support = 0.0
        if priorities is not None and any(state.strategy_id in item.related_strategy_ids for item in priorities.items):
            strategy_support = max(strategy_support, research_support)
        if doctrine is not None:
            strategy_support = max(strategy_support, doctrine_support * 0.6)
        resilience = _clamp(
            0.36 * state.posterior_edge_confidence
            + 0.20 * scenario_avg
            + 0.16 * scenario_floor
            + 0.12 * (1.0 - state.degradation_score)
            + 0.08 * state.recovery_score
            + 0.08 * (1.0 - transition_sensitivity)
            + 0.06 * strategy_support
        )
        cohort_rank = _clamp(
            0.42 * resilience
            + 0.16 * state.posterior_edge_confidence
            + 0.14 * scenario_avg
            + 0.10 * scenario_floor
            + 0.08 * (1.0 - thesis_pressure)
            + 0.06 * (1.0 - queue_pressure)
            + 0.04 * (1.0 - transition_sensitivity)
            + 0.10 * strategy_support
        )
        bucket = _bucket_from_scores(cohort_rank, scenario_floor, thesis_pressure, state.posterior_edge_confidence)
        built_item = OracleStrategyCohortItem(
                strategy_id=state.strategy_id,
                strategy_type=state.strategy_type,
                cohort_bucket=bucket,
                exact_evidence_support_score=round(strategy_support, 6),
                cohort_rank_score=round(cohort_rank, 6),
                resilience_score=round(resilience, 6),
                current_posterior_edge_confidence=round(state.posterior_edge_confidence, 6),
                scenario_average_posterior=round(scenario_avg, 6),
                scenario_downside_floor=round(scenario_floor, 6),
                transition_sensitivity_score=transition_sensitivity,
                thesis_pressure_score=thesis_pressure,
                queue_pressure_score=queue_pressure,
                summary_line=(
                    f"{state.strategy_id} ranks {bucket.lower()} with cohort score {cohort_rank:.2f}, "
                    f"posterior {state.posterior_edge_confidence:.2f}, and downside floor {scenario_floor:.2f}."
                ),
                evidence=_unique([
                    f"regime_fit={state.regime_fit}",
                    f"recommended_action={state.recommended_action}",
                    f"resilience_score={resilience:.2f}",
                    f"transition_sensitivity={transition_sensitivity:.2f}",
                    f"thesis_pressure={thesis_pressure:.2f}",
                    f"queue_pressure={queue_pressure:.2f}",
                    *preferred_artifact_evidence_fact("cohort_support", research_artifact_evidence if strategy_support >= research_support and research_support > 0 else doctrine_artifact_evidence if strategy_support > 0 else None),
                    *state.reasons[:3],
                    *scenario_evidence,
                    *thesis_evidence,
                    *queue_evidence,
                ])[:10],
                operator_action=(
                    _operator_action(bucket, state.strategy_id)
                    if strategy_support < 0.99 else f"Advance {state.strategy_id} with the exact sealed supporting subject while keeping strategist outputs advisory-only."
                ),
            )
        built_item = _apply_execution_memory(built_item, execution_memory_report)
        items.append(built_item)

    items.sort(key=lambda item: (-item.cohort_rank_score, item.cohort_bucket, item.strategy_id))
    lead_ids = [item.strategy_id for item in items if item.cohort_bucket == "LEAD"]
    pressured_ids = [item.strategy_id for item in items if item.cohort_bucket in {"PRESSURED", "RESEARCH_ONLY"}]
    operator_actions = _unique([item.operator_action for item in items] + queue.operator_actions + thesis.operator_actions)[:8]
    return OracleStrategyCohortReport(
        generated_at_utc=issued_at,
        universe_label=payload.universe_label,
        oracle_run_id=oracle_run_id,
        input_timestamp_utc=input_timestamp_utc,
        dominant_regime=fusion.dominant_regime,
        strategic_posture=fusion.strategic_posture,
        preferred_strategic_backing_source=(getattr(doctrine, 'preferred_strategic_backing_source', None) if doctrine is not None else None) or (getattr(priorities, 'preferred_strategic_backing_source', None) if priorities is not None else None) or preferred_strategic_backing_source(getattr(doctrine, 'strategic_memory_horizon_report', None) if doctrine is not None and hasattr(doctrine, 'strategic_memory_horizon_report') else None),
        preferred_strategic_backing_classification=(getattr(doctrine, 'preferred_strategic_backing_classification', None) if doctrine is not None else None) or (getattr(priorities, 'preferred_strategic_backing_classification', None) if priorities is not None else None) or preferred_strategic_backing_classification(getattr(doctrine, 'strategic_memory_horizon_report', None) if doctrine is not None and hasattr(doctrine, 'strategic_memory_horizon_report') else None),
        exact_evidence_support_score=exact_evidence_support,
        transition_classification=(transition.transition_classification if transition else None),
        summary_line=(
            f"Ranked {len(items)} strategies into {len(lead_ids)} lead, "
            f"{sum(item.cohort_bucket == 'WATCH' for item in items)} watch, and {len(pressured_ids)} pressured/research-only cohorts."
        ),
        lead_strategy_ids=lead_ids,
        pressured_strategy_ids=pressured_ids,
        items=items,
        operator_actions=operator_actions,
    )


def render_oracle_strategy_cohort_markdown(report: OracleStrategyCohortReport) -> str:
    blocks: list[str] = []
    for item in report.items:
        evidence = "\n".join(f"- {entry}" for entry in item.evidence) or "- none"
        blocks.append(
            f"## {item.strategy_id}\n\n"
            f"- Type: {item.strategy_type}\n"
            f"- Cohort bucket: {item.cohort_bucket}\n"
            f"- Cohort rank score: {item.cohort_rank_score:.2f}\n"
            f"- Resilience score: {item.resilience_score:.2f}\n"
            f"- Current posterior: {item.current_posterior_edge_confidence:.2f}\n"
            f"- Scenario average posterior: {item.scenario_average_posterior:.2f}\n"
            f"- Downside floor: {item.scenario_downside_floor:.2f}\n"
            f"- Summary: {item.summary_line}\n\n"
            f"### Evidence\n\n{evidence}\n\n"
            f"### Operator action\n\n- {item.operator_action}"
        )
    actions = "\n".join(f"- {item}" for item in report.operator_actions) or "- none"
    return f"""# ORACLE STRATEGY COHORT REPORT

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Universe: {report.universe_label}
- Dominant regime: {report.dominant_regime}
- Strategic posture: {report.strategic_posture}
- Preferred backing source: {report.preferred_strategic_backing_source or 'none'}
- Preferred backing classification: {report.preferred_strategic_backing_classification or 'none'}
- Exact evidence support score: {report.exact_evidence_support_score:.2f}
- Transition classification: {report.transition_classification or 'N/A'}

## Summary

{report.summary_line}

{"\n\n".join(blocks) if blocks else 'No strategy cohorts were available.'}

## Operator actions

{actions}
"""


def load_strategy_cohort_report(path: Path) -> OracleStrategyCohortReport:
    return OracleStrategyCohortReport.model_validate(json.loads(path.read_text(encoding="utf-8")))
