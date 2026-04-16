from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from strategy_validator.contracts.oracle import (
    OracleAdvisoryInput,
    OracleContradictionResolutionReport,
    OracleDoctrineAdaptationReport,
    OracleResearchExecutionMemoryReport,
    OracleResearchPriorityReport,
    OracleScenarioLabReport,
    OracleStrategicFusionReport,
    OracleStrategicInterventionItem,
    OracleStrategicInterventionReport,
    OracleStrategicMemoryHorizonReport,
    OracleStrategicNarrativeReport,
    OracleStrategicTensionReport,
    OracleStrategyCohortReport,
    OracleThesisGraphReport,
    OracleThesisMemoryReport,
    StrategyHealthPosteriorReport,
)
from strategy_validator.validator.oracle_contradiction_resolution import build_oracle_contradiction_resolution_report
from strategy_validator.validator.oracle_doctrine_adaptation import build_oracle_doctrine_adaptation_report
from strategy_validator.validator.oracle_research_planner import build_oracle_research_priority_report
from strategy_validator.validator.oracle_scenario_lab import build_oracle_scenario_lab_report
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report
from strategy_validator.validator.oracle_strategy_cohort import build_oracle_strategy_cohort_report
from strategy_validator.validator.oracle_strategic_memory_horizon import build_oracle_strategic_memory_horizon_report
from strategy_validator.validator.oracle_strategic_narrative import build_oracle_strategic_narrative_report
from strategy_validator.validator.oracle_strategic_tension import build_oracle_strategic_tension_report
from strategy_validator.validator.oracle_thesis_graph import build_oracle_thesis_graph_report
from strategy_validator.validator.oracle_thesis_memory import build_oracle_thesis_memory_report
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.oracle_strategic_artifact_evidence import discover_preferred_strategic_artifact_evidence, strategic_artifact_evidence_support_score, preferred_artifact_evidence_fact
from strategy_validator.validator.oracle_cadence_feedback import summarize_exact_cadence_feedback, classify_exact_cadence_signal, cadence_operator_action, cadence_recommendation_suffix
from strategy_validator.validator.strategy_health_posterior import build_strategy_health_posterior_report
from strategy_validator.validator.oracle_run_identity import assert_matching_strategic_epoch
from strategy_validator.validator.oracle_history_integrity import (
    history_integrity_status,
    sealed_history_observation_count,
    unsealed_history_excluded_count,
    intervention_penalty,
    integrity_operator_action,
    preferred_strategic_backing_source,
    preferred_strategic_backing_classification,
)


