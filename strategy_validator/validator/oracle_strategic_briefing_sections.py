from __future__ import annotations

from datetime import datetime
from pathlib import Path

from strategy_validator.contracts.oracle_core import OracleAdvisoryInput
from strategy_validator.contracts.oracle_strategic_memory import (
    OracleDoctrineAdaptationReport,
    OracleResearchExecutionMemoryReport,
    OracleResearchPriorityReport,
    OracleStrategicMemoryHorizonReport,
    OracleStrategicNarrativeReport,
    OracleContradictionResolutionReport,
    OracleStrategicInterventionReport,
    OracleStrategicTensionReport,
    OracleThesisGraphReport,
    OracleThesisMemoryReport,
)
from strategy_validator.contracts.oracle_strategic_fusion import (
    OracleOpportunityQueueReport,
    OracleRegimeTransitionSignalReport,
    OracleStrategicFusionReport,
    StrategyHealthPosteriorReport,
)
from strategy_validator.contracts.oracle_strategic_programs import (
    OracleScenarioLabReport,
    OracleStrategicBriefingReport,
    OracleStrategicBriefingSection,
    OracleStrategicCampaignReport,
    OracleStrategicCampaignExecutionReport,
    OracleStrategyCohortReport,
)
from strategy_validator.validator.oracle_opportunity_queue import build_oracle_opportunity_queue_report
from strategy_validator.validator.oracle_regime_transition import compare_strategic_fusion_reports
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report
from strategy_validator.validator.oracle_scenario_lab import build_oracle_scenario_lab_report
from strategy_validator.validator.oracle_strategy_cohort import build_oracle_strategy_cohort_report
from strategy_validator.validator.oracle_doctrine_adaptation import build_oracle_doctrine_adaptation_report
from strategy_validator.validator.oracle_research_planner import build_oracle_research_priority_report
from strategy_validator.validator.oracle_research_execution_memory import load_research_execution_memory_report
from strategy_validator.validator.oracle_thesis_graph import build_oracle_thesis_graph_report
from strategy_validator.validator.oracle_strategic_narrative import build_oracle_strategic_narrative_report
from strategy_validator.validator.oracle_strategic_memory_horizon import build_oracle_strategic_memory_horizon_report
from strategy_validator.validator.oracle_strategic_tension import build_oracle_strategic_tension_report
from strategy_validator.validator.oracle_contradiction_resolution import build_oracle_contradiction_resolution_report
from strategy_validator.validator.oracle_intervention_simulator import build_oracle_strategic_intervention_report
from strategy_validator.validator.oracle_campaign_planner import build_oracle_strategic_campaign_report
from strategy_validator.validator.oracle_campaign_execution import build_oracle_strategic_campaign_execution_report
from strategy_validator.validator.oracle_thesis_memory import build_oracle_thesis_memory_report, load_thesis_memory_report
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.oracle_history_integrity import preferred_strategic_backing_source, preferred_strategic_backing_classification, strategic_backing_facts
from strategy_validator.validator.oracle_cadence_feedback import summarize_exact_cadence_feedback, classify_exact_cadence_signal
from strategy_validator.validator.strategy_health_posterior import build_strategy_health_posterior_report
from strategy_validator.validator.oracle_run_identity import assert_matching_strategic_epoch
from strategy_validator.validator.oracle_strategic_artifact_evidence import discover_preferred_strategic_artifact_evidence


