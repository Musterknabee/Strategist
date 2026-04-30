from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from strategy_validator.contracts.oracle_core import OracleAdvisoryInput
from strategy_validator.contracts.oracle_strategic_memory import (
    OracleContradictionResolutionReport,
    OracleDoctrineAdaptationReport,
    OracleResearchExecutionMemoryReport,
    OracleResearchPriorityReport,
    OracleStrategicInterventionReport,
    OracleStrategicMemoryHorizonReport,
    OracleStrategicNarrativeReport,
    OracleStrategicTensionReport,
    OracleThesisGraphReport,
    OracleThesisMemoryReport,
)
from strategy_validator.contracts.oracle_strategic_fusion import (
    OracleOpportunityQueueReport,
    OracleStrategicFusionReport,
    StrategyHealthPosteriorReport,
)
from strategy_validator.contracts.oracle_strategic_programs import (
    OracleScenarioLabReport,
    OracleStrategicCampaignItem,
    OracleStrategicCampaignReport,
    OracleStrategicCampaignStep,
    OracleStrategyCohortReport,
)
from strategy_validator.validator.oracle_contradiction_resolution import build_oracle_contradiction_resolution_report
from strategy_validator.validator.oracle_doctrine_adaptation import build_oracle_doctrine_adaptation_report
from strategy_validator.validator.oracle_intervention_simulator import build_oracle_strategic_intervention_report
from strategy_validator.validator.oracle_opportunity_queue import build_oracle_opportunity_queue_report
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
from strategy_validator.validator.oracle_run_identity import assert_matching_strategic_epoch
from strategy_validator.validator.strategy_health_posterior import build_strategy_health_posterior_report
from strategy_validator.validator.oracle_history_integrity import (
    history_integrity_status,
    sealed_history_observation_count,
    unsealed_history_excluded_count,
    campaign_penalty,
    campaign_operator_friction,
    integrity_operator_action,
    preferred_strategic_backing_source,
    preferred_strategic_backing_classification,
)
from strategy_validator.validator.oracle_strategic_artifact_evidence import discover_preferred_strategic_artifact_evidence, strategic_artifact_evidence_support_score, preferred_artifact_evidence_fact
from strategy_validator.validator.oracle_cadence_feedback import summarize_exact_cadence_feedback, classify_exact_cadence_signal, cadence_operator_action, cadence_recommendation_suffix


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _unique(items: list[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if normalized and normalized not in output:
            output.append(normalized)
    return output


def _sort_items(items: list[OracleStrategicCampaignItem]) -> list[OracleStrategicCampaignItem]:
    return sorted(
        items,
        key=lambda item: (
            -item.priority_score,
            -item.expected_conviction_gain_score,
            -item.expected_fragility_reduction_score,
            item.objective_kind,
            item.title,
        ),
    )


def _step(step_id: str, kind: str, title: str, summary: str, *, targets: list[str] | None = None, depends_on: list[str] | None = None) -> OracleStrategicCampaignStep:
    return OracleStrategicCampaignStep(
        step_id=step_id,
        step_kind=kind,
        title=title,
        summary_line=summary,
        target_ids=_unique(targets or []),
        depends_on_step_ids=_unique(depends_on or []),
    )


def build_oracle_strategic_campaign_report(
    payload: OracleAdvisoryInput,
    *,
    fusion_report: OracleStrategicFusionReport | None = None,
    posterior_report: StrategyHealthPosteriorReport | None = None,
    queue_report: OracleOpportunityQueueReport | None = None,
    thesis_memory_report: OracleThesisMemoryReport | None = None,
    scenario_lab_report: OracleScenarioLabReport | None = None,
    strategy_cohort_report: OracleStrategyCohortReport | None = None,
    doctrine_adaptation_report: OracleDoctrineAdaptationReport | None = None,
    research_priority_report: OracleResearchPriorityReport | None = None,
    research_execution_memory_report: OracleResearchExecutionMemoryReport | None = None,
    thesis_graph_report: OracleThesisGraphReport | None = None,
    strategic_tension_report: OracleStrategicTensionReport | None = None,
    strategic_narrative_report: OracleStrategicNarrativeReport | None = None,
    strategic_memory_horizon_report: OracleStrategicMemoryHorizonReport | None = None,
    contradiction_resolution_report: OracleContradictionResolutionReport | None = None,
    intervention_report: OracleStrategicInterventionReport | None = None,
    repo_root: Path | None = None,
    search_root: Path | None = None,
    doctrine_adaptation_report_path: Path | None = None,
    research_priority_report_path: Path | None = None,
    intervention_report_path: Path | None = None,
    now_utc: datetime | None = None,
) -> OracleStrategicCampaignReport:
    issued_at = now_utc or _utc_now()
    fusion = fusion_report or build_oracle_strategic_fusion_report(payload, now_utc=issued_at)
    posterior = posterior_report or build_strategy_health_posterior_report(payload, fusion, now_utc=issued_at)
    queue = queue_report or build_oracle_opportunity_queue_report(payload, fusion_report=fusion, posterior_report=posterior, now_utc=issued_at)
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
        queue_report=queue,
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
        queue_report=queue,
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
        queue_report=queue,
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
        queue_report=queue,
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
    intervention = intervention_report or build_oracle_strategic_intervention_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        thesis_memory_report=thesis,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        research_execution_memory_report=research_execution_memory_report,
        thesis_graph_report=graph,
        strategic_tension_report=tensions,
        strategic_narrative_report=narrative,
        strategic_memory_horizon_report=memory,
        contradiction_resolution_report=contradiction,
        scenario_lab_report=scenario_lab,
        now_utc=issued_at,
    )

    top_priority = priorities.items[0] if priorities.items else None
    top_doctrine = doctrine.items[0] if doctrine.items else None
    pressured_cohort = next((item for item in cohorts.items if item.cohort_bucket in {"PRESSURED", "RESEARCH_ONLY"}), cohorts.items[0] if cohorts.items else None)
    top_opportunity = next((item for item in queue.items if item.queue_kind == "OPPORTUNITY"), None)
    top_queue_risk = next((item for item in queue.items if item.queue_kind != "OPPORTUNITY"), queue.items[0] if queue.items else None)
    top_intervention = intervention.items[0] if intervention.items else None
    top_resolution = contradiction.items[0] if contradiction.items else None
    strongest_tension = next((item for item in tensions.items if item.alignment_state != "CONSENSUS"), tensions.items[0] if tensions.items else None)
    downside = next((item for item in scenario_lab.scenarios if item.scenario_id == scenario_lab.highest_downside_scenario_id), None)
    escalation_count = len([item for item in (research_execution_memory_report.items if research_execution_memory_report else []) if item.outcome_disposition in {"ESCALATED", "REFUTED"}])

    oracle_run_id, input_timestamp_utc, _ = assert_matching_strategic_epoch(fusion, posterior, queue, thesis, scenario_lab, cohorts, doctrine, priorities, research_execution_memory_report, graph, tensions, narrative, memory, contradiction, intervention)
    integrity_status = history_integrity_status(memory)
    resolved_repo_root = (repo_root or Path.cwd()).resolve()
    resolved_search_root = (search_root or resolved_repo_root / "docs" / "artifacts").resolve()
    doctrine_artifact_evidence = discover_preferred_strategic_artifact_evidence(report_path=Path(doctrine_adaptation_report_path), repo_root=resolved_repo_root, search_root=resolved_search_root) if doctrine_adaptation_report_path is not None and Path(doctrine_adaptation_report_path).exists() else None
    research_artifact_evidence = discover_preferred_strategic_artifact_evidence(report_path=Path(research_priority_report_path), repo_root=resolved_repo_root, search_root=resolved_search_root) if research_priority_report_path is not None and Path(research_priority_report_path).exists() else None
    intervention_artifact_evidence = discover_preferred_strategic_artifact_evidence(report_path=Path(intervention_report_path), repo_root=resolved_repo_root, search_root=resolved_search_root) if intervention_report_path is not None and Path(intervention_report_path).exists() else None
    doctrine_exact_support = strategic_artifact_evidence_support_score(doctrine_artifact_evidence)
    research_exact_support = strategic_artifact_evidence_support_score(research_artifact_evidence)
    intervention_exact_support = strategic_artifact_evidence_support_score(intervention_artifact_evidence)
    execution_exact_support = round(float(getattr(research_execution_memory_report, "exact_evidence_support_score", 0.0) or 0.0), 6)
    exact_evidence_support_score = round(max(doctrine_exact_support, research_exact_support, intervention_exact_support, execution_exact_support), 6)
    integrity_penalty_score = campaign_penalty(memory)
    integrity_friction_score = campaign_operator_friction(memory)
    preferred_backing_source = preferred_strategic_backing_source(memory)
    preferred_backing_classification = preferred_strategic_backing_classification(memory)
    cadence = summarize_exact_cadence_feedback(repo_root=resolved_repo_root, search_root=resolved_search_root, window_size=6)
    exact_cadence_signal_classification = classify_exact_cadence_signal(
        exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
        exact_feedback_relief_count=cadence.exact_feedback_relief_count,
    )
    sealed_history_count = sealed_history_observation_count(memory)
    unsealed_history_count = unsealed_history_excluded_count(memory)
    items: list[OracleStrategicCampaignItem] = []

    objective_exact_support = {
        "CONVICTION_REPAIR": round(max(intervention_exact_support, research_exact_support, execution_exact_support), 6),
        "DOCTRINE_STABILIZATION": round(max(doctrine_exact_support, research_exact_support, execution_exact_support), 6),
        "COHORT_RECOVERY": round(max(intervention_exact_support, research_exact_support, execution_exact_support), 6),
        "THESIS_VALIDATION": round(max(research_exact_support, execution_exact_support), 6),
        "OPPORTUNITY_EXPANSION": round(max(research_exact_support, intervention_exact_support, execution_exact_support), 6),
    }

    def add_campaign(
        campaign_id: str,
        objective_kind: str,
        title: str,
        summary_line: str,
        evidence: list[str],
        related_strategy_ids: list[str],
        source_intervention_ids: list[str],
        source_priority_ids: list[str],
        steps: list[OracleStrategicCampaignStep],
        recommended_campaign: str,
        *,
        conviction_gain: float,
        fragility_reduction: float,
        queue_relief: float,
        doctrine_relief: float,
        cohort_gain: float,
    ) -> None:
        exact_support = objective_exact_support.get(objective_kind, exact_evidence_support_score)
        local_penalty = _clamp(max(0.0, integrity_penalty_score - (0.12 * exact_support if objective_kind in {"DOCTRINE_STABILIZATION", "THESIS_VALIDATION", "OPPORTUNITY_EXPANSION", "CONVICTION_REPAIR"} else 0.06 * exact_support)))
        local_friction = _clamp(max(0.0, integrity_friction_score - (0.10 * exact_support if objective_kind in {"DOCTRINE_STABILIZATION", "THESIS_VALIDATION", "OPPORTUNITY_EXPANSION", "CONVICTION_REPAIR"} else 0.05 * exact_support)))
        if objective_kind in {"DOCTRINE_STABILIZATION", "OPPORTUNITY_EXPANSION"} and integrity_status != "SEALED_HISTORY" and exact_support < 0.85:
            local_penalty = _clamp(local_penalty + 0.06)
            local_friction = _clamp(local_friction + 0.08)
        elif objective_kind == "THESIS_VALIDATION" and integrity_status == "CURRENT_ONLY" and exact_support < 0.85:
            local_penalty = _clamp(local_penalty + 0.03)
        priority_score = _clamp(
            0.30 * conviction_gain
            + 0.22 * fragility_reduction
            + 0.18 * queue_relief
            + 0.16 * doctrine_relief
            + 0.14 * cohort_gain
            - local_penalty
        )
        items.append(
            OracleStrategicCampaignItem(
                campaign_id=campaign_id,
                objective_kind=objective_kind,
                exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
                exact_feedback_relief_count=cadence.exact_feedback_relief_count,
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                exact_evidence_support_score=round(exact_support, 6),
                integrity_penalty_score=round(local_penalty, 6),
                operator_friction_score=round(local_friction, 6),
                priority_score=round(priority_score, 6),
                expected_conviction_gain_score=round(_clamp(conviction_gain), 6),
                expected_fragility_reduction_score=round(_clamp(fragility_reduction), 6),
                expected_queue_pressure_relief_score=round(_clamp(queue_relief), 6),
                expected_doctrine_relief_score=round(_clamp(doctrine_relief), 6),
                expected_cohort_resilience_gain_score=round(_clamp(cohort_gain), 6),
                title=title,
                summary_line=summary_line,
                evidence=_unique(
                    evidence
                    + preferred_artifact_evidence_fact("doctrine", doctrine_artifact_evidence)
                    + preferred_artifact_evidence_fact("research", research_artifact_evidence)
                    + preferred_artifact_evidence_fact("intervention", intervention_artifact_evidence)
                    + ([f"execution_memory_exact_evidence_support={execution_exact_support:.2f}"] if research_execution_memory_report is not None else [])
                )[:10],
                related_strategy_ids=_unique(related_strategy_ids)[:8],
                source_intervention_ids=_unique(source_intervention_ids)[:6],
                source_priority_ids=_unique(source_priority_ids)[:6],
                steps=steps,
                recommended_campaign=(
                    recommended_campaign
                    + cadence_recommendation_suffix(
                        exact_cadence_signal_classification=exact_cadence_signal_classification,
                        exact_evidence_support_score=exact_support,
                    )
                ),
            )
        )

    if top_intervention is not None or top_resolution is not None:
        step_ids = []
        steps: list[OracleStrategicCampaignStep] = []
        if top_intervention is not None:
            step_ids.append("campaign:repair:intervention")
            steps.append(_step(
                "campaign:repair:intervention",
                "INTERVENTION",
                top_intervention.title,
                top_intervention.recommended_intervention,
                targets=top_intervention.related_strategy_ids,
            ))
        if top_priority is not None:
            step_ids.append("campaign:repair:investigation")
            steps.append(_step(
                "campaign:repair:investigation",
                "INVESTIGATION",
                top_priority.title,
                top_priority.recommended_investigation,
                targets=top_priority.related_strategy_ids,
                depends_on=step_ids[:1],
            ))
        if strongest_tension is not None:
            steps.append(_step(
                "campaign:repair:validation",
                "VALIDATION",
                f"Validate tension {strongest_tension.tension_id}",
                strongest_tension.resolution_guidance,
                targets=strongest_tension.related_strategy_ids,
                depends_on=step_ids,
            ))
        add_campaign(
            "campaign:conviction-repair",
            "CONVICTION_REPAIR",
            "Conviction repair campaign",
            "Bundle the top contradiction intervention with the matching investigation path so conviction quality improves through one coordinated repair cycle instead of isolated single-step moves.",
            [
                f"baseline_conviction={intervention.baseline_conviction_state}:{intervention.baseline_conviction_score:.2f}",
                f"baseline_fragility={intervention.baseline_fragility_score:.2f}",
                f"top_intervention={top_intervention.intervention_id if top_intervention is not None else 'none'}",
                f"top_resolution={top_resolution.resolution_id if top_resolution is not None else 'none'}",
                f"tension={strongest_tension.tension_id if strongest_tension is not None else 'none'}",
            ],
            (top_intervention.related_strategy_ids if top_intervention is not None else top_resolution.related_strategy_ids if top_resolution is not None else []),
            ([top_intervention.intervention_id] if top_intervention is not None else []),
            ([top_priority.priority_id] if top_priority is not None else []),
            steps,
            "Run the top intervention, immediately follow with the matching investigation, then validate whether conviction and fragility actually improve before expanding posture." + (" Advance on the strength of the exact sealed supporting subjects, but keep unrelated expansion constrained until more history is sealed." if exact_evidence_support_score >= 0.85 else (" Keep expansion constrained until sealed strategic history is available." if integrity_status != "SEALED_HISTORY" else "")),
            conviction_gain=(top_intervention.projected_conviction_gain_score if top_intervention is not None else top_resolution.expected_conviction_gain_score if top_resolution is not None else 0.34),
            fragility_reduction=(top_intervention.projected_fragility_reduction_score if top_intervention is not None else top_resolution.fragility_reduction_score if top_resolution is not None else 0.28),
            queue_relief=(top_intervention.projected_queue_pressure_relief_score if top_intervention is not None else 0.24),
            doctrine_relief=(top_intervention.projected_doctrine_stress_relief_score if top_intervention is not None else 0.18),
            cohort_gain=(top_intervention.projected_cohort_resilience_gain_score if top_intervention is not None else 0.16),
        )

    if doctrine.freeze_recommended or top_doctrine is not None:
        steps = []
        if top_doctrine is not None:
            steps.append(_step(
                "campaign:doctrine:review",
                "DOCTRINE_ACTION",
                f"Review doctrine clause {top_doctrine.clause_id}",
                top_doctrine.recommended_adaptation,
                targets=[top_doctrine.clause_id],
            ))
        if top_priority is not None:
            steps.append(_step(
                "campaign:doctrine:probe",
                "INVESTIGATION",
                top_priority.title,
                top_priority.recommended_investigation,
                targets=top_priority.related_strategy_ids + ([top_doctrine.clause_id] if top_doctrine is not None else []),
                depends_on=["campaign:doctrine:review"] if top_doctrine is not None else [],
            ))
        if downside is not None:
            steps.append(_step(
                "campaign:doctrine:hedge",
                "SCENARIO_HEDGE",
                f"Stress-test doctrine under {downside.scenario_id}",
                f"Probe whether doctrine remains coherent if {downside.title.lower()} persists.",
                depends_on=[step.step_id for step in steps[:2]],
            ))
        add_campaign(
            "campaign:doctrine-stabilization",
            "DOCTRINE_STABILIZATION",
            "Doctrine stabilization campaign",
            "Convert doctrine stress into a multi-step clause review, targeted investigation, and scenario hedge so doctrine adaptation becomes coordinated rather than reactive.",
            [
                f"freeze_recommended={'yes' if doctrine.freeze_recommended else 'no'}",
                f"top_clause={top_doctrine.clause_id if top_doctrine is not None else 'none'}",
                f"clause_stress={top_doctrine.stress_score if top_doctrine is not None else 0.0:.2f}",
                f"scenario_downside={scenario_lab.highest_downside_scenario_id or 'none'}",
            ],
            [sid for sid in (top_priority.related_strategy_ids if top_priority is not None else [])],
            [],
            ([top_priority.priority_id] if top_priority is not None else []),
            steps,
            "Review the highest-stress doctrine clause first, pair it with a targeted investigation, and validate the clause under downside scenarios before relaxing freeze pressure." + (" Exact sealed doctrine/research subjects allow this stabilization campaign to advance, but still avoid portfolio-widening permission beyond the sealed scope." if objective_exact_support.get("DOCTRINE_STABILIZATION", 0.0) >= 0.85 else (" Do not treat doctrine relief as portfolio-widening permission until prior strategic history is sealed." if integrity_status != "SEALED_HISTORY" else "")),
            conviction_gain=0.18 + 0.18 * float(doctrine.freeze_recommended) + 0.24 * (top_doctrine.review_priority_score if top_doctrine is not None else 0.25),
            fragility_reduction=0.20 + 0.24 * (top_doctrine.stress_score if top_doctrine is not None else 0.25),
            queue_relief=0.14 + 0.16 * (top_queue_risk.priority_score if top_queue_risk is not None else 0.2),
            doctrine_relief=0.30 + 0.42 * (top_doctrine.stress_score if top_doctrine is not None else 0.25),
            cohort_gain=0.10 + 0.12 * (pressured_cohort.resilience_score if pressured_cohort is not None else 0.2),
        )

    if pressured_cohort is not None:
        steps = [
            _step(
                "campaign:cohort:stabilize",
                "INTERVENTION",
                f"Stabilize cohort around {pressured_cohort.strategy_id}",
                pressured_cohort.operator_action,
                targets=[pressured_cohort.strategy_id],
            )
        ]
        if top_priority is not None:
            steps.append(_step(
                "campaign:cohort:validate",
                "INVESTIGATION",
                top_priority.title,
                top_priority.recommended_investigation,
                targets=_unique(top_priority.related_strategy_ids + [pressured_cohort.strategy_id]),
                depends_on=["campaign:cohort:stabilize"],
            ))
        add_campaign(
            "campaign:cohort-recovery",
            "COHORT_RECOVERY",
            "Cohort recovery campaign",
            "Stabilize the most pressured cohort, then validate whether recovery is real before promoting it back into lead posture.",
            [
                f"pressure_strategy={pressured_cohort.strategy_id}",
                f"bucket={pressured_cohort.cohort_bucket}",
                f"resilience={pressured_cohort.resilience_score:.2f}",
                f"scenario_floor={pressured_cohort.scenario_downside_floor:.2f}",
            ],
            [pressured_cohort.strategy_id],
            ([top_intervention.intervention_id] if top_intervention is not None else []),
            ([top_priority.priority_id] if top_priority is not None else []),
            steps,
            "Treat the most pressured cohort as a campaign target: stabilize first, validate second, and only then consider returning it to lead focus.",
            conviction_gain=0.16 + 0.16 * (1.0 - pressured_cohort.resilience_score),
            fragility_reduction=0.14 + 0.24 * pressured_cohort.transition_sensitivity_score,
            queue_relief=0.18 + 0.24 * pressured_cohort.queue_pressure_score,
            doctrine_relief=0.08 + 0.12 * pressured_cohort.thesis_pressure_score,
            cohort_gain=0.32 + 0.38 * (1.0 - pressured_cohort.resilience_score),
        )

    if top_priority is not None:
        related_theses = [item.thesis_id for item in thesis.items if item.evolution_state in {"REVERSING", "WEAKENING"}][:3]
        steps = [
            _step(
                "campaign:thesis:investigate",
                "INVESTIGATION",
                top_priority.title,
                top_priority.recommended_investigation,
                targets=_unique(top_priority.related_strategy_ids + related_theses),
            )
        ]
        if strongest_tension is not None:
            steps.append(_step(
                "campaign:thesis:validate",
                "VALIDATION",
                f"Resolve supporting contradiction {strongest_tension.tension_id}",
                strongest_tension.resolution_guidance,
                targets=strongest_tension.related_strategy_ids,
                depends_on=["campaign:thesis:investigate"],
            ))
        add_campaign(
            "campaign:thesis-validation",
            "THESIS_VALIDATION",
            "Thesis validation campaign",
            "Use the highest-urgency investigation as the anchor for validating weakening theses, then resolve the attached contradiction chain before updating confidence.",
            [
                f"top_priority={top_priority.priority_id}",
                f"urgency={top_priority.urgency_score:.2f}",
                f"weakening_theses={len(thesis.weakening_thesis_ids)}",
                f"escalated_outcomes={escalation_count}",
            ],
            top_priority.related_strategy_ids,
            ([top_intervention.intervention_id] if top_intervention is not None else []),
            [top_priority.priority_id],
            steps,
            "Run the investigation that most directly tests the weakening thesis set, then use the resulting evidence to update confidence rather than carrying unresolved drift forward." + (" Exact sealed research evidence permits advancing this thesis-validation cycle while broader doctrine or expansion changes remain constrained." if objective_exact_support.get("THESIS_VALIDATION", 0.0) >= 0.85 else (" Seal prior strategic history before using this thesis validation to justify broader doctrine or expansion changes." if integrity_status == "CURRENT_ONLY" else "")),
            conviction_gain=0.18 + 0.28 * top_priority.urgency_score,
            fragility_reduction=0.10 + 0.18 * max(0.0, narrative.fragility_score - 0.25),
            queue_relief=0.12 + 0.10 * (top_queue_risk.priority_score if top_queue_risk is not None else 0.2),
            doctrine_relief=0.08 + 0.10 * (top_doctrine.review_priority_score if top_doctrine is not None else 0.2),
            cohort_gain=0.08 + 0.12 * (1.0 - pressured_cohort.resilience_score) if pressured_cohort is not None else 0.08,
        )

    if top_opportunity is not None and narrative.conviction_state in {"HIGH_CONVICTION", "GUARDED_CONVICTION"}:
        steps = [
            _step(
                "campaign:opportunity:validate",
                "VALIDATION",
                top_opportunity.title,
                top_opportunity.operator_action,
                targets=([top_opportunity.strategy_id] if top_opportunity.strategy_id else []),
            )
        ]
        if scenario_lab.highest_upside_scenario_id:
            steps.append(_step(
                "campaign:opportunity:hedge",
                "SCENARIO_HEDGE",
                f"Stress upside against {scenario_lab.highest_upside_scenario_id}",
                "Validate the upside path while making sure downside fragility remains contained.",
                depends_on=["campaign:opportunity:validate"],
            ))
        add_campaign(
            "campaign:opportunity-expansion",
            "OPPORTUNITY_EXPANSION",
            "Opportunity expansion campaign",
            "Treat the best opportunity as a campaign: validate its edge, then hedge it through the scenario lens before expanding attention or capital allocation research.",
            [
                f"opportunity_id={top_opportunity.queue_id}",
                f"opportunity_score={top_opportunity.priority_score:.2f}",
                f"conviction_state={narrative.conviction_state}",
                f"consensus_strength={tensions.consensus_strength_score:.2f}",
            ],
            ([top_opportunity.strategy_id] if top_opportunity.strategy_id else []),
            [],
            [],
            steps,
            "Only expand around the top opportunity after validating the queue item and testing that upside does not hide unresolved downside fragility." + (" Exact sealed supporting subjects permit this expansion campaign to proceed within the sealed scope." if objective_exact_support.get("OPPORTUNITY_EXPANSION", 0.0) >= 0.85 else (" Verified sealed history is required before treating this as an expansion-grade campaign." if integrity_status != "SEALED_HISTORY" else "")),
            conviction_gain=0.12 + 0.20 * top_opportunity.priority_score,
            fragility_reduction=0.06 + 0.08 * max(0.0, 1.0 - narrative.fragility_score),
            queue_relief=0.08 + 0.10 * top_opportunity.priority_score,
            doctrine_relief=0.06 + 0.04 * tensions.consensus_strength_score,
            cohort_gain=0.10 + 0.14 * (cohorts.items[0].resilience_score if cohorts.items else 0.4),
        )

    sorted_items = _sort_items(items)
    highest = sorted_items[0] if sorted_items else None
    operator_actions = _unique((
        [cadence_operator_action(
            exact_cadence_signal_classification=exact_cadence_signal_classification,
            exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
            exact_feedback_relief_count=cadence.exact_feedback_relief_count,
        )]
        + intervention.operator_actions
        + contradiction.operator_actions
        + priorities.operator_actions
        + doctrine.operator_actions
        + queue.operator_actions
        + [
            "bundle the top intervention, investigation, and doctrine action into one campaign before expanding posture",
            "prefer campaigns with explicit downstream payoff rather than disconnected single-step actions",
            integrity_operator_action(memory),
        ]
    ))[:8]
    return OracleStrategicCampaignReport(
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
        exact_evidence_support_score=round(exact_evidence_support_score, 6),
        integrity_penalty_score=round(min((item.integrity_penalty_score for item in sorted_items), default=integrity_penalty_score), 6),
        integrity_operator_friction_score=round(integrity_friction_score, 6),
        baseline_conviction_state=narrative.conviction_state,
        baseline_conviction_score=round(narrative.conviction_score, 6),
        baseline_fragility_score=round(narrative.fragility_score, 6),
        summary_line=(
            f"Strategic campaigns for {payload.universe_label}: baseline_conviction={narrative.conviction_state}:{narrative.conviction_score:.2f}, "
            f"history_integrity={integrity_status.lower()}, exact_evidence_support={exact_evidence_support_score:.2f}, cadence={exact_cadence_signal_classification}, exact_confirm={cadence.exact_feedback_confirmation_count}, exact_relief={cadence.exact_feedback_relief_count}, top_campaign={highest.campaign_id if highest is not None else 'none'}, top_intervention={intervention.highest_impact_intervention_id or 'none'}, "
            f"top_priority={priorities.highest_priority_id or 'none'}, freeze={'yes' if doctrine.freeze_recommended else 'no'}, "
            f"top_tension={tensions.highest_severity_tension_id or 'none'}."
        ),
        highest_priority_campaign_id=(highest.campaign_id if highest is not None else None),
        items=sorted_items,
        operator_actions=operator_actions,
    )


from strategy_validator.validator.oracle_campaign_planner_io import load_strategic_campaign_report
from strategy_validator.validator.oracle_campaign_planner_rendering import render_oracle_strategic_campaign_markdown