_DEFENSIVE = {"CAUTION_BIASED", "DEFENSIVE_RESEARCH", "RESEARCH_FREEZE"}


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _unique(items: list[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if normalized and normalized not in output:
            output.append(normalized)
    return output


def _projected_state(score: float) -> str:
    if score >= 0.78:
        return "HIGH_CONVICTION"
    if score >= 0.58:
        return "GUARDED_CONVICTION"
    if score >= 0.35:
        return "FRAGILE_CONVICTION"
    return "BROKEN_CONVICTION"


def _kind_for_resolution(kind: str) -> str:
    mapping = {
        "DOCTRINE_CONTRADICTION": "DOCTRINE_RELIEF",
        "COHORT_CONTRADICTION": "COHORT_STABILIZATION",
        "CASCADE_CONTRADICTION": "RESOLVE_CONTRADICTION",
        "POSTURE_RISK_CONTRADICTION": "SCENARIO_HEDGE",
        "INVESTIGATION_CONTRADICTION": "RESOLVE_CONTRADICTION",
        "CONSENSUS_VALIDATION": "VALIDATE_CONSENSUS",
    }
    return mapping.get(kind, "RESOLVE_CONTRADICTION")


def _sort_items(items: list[OracleStrategicInterventionItem]) -> list[OracleStrategicInterventionItem]:
    return sorted(
        items,
        key=lambda item: (
            -(0.34 * item.projected_conviction_gain_score
              + 0.22 * item.projected_fragility_reduction_score
              + 0.14 * item.projected_queue_pressure_relief_score
              + 0.12 * item.projected_doctrine_stress_relief_score
              + 0.10 * item.projected_cohort_resilience_gain_score
              + 0.08 * item.projected_cascade_relief_score),
            item.intervention_kind,
            item.title,
        ),
    )


def build_oracle_strategic_intervention_report(
    payload: OracleAdvisoryInput,
    *,
    fusion_report: OracleStrategicFusionReport | None = None,
    posterior_report: StrategyHealthPosteriorReport | None = None,
    thesis_memory_report: OracleThesisMemoryReport | None = None,
    strategy_cohort_report: OracleStrategyCohortReport | None = None,
    doctrine_adaptation_report: OracleDoctrineAdaptationReport | None = None,
    research_priority_report: OracleResearchPriorityReport | None = None,
    research_execution_memory_report: OracleResearchExecutionMemoryReport | None = None,
    thesis_graph_report: OracleThesisGraphReport | None = None,
    strategic_tension_report: OracleStrategicTensionReport | None = None,
    strategic_narrative_report: OracleStrategicNarrativeReport | None = None,
    strategic_memory_horizon_report: OracleStrategicMemoryHorizonReport | None = None,
    contradiction_resolution_report: OracleContradictionResolutionReport | None = None,
    scenario_lab_report: OracleScenarioLabReport | None = None,
    doctrine_adaptation_report_path: Path | None = None,
    research_priority_report_path: Path | None = None,
    repo_root: Path | None = None,
    search_root: Path | None = None,
    now_utc: datetime | None = None,
) -> OracleStrategicInterventionReport:
    issued_at = now_utc or _utc_now()
    fusion = fusion_report or build_oracle_strategic_fusion_report(payload, now_utc=issued_at)
    posterior = posterior_report or build_strategy_health_posterior_report(payload, fusion, now_utc=issued_at)
    thesis = thesis_memory_report or build_oracle_thesis_memory_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        execution_memory_report=research_execution_memory_report,
        now_utc=issued_at,
    )
    scenario_lab = scenario_lab_report or build_oracle_scenario_lab_report(payload, baseline_fusion_report=fusion, now_utc=issued_at)
    cohorts = strategy_cohort_report or build_oracle_strategy_cohort_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        thesis_memory_report=thesis,
        execution_memory_report=research_execution_memory_report,
        now_utc=issued_at,
    )
    doctrine = doctrine_adaptation_report or build_oracle_doctrine_adaptation_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=cohorts,
        execution_memory_report=research_execution_memory_report,
        now_utc=issued_at,
    )
    priorities = research_priority_report or build_oracle_research_priority_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        now_utc=issued_at,
    )
    graph = thesis_graph_report or build_oracle_thesis_graph_report(
        payload,
        fusion_report=fusion,
        thesis_memory_report=thesis,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        research_execution_memory_report=research_execution_memory_report,
        now_utc=issued_at,
    )
    tensions = strategic_tension_report or build_oracle_strategic_tension_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        research_execution_memory_report=research_execution_memory_report,
        thesis_graph_report=graph,
        now_utc=issued_at,
    )
    narrative = strategic_narrative_report or build_oracle_strategic_narrative_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        research_execution_memory_report=research_execution_memory_report,
        thesis_graph_report=graph,
        strategic_tension_report=tensions,
        now_utc=issued_at,
    )
    memory = strategic_memory_horizon_report or build_oracle_strategic_memory_horizon_report(narrative, history_reports=[], now_utc=issued_at)
    contradiction = contradiction_resolution_report or build_oracle_contradiction_resolution_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        research_execution_memory_report=research_execution_memory_report,
        thesis_graph_report=graph,
        strategic_tension_report=tensions,
        strategic_narrative_report=narrative,
        strategic_memory_horizon_report=memory,
        now_utc=issued_at,
    )

    top_priority = priorities.items[0] if priorities.items else None
    top_downside = next((item for item in scenario_lab.scenarios if item.scenario_id == scenario_lab.highest_downside_scenario_id), None)
    top_cascade = graph.nodes[0] if graph.nodes else None
    doctrine_lookup = {item.clause_id: item for item in doctrine.items}
    cohort_lookup = {item.strategy_id: item for item in cohorts.items}
    tension_lookup = {item.tension_id: item for item in tensions.items}
    escalating_outcomes = [
        item for item in (research_execution_memory_report.items if research_execution_memory_report is not None else [])
        if item.outcome_disposition in {"ESCALATED", "REFUTED"}
    ]

    oracle_run_id, input_timestamp_utc, _ = assert_matching_strategic_epoch(fusion, posterior, thesis, cohorts, doctrine, priorities, research_execution_memory_report, graph, tensions, narrative, memory, contradiction, scenario_lab)
    integrity_status = history_integrity_status(memory)
    integrity_penalty_score = intervention_penalty(memory)
    preferred_backing_source = preferred_strategic_backing_source(memory)
    preferred_backing_classification = preferred_strategic_backing_classification(memory)
    sealed_history_count = sealed_history_observation_count(memory)
    unsealed_history_count = unsealed_history_excluded_count(memory)
    resolved_repo_root = (repo_root or Path.cwd()).resolve()
    resolved_search_root = (search_root or (resolved_repo_root / "docs" / "artifacts")).resolve()
    cadence = summarize_exact_cadence_feedback(repo_root=resolved_repo_root, search_root=resolved_search_root, window_size=6)
    exact_cadence_signal_classification = classify_exact_cadence_signal(
        exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
        exact_feedback_relief_count=cadence.exact_feedback_relief_count,
    )
    doctrine_artifact_evidence = discover_preferred_strategic_artifact_evidence(report_path=Path(doctrine_adaptation_report_path), repo_root=resolved_repo_root, search_root=resolved_search_root) if doctrine_adaptation_report_path is not None and Path(doctrine_adaptation_report_path).exists() else None
    research_artifact_evidence = discover_preferred_strategic_artifact_evidence(report_path=Path(research_priority_report_path), repo_root=resolved_repo_root, search_root=resolved_search_root) if research_priority_report_path is not None and Path(research_priority_report_path).exists() else None
    doctrine_exact_support = strategic_artifact_evidence_support_score(doctrine_artifact_evidence)
    research_exact_support = strategic_artifact_evidence_support_score(research_artifact_evidence)
    exact_evidence_support_score = round(max(doctrine_exact_support, research_exact_support), 6)
    items: list[OracleStrategicInterventionItem] = []
    for resolution in contradiction.items[:6]:
        matching_tension = tension_lookup.get(resolution.source_tension_id or "")
        related_cohorts = [cohort_lookup[strategy_id] for strategy_id in resolution.related_strategy_ids if strategy_id in cohort_lookup]
        related_doctrine = [
            item for item in doctrine.items
            if any(source.endswith(item.clause_id.split(':', 1)[-1]) or source == item.clause_id for source in resolution.evidence)
        ]
        if not related_doctrine and doctrine.items:
            related_doctrine = doctrine.items[:1]
        queue_pressure = min(
            1.0,
            0.28 * len(resolution.related_strategy_ids)
            + 0.46 * resolution.resolution_priority_score
            + (0.16 if top_priority is not None and set(top_priority.related_strategy_ids) & set(resolution.related_strategy_ids) else 0.0)
            + (0.10 if matching_tension is not None and matching_tension.alignment_state == "SEVERE_TENSION" else 0.0),
        )
        doctrine_relief = min(
            1.0,
            0.52 * resolution.fragility_reduction_score
            + 0.32 * max((item.stress_score for item in related_doctrine), default=doctrine.items[0].stress_score if doctrine.items else 0.0)
            + (0.10 if doctrine.freeze_recommended else 0.0),
        )
        cohort_relief = min(
            1.0,
            0.50 * resolution.expected_conviction_gain_score
            + 0.30 * max((1.0 - item.resilience_score for item in related_cohorts), default=0.0)
            + (0.10 if any(item.cohort_bucket in {"PRESSURED", "RESEARCH_ONLY"} for item in related_cohorts) else 0.0),
        )
        cascade_relief = min(
            1.0,
            0.62 * resolution.cascade_relief_score + 0.22 * (top_cascade.cascade_risk_score if top_cascade is not None else 0.0)
        )
        kind = _kind_for_resolution(resolution.resolution_kind)
        kind_multiplier = 1.25 if (kind in {"VALIDATE_CONSENSUS", "DOCTRINE_RELIEF"} and integrity_status != "SEALED_HISTORY") else 1.0
        evidence_support = 0.0
        if kind == "DOCTRINE_RELIEF":
            evidence_support = doctrine_exact_support
        elif kind == "VALIDATE_CONSENSUS":
            evidence_support = max(doctrine_exact_support, research_exact_support)
        elif kind in {"RESOLVE_CONTRADICTION", "COHORT_STABILIZATION"}:
            evidence_support = research_exact_support
        effective_penalty = _clamp(integrity_penalty_score * kind_multiplier - 0.10 * evidence_support)
        conviction_gain = min(
            1.0,
            max(
                0.0,
                0.58 * resolution.expected_conviction_gain_score
                + 0.18 * resolution.fragility_reduction_score
                + 0.10 * (0.0 if memory.drift_state in {"STABLE", "STRENGTHENING"} else 0.18)
                + 0.08 * (0.10 if top_downside is not None and top_downside.transition_classification == "STRUCTURAL_BREAK_CANDIDATE" else 0.0)
                + 0.06 * (0.12 if escalating_outcomes else 0.0)
                - effective_penalty,
            ),
        )
        fragility_reduction = min(
            1.0,
            0.64 * resolution.fragility_reduction_score
            + 0.18 * resolution.cascade_relief_score
            + 0.10 * (matching_tension.severity_score if matching_tension is not None else 0.0),
        )
        if kind == "DOCTRINE_RELIEF" and doctrine_exact_support > 0.0:
            doctrine_relief = _clamp(doctrine_relief + 0.12 * doctrine_exact_support)
            conviction_gain = _clamp(conviction_gain + 0.06 * doctrine_exact_support)
        elif kind == "VALIDATE_CONSENSUS" and max(doctrine_exact_support, research_exact_support) > 0.0:
            queue_pressure = _clamp(queue_pressure + 0.06 * max(doctrine_exact_support, research_exact_support))
            conviction_gain = _clamp(conviction_gain + 0.05 * max(doctrine_exact_support, research_exact_support))
        elif kind in {"RESOLVE_CONTRADICTION", "COHORT_STABILIZATION"} and research_exact_support > 0.0:
            conviction_gain = _clamp(conviction_gain + 0.04 * research_exact_support)
            cohort_relief = _clamp(cohort_relief + 0.05 * research_exact_support)
        projected_conviction_score = _clamp(narrative.conviction_score + 0.42 * conviction_gain - 0.12 * max(0.0, narrative.fragility_score - fragility_reduction))
        projected_state = _projected_state(projected_conviction_score)
        items.append(
            OracleStrategicInterventionItem(
                intervention_id=f"intervention:{resolution.resolution_id}",
                intervention_kind=kind,
                source_resolution_id=resolution.resolution_id,
                exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
                exact_feedback_relief_count=cadence.exact_feedback_relief_count,
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                integrity_penalty_score=round(effective_penalty, 6),
                exact_evidence_support_score=round(evidence_support, 6),
                projected_conviction_gain_score=round(conviction_gain, 6),
                projected_fragility_reduction_score=round(fragility_reduction, 6),
                projected_queue_pressure_relief_score=round(_clamp(queue_pressure), 6),
                projected_doctrine_stress_relief_score=round(_clamp(doctrine_relief), 6),
                projected_cohort_resilience_gain_score=round(_clamp(cohort_relief), 6),
                projected_cascade_relief_score=round(_clamp(cascade_relief), 6),
                projected_conviction_state=projected_state,
                title=f"Intervention around {resolution.title.lower()}",
                summary_line=(
                    f"Resolving this chain should move conviction toward {projected_state.lower().replace('_', ' ')} "
                    f"while relieving queue pressure by ~{queue_pressure:.2f} and doctrine stress by ~{doctrine_relief:.2f}."
                ),
                evidence=_unique(
                    resolution.evidence
                    + [
                        f"baseline_conviction={narrative.conviction_state}:{narrative.conviction_score:.2f}",
                        f"baseline_fragility={narrative.fragility_score:.2f}",
                        f"baseline_drift={memory.drift_state}",
                        f"history_integrity={integrity_status}",
                        *( [f"top_downside={top_downside.scenario_id}:{top_downside.transition_classification}"] if top_downside is not None else [] ),
                        *( [f"top_cascade={top_cascade.node_id}:risk={top_cascade.cascade_risk_score:.2f}"] if top_cascade is not None else [] ),
                    ]
                    + (preferred_artifact_evidence_fact("doctrine", doctrine_artifact_evidence) if kind in {"DOCTRINE_RELIEF", "VALIDATE_CONSENSUS"} else [])
                    + (preferred_artifact_evidence_fact("research", research_artifact_evidence) if kind in {"VALIDATE_CONSENSUS", "RESOLVE_CONTRADICTION", "COHORT_STABILIZATION"} else [])
                    + [
                        f"exact_cadence_signal_classification={exact_cadence_signal_classification}",
                        f"exact_feedback_confirmation_count={cadence.exact_feedback_confirmation_count}",
                        f"exact_feedback_relief_count={cadence.exact_feedback_relief_count}",
                    ]
                )[:10],
                related_strategy_ids=resolution.related_strategy_ids[:6],
                recommended_intervention=(
                    (
                        resolution.recommended_resolution
                        if resolution.resolution_kind != "CONSENSUS_VALIDATION"
                        else "Validate the supportive consensus with one downside probe before increasing trust in the map."
                    )
                    + (" Advance with the exact sealed subject already available, but keep broader strategic history sealing in parallel." if evidence_support >= 0.85 and kind in {"VALIDATE_CONSENSUS", "DOCTRINE_RELIEF"} else "")
                    + (" Seal and verify prior strategic stack history before treating this intervention as doctrine-changing or expansion-grade." if effective_penalty > 0.0 and evidence_support < 0.85 and kind in {"VALIDATE_CONSENSUS", "DOCTRINE_RELIEF"} else "")
                    + cadence_recommendation_suffix(
                        exact_cadence_signal_classification=exact_cadence_signal_classification,
                        exact_evidence_support_score=evidence_support,
                    )
                ),
            )
        )

    items = _sort_items(items)
    summary = (
        f"Strategic intervention simulation for {payload.universe_label}: baseline conviction={narrative.conviction_state} ({narrative.conviction_score:.2f}), "
        f"fragility={narrative.fragility_score:.2f}, drift={memory.drift_state.lower().replace('_', ' ')}, "
        f"history_integrity={integrity_status.lower()}, exact_evidence_support={exact_evidence_support_score:.2f}, cadence={exact_cadence_signal_classification}, exact_confirm={cadence.exact_feedback_confirmation_count}, exact_relief={cadence.exact_feedback_relief_count}, top_intervention={items[0].intervention_kind if items else 'none'}."
    )
    operator_actions = _unique(
        [cadence_operator_action(
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
                exact_feedback_relief_count=cadence.exact_feedback_relief_count,
            )]
        + [item.recommended_intervention for item in items]
        + contradiction.operator_actions
        + narrative.operator_actions
        + memory.operator_actions
        + tensions.operator_actions
        + [
            integrity_operator_action(memory),
        ]
    )[:8]
    return OracleStrategicInterventionReport(
        generated_at_utc=issued_at,
        universe_label=payload.universe_label,
        oracle_run_id=oracle_run_id,
        input_timestamp_utc=input_timestamp_utc,
        dominant_regime=fusion.dominant_regime,
        strategic_posture=fusion.strategic_posture,
        exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
        exact_feedback_relief_count=cadence.exact_feedback_relief_count,
        exact_cadence_signal_classification=exact_cadence_signal_classification,
        history_integrity_status=integrity_status,
        sealed_history_observation_count=sealed_history_count,
        unsealed_history_excluded_count=unsealed_history_count,
        preferred_strategic_backing_source=preferred_backing_source,
        preferred_strategic_backing_classification=preferred_backing_classification,
        exact_evidence_support_score=exact_evidence_support_score,
        integrity_penalty_score=round(integrity_penalty_score, 6),
        baseline_conviction_state=narrative.conviction_state,
        baseline_conviction_score=round(narrative.conviction_score, 6),
        baseline_fragility_score=round(narrative.fragility_score, 6),
        baseline_drift_state=memory.drift_state,
        summary_line=summary,
        highest_impact_intervention_id=(items[0].intervention_id if items else None),
        items=items,
        operator_actions=operator_actions,
    )