def _unique(items: list[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if normalized and normalized not in output:
            output.append(normalized)
    return output


def build_oracle_strategic_briefing(
    payload: OracleAdvisoryInput,
    previous_fusion_report: OracleStrategicFusionReport | None = None,
    now_utc: datetime | None = None,
    fusion_report: OracleStrategicFusionReport | None = None,
    posterior_report: StrategyHealthPosteriorReport | None = None,
    transition_report: OracleRegimeTransitionSignalReport | None = None,
    queue_report: OracleOpportunityQueueReport | None = None,
    thesis_memory_report: OracleThesisMemoryReport | None = None,
    previous_thesis_memory_report: OracleThesisMemoryReport | None = None,
    scenario_lab_report: OracleScenarioLabReport | None = None,
    strategy_cohort_report: OracleStrategyCohortReport | None = None,
    doctrine_adaptation_report: OracleDoctrineAdaptationReport | None = None,
    doctrine_adaptation_report_path: Path | None = None,
    research_priority_report: OracleResearchPriorityReport | None = None,
    research_priority_report_path: Path | None = None,
    research_execution_memory_report: OracleResearchExecutionMemoryReport | None = None,
    thesis_graph_report: OracleThesisGraphReport | None = None,
    strategic_tension_report: OracleStrategicTensionReport | None = None,
    strategic_narrative_report: OracleStrategicNarrativeReport | None = None,
    strategic_memory_horizon_report: OracleStrategicMemoryHorizonReport | None = None,
    contradiction_resolution_report: OracleContradictionResolutionReport | None = None,
    intervention_simulation_report: OracleStrategicInterventionReport | None = None,
    intervention_simulation_report_path: Path | None = None,
    strategic_campaign_report: OracleStrategicCampaignReport | None = None,
    strategic_campaign_report_path: Path | None = None,
    campaign_execution_report: OracleStrategicCampaignExecutionReport | None = None,
    campaign_execution_report_path: Path | None = None,
    repo_root: Path | None = None,
    search_root: Path | None = None,
) -> OracleStrategicBriefingReport:
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
        strategic_memory_horizon_report=strategic_memory_horizon_report,
        now_utc=issued_at,
    )
    thesis = thesis_memory_report or build_oracle_thesis_memory_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        previous_report=previous_thesis_memory_report,
        now_utc=issued_at,
    )
    scenario_lab = scenario_lab_report or build_oracle_scenario_lab_report(
        payload,
        baseline_fusion_report=fusion,
        now_utc=issued_at,
    )
    strategy_cohorts = strategy_cohort_report or build_oracle_strategy_cohort_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        queue_report=queue,
        thesis_memory_report=thesis,
        now_utc=issued_at,
    )

    doctrine_adaptation = doctrine_adaptation_report or build_oracle_doctrine_adaptation_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        previous_fusion_report=previous_fusion_report,
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=strategy_cohorts,
        now_utc=issued_at,
    )
    research_priorities = research_priority_report or build_oracle_research_priority_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        previous_fusion_report=previous_fusion_report,
        queue_report=queue,
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=strategy_cohorts,
        doctrine_adaptation_report=doctrine_adaptation,
        strategic_memory_horizon_report=strategic_memory_horizon_report,
        now_utc=issued_at,
    )

    thesis_graph = thesis_graph_report or build_oracle_thesis_graph_report(
        payload,
        fusion_report=fusion,
        thesis_memory_report=thesis,
        strategy_cohort_report=strategy_cohorts,
        doctrine_adaptation_report=doctrine_adaptation,
        research_priority_report=research_priorities,
        research_execution_memory_report=research_execution_memory_report,
        now_utc=issued_at,
    )
    strategic_tensions = strategic_tension_report or build_oracle_strategic_tension_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        queue_report=queue,
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=strategy_cohorts,
        doctrine_adaptation_report=doctrine_adaptation,
        research_priority_report=research_priorities,
        research_execution_memory_report=research_execution_memory_report,
        thesis_graph_report=thesis_graph,
        now_utc=issued_at,
    )
    strategic_narrative = strategic_narrative_report or build_oracle_strategic_narrative_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        queue_report=queue,
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=strategy_cohorts,
        doctrine_adaptation_report=doctrine_adaptation,
        research_priority_report=research_priorities,
        research_execution_memory_report=research_execution_memory_report,
        thesis_graph_report=thesis_graph,
        strategic_tension_report=strategic_tensions,
        now_utc=issued_at,
    )
    strategic_memory_horizon = strategic_memory_horizon_report
    contradiction_resolution = contradiction_resolution_report or build_oracle_contradiction_resolution_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=strategy_cohorts,
        doctrine_adaptation_report=doctrine_adaptation,
        research_priority_report=research_priorities,
        research_execution_memory_report=research_execution_memory_report,
        thesis_graph_report=thesis_graph,
        strategic_tension_report=strategic_tensions,
        strategic_narrative_report=strategic_narrative,
        strategic_memory_horizon_report=strategic_memory_horizon,
        now_utc=issued_at,
    )
    intervention_simulation = intervention_simulation_report or build_oracle_strategic_intervention_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        thesis_memory_report=thesis,
        strategy_cohort_report=strategy_cohorts,
        doctrine_adaptation_report=doctrine_adaptation,
        research_priority_report=research_priorities,
        research_execution_memory_report=research_execution_memory_report,
        thesis_graph_report=thesis_graph,
        strategic_tension_report=strategic_tensions,
        strategic_narrative_report=strategic_narrative,
        strategic_memory_horizon_report=strategic_memory_horizon,
        contradiction_resolution_report=contradiction_resolution,
        scenario_lab_report=scenario_lab,
        now_utc=issued_at,
    )

    strategic_campaigns = strategic_campaign_report or build_oracle_strategic_campaign_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        queue_report=queue,
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=strategy_cohorts,
        doctrine_adaptation_report=doctrine_adaptation,
        research_priority_report=research_priorities,
        research_execution_memory_report=research_execution_memory_report,
        thesis_graph_report=thesis_graph,
        strategic_tension_report=strategic_tensions,
        strategic_narrative_report=strategic_narrative,
        strategic_memory_horizon_report=strategic_memory_horizon,
        contradiction_resolution_report=contradiction_resolution,
        intervention_report=intervention_simulation,
        now_utc=issued_at,
    )
    campaign_execution = campaign_execution_report or build_oracle_strategic_campaign_execution_report(
        strategic_campaigns,
        research_execution_memory_report=research_execution_memory_report,
        doctrine_adaptation_report=doctrine_adaptation,
        strategic_memory_horizon_report=strategic_memory_horizon,
        now_utc=issued_at,
    )

    oracle_run_id, input_timestamp_utc, _ = assert_matching_strategic_epoch(fusion, posterior, transition, queue, thesis, doctrine_adaptation, research_priorities, research_execution_memory_report, thesis_graph, strategic_tensions, strategic_narrative, strategic_memory_horizon, contradiction_resolution, intervention_simulation, strategic_campaigns, campaign_execution)
    resolved_repo_root = (repo_root or Path.cwd()).resolve()
    resolved_search_root = (search_root or (resolved_repo_root / "docs" / "artifacts")).resolve()

    def _section_evidence(report_path: Path | None) -> dict[str, str] | None:
        if report_path is None:
            return None
        candidate = Path(report_path)
        if not candidate.exists():
            return None
        return discover_preferred_strategic_artifact_evidence(report_path=candidate, repo_root=resolved_repo_root, search_root=resolved_search_root)

    doctrine_adaptation_evidence = _section_evidence(doctrine_adaptation_report_path)
    research_priorities_evidence = _section_evidence(research_priority_report_path)
    intervention_simulation_evidence = _section_evidence(intervention_simulation_report_path)
    strategic_campaigns_evidence = _section_evidence(strategic_campaign_report_path)
    campaign_execution_evidence = _section_evidence(campaign_execution_report_path)

    def _merge_section_grounding(*, facts: list[str], provenance: list[str], artifact_evidence: dict[str, str] | None) -> tuple[str | None, str | None, str | None, str | None, str | None, list[str], list[str]]:
        if artifact_evidence is None:
            return preferred_backing_source, preferred_backing_classification, None, None, None, _unique(facts), provenance
        manifest_path = artifact_evidence.get("manifest_path") or None
        artifact_kind = artifact_evidence.get("artifact_kind") or None
        evidence_status = artifact_evidence.get("evidence_status") or None
        evidence_classification = artifact_evidence.get("preferred_strategic_backing_classification") or preferred_backing_classification
        evidence_facts = [
            f"strategic_artifact_evidence_manifest={manifest_path}" if manifest_path else "",
            f"strategic_artifact_evidence_kind={artifact_kind}" if artifact_kind else "",
            f"strategic_artifact_evidence_status={evidence_status}" if evidence_status else "",
        ]
        evidence_provenance = provenance + ([f"strategic_artifact_evidence:{artifact_kind}"] if artifact_kind else [])
        return "strategic_artifact_evidence_manifest", evidence_classification, manifest_path, artifact_kind, evidence_status, _unique(evidence_facts + facts), evidence_provenance

    preferred_backing_source = preferred_strategic_backing_source(strategic_memory_horizon)
    preferred_backing_classification = preferred_strategic_backing_classification(strategic_memory_horizon)
    backing_facts = strategic_backing_facts(strategic_memory_horizon)
    resolved_repo_root = repo_root.resolve() if repo_root is not None else None
    resolved_search_root = search_root.resolve() if search_root is not None else resolved_repo_root
    cadence = summarize_exact_cadence_feedback(repo_root=resolved_repo_root, search_root=resolved_search_root, window_size=6)
    exact_cadence_signal_classification = classify_exact_cadence_signal(
        exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
        exact_feedback_relief_count=cadence.exact_feedback_relief_count,
    )
    cadence_facts = [
        f"exact_cadence_signal_classification={exact_cadence_signal_classification}",
        f"exact_feedback_confirmation_count={cadence.exact_feedback_confirmation_count}",
        f"exact_feedback_relief_count={cadence.exact_feedback_relief_count}",
    ]
    sections: list[OracleStrategicBriefingSection] = []
    if transition is not None:
        facts = [
            f"previous_regime={transition.previous_dominant_regime}",
            f"current_regime={transition.current_dominant_regime}",
            f"confidence_delta={transition.confidence_delta:+.2f}",
        ] + transition.drivers[:4]
        actions = transition.operator_actions[:3]
        status = transition.transition_classification
        summary_line = transition.summary_line
        provenance = [f"fusion:{fusion.schema_version}", f"transition:{transition.schema_version}"]
    else:
        facts = [f"dominant_regime={fusion.dominant_regime}", f"regime_confidence={fusion.regime_confidence:.2f}"]
        actions = ["Persist a previous strategic fusion report to unlock what-changed transition analysis."]
        status = "FIRST_OBSERVATION"
        summary_line = "This is the first strategic observation in the current briefing horizon, so regime change is not yet comparable."
        provenance = [f"fusion:{fusion.schema_version}"]
    sections.append(
        OracleStrategicBriefingSection(
            section_id="what_changed",
            title="What Changed",
            status=status,
            summary_line=summary_line,
            preferred_strategic_backing_source=preferred_backing_source,
            preferred_strategic_backing_classification=preferred_backing_classification,
            facts=_unique(backing_facts + facts),
            operator_actions=actions,
            provenance_refs=provenance,
        )
    )

    sections.append(
        OracleStrategicBriefingSection(
            section_id="strategic_posture",
            title="Strategic Posture",
            status=fusion.strategic_posture,
            summary_line=fusion.summary_line,
            preferred_strategic_backing_source=preferred_backing_source,
            exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
            exact_feedback_relief_count=cadence.exact_feedback_relief_count,
            exact_cadence_signal_classification=exact_cadence_signal_classification,
            preferred_strategic_backing_classification=preferred_backing_classification,
            facts=_unique(backing_facts + cadence_facts + [
                f"epistemic_status={fusion.epistemic_status}",
                f"regime_confidence={fusion.regime_confidence:.2f}",
                f"opportunity_score={fusion.opportunity_score:.2f}",
                f"caution_score={fusion.caution_score:.2f}",
                f"doctrine_stress_score={fusion.doctrine_stress_score:.2f}",
            ]),
            operator_actions=fusion.operator_actions[:3],
            provenance_refs=[f"fusion:{fusion.schema_version}"],
        )
    )

    sections.append(
        OracleStrategicBriefingSection(
            section_id="strategic_narrative",
            title="Strategic Narrative",
            status=strategic_narrative.conviction_state,
            summary_line=strategic_narrative.summary_line,
            preferred_strategic_backing_source=preferred_backing_source,
            exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
            exact_feedback_relief_count=cadence.exact_feedback_relief_count,
            exact_cadence_signal_classification=exact_cadence_signal_classification,
            preferred_strategic_backing_classification=preferred_backing_classification,
            facts=(backing_facts + cadence_facts + [
                f"conviction_score={strategic_narrative.conviction_score:.2f}",
                f"fragility_score={strategic_narrative.fragility_score:.2f}",
                *[f"{item.driver_kind}:{item.trust_bias}:rank={item.rank_score:.2f}:{item.title}" for item in strategic_narrative.items[:5]],
            ])[:8],
            operator_actions=strategic_narrative.operator_actions[:4],
            provenance_refs=[f"strategic_narrative:{strategic_narrative.schema_version}"],
        )
    )

    if strategic_memory_horizon is not None:
        sections.append(
            OracleStrategicBriefingSection(
                section_id="belief_drift_timeline",
                title="Belief Drift Timeline",
                status=strategic_memory_horizon.drift_state,
                summary_line=strategic_memory_horizon.summary_line,
                preferred_strategic_backing_source=preferred_backing_source,
                preferred_strategic_backing_classification=preferred_backing_classification,
                facts=backing_facts + [
                    f"conviction_delta={strategic_memory_horizon.conviction_score_delta:+.2f}",
                    f"fragility_delta={strategic_memory_horizon.fragility_score_delta:+.2f}",
                    f"history_integrity={strategic_memory_horizon.history_integrity_status}",
                    f"sealed_history={strategic_memory_horizon.sealed_history_observation_count}",
                    f"rising_driver={strategic_memory_horizon.strongest_rising_driver_kind or 'none'}",
                    f"falling_driver={strategic_memory_horizon.strongest_falling_driver_kind or 'none'}",
                    *[f"{point.generated_at_utc.isoformat()}:{point.conviction_state}:driver={point.top_driver_kind or 'none'}:score={point.conviction_score:.2f}" for point in strategic_memory_horizon.points[-4:]],
                ][:8],
                operator_actions=strategic_memory_horizon.operator_actions[:4],
                provenance_refs=[f"strategic_memory_horizon:{strategic_memory_horizon.schema_version}"],
            )
        )

    opportunity_items = [item for item in queue.items if item.queue_kind == "OPPORTUNITY"]
    sections.append(
        OracleStrategicBriefingSection(
            section_id="opportunity_queue",
            title="Opportunity Queue",
            status=("INTEGRITY_GATED" if queue.history_integrity_status != "SEALED_HISTORY" and opportunity_items else "ACTIVE" if opportunity_items else "QUIET"),
            summary_line=(opportunity_items[0].summary_line if opportunity_items else "No immediate opportunity items dominate the current strategic queue."),
            preferred_strategic_backing_source=preferred_backing_source,
            preferred_strategic_backing_classification=preferred_backing_classification,
            facts=(backing_facts + [f"history_integrity={queue.history_integrity_status}", f"integrity_friction={queue.integrity_operator_friction_score:.2f}", f"sealed_history={queue.sealed_history_observation_count}"] + [f"{item.title}:score={item.priority_score:.2f}:friction={item.operator_friction_score:.2f}:action={item.operator_action}" for item in opportunity_items[:6]])[:6],
            operator_actions=_unique([item.operator_action for item in opportunity_items][:3]) or ["Continue scanning for supportive regime and recovery evidence."],
            provenance_refs=[f"queue:{queue.schema_version}"],
        )
    )

    caution_items = [item for item in queue.items if item.queue_kind != "OPPORTUNITY"]
    sections.append(
        OracleStrategicBriefingSection(
            section_id="caution_queue",
            title="Caution Queue",
            status=("ELEVATED" if caution_items else "CLEAR"),
            summary_line=(caution_items[0].summary_line if caution_items else "No dominant caution or review items were surfaced by the current strategic queue."),
            preferred_strategic_backing_source=preferred_backing_source,
            preferred_strategic_backing_classification=preferred_backing_classification,
            facts=(backing_facts + [f"history_integrity={queue.history_integrity_status}"] + [f"{item.title}:kind={item.queue_kind}:score={item.priority_score:.2f}:friction={item.operator_friction_score:.2f}" for item in caution_items[:6]])[:6],
            operator_actions=_unique([item.operator_action for item in caution_items][:3]) or ["Maintain monitoring cadence while caution remains contained."],
            provenance_refs=[f"queue:{queue.schema_version}"],
        )
    )

    sections.append(
        OracleStrategicBriefingSection(
            section_id="doctrine_pressure",
            title="Doctrine Pressure",
            status="PRESSURED" if fusion.doctrine_pressure_points else "STABLE",
            summary_line=(fusion.doctrine_pressure_points[0] if fusion.doctrine_pressure_points else "Doctrine assumptions are not under unusual pressure in the current fusion stack."),
            preferred_strategic_backing_source=preferred_backing_source,
            preferred_strategic_backing_classification=preferred_backing_classification,
            facts=_unique(backing_facts + fusion.doctrine_pressure_points)[:6],
            operator_actions=["Review doctrine clauses most exposed to the current contradiction and regime-mismatch pressures."] if fusion.doctrine_pressure_points else ["Keep doctrine review periodic until pressure rises."],
            provenance_refs=[f"fusion:{fusion.schema_version}"],
        )
    )

    doctrine_source, doctrine_classification, doctrine_manifest, doctrine_kind, doctrine_status, doctrine_facts, doctrine_provenance = _merge_section_grounding(
        facts=backing_facts + [
            f"{item.clause_id}:{item.adaptation_state}:stress={item.stress_score:.2f}:priority={item.review_priority_score:.2f}"
            for item in doctrine_adaptation.items[:6]
        ],
        provenance=[f"doctrine_adaptation:{doctrine_adaptation.schema_version}"],
        artifact_evidence=doctrine_adaptation_evidence,
    )
    sections.append(
        OracleStrategicBriefingSection(
            section_id="doctrine_adaptation",
            title="Doctrine Adaptation",
            status=("FREEZE" if doctrine_adaptation.freeze_recommended else doctrine_adaptation.items[0].adaptation_state if doctrine_adaptation.items else "MONITOR"),
            summary_line=doctrine_adaptation.summary_line,
            preferred_strategic_backing_source=doctrine_source,
            preferred_strategic_backing_classification=doctrine_classification,
            preferred_strategic_artifact_evidence_manifest=doctrine_manifest,
            preferred_strategic_artifact_evidence_kind=doctrine_kind,
            preferred_strategic_artifact_evidence_status=doctrine_status,
            facts=doctrine_facts,
            operator_actions=doctrine_adaptation.operator_actions[:4],
            provenance_refs=doctrine_provenance,
        )
    )

    research_source, research_classification, research_manifest, research_kind, research_status, research_facts, research_provenance = _merge_section_grounding(
        facts=(backing_facts + [f"history_integrity={research_priorities.history_integrity_status}", f"integrity_penalty={research_priorities.integrity_penalty_score:.2f}", f"sealed_history={research_priorities.sealed_history_observation_count}"] + [
            f"{item.priority_kind}:{item.title}:urgency={item.urgency_score:.2f}:penalty={item.integrity_penalty_score:.2f}"
            for item in research_priorities.items[:6]
        ])[:6],
        provenance=[f"research_priorities:{research_priorities.schema_version}"],
        artifact_evidence=research_priorities_evidence,
    )
    sections.append(
        OracleStrategicBriefingSection(
            section_id="research_priorities",
            title="Research Priorities",
            status=(research_priorities.items[0].priority_kind if research_priorities.items else "CLEAR"),
            summary_line=research_priorities.summary_line,
            preferred_strategic_backing_source=research_source,
            preferred_strategic_backing_classification=research_classification,
            preferred_strategic_artifact_evidence_manifest=research_manifest,
            preferred_strategic_artifact_evidence_kind=research_kind,
            preferred_strategic_artifact_evidence_status=research_status,
            facts=research_facts,
            operator_actions=research_priorities.operator_actions[:4],
            provenance_refs=research_provenance,
        )
    )

    if research_execution_memory_report is not None:
        sections.append(
            OracleStrategicBriefingSection(
                section_id="investigation_outcomes",
                title="Investigation Outcomes",
                status=(research_execution_memory_report.items[0].outcome_disposition or research_execution_memory_report.items[0].execution_state if research_execution_memory_report.items else "QUIET"),
                summary_line=research_execution_memory_report.summary_line,
                preferred_strategic_backing_source=preferred_backing_source,
                preferred_strategic_backing_classification=preferred_backing_classification,
                facts=backing_facts + [
                    f"{item.priority_id}:{item.execution_state}:{item.outcome_disposition or 'NONE'}:impact={item.confidence_impact:+.2f}"
                    for item in research_execution_memory_report.items[:6]
                ],
                operator_actions=research_execution_memory_report.operator_actions[:4],
                provenance_refs=[f"research_execution_memory:{research_execution_memory_report.schema_version}"],
            )
        )

    top_states = sorted(posterior.strategies, key=lambda item: item.posterior_edge_confidence)
    sections.append(
        OracleStrategicBriefingSection(
            section_id="strategy_health",
            title="Strategy Health",
            status=("DEGRADED" if posterior.degraded_strategy_ids else "RECOVERING" if posterior.recovering_strategy_ids else "STABLE"),
            summary_line=posterior.summary_line,
            preferred_strategic_backing_source=preferred_backing_source,
            preferred_strategic_backing_classification=preferred_backing_classification,
            facts=backing_facts + [
                f"{item.strategy_id}:{item.recommended_action}:posterior={item.posterior_edge_confidence:.2f}:delta={item.confidence_delta:+.2f}"
                for item in top_states[:6]
            ],
            operator_actions=posterior.operator_actions[:4],
            provenance_refs=[f"posterior:{posterior.schema_version}"],
        )
    )

    sections.append(
        OracleStrategicBriefingSection(
            section_id="strategy_cohorts",
            title="Strategy Cohorts",
            status=(strategy_cohorts.items[0].cohort_bucket if strategy_cohorts.items else "UNKNOWN"),
            summary_line=strategy_cohorts.summary_line,
            preferred_strategic_backing_source=preferred_backing_source,
            preferred_strategic_backing_classification=preferred_backing_classification,
            facts=backing_facts + [
                f"{item.strategy_id}:{item.cohort_bucket}:rank={item.cohort_rank_score:.2f}:floor={item.scenario_downside_floor:.2f}"
                for item in strategy_cohorts.items[:6]
            ],
            operator_actions=strategy_cohorts.operator_actions[:4],
            provenance_refs=[f"strategy_cohort:{strategy_cohorts.schema_version}"],
        )
    )

    priority_theses = sorted(
        thesis.items,
        key=lambda item: (
            0 if item.evolution_state in {"REVERSING", "WEAKENING"} else 1 if item.evolution_state in {"STRENGTHENING", "EMERGING"} else 2,
            item.confidence_score,
        ),
    )
    sections.append(
        OracleStrategicBriefingSection(
            section_id="thesis_evolution",
            title="Thesis Evolution",
            status=("UNDER_REVIEW" if thesis.weakening_thesis_ids else "STRENGTHENING" if thesis.strengthening_thesis_ids else "STABLE"),
            summary_line=thesis.summary_line,
            preferred_strategic_backing_source=preferred_backing_source,
            preferred_strategic_backing_classification=preferred_backing_classification,
            facts=backing_facts + [
                f"{item.thesis_id}:{item.current_state}:{item.evolution_state}:confidence={item.confidence_score:.2f}"
                for item in priority_theses[:6]
            ],
            operator_actions=thesis.operator_actions[:4],
            provenance_refs=[f"thesis:{thesis.schema_version}"],
        )
    )

    sections.append(
        OracleStrategicBriefingSection(
            section_id="thesis_graph",
            title="Thesis Dependency Graph",
            status=("CASCADE_RISK" if thesis_graph.nodes and thesis_graph.nodes[0].cascade_risk_score >= 0.70 else "CONNECTED"),
            summary_line=thesis_graph.summary_line,
            preferred_strategic_backing_source=preferred_backing_source,
            preferred_strategic_backing_classification=preferred_backing_classification,
            facts=backing_facts + [
                f"{item.node_id}:{item.node_kind}:{item.status}:risk={item.cascade_risk_score:.2f}:links={len(item.connected_node_ids)}"
                for item in thesis_graph.nodes[:6]
            ],
            operator_actions=thesis_graph.operator_actions[:4],
            provenance_refs=[f"thesis_graph:{thesis_graph.schema_version}"],
        )
    )

    sections.append(
        OracleStrategicBriefingSection(
            section_id="strategic_tensions",
            title="Strategic Tensions",
            status=(strategic_tensions.items[0].alignment_state if strategic_tensions.items else "CLEAR"),
            summary_line=strategic_tensions.summary_line,
            preferred_strategic_backing_source=preferred_backing_source,
            preferred_strategic_backing_classification=preferred_backing_classification,
            facts=backing_facts + [
                f"{item.tension_kind}:{item.alignment_state}:severity={item.severity_score:.2f}:{item.title}"
                for item in strategic_tensions.items[:6]
            ],
            operator_actions=strategic_tensions.operator_actions[:4],
            provenance_refs=[f"strategic_tensions:{strategic_tensions.schema_version}"],
        )
    )


    sections.append(
        OracleStrategicBriefingSection(
            section_id="contradiction_resolution",
            title="Contradiction Resolution",
            status=(contradiction_resolution.items[0].resolution_kind if contradiction_resolution.items else "CLEAR"),
            summary_line=contradiction_resolution.summary_line,
            preferred_strategic_backing_source=preferred_backing_source,
            preferred_strategic_backing_classification=preferred_backing_classification,
            facts=backing_facts + [
                f"conviction_state={contradiction_resolution.conviction_state}",
                f"drift_state={contradiction_resolution.drift_state}",
                f"history_integrity={contradiction_resolution.history_integrity_status}",
                *[
                    f"{item.resolution_kind}:priority={item.resolution_priority_score:.2f}:gain={item.expected_conviction_gain_score:.2f}:{item.title}"
                    for item in contradiction_resolution.items[:5]
                ],
            ][:8],
            operator_actions=contradiction_resolution.operator_actions[:4],
            provenance_refs=[f"contradiction_resolution:{contradiction_resolution.schema_version}"],
        )
    )

    sections.append(
        OracleStrategicBriefingSection(
            section_id="intervention_simulation",
            title="Intervention Simulation",
            status=(intervention_simulation.items[0].projected_conviction_state if intervention_simulation.items else intervention_simulation.baseline_conviction_state),
            summary_line=intervention_simulation.summary_line,
            preferred_strategic_backing_source=preferred_backing_source,
            preferred_strategic_backing_classification=preferred_backing_classification,
            facts=(backing_facts + [
                f"baseline_conviction={intervention_simulation.baseline_conviction_state}:{intervention_simulation.baseline_conviction_score:.2f}",
                f"baseline_fragility={intervention_simulation.baseline_fragility_score:.2f}",
                f"baseline_drift={intervention_simulation.baseline_drift_state}",
                f"history_integrity={intervention_simulation.history_integrity_status}",
                f"integrity_penalty={intervention_simulation.integrity_penalty_score:.2f}",
            ] + [
                f"{item.intervention_kind}:gain={item.projected_conviction_gain_score:.2f}:penalty={item.integrity_penalty_score:.2f}:{item.title}"
                for item in intervention_simulation.items[:4]
            ])[:8],
            operator_actions=intervention_simulation.operator_actions[:4],
            provenance_refs=[f"intervention_simulation:{intervention_simulation.schema_version}"],
        )
    )

    sections.append(
        OracleStrategicBriefingSection(
            section_id="strategic_campaigns",
            title="Strategic Campaigns",
            status=(strategic_campaigns.items[0].objective_kind if strategic_campaigns.items else "CLEAR"),
            summary_line=strategic_campaigns.summary_line,
            preferred_strategic_backing_source=preferred_backing_source,
            preferred_strategic_backing_classification=preferred_backing_classification,
            facts=(backing_facts + [
                f"baseline_conviction={strategic_campaigns.baseline_conviction_state}:{strategic_campaigns.baseline_conviction_score:.2f}",
                f"baseline_fragility={strategic_campaigns.baseline_fragility_score:.2f}",
                f"history_integrity={strategic_campaigns.history_integrity_status}",
                f"integrity_penalty={strategic_campaigns.integrity_penalty_score:.2f}",
                f"integrity_friction={strategic_campaigns.integrity_operator_friction_score:.2f}",
            ] + [
                f"{item.objective_kind}:priority={item.priority_score:.2f}:penalty={item.integrity_penalty_score:.2f}:steps={len(item.steps)}:{item.title}"
                for item in strategic_campaigns.items[:4]
            ])[:8],
            operator_actions=strategic_campaigns.operator_actions[:4],
            provenance_refs=[f"strategic_campaigns:{strategic_campaigns.schema_version}"],
        )
    )

    sections.append(
        OracleStrategicBriefingSection(
            section_id="campaign_execution",
            title="Campaign Execution",
            status=(campaign_execution.items[0].execution_state if campaign_execution.items else "QUEUED"),
            summary_line=campaign_execution.summary_line,
            preferred_strategic_backing_source=preferred_backing_source,
            exact_feedback_confirmation_count=campaign_execution.exact_feedback_confirmation_count,
            exact_feedback_relief_count=campaign_execution.exact_feedback_relief_count,
            exact_cadence_signal_classification=campaign_execution.exact_cadence_signal_classification,
            preferred_strategic_backing_classification=preferred_backing_classification,
            facts=(backing_facts + [
                f"baseline_conviction={campaign_execution.baseline_conviction_state}:{campaign_execution.baseline_conviction_score:.2f}",
                f"baseline_fragility={campaign_execution.baseline_fragility_score:.2f}",
                f"history_integrity={campaign_execution.history_integrity_status}",
                f"exact_cadence_signal_classification={campaign_execution.exact_cadence_signal_classification}",
                f"exact_feedback_confirmation_count={campaign_execution.exact_feedback_confirmation_count}",
                f"exact_feedback_relief_count={campaign_execution.exact_feedback_relief_count}",
                f"active={','.join(campaign_execution.active_campaign_ids) if campaign_execution.active_campaign_ids else 'none'}",
                f"blocked={','.join(campaign_execution.blocked_campaign_ids) if campaign_execution.blocked_campaign_ids else 'none'}",
                f"drifting={','.join(campaign_execution.drifting_campaign_ids) if campaign_execution.drifting_campaign_ids else 'none'}",
            ] + [
                f"{item.execution_state}:progress={item.progress_score:.2f}:blocker={item.blocker_score:.2f}:{item.title}"
                for item in campaign_execution.items[:4]
            ])[:8],
            operator_actions=campaign_execution.operator_actions[:4],
            provenance_refs=[f"campaign_execution:{campaign_execution.schema_version}"],
        )
    )

    downside = next((item for item in scenario_lab.scenarios if item.scenario_id == scenario_lab.highest_downside_scenario_id), None)
    upside = next((item for item in scenario_lab.scenarios if item.scenario_id == scenario_lab.highest_upside_scenario_id), None)
    scenario_facts = []
    if downside is not None:
        scenario_facts.append(
            f"downside={downside.scenario_id}:{downside.resulting_strategic_posture}:caution_delta={downside.caution_delta:+.2f}:doctrine_delta={downside.doctrine_stress_delta:+.2f}"
        )
    if upside is not None:
        scenario_facts.append(
            f"upside={upside.scenario_id}:{upside.resulting_strategic_posture}:opportunity_delta={upside.opportunity_delta:+.2f}:posterior_delta={upside.average_posterior_delta:+.2f}"
        )
    scenario_facts.extend(
        f"{item.scenario_id}:{item.transition_classification}:{item.leading_queue_kind or 'NONE'}"
        for item in scenario_lab.scenarios[:4]
    )
    sections.append(
        OracleStrategicBriefingSection(
            section_id="scenario_lab",
            title="Scenario Lab",
            status=("DOWNSIDE_PRESSURE" if downside is not None and downside.caution_delta > 0.10 else "UPSIDE_OPTIONALITY" if upside is not None and upside.opportunity_delta > 0.08 else "BALANCED_SCENARIOS"),
            summary_line=scenario_lab.summary_line,
            preferred_strategic_backing_source=preferred_backing_source,
            preferred_strategic_backing_classification=preferred_backing_classification,
            facts=_unique(backing_facts + scenario_facts)[:8],
            operator_actions=scenario_lab.operator_actions[:4],
            provenance_refs=[f"scenario_lab:{scenario_lab.schema_version}"],
        )
    )

    operator_actions = _unique(
        fusion.operator_actions
        + posterior.operator_actions
        + queue.operator_actions
        + thesis.operator_actions
        + strategy_cohorts.operator_actions
        + doctrine_adaptation.operator_actions
        + research_priorities.operator_actions
        + (research_execution_memory_report.operator_actions if research_execution_memory_report is not None else [])
        + scenario_lab.operator_actions
        + thesis_graph.operator_actions
        + strategic_tensions.operator_actions
        + strategic_narrative.operator_actions
        + intervention_simulation.operator_actions
        + strategic_campaigns.operator_actions
        + campaign_execution.operator_actions
        + (transition.operator_actions if transition else [])
    )[:8]
    return OracleStrategicBriefingReport(
        generated_at_utc=issued_at,
        universe_label=payload.universe_label,
        oracle_run_id=oracle_run_id,
        input_timestamp_utc=input_timestamp_utc,
        dominant_regime=fusion.dominant_regime,
        strategic_posture=fusion.strategic_posture,
        transition_classification=(transition.transition_classification if transition else None),
        preferred_strategic_backing_source=preferred_backing_source,
        exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
        exact_feedback_relief_count=cadence.exact_feedback_relief_count,
        exact_cadence_signal_classification=exact_cadence_signal_classification,
        preferred_strategic_backing_classification=preferred_backing_classification,
        summary_line=(
            f"Strategic briefing for {payload.universe_label}: posture={fusion.strategic_posture}, "
            f"dominant_regime={fusion.dominant_regime}, avg_posterior={posterior.average_posterior_edge_confidence:.1%}, "
            f"lead_cohorts={','.join(strategy_cohorts.lead_strategy_ids) if strategy_cohorts.lead_strategy_ids else 'none'}, "
            f"thesis_review={'open' if thesis.weakening_thesis_ids else 'contained'}, "
            f"doctrine_freeze={'yes' if doctrine_adaptation.freeze_recommended else 'no'}, "
            f"top_research_priority={research_priorities.highest_priority_id or 'none'}, "
            f"completed_investigations={len(research_execution_memory_report.completed_priority_ids) if research_execution_memory_report is not None else 0}, "
            f"scenario_pressure={scenario_lab.highest_downside_scenario_id or 'none'}, "
            f"cascade_focus={thesis_graph.highest_cascade_risk_node_ids[0] if thesis_graph.highest_cascade_risk_node_ids else 'none'}, "
            f"top_tension={strategic_tensions.highest_severity_tension_id or 'none'}, "
            f"top_narrative={strategic_narrative.highest_ranked_narrative_id or 'none'}, "
            f"top_intervention={intervention_simulation.highest_impact_intervention_id or 'none'}, "
            f"top_campaign={strategic_campaigns.highest_priority_campaign_id or 'none'}, "
            f"active_campaign={campaign_execution.active_campaign_ids[0] if campaign_execution.active_campaign_ids else 'none'}, "
            f"cadence={exact_cadence_signal_classification}, exact_confirm={cadence.exact_feedback_confirmation_count}, exact_relief={cadence.exact_feedback_relief_count}."
        ),
        sections=sections,
        operator_actions=operator_actions,
    )