def render_oracle_strategic_intervention_markdown(report: OracleStrategicInterventionReport) -> str:
    item_blocks = []
    for item in report.items:
        evidence = "\n".join(f"- {entry}" for entry in item.evidence) or "- none"
        strategies = ", ".join(item.related_strategy_ids) if item.related_strategy_ids else "none"
        item_blocks.append(
            "\n".join(
                [
                    f"## {item.title}",
                    "",
                    f"- Intervention kind: {item.intervention_kind}",
                    f"- Projected conviction state: {item.projected_conviction_state}",
                    f"- Conviction gain: {item.projected_conviction_gain_score:.2f}",
                    f"- Fragility reduction: {item.projected_fragility_reduction_score:.2f}",
                    f"- Queue-pressure relief: {item.projected_queue_pressure_relief_score:.2f}",
                    f"- Doctrine-stress relief: {item.projected_doctrine_stress_relief_score:.2f}",
                    f"- Cohort resilience gain: {item.projected_cohort_resilience_gain_score:.2f}",
                    f"- Cascade relief: {item.projected_cascade_relief_score:.2f}",
                    f"- Exact cadence signal: {item.exact_cadence_signal_classification}",
                    f"- Exact feedback confirmation count: {item.exact_feedback_confirmation_count}",
                    f"- Exact feedback relief count: {item.exact_feedback_relief_count}",
                    f"- Exact evidence support: {item.exact_evidence_support_score:.2f}",
                    f"- Related strategies: {strategies}",
                    f"- Summary: {item.summary_line}",
                    f"- Recommended intervention: {item.recommended_intervention}",
                    "",
                    "### Evidence",
                    "",
                    evidence,
                ]
            )
        )
    actions = "\n".join(f"- {item}" for item in report.operator_actions) or "- none"
    body = "\n\n".join(item_blocks) if item_blocks else "No interventions were simulated."
    return f"""# ORACLE STRATEGIC INTERVENTION REPORT

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Universe: {report.universe_label}
- Dominant regime: {report.dominant_regime}
- Strategic posture: {report.strategic_posture}
- Baseline conviction: {report.baseline_conviction_state} ({report.baseline_conviction_score:.2f})
- Baseline fragility: {report.baseline_fragility_score:.2f}
- Baseline drift: {report.baseline_drift_state}
- Highest-impact intervention: {report.highest_impact_intervention_id or 'none'}
- Preferred strategic backing source: {report.preferred_strategic_backing_source or 'none'}
- Preferred strategic backing classification: {report.preferred_strategic_backing_classification or 'none'}
- Exact cadence signal: {report.exact_cadence_signal_classification}
- Exact feedback confirmation count: {report.exact_feedback_confirmation_count}
- Exact feedback relief count: {report.exact_feedback_relief_count}
- Exact evidence support: {report.exact_evidence_support_score:.2f}
- Summary: {report.summary_line}

## Operator actions

{actions}

{body}
"""


def load_strategic_intervention_report(path: Path) -> OracleStrategicInterventionReport:
    return OracleStrategicInterventionReport.model_validate(json.loads(path.read_text(encoding="utf-8")))
