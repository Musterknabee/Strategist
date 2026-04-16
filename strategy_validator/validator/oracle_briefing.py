from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Iterable

from strategy_validator.contracts.oracle import (
    OracleBriefingPackReport,
    OracleBriefingSection,
    OracleDerivedViewReport,
    OracleDoctrineAdaptationReport,
    OracleIncidentPackReport,
    OracleResearchExecutionMemoryReport,
    OracleThesisGraphReport,
    OracleResearchPriorityReport,
    OracleScenarioLabReport,
    OracleStatusPackReport,
    OracleStrategicBriefingReport,
    OracleStrategicMemoryHorizonReport,
    OracleStrategicCampaignReport,
    OracleStrategicCampaignExecutionReport,
    OracleStrategicInterventionReport,
    OracleStrategicNarrativeReport,
    OracleContradictionResolutionReport,
    OracleStrategicTensionReport,
    OracleStrategyCohortReport,
    OracleThesisMemoryReport,
)
from strategy_validator.validator.oracle_diagnostics import (
    build_oracle_incident_pack,
    build_oracle_status_pack,
)
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.oracle_strategic_artifact_evidence import discover_preferred_strategic_artifact_evidence
from strategy_validator.validator.oracle_policy import load_oracle_policy, oracle_policy_sha256
from strategy_validator.validator.oracle_artifact_freshness import build_freshness_item, summarize_freshness
from strategy_validator.control_plane import (
    build_briefing_pack_header,
    build_briefing_pack_html,
    render_operator_pack_header_markdown_lines,
)
from strategy_validator.validator.oracle_artifact_lineage import build_lineage_item, build_lineage_item_from_model, build_lineage_item_from_registered_artifact, summarize_lineage
from strategy_validator.validator.oracle_artifact_integrity import summarize_artifact_integrity
from strategy_validator.validator.oracle_artifact_coverage import summarize_artifact_coverage
from strategy_validator.validator.oracle_operator_readiness import assess_briefing_operator_readiness
from strategy_validator.validator.oracle_support_verification import summarize_support_verification
from strategy_validator.validator.oracle_support_chain_trust import assess_support_chain_trust
from strategy_validator.validator.oracle_support_chain_remediation import assess_support_chain_remediation
from strategy_validator.validator.oracle_governance_plane import assess_governance_plane
from strategy_validator.control_plane.operator_board_sections import build_operator_queue_briefing_section
from strategy_validator.control_plane.operator_pack_comparison import (
    build_operator_pack_comparison_request,
    materialize_operator_pack_comparison,
    render_operator_pack_comparison_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_timeline import (
    build_operator_pack_timeline_request,
    materialize_operator_pack_timeline,
    render_operator_pack_timeline_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_drift import (
    build_operator_pack_drift_request,
    materialize_operator_pack_drift,
    render_operator_pack_drift_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_assignment import (
    build_operator_pack_assignment_request,
    materialize_operator_pack_assignment,
    render_operator_pack_assignment_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_handoff import (
    build_operator_pack_handoff_request,
    materialize_operator_pack_handoff,
    render_operator_pack_handoff_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_claim_lease import (
    build_operator_pack_claim_lease_request,
    materialize_operator_pack_claim_lease,
    render_operator_pack_claim_lease_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_claim_lifecycle import (
    build_operator_pack_claim_lifecycle_request,
    materialize_operator_pack_claim_lifecycle,
    render_operator_pack_claim_lifecycle_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_lease_governance import (
    build_operator_pack_lease_governance_request,
    materialize_operator_pack_lease_governance,
    render_operator_pack_lease_governance_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_claim_operability import (
    build_operator_pack_claim_operability_request,
    materialize_operator_pack_claim_operability,
    render_operator_pack_claim_operability_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_execution_readiness import (
    build_operator_pack_execution_readiness_request,
    materialize_operator_pack_execution_readiness,
    render_operator_pack_execution_readiness_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_dispatch_permission import (
    build_operator_pack_dispatch_permission_request,
    materialize_operator_pack_dispatch_permission,
    render_operator_pack_dispatch_permission_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_dispatch_outcome import (
    build_operator_pack_dispatch_outcome_request,
    materialize_operator_pack_dispatch_outcome,
    render_operator_pack_dispatch_outcome_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_execution_exception import (
    build_operator_pack_execution_exception_request,
    materialize_operator_pack_execution_exception,
    render_operator_pack_execution_exception_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_approval_needed import (
    build_operator_pack_approval_needed_request,
    materialize_operator_pack_approval_needed,
    render_operator_pack_approval_needed_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_approval_disposition import (
    build_operator_pack_approval_disposition_request,
    materialize_operator_pack_approval_disposition,
    render_operator_pack_approval_disposition_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_execution_authorization import (
    build_operator_pack_execution_authorization_request,
    materialize_operator_pack_execution_authorization,
    render_operator_pack_execution_authorization_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_execution_finality import (
    build_operator_pack_execution_finality_request,
    materialize_operator_pack_execution_finality,
    render_operator_pack_execution_finality_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_terminal_resolution import (
    build_operator_pack_terminal_resolution_request,
    materialize_operator_pack_terminal_resolution,
    render_operator_pack_terminal_resolution_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_terminal_closure import (
    build_operator_pack_terminal_closure_request,
    materialize_operator_pack_terminal_closure,
    render_operator_pack_terminal_closure_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_terminal_archive import (
    build_operator_pack_terminal_archive_request,
    materialize_operator_pack_terminal_archive,
    render_operator_pack_terminal_archive_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_terminal_record import (
    build_operator_pack_terminal_record_request,
    materialize_operator_pack_terminal_record,
    render_operator_pack_terminal_record_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_execution_force import (
    build_operator_pack_execution_force_request,
    materialize_operator_pack_execution_force,
    render_operator_pack_execution_force_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_escalation import (
    build_operator_pack_escalation_request,
    materialize_operator_pack_escalation,
    render_operator_pack_escalation_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_dashboard import (
    build_operator_pack_dashboard_request,
    materialize_operator_pack_dashboard,
    render_operator_pack_dashboard_markdown_lines,
)
from strategy_validator.control_plane.operator_queue_snapshot import materialize_operator_queue_snapshot
from strategy_validator.control_plane.operator_section_registry import compose_briefing_pack_sections
from strategy_validator.projections.operator_materialization import with_report_provenance_digest
from strategy_validator.projections.operator_pack_service import materialize_briefing_pack_bundle


from strategy_validator.validator.oracle_briefing_io import (
    _briefing_pack_projection_inputs,
    _find_latest,
    _load_contradiction_resolution,
    _load_doctrine_adaptation,
    _load_derived_view,
    _load_json,
    _load_research_execution_memory,
    _load_research_priorities,
    _load_scenario_lab,
    _load_strategic_briefing,
    _load_strategic_campaign,
    _load_strategic_campaign_execution,
    _load_strategic_intervention,
    _load_strategic_memory_horizon,
    _load_strategic_narrative,
    _load_strategic_tensions,
    _load_strategy_cohort,
    _load_thesis_graph,
    _load_thesis_memory,
    _resolve_briefing_derived_view_path,
    _sha256_json,
    _with_provenance_digest,
    emit_oracle_briefing_pack_projection_registry,
)


def _unique(items: Iterable[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if normalized and normalized not in output:
            output.append(normalized)
    return output


def _exact_cadence_summary(*, exact_feedback_confirmation_count: int, exact_feedback_relief_count: int) -> tuple[str, str]:
    if exact_feedback_confirmation_count > 0 and exact_feedback_confirmation_count >= exact_feedback_relief_count:
        return (
            "EXACT_CONFIRMED_PRESSURE",
            f"current constitutional pressure is being driven by repeated exact sealed confirmations ({exact_feedback_confirmation_count})",
        )
    if exact_feedback_relief_count > 0:
        return (
            "EXACT_RELIEF_PRESSURE",
            f"current constitutional pressure is being softened by repeated exact sealed relief signals ({exact_feedback_relief_count})",
        )
    return (
        "AMBIENT_DRIFT",
        "current constitutional pressure is being explained by broader ambient doctrine drift rather than repeated exact sealed cadence signals",
    )


def _find_section(report: OracleStatusPackReport, section_id: str):
    for section in report.sections:
        if section.section_id == section_id:
            return section
    return None


def _find_latest(search_root: Path, candidates: Iterable[str]) -> Path | None:
    discovered: list[Path] = []
    candidate_set = set(candidates)
    if not search_root.exists():
        return None
    for path in search_root.rglob("*"):
        if path.is_file() and path.name in candidate_set:
            discovered.append(path)
    if not discovered:
        return None
    discovered.sort(key=lambda path: (path.stat().st_mtime, str(path)))
    return discovered[-1]


def _briefing_sections(
    *,
    status_pack: OracleStatusPackReport,
    incident_pack: OracleIncidentPackReport | None,
    derived_view: OracleDerivedViewReport | None,
    strategic_briefing: OracleStrategicBriefingReport | None,
    strategic_narrative: OracleStrategicNarrativeReport | None,
    strategic_memory_horizon: OracleStrategicMemoryHorizonReport | None,
    contradiction_resolution: OracleContradictionResolutionReport | None,
    intervention_simulation: OracleStrategicInterventionReport | None,
    strategic_campaigns: OracleStrategicCampaignReport | None,
    campaign_execution: OracleStrategicCampaignExecutionReport | None,
    strategy_cohort: OracleStrategyCohortReport | None,
    thesis_memory: OracleThesisMemoryReport | None,
    doctrine_adaptation: OracleDoctrineAdaptationReport | None,
    research_priorities: OracleResearchPriorityReport | None,
    research_execution_memory: OracleResearchExecutionMemoryReport | None,
    thesis_graph: OracleThesisGraphReport | None,
    strategic_tensions: OracleStrategicTensionReport | None,
    scenario_lab: OracleScenarioLabReport | None,
    doctrine_adaptation_evidence: dict[str, str] | None = None,
    research_priorities_evidence: dict[str, str] | None = None,
    intervention_simulation_evidence: dict[str, str] | None = None,
    strategic_campaigns_evidence: dict[str, str] | None = None,
    campaign_execution_evidence: dict[str, str] | None = None,
) -> list[OracleBriefingSection]:
    sections: list[OracleBriefingSection] = []

    def _evidence_facts(evidence: dict[str, str] | None) -> list[str]:
        if not evidence:
            return []
        facts: list[str] = []
        manifest_path = evidence.get("manifest_path")
        artifact_kind = evidence.get("artifact_kind")
        evidence_status = evidence.get("evidence_status")
        if manifest_path:
            facts.append(f"strategic_artifact_evidence_manifest={manifest_path}")
        if artifact_kind:
            facts.append(f"strategic_artifact_evidence_kind={artifact_kind}")
        if evidence_status:
            facts.append(f"strategic_artifact_evidence_status={evidence_status}")
        return facts


    cadence_signal, cadence_summary = _exact_cadence_summary(
        exact_feedback_confirmation_count=status_pack.exact_feedback_confirmation_count,
        exact_feedback_relief_count=status_pack.exact_feedback_relief_count,
    )
    trust_facts = [
        f"status_pack_digest={status_pack.provenance_digest_sha256}",
        f"active_governed_exceptions={','.join(status_pack.active_governed_exception_ids) if status_pack.active_governed_exception_ids else 'none'}",
        f"exact_cadence_signal_classification={cadence_signal}",
        f"exact_feedback_confirmation_count={status_pack.exact_feedback_confirmation_count}",
        f"exact_feedback_relief_count={status_pack.exact_feedback_relief_count}",
        f"cadence_pressure_summary={cadence_summary}",
    ]
    if status_pack.preferred_strategic_backing_source:
        trust_facts.append(f"preferred_strategic_backing_source={status_pack.preferred_strategic_backing_source}")
    if status_pack.preferred_strategic_backing_classification:
        trust_facts.append(f"preferred_strategic_backing_classification={status_pack.preferred_strategic_backing_classification}")
    if incident_pack is not None:
        trust_facts.append(f"incident_kind={incident_pack.incident_kind}")
        trust_facts.append(f"incident_pack_digest={incident_pack.provenance_digest_sha256}")
    sections.append(
        OracleBriefingSection(
            section_id="trust_banner",
            title="Trust Banner",
            status=status_pack.trust_status,
            summary_line=status_pack.summary_line,
            preferred_strategic_backing_source=status_pack.preferred_strategic_backing_source,
            exact_feedback_confirmation_count=status_pack.exact_feedback_confirmation_count,
            exact_feedback_relief_count=status_pack.exact_feedback_relief_count,
            exact_cadence_signal_classification=cadence_signal,
            preferred_strategic_backing_classification=status_pack.preferred_strategic_backing_classification,
            facts=trust_facts,
            operator_actions=status_pack.operator_actions[:3],
            provenance_refs=_unique([
                f"status_pack:{status_pack.provenance_digest_sha256}",
                *([f"incident_pack:{incident_pack.provenance_digest_sha256}"] if incident_pack is not None else []),
            ]),
        )
    )

    if derived_view is not None:
        regime_summary = (
            f"Latest regime is {derived_view.latest_dominant_regime or 'UNKNOWN'} with advisory action "
            f"{derived_view.latest_global_action or 'UNKNOWN'} and epistemic status {derived_view.latest_epistemic_status or 'UNKNOWN'}."
        )
        sections.append(
            OracleBriefingSection(
                section_id="regime_state",
                title="Regime State",
                status=str(derived_view.latest_dominant_regime or "UNKNOWN"),
                summary_line=regime_summary,
                facts=_unique([
                    f"view_label={derived_view.view_label}",
                    f"latest_event_id={derived_view.latest_event_id or 'none'}",
                    f"window_entry_count={derived_view.window_entry_count}",
                    f"global_action={derived_view.latest_global_action or 'UNKNOWN'}",
                    f"epistemic_status={derived_view.latest_epistemic_status or 'UNKNOWN'}",
                ]),
                operator_actions=derived_view.operator_actions[:3],
                provenance_refs=[f"status_pack:{status_pack.provenance_digest_sha256}"],
            )
        )
        sections.append(
            OracleBriefingSection(
                section_id="strategy_health",
                title="Strategy Health",
                status=derived_view.derived_classification,
                summary_line=(
                    f"Strategy-health posture is {derived_view.derived_classification} with posterior confidence "
                    f"{derived_view.average_posterior_edge_confidence:.2f}."
                ),
                facts=_unique([
                    f"average_posterior_edge_confidence={derived_view.average_posterior_edge_confidence:.2f}",
                    f"evidence_gap_count={derived_view.evidence_gap_count}",
                    f"elevated_or_unknown_count={derived_view.elevated_or_unknown_count}",
                    f"defensive_posture_count={derived_view.defensive_posture_count}",
                    f"retrain_pressure_count={derived_view.retrain_pressure_count}",
                ]),
                operator_actions=derived_view.operator_actions[:3],
                provenance_refs=[f"status_pack:{status_pack.provenance_digest_sha256}"],
            )
        )
    else:
        for section_id, title in (("regime_state", "Regime State"), ("strategy_health", "Strategy Health")):
            sections.append(
                OracleBriefingSection(
                    section_id=section_id,
                    title=title,
                    status="UNKNOWN",
                    summary_line=f"{title} could not be derived because no canonical derived view report was available.",
                    facts=[],
                    operator_actions=["emit a canonical derived oracle view before relying on this briefing pack"],
                    provenance_refs=[f"status_pack:{status_pack.provenance_digest_sha256}"],
                )
            )

    if strategic_briefing is not None:
        strategic_section = next((section for section in strategic_briefing.sections if section.section_id == "strategic_posture"), None)
        narrative_section = next((section for section in strategic_briefing.sections if section.section_id == "strategic_narrative"), None)
        opportunity_section = next((section for section in strategic_briefing.sections if section.section_id == "opportunity_queue"), None)
        sections.append(
            OracleBriefingSection(
                section_id="strategic_posture",
                title="Strategic Posture",
                status=strategic_briefing.strategic_posture,
                summary_line=(strategic_section.summary_line if strategic_section is not None else strategic_briefing.summary_line),
                facts=(strategic_section.facts[:6] if strategic_section is not None else [f"dominant_regime={strategic_briefing.dominant_regime}"]),
                operator_actions=(strategic_section.operator_actions[:3] if strategic_section is not None else strategic_briefing.operator_actions[:3]),
                provenance_refs=[f"strategic_briefing:{strategic_briefing.schema_version}"],
            )
        )
        sections.append(
            OracleBriefingSection(
                section_id="strategic_narrative",
                title="Strategic Narrative",
                status=(narrative_section.status if narrative_section is not None else strategic_narrative.conviction_state if strategic_narrative is not None else "UNKNOWN"),
                summary_line=(narrative_section.summary_line if narrative_section is not None else strategic_narrative.summary_line if strategic_narrative is not None else "No strategic narrative report was available."),
                facts=(narrative_section.facts[:6] if narrative_section is not None else ([f"conviction_score={strategic_narrative.conviction_score:.2f}", f"fragility_score={strategic_narrative.fragility_score:.2f}"] + [f"{item.driver_kind}:{item.trust_bias}:rank={item.rank_score:.2f}:{item.title}" for item in strategic_narrative.items[:4]])[:6] if strategic_narrative is not None else []),
                operator_actions=(narrative_section.operator_actions[:3] if narrative_section is not None else strategic_narrative.operator_actions[:3] if strategic_narrative is not None else ["emit a strategic narrative report to explain what is actually driving conviction"]),
                provenance_refs=([f"strategic_narrative:{strategic_narrative.schema_version}"] if strategic_narrative is not None else [f"strategic_briefing:{strategic_briefing.schema_version}"]),
            )
        )
        if strategic_memory_horizon is not None:
            sections.append(
                OracleBriefingSection(
                    section_id="belief_drift_timeline",
                    title="Belief Drift Timeline",
                    status=strategic_memory_horizon.drift_state,
                    summary_line=strategic_memory_horizon.summary_line,
                    facts=([f"conviction_delta={strategic_memory_horizon.conviction_score_delta:+.2f}", f"fragility_delta={strategic_memory_horizon.fragility_score_delta:+.2f}", f"history_integrity={strategic_memory_horizon.history_integrity_status}", f"sealed_history={strategic_memory_horizon.sealed_history_observation_count}", f"rising_driver={strategic_memory_horizon.strongest_rising_driver_kind or 'none'}", f"falling_driver={strategic_memory_horizon.strongest_falling_driver_kind or 'none'}"] + [f"{point.generated_at_utc.isoformat()}:{point.conviction_state}:driver={point.top_driver_kind or 'none'}:score={point.conviction_score:.2f}" for point in strategic_memory_horizon.points[-4:]])[:8],
                    operator_actions=strategic_memory_horizon.operator_actions[:3],
                    provenance_refs=[f"strategic_memory_horizon:{strategic_memory_horizon.schema_version}"],
                )
            )
        else:
            sections.append(
                OracleBriefingSection(
                    section_id="belief_drift_timeline",
                    title="Belief Drift Timeline",
                    status="UNKNOWN",
                    summary_line="No strategic memory horizon report was available, so conviction drift across recent cycles could not be summarized.",
                    facts=[],
                    operator_actions=["emit a strategic memory horizon report to track belief drift and changing driver dominance over time"],
                    provenance_refs=[],
                )
            )
        sections.append(
            OracleBriefingSection(
                section_id="opportunity_queue",
                title="Opportunity Queue",
                status=(opportunity_section.status if opportunity_section is not None else "QUIET"),
                summary_line=(opportunity_section.summary_line if opportunity_section is not None else "No strategic opportunity queue section was present in the latest strategic briefing."),
                facts=(opportunity_section.facts[:6] if opportunity_section is not None else []),
                operator_actions=(opportunity_section.operator_actions[:3] if opportunity_section is not None else ["emit a fresh strategic briefing to populate the opportunity queue"]),
                provenance_refs=[f"strategic_briefing:{strategic_briefing.schema_version}"],
            )
        )
    else:
        sections.append(
            OracleBriefingSection(
                section_id="strategic_posture",
                title="Strategic Posture",
                status="UNKNOWN",
                summary_line="Strategic Posture could not be derived because no strategic briefing report was available.",
                facts=[],
                operator_actions=["emit a strategic briefing to enrich the canonical morning pack"],
                provenance_refs=[],
            )
        )
        if strategic_narrative is not None:
            sections.append(
                OracleBriefingSection(
                    section_id="strategic_narrative",
                    title="Strategic Narrative",
                    status=strategic_narrative.conviction_state,
                    summary_line=strategic_narrative.summary_line,
                    facts=([f"conviction_score={strategic_narrative.conviction_score:.2f}", f"fragility_score={strategic_narrative.fragility_score:.2f}"] + [f"{item.driver_kind}:{item.trust_bias}:rank={item.rank_score:.2f}:{item.title}" for item in strategic_narrative.items[:4]])[:6],
                    operator_actions=strategic_narrative.operator_actions[:3],
                    provenance_refs=[f"strategic_narrative:{strategic_narrative.schema_version}"],
                )
            )
        else:
            sections.append(
                OracleBriefingSection(
                    section_id="strategic_narrative",
                    title="Strategic Narrative",
                    status="UNKNOWN",
                    summary_line="Strategic Narrative could not be derived because no strategic narrative report was available.",
                    facts=[],
                    operator_actions=["emit a strategic narrative report to explain what is driving conviction"],
                    provenance_refs=[],
                )
            )
        if strategic_memory_horizon is not None:
            sections.append(
                OracleBriefingSection(
                    section_id="belief_drift_timeline",
                    title="Belief Drift Timeline",
                    status=strategic_memory_horizon.drift_state,
                    summary_line=strategic_memory_horizon.summary_line,
                    facts=([f"conviction_delta={strategic_memory_horizon.conviction_score_delta:+.2f}", f"fragility_delta={strategic_memory_horizon.fragility_score_delta:+.2f}", f"history_integrity={strategic_memory_horizon.history_integrity_status}", f"sealed_history={strategic_memory_horizon.sealed_history_observation_count}", f"rising_driver={strategic_memory_horizon.strongest_rising_driver_kind or 'none'}", f"falling_driver={strategic_memory_horizon.strongest_falling_driver_kind or 'none'}"] + [f"{point.generated_at_utc.isoformat()}:{point.conviction_state}:driver={point.top_driver_kind or 'none'}:score={point.conviction_score:.2f}" for point in strategic_memory_horizon.points[-4:]])[:8],
                    operator_actions=strategic_memory_horizon.operator_actions[:3],
                    provenance_refs=[f"strategic_memory_horizon:{strategic_memory_horizon.schema_version}"],
                )
            )
        else:
            sections.append(
                OracleBriefingSection(
                    section_id="belief_drift_timeline",
                    title="Belief Drift Timeline",
                    status="UNKNOWN",
                    summary_line="No strategic memory horizon report was available, so conviction drift across recent cycles could not be summarized.",
                    facts=[],
                    operator_actions=["emit a strategic memory horizon report to track belief drift and changing driver dominance over time"],
                    provenance_refs=[],
                )
            )
        sections.append(
            OracleBriefingSection(
                section_id="opportunity_queue",
                title="Opportunity Queue",
                status="UNKNOWN",
                summary_line="Opportunity Queue could not be derived because no strategic briefing report was available.",
                facts=[],
                operator_actions=["emit a strategic briefing to enrich the canonical morning pack"],
                provenance_refs=[],
            )
        )

    if strategy_cohort is not None:
        sections.append(
            OracleBriefingSection(
                section_id="strategy_cohorts",
                title="Strategy Cohorts",
                status=(strategy_cohort.items[0].cohort_bucket if strategy_cohort.items else "UNKNOWN"),
                summary_line=strategy_cohort.summary_line,
                facts=[
                    f"{item.strategy_id}:{item.cohort_bucket}:rank={item.cohort_rank_score:.2f}:floor={item.scenario_downside_floor:.2f}"
                    for item in strategy_cohort.items[:6]
                ],
                operator_actions=strategy_cohort.operator_actions[:3],
                provenance_refs=[f"strategy_cohort:{strategy_cohort.schema_version}"],
            )
        )
    else:
        sections.append(
            OracleBriefingSection(
                section_id="strategy_cohorts",
                title="Strategy Cohorts",
                status="UNKNOWN",
                summary_line="No strategy cohort report was available, so resilience-ranked cohorts could not be summarized.",
                facts=[],
                operator_actions=["emit a strategy cohort report to compare resilience across the active strategy universe"],
                provenance_refs=[],
            )
        )

    if thesis_memory is not None:
        sections.append(
            OracleBriefingSection(
                section_id="thesis_evolution",
                title="Thesis Evolution",
                status=("UNDER_REVIEW" if thesis_memory.weakening_thesis_ids else "STRENGTHENING" if thesis_memory.strengthening_thesis_ids else "STABLE"),
                summary_line=thesis_memory.summary_line,
                facts=[
                    f"{item.thesis_id}:{item.current_state}:{item.evolution_state}:confidence={item.confidence_score:.2f}"
                    for item in thesis_memory.items[:6]
                ],
                operator_actions=thesis_memory.operator_actions[:3],
                provenance_refs=[f"thesis_memory:{thesis_memory.schema_version}"],
            )
        )
    else:
        sections.append(
            OracleBriefingSection(
                section_id="thesis_evolution",
                title="Thesis Evolution",
                status="UNKNOWN",
                summary_line="No thesis memory report was available, so belief evolution could not be summarized.",
                facts=[],
                operator_actions=["emit a thesis memory report to make strategic belief shifts replayable"],
                provenance_refs=[],
            )
        )

    if thesis_graph is not None:
        sections.append(
            OracleBriefingSection(
                section_id="thesis_graph",
                title="Thesis Dependency Graph",
                status=("CASCADE_RISK" if thesis_graph.nodes and thesis_graph.nodes[0].cascade_risk_score >= 0.70 else "CONNECTED"),
                summary_line=thesis_graph.summary_line,
                facts=[
                    f"{item.node_id}:{item.node_kind}:{item.status}:risk={item.cascade_risk_score:.2f}:links={len(item.connected_node_ids)}"
                    for item in thesis_graph.nodes[:6]
                ],
                operator_actions=thesis_graph.operator_actions[:3],
                provenance_refs=[f"thesis_graph:{thesis_graph.schema_version}"],
            )
        )
    else:
        sections.append(
            OracleBriefingSection(
                section_id="thesis_graph",
                title="Thesis Dependency Graph",
                status="UNKNOWN",
                summary_line="No thesis graph report was available, so cascade dependencies across theses, doctrine, and strategy cohorts could not be summarized.",
                facts=[],
                operator_actions=["emit a thesis graph report to see which weakening nodes are driving wider strategic cascades"],
                provenance_refs=[],
            )
        )

    if strategic_tensions is not None:
        sections.append(
            OracleBriefingSection(
                section_id="strategic_tensions",
                title="Strategic Tensions",
                status=(strategic_tensions.items[0].alignment_state if strategic_tensions.items else "CLEAR"),
                summary_line=strategic_tensions.summary_line,
                facts=[
                    f"{item.tension_kind}:{item.alignment_state}:severity={item.severity_score:.2f}:{item.title}"
                    for item in strategic_tensions.items[:6]
                ],
                operator_actions=strategic_tensions.operator_actions[:3],
                provenance_refs=[f"strategic_tensions:{strategic_tensions.schema_version}"],
            )
        )
    else:
        sections.append(
            OracleBriefingSection(
                section_id="strategic_tensions",
                title="Strategic Tensions",
                status="UNKNOWN",
                summary_line="No strategic tension report was available, so contradictions and consensus conflicts across the strategic stack could not be summarized.",
                facts=[],
                operator_actions=["emit a strategic tension report to surface which strategic layers disagree or align too dangerously"],
                provenance_refs=[],
            )
        )


    if contradiction_resolution is not None:
        sections.append(
            OracleBriefingSection(
                section_id="contradiction_resolution",
                title="Contradiction Resolution",
                status=(contradiction_resolution.items[0].resolution_kind if contradiction_resolution.items else "CLEAR"),
                summary_line=contradiction_resolution.summary_line,
                facts=([f"conviction_state={contradiction_resolution.conviction_state}", f"drift_state={contradiction_resolution.drift_state}", f"history_integrity={contradiction_resolution.history_integrity_status}"] + [f"{item.resolution_kind}:priority={item.resolution_priority_score:.2f}:gain={item.expected_conviction_gain_score:.2f}:{item.title}" for item in contradiction_resolution.items[:4]])[:6],
                operator_actions=contradiction_resolution.operator_actions[:4],
                provenance_refs=[f"contradiction_resolution:{contradiction_resolution.schema_version}"],
            )
        )

    if intervention_simulation is not None:
        sections.append(
            OracleBriefingSection(
                section_id="intervention_simulation",
                title="Intervention Simulation",
                status=(intervention_simulation.items[0].projected_conviction_state if intervention_simulation.items else intervention_simulation.baseline_conviction_state),
                summary_line=intervention_simulation.summary_line,
                preferred_strategic_backing_source=intervention_simulation.preferred_strategic_backing_source,
                preferred_strategic_backing_classification=intervention_simulation.preferred_strategic_backing_classification,
                facts=(([
                    f"baseline_conviction={intervention_simulation.baseline_conviction_state}:{intervention_simulation.baseline_conviction_score:.2f}",
                    f"baseline_fragility={intervention_simulation.baseline_fragility_score:.2f}",
                    f"baseline_drift={intervention_simulation.baseline_drift_state}",
                ] + [
                    f"{item.intervention_kind}:gain={item.projected_conviction_gain_score:.2f}:queue_relief={item.projected_queue_pressure_relief_score:.2f}:{item.title}"
                    for item in intervention_simulation.items[:4]
                ])[:8]) + _evidence_facts(intervention_simulation_evidence),
                operator_actions=intervention_simulation.operator_actions[:4],
                provenance_refs=[f"intervention_simulation:{intervention_simulation.schema_version}", *([f"strategic_artifact_evidence:{intervention_simulation_evidence['artifact_kind']}"] if intervention_simulation_evidence else [])],
            )
        )

    if strategic_campaigns is not None:
        sections.append(
            OracleBriefingSection(
                section_id="strategic_campaigns",
                title="Strategic Campaigns",
                status=(strategic_campaigns.items[0].objective_kind if strategic_campaigns.items else "CLEAR"),
                summary_line=strategic_campaigns.summary_line,
                preferred_strategic_backing_source=strategic_campaigns.preferred_strategic_backing_source,
                preferred_strategic_backing_classification=strategic_campaigns.preferred_strategic_backing_classification,
                facts=(([
                    f"baseline_conviction={strategic_campaigns.baseline_conviction_state}:{strategic_campaigns.baseline_conviction_score:.2f}",
                    f"baseline_fragility={strategic_campaigns.baseline_fragility_score:.2f}",
                ] + [
                    f"{item.objective_kind}:priority={item.priority_score:.2f}:steps={len(item.steps)}:{item.title}"
                    for item in strategic_campaigns.items[:4]
                ])[:8]) + _evidence_facts(strategic_campaigns_evidence),
                operator_actions=strategic_campaigns.operator_actions[:4],
                provenance_refs=[f"strategic_campaigns:{strategic_campaigns.schema_version}", *([f"strategic_artifact_evidence:{strategic_campaigns_evidence['artifact_kind']}"] if strategic_campaigns_evidence else [])],
            )
        )

    if campaign_execution is not None:
        sections.append(
            OracleBriefingSection(
                section_id="campaign_execution",
                title="Campaign Execution",
                status=(campaign_execution.items[0].execution_state if campaign_execution.items else "QUEUED"),
                summary_line=campaign_execution.summary_line,
                preferred_strategic_backing_source=campaign_execution.preferred_strategic_backing_source,
                preferred_strategic_backing_classification=campaign_execution.preferred_strategic_backing_classification,
                facts=((
                    [
                        f"baseline_conviction={campaign_execution.baseline_conviction_state}:{campaign_execution.baseline_conviction_score:.2f}",
                        f"baseline_fragility={campaign_execution.baseline_fragility_score:.2f}",
                        f"history_integrity={campaign_execution.history_integrity_status}",
                        f"active={','.join(campaign_execution.active_campaign_ids) if campaign_execution.active_campaign_ids else 'none'}",
                        f"blocked={','.join(campaign_execution.blocked_campaign_ids) if campaign_execution.blocked_campaign_ids else 'none'}",
                        f"drifting={','.join(campaign_execution.drifting_campaign_ids) if campaign_execution.drifting_campaign_ids else 'none'}",
                    ] + [
                        f"{item.execution_state}:progress={item.progress_score:.2f}:blocker={item.blocker_score:.2f}:{item.title}"
                        for item in campaign_execution.items[:4]
                    ]
                )[:8]) + _evidence_facts(campaign_execution_evidence),
                operator_actions=campaign_execution.operator_actions[:4],
                provenance_refs=[f"campaign_execution:{campaign_execution.schema_version}", *([f"strategic_artifact_evidence:{campaign_execution_evidence['artifact_kind']}"] if campaign_execution_evidence else [])],
            )
        )

    if scenario_lab is not None:
        downside = next((item for item in scenario_lab.scenarios if item.scenario_id == scenario_lab.highest_downside_scenario_id), None)
        upside = next((item for item in scenario_lab.scenarios if item.scenario_id == scenario_lab.highest_upside_scenario_id), None)
        facts = []
        if downside is not None:
            facts.append(f"downside={downside.scenario_id}:{downside.resulting_strategic_posture}:caution_delta={downside.caution_delta:+.2f}")
        if upside is not None:
            facts.append(f"upside={upside.scenario_id}:{upside.resulting_strategic_posture}:opportunity_delta={upside.opportunity_delta:+.2f}")
        facts.extend(f"{item.scenario_id}:{item.transition_classification}:{item.leading_queue_kind or 'NONE'}" for item in scenario_lab.scenarios[:4])
        sections.append(
            OracleBriefingSection(
                section_id="scenario_lab",
                title="Scenario Lab",
                status=("DOWNSIDE_PRESSURE" if downside is not None and downside.caution_delta > 0.10 else "UPSIDE_OPTIONALITY" if upside is not None and upside.opportunity_delta > 0.08 else "BALANCED_SCENARIOS"),
                summary_line=scenario_lab.summary_line,
                facts=_unique(facts)[:8],
                operator_actions=scenario_lab.operator_actions[:3],
                provenance_refs=[f"scenario_lab:{scenario_lab.schema_version}"],
            )
        )
    else:
        sections.append(
            OracleBriefingSection(
                section_id="scenario_lab",
                title="Scenario Lab",
                status="UNKNOWN",
                summary_line="No scenario lab report was available, so counterfactual futures could not be summarized.",
                facts=[],
                operator_actions=["emit a scenario lab report to stress-test the strategic posture before acting on it"],
                provenance_refs=[],
            )
        )

    if doctrine_adaptation is not None:
        sections.append(
            OracleBriefingSection(
                section_id="doctrine_adaptation",
                title="Doctrine Adaptation",
                status=("FREEZE" if doctrine_adaptation.freeze_recommended else doctrine_adaptation.items[0].adaptation_state if doctrine_adaptation.items else "MONITOR"),
                summary_line=doctrine_adaptation.summary_line,
                preferred_strategic_backing_source=doctrine_adaptation.preferred_strategic_backing_source,
                preferred_strategic_backing_classification=doctrine_adaptation.preferred_strategic_backing_classification,
                facts=[
                    f"{item.clause_id}:{item.adaptation_state}:stress={item.stress_score:.2f}:priority={item.review_priority_score:.2f}"
                    for item in doctrine_adaptation.items[:6]
                ] + _evidence_facts(doctrine_adaptation_evidence),
                operator_actions=doctrine_adaptation.operator_actions[:3],
                provenance_refs=[f"doctrine_adaptation:{doctrine_adaptation.schema_version}", *([f"strategic_artifact_evidence:{doctrine_adaptation_evidence['artifact_kind']}"] if doctrine_adaptation_evidence else [])],
            )
        )
    else:
        sections.append(
            OracleBriefingSection(
                section_id="doctrine_adaptation",
                title="Doctrine Adaptation",
                status="UNKNOWN",
                summary_line="No doctrine adaptation report was available, so clause-level adaptation guidance could not be summarized.",
                facts=[],
                operator_actions=["emit a doctrine adaptation report to translate doctrine pressure into concrete review or freeze guidance"],
                provenance_refs=[],
            )
        )

    if research_priorities is not None:
        sections.append(
            OracleBriefingSection(
                section_id="research_priorities",
                title="Research Priorities",
                status=(research_priorities.items[0].priority_kind if research_priorities.items else "UNKNOWN"),
                summary_line=research_priorities.summary_line,
                preferred_strategic_backing_source=research_priorities.preferred_strategic_backing_source,
                preferred_strategic_backing_classification=research_priorities.preferred_strategic_backing_classification,
                facts=[
                    f"{item.priority_kind}:{item.title}:urgency={item.urgency_score:.2f}"
                    for item in research_priorities.items[:6]
                ] + _evidence_facts(research_priorities_evidence),
                operator_actions=research_priorities.operator_actions[:4],
                provenance_refs=[f"research_priorities:{research_priorities.schema_version}", *([f"strategic_artifact_evidence:{research_priorities_evidence['artifact_kind']}"] if research_priorities_evidence else [])],
            )
        )
    else:
        sections.append(
            OracleBriefingSection(
                section_id="research_priorities",
                title="Research Priorities",
                status="UNKNOWN",
                summary_line="No research priority report was available, so the next ranked investigation plan could not be summarized.",
                facts=[],
                operator_actions=["emit a research priority report to rank the next strategic investigations"],
                provenance_refs=[],
            )
        )

    if research_execution_memory is not None:
        sections.append(
            OracleBriefingSection(
                section_id="investigation_outcomes",
                title="Investigation Outcomes",
                status=(research_execution_memory.items[0].outcome_disposition or research_execution_memory.items[0].execution_state if research_execution_memory.items else "UNKNOWN"),
                summary_line=research_execution_memory.summary_line,
                facts=[
                    f"{item.priority_id}:{item.execution_state}:{item.outcome_disposition or 'NONE'}:impact={item.confidence_impact:+.2f}"
                    for item in research_execution_memory.items[:6]
                ],
                operator_actions=research_execution_memory.operator_actions[:4],
                provenance_refs=[f"research_execution_memory:{research_execution_memory.schema_version}"],
            )
        )
    else:
        sections.append(
            OracleBriefingSection(
                section_id="investigation_outcomes",
                title="Investigation Outcomes",
                status="UNKNOWN",
                summary_line="No research execution memory report was available, so completed and escalated investigation outcomes could not be summarized.",
                facts=[],
                operator_actions=["emit a research execution memory report to keep investigation outcomes replayable across strategic cycles"],
                provenance_refs=[],
            )
        )

    lineage_section = _find_section(status_pack, "lineage")
    sections.append(
        OracleBriefingSection(
            section_id="doctrine_posture",
            title="Doctrine Posture",
            status=lineage_section.status if lineage_section is not None else "UNKNOWN",
            summary_line=(lineage_section.summary_line if lineage_section is not None else "Doctrine lineage state was unavailable in the status pack."),
            exact_feedback_confirmation_count=(lineage_section.exact_feedback_confirmation_count if lineage_section is not None else 0),
            exact_feedback_relief_count=(lineage_section.exact_feedback_relief_count if lineage_section is not None else 0),
            exact_cadence_signal_classification=(lineage_section.exact_cadence_signal_classification if lineage_section is not None else "AMBIENT_DRIFT"),
            facts=(lineage_section.facts[:5] if lineage_section is not None else []),
            operator_actions=(lineage_section.operator_actions[:3] if lineage_section is not None else ["repair doctrine lineage before constitutional reliance"]),
            provenance_refs=[f"status_pack:{status_pack.provenance_digest_sha256}"],
        )
    )

    closure_section = _find_section(status_pack, "closure_attestation")
    sections.append(
        OracleBriefingSection(
            section_id="closure_posture",
            title="Closure Posture",
            status=closure_section.status if closure_section is not None else "UNKNOWN",
            summary_line=(closure_section.summary_line if closure_section is not None else "Closure attestation state was unavailable in the status pack."),
            exact_feedback_confirmation_count=(closure_section.exact_feedback_confirmation_count if closure_section is not None else 0),
            exact_feedback_relief_count=(closure_section.exact_feedback_relief_count if closure_section is not None else 0),
            exact_cadence_signal_classification=(closure_section.exact_cadence_signal_classification if closure_section is not None else "AMBIENT_DRIFT"),
            facts=(closure_section.facts[:5] if closure_section is not None else []),
            operator_actions=(closure_section.operator_actions[:3] if closure_section is not None else ["emit a fresh closure snapshot before release review"]),
            provenance_refs=[f"status_pack:{status_pack.provenance_digest_sha256}"],
        )
    )


    open_risks: list[str] = []
    risk_actions: list[str] = []
    for section in status_pack.sections:
        if section.status not in {"VERIFIED", "FULLY_SEALED", "APPROVED", "ACCEPTED", "TRUSTED"}:
            open_risks.append(section.summary_line)
            risk_actions.extend(section.operator_actions)
    if incident_pack is not None and incident_pack.primary_diagnostic is not None:
        open_risks.extend(incident_pack.primary_diagnostic.reasons)
        risk_actions.extend(incident_pack.primary_diagnostic.operator_actions)
    if thesis_memory is not None:
        open_risks.extend(item.summary_line for item in thesis_memory.items if item.current_state in {"AT_RISK", "BROKEN"})
        risk_actions.extend(item.recommended_research_action for item in thesis_memory.items if item.current_state in {"AT_RISK", "BROKEN"})
    sections.append(
        OracleBriefingSection(
            section_id="open_risks",
            title="Open Risks",
            status="OPEN" if open_risks else "CLEAR",
            summary_line=(open_risks[0] if open_risks else f"No additional open risks were surfaced by the canonical status pack; {cadence_summary}."),
            exact_feedback_confirmation_count=status_pack.exact_feedback_confirmation_count,
            exact_feedback_relief_count=status_pack.exact_feedback_relief_count,
            exact_cadence_signal_classification=cadence_signal,
            facts=_unique([*open_risks[:8], f"exact_cadence_signal_classification={cadence_signal}", f"exact_feedback_confirmation_count={status_pack.exact_feedback_confirmation_count}", f"exact_feedback_relief_count={status_pack.exact_feedback_relief_count}", f"cadence_pressure_summary={cadence_summary}"]),
            operator_actions=_unique(risk_actions)[:5],
            provenance_refs=_unique([
                f"status_pack:{status_pack.provenance_digest_sha256}",
                *([f"incident_pack:{incident_pack.provenance_digest_sha256}"] if incident_pack is not None else []),
                *([f"thesis_memory:{thesis_memory.schema_version}"] if thesis_memory is not None else []),
            ]),
        )
    )

    exception_summary = (
        f"Active governed exceptions: {', '.join(status_pack.active_governed_exception_ids)}"
        if status_pack.active_governed_exception_ids
        else "No active governed exceptions were detected in the canonical status pack."
    )
    sections.append(
        OracleBriefingSection(
            section_id="active_exceptions",
            title="Active Exceptions",
            status="ACTIVE" if status_pack.active_governed_exception_ids else "NONE",
            summary_line=f"{exception_summary} Also, {cadence_summary}.",
            exact_feedback_confirmation_count=status_pack.exact_feedback_confirmation_count,
            exact_feedback_relief_count=status_pack.exact_feedback_relief_count,
            exact_cadence_signal_classification=cadence_signal,
            facts=[f"exception_id={item}" for item in status_pack.active_governed_exception_ids] + [f"exact_cadence_signal_classification={cadence_signal}", f"exact_feedback_confirmation_count={status_pack.exact_feedback_confirmation_count}", f"exact_feedback_relief_count={status_pack.exact_feedback_relief_count}"],
            operator_actions=[
                "reconfirm each governed exception against closure posture before relying on it"
            ]
            if status_pack.active_governed_exception_ids
            else [
                "continue without governed exceptions unless constitutional policy explicitly requires one"
            ],
            provenance_refs=[f"status_pack:{status_pack.provenance_digest_sha256}"],
        )
    )

    return sections


def _build_oracle_briefing_pack_impl(
    *,
    repo_root: Path,
    search_root: Path | None = None,
    derived_view_report_path: Path | None = None,
    constitutional_gate_report_path: Path | None = None,
    closure_snapshot_path: Path | None = None,
    closure_dsse_path: Path | None = None,
    closure_public_key_path: Path | None = None,
    governed_exception_memo_path: Path | None = None,
    governed_exception_dsse_path: Path | None = None,
    governed_exception_public_key_path: Path | None = None,
    strategic_briefing_report_path: Path | None = None,
    strategic_narrative_report_path: Path | None = None,
    strategic_memory_horizon_report_path: Path | None = None,
    contradiction_resolution_report_path: Path | None = None,
    strategic_intervention_report_path: Path | None = None,
    strategic_campaign_report_path: Path | None = None,
    strategic_campaign_execution_report_path: Path | None = None,
    thesis_memory_report_path: Path | None = None,
    strategy_cohort_report_path: Path | None = None,
    doctrine_adaptation_report_path: Path | None = None,
    research_priority_report_path: Path | None = None,
    research_execution_memory_report_path: Path | None = None,
    thesis_graph_report_path: Path | None = None,
    strategic_tension_report_path: Path | None = None,
) -> OracleBriefingPackReport:
    resolved_repo_root = repo_root.resolve()
    resolved_search_root = (search_root or (resolved_repo_root / "docs" / "artifacts")).resolve()
    derived_view_report_path = _resolve_briefing_derived_view_path(
        search_root=resolved_search_root,
        repo_root=resolved_repo_root,
        explicit_path=derived_view_report_path,
    )
    strategic_briefing_report_path = strategic_briefing_report_path or _find_latest(resolved_search_root, {"ORACLE_STRATEGIC_BRIEFING_REPORT.json"})
    strategic_narrative_report_path = strategic_narrative_report_path or _find_latest(resolved_search_root, {"ORACLE_STRATEGIC_NARRATIVE_REPORT.json"})
    strategic_memory_horizon_report_path = strategic_memory_horizon_report_path or _find_latest(resolved_search_root, {"ORACLE_STRATEGIC_MEMORY_HORIZON_REPORT.json"})
    contradiction_resolution_report_path = contradiction_resolution_report_path or _find_latest(resolved_search_root, {"ORACLE_CONTRADICTION_RESOLUTION_REPORT.json"})
    strategic_intervention_report_path = strategic_intervention_report_path or _find_latest(resolved_search_root, {"ORACLE_STRATEGIC_INTERVENTION_REPORT.json"})
    strategic_campaign_report_path = strategic_campaign_report_path or _find_latest(resolved_search_root, {"ORACLE_STRATEGIC_CAMPAIGN_REPORT.json"})
    strategic_campaign_execution_report_path = strategic_campaign_execution_report_path or _find_latest(resolved_search_root, {"ORACLE_STRATEGIC_CAMPAIGN_EXECUTION_REPORT.json"})
    thesis_memory_report_path = thesis_memory_report_path or _find_latest(resolved_search_root, {"ORACLE_THESIS_MEMORY_REPORT.json"})
    strategy_cohort_report_path = strategy_cohort_report_path or _find_latest(resolved_search_root, {"ORACLE_STRATEGY_COHORT_REPORT.json"})
    doctrine_adaptation_report_path = doctrine_adaptation_report_path or _find_latest(resolved_search_root, {"ORACLE_DOCTRINE_ADAPTATION_REPORT.json"})
    research_priority_report_path = research_priority_report_path or _find_latest(resolved_search_root, {"ORACLE_RESEARCH_PRIORITY_REPORT.json"})
    research_execution_memory_report_path = research_execution_memory_report_path or _find_latest(resolved_search_root, {"ORACLE_RESEARCH_EXECUTION_MEMORY_REPORT.json"})
    thesis_graph_report_path = thesis_graph_report_path or _find_latest(resolved_search_root, {"ORACLE_THESIS_GRAPH_REPORT.json"})
    strategic_tension_report_path = strategic_tension_report_path or _find_latest(resolved_search_root, {"ORACLE_STRATEGIC_TENSION_REPORT.json"})
    scenario_lab_report_path = _find_latest(resolved_search_root, {"ORACLE_SCENARIO_LAB_REPORT.json"})
    status_pack = build_oracle_status_pack(
        repo_root=resolved_repo_root,
        search_root=resolved_search_root,
        derived_view_report_path=derived_view_report_path,
        constitutional_gate_report_path=constitutional_gate_report_path,
        closure_snapshot_path=closure_snapshot_path,
        closure_dsse_path=closure_dsse_path,
        closure_public_key_path=closure_public_key_path,
        governed_exception_memo_path=governed_exception_memo_path,
        governed_exception_dsse_path=governed_exception_dsse_path,
        governed_exception_public_key_path=governed_exception_public_key_path,
    )
    incident_pack = None
    if status_pack.trust_status != "TRUSTED":
        incident_pack = build_oracle_incident_pack(
            repo_root=resolved_repo_root,
            search_root=resolved_search_root,
            derived_view_report_path=derived_view_report_path,
            constitutional_gate_report_path=constitutional_gate_report_path,
            closure_snapshot_path=closure_snapshot_path,
            closure_dsse_path=closure_dsse_path,
            closure_public_key_path=closure_public_key_path,
            governed_exception_memo_path=governed_exception_memo_path,
            governed_exception_dsse_path=governed_exception_dsse_path,
            governed_exception_public_key_path=governed_exception_public_key_path,
        )
    derived_view = _load_derived_view(derived_view_report_path)
    strategic_briefing = _load_strategic_briefing(strategic_briefing_report_path)
    strategic_narrative = _load_strategic_narrative(strategic_narrative_report_path)
    strategic_memory_horizon = _load_strategic_memory_horizon(strategic_memory_horizon_report_path)
    contradiction_resolution = _load_contradiction_resolution(contradiction_resolution_report_path)
    intervention_simulation = _load_strategic_intervention(strategic_intervention_report_path)
    strategic_campaigns = _load_strategic_campaign(strategic_campaign_report_path)
    campaign_execution = _load_strategic_campaign_execution(strategic_campaign_execution_report_path)
    thesis_memory = _load_thesis_memory(thesis_memory_report_path)
    strategy_cohort = _load_strategy_cohort(strategy_cohort_report_path)
    doctrine_adaptation = _load_doctrine_adaptation(doctrine_adaptation_report_path)
    research_priorities = _load_research_priorities(research_priority_report_path)
    research_execution_memory = _load_research_execution_memory(research_execution_memory_report_path)
    thesis_graph = _load_thesis_graph(thesis_graph_report_path)
    strategic_tensions = _load_strategic_tensions(strategic_tension_report_path)
    scenario_lab = _load_scenario_lab(scenario_lab_report_path)
    doctrine_adaptation_evidence = discover_preferred_strategic_artifact_evidence(report_path=doctrine_adaptation_report_path, repo_root=resolved_repo_root, search_root=resolved_search_root) if doctrine_adaptation_report_path is not None and doctrine_adaptation_report_path.exists() else None
    research_priorities_evidence = discover_preferred_strategic_artifact_evidence(report_path=research_priority_report_path, repo_root=resolved_repo_root, search_root=resolved_search_root) if research_priority_report_path is not None and research_priority_report_path.exists() else None
    intervention_simulation_evidence = discover_preferred_strategic_artifact_evidence(report_path=strategic_intervention_report_path, repo_root=resolved_repo_root, search_root=resolved_search_root) if strategic_intervention_report_path is not None and strategic_intervention_report_path.exists() else None
    strategic_campaigns_evidence = discover_preferred_strategic_artifact_evidence(report_path=strategic_campaign_report_path, repo_root=resolved_repo_root, search_root=resolved_search_root) if strategic_campaign_report_path is not None and strategic_campaign_report_path.exists() else None
    campaign_execution_evidence = discover_preferred_strategic_artifact_evidence(report_path=strategic_campaign_execution_report_path, repo_root=resolved_repo_root, search_root=resolved_search_root) if strategic_campaign_execution_report_path is not None and strategic_campaign_execution_report_path.exists() else None
    sections = _briefing_sections(
        status_pack=status_pack,
        incident_pack=incident_pack,
        derived_view=derived_view,
        strategic_briefing=strategic_briefing,
        strategic_narrative=strategic_narrative,
        strategic_memory_horizon=strategic_memory_horizon,
        contradiction_resolution=contradiction_resolution,
        intervention_simulation=intervention_simulation,
        strategic_campaigns=strategic_campaigns,
        campaign_execution=campaign_execution,
        strategy_cohort=strategy_cohort,
        thesis_memory=thesis_memory,
        doctrine_adaptation=doctrine_adaptation,
        research_priorities=research_priorities,
        research_execution_memory=research_execution_memory,
        thesis_graph=thesis_graph,
        strategic_tensions=strategic_tensions,
        scenario_lab=scenario_lab,
        doctrine_adaptation_evidence=doctrine_adaptation_evidence,
        research_priorities_evidence=research_priorities_evidence,
        intervention_simulation_evidence=intervention_simulation_evidence,
        strategic_campaigns_evidence=strategic_campaigns_evidence,
        campaign_execution_evidence=campaign_execution_evidence,
    )
    operator_actions = _unique([action for section in sections for action in section.operator_actions] + status_pack.operator_actions)
    if incident_pack is not None:
        operator_actions = _unique(operator_actions + incident_pack.recommended_next_actions)
    policy_version, policy_sha256, policy_path = oracle_policy_sha256(repo_root=resolved_repo_root)
    policy_artifact, _ = load_oracle_policy(repo_root=resolved_repo_root)
    cadence_signal, cadence_summary = _exact_cadence_summary(
        exact_feedback_confirmation_count=status_pack.exact_feedback_confirmation_count,
        exact_feedback_relief_count=status_pack.exact_feedback_relief_count,
    )
    artifact_freshness = [
        build_freshness_item(artifact_label="status_pack", generated_at_utc=status_pack.generated_at_utc, as_of_utc=_utc_now(), fresh_hours=24.0, aging_hours=72.0),
    ]
    if incident_pack is not None:
        artifact_freshness.append(build_freshness_item(artifact_label="incident_pack", generated_at_utc=incident_pack.generated_at_utc, as_of_utc=_utc_now(), fresh_hours=24.0, aging_hours=72.0))
    for label, model, source_path in [
        ("derived_view", derived_view, derived_view_report_path),
        ("strategic_briefing", strategic_briefing, strategic_briefing_report_path),
        ("strategic_narrative", strategic_narrative, strategic_narrative_report_path),
        ("strategic_memory_horizon", strategic_memory_horizon, strategic_memory_horizon_report_path),
        ("contradiction_resolution", contradiction_resolution, contradiction_resolution_report_path),
        ("strategic_intervention", intervention_simulation, strategic_intervention_report_path),
        ("strategic_campaign", strategic_campaigns, strategic_campaign_report_path),
        ("campaign_execution", campaign_execution, strategic_campaign_execution_report_path),
        ("thesis_memory", thesis_memory, thesis_memory_report_path),
        ("strategy_cohort", strategy_cohort, strategy_cohort_report_path),
        ("doctrine_adaptation", doctrine_adaptation, doctrine_adaptation_report_path),
        ("research_priorities", research_priorities, research_priority_report_path),
        ("research_execution_memory", research_execution_memory, research_execution_memory_report_path),
        ("thesis_graph", thesis_graph, thesis_graph_report_path),
        ("strategic_tensions", strategic_tensions, strategic_tension_report_path),
        ("scenario_lab", scenario_lab, scenario_lab_report_path),
    ]:
        if model is not None:
            artifact_freshness.append(build_freshness_item(artifact_label=label, generated_at_utc=getattr(model, "generated_at_utc", None), as_of_utc=_utc_now(), source_path=source_path, fresh_hours=72.0, aging_hours=168.0))
    evidence_freshness_status, stale_artifact_count, freshness_summary_line = summarize_freshness(artifact_freshness)
    artifact_lineage = [
        build_lineage_item_from_model(artifact_label="oracle_policy", artifact_role="POLICY", model=policy_artifact, source_path=policy_path, integrity_status="VERIFIED"),
        build_lineage_item(artifact_label="status_pack", artifact_role="STATUS", schema_version=status_pack.schema_version, integrity_status="NOT_APPLICABLE"),
    ]
    if incident_pack is not None:
        artifact_lineage.append(build_lineage_item(artifact_label="incident_pack", artifact_role="INCIDENT", schema_version=incident_pack.schema_version, integrity_status="NOT_APPLICABLE"))
    for label, model, source_path in [
        ("derived_view", derived_view, derived_view_report_path),
        ("strategic_briefing", strategic_briefing, strategic_briefing_report_path),
        ("strategic_narrative", strategic_narrative, strategic_narrative_report_path),
        ("strategic_memory_horizon", strategic_memory_horizon, strategic_memory_horizon_report_path),
        ("contradiction_resolution", contradiction_resolution, contradiction_resolution_report_path),
        ("strategic_intervention", intervention_simulation, strategic_intervention_report_path),
        ("strategic_campaign", strategic_campaigns, strategic_campaign_report_path),
        ("campaign_execution", campaign_execution, strategic_campaign_execution_report_path),
        ("thesis_memory", thesis_memory, thesis_memory_report_path),
        ("strategy_cohort", strategy_cohort, strategy_cohort_report_path),
        ("doctrine_adaptation", doctrine_adaptation, doctrine_adaptation_report_path),
        ("research_priorities", research_priorities, research_priority_report_path),
        ("research_execution_memory", research_execution_memory, research_execution_memory_report_path),
        ("thesis_graph", thesis_graph, thesis_graph_report_path),
        ("strategic_tensions", strategic_tensions, strategic_tension_report_path),
        ("scenario_lab", scenario_lab, scenario_lab_report_path),
    ]:
        if model is not None:
            artifact_lineage.append(build_lineage_item_from_model(artifact_label=label, artifact_role="DERIVED", model=model, source_path=source_path))
    for label, evidence in [
        ("doctrine_adaptation_evidence", doctrine_adaptation_evidence),
        ("research_priorities_evidence", research_priorities_evidence),
        ("strategic_intervention_evidence", intervention_simulation_evidence),
        ("strategic_campaign_evidence", strategic_campaigns_evidence),
        ("campaign_execution_evidence", campaign_execution_evidence),
    ]:
        if evidence is not None and evidence.get("manifest_path"):
            try:
                artifact_lineage.append(build_lineage_item_from_registered_artifact(artifact_label=label, artifact_role="EVIDENCE", path=Path(evidence["manifest_path"]), integrity_status=evidence.get("evidence_status")))
            except Exception:
                pass
    artifact_lineage_summary_line = summarize_lineage(artifact_lineage)
    evidence_integrity_status, unverified_artifact_count, integrity_summary_line = summarize_artifact_integrity(artifact_lineage)
    expected_labels = ["oracle_policy", "status_pack"]
    if incident_pack is not None:
        expected_labels.append("incident_pack")
    evidence_coverage_status, missing_expected_artifact_count, evidence_coverage_summary_line, missing_expected_artifact_labels = summarize_artifact_coverage(expected_labels=expected_labels, items=artifact_lineage)
    support_manifest_paths = [
        Path(evidence["manifest_path"])
        for evidence in [doctrine_adaptation_evidence, research_priorities_evidence, intervention_simulation_evidence, strategic_campaigns_evidence, campaign_execution_evidence]
        if evidence is not None and evidence.get("manifest_path")
    ]
    support_verification_status, support_verification_paths, support_verification_summary_line = summarize_support_verification(support_manifest_paths)
    support_chain_trust_status, support_chain_trust_summary_line, support_chain_trust_reasons = assess_support_chain_trust(
        evidence_freshness_status=evidence_freshness_status,
        stale_artifact_count=stale_artifact_count,
        evidence_integrity_status=evidence_integrity_status,
        unverified_artifact_count=unverified_artifact_count,
        evidence_coverage_status=evidence_coverage_status,
        missing_expected_artifact_count=missing_expected_artifact_count,
        support_verification_status=support_verification_status,
        formal_verification_required=True,
    )
    support_chain_remediation_status, support_chain_remediation_summary_line, support_chain_remediation_actions = assess_support_chain_remediation(
        evidence_freshness_status=evidence_freshness_status,
        stale_artifact_count=stale_artifact_count,
        evidence_integrity_status=evidence_integrity_status,
        unverified_artifact_count=unverified_artifact_count,
        evidence_coverage_status=evidence_coverage_status,
        missing_expected_artifact_labels=missing_expected_artifact_labels,
        support_verification_status=support_verification_status,
        formal_verification_required=True,
    )
    if stale_artifact_count > 0:
        operator_actions = _unique(operator_actions + ["Refresh stale strategist artifacts before treating this briefing pack as the canonical operator surface."])
    if support_verification_status == "UNVERIFIED":
        operator_actions = _unique(operator_actions + ["Investigate failed or unverified support verification artifacts before treating this briefing pack as a strongly grounded canonical surface."])
    elif support_verification_status == "INCOMPLETE":
        operator_actions = _unique(operator_actions + ["Complete support verification for the canonical strategist evidence chain before increasing reliance on this briefing pack."])
    elif support_verification_status == "ABSENT" and evidence_coverage_status == "COMPLETE":
        operator_actions = _unique(operator_actions + ["Produce formal support verification artifacts for the canonical strategist evidence chain to strengthen provenance discipline and operator trust."])
    if status_pack.trust_status == "UNTRUSTED":
        summary_line = f"Canonical briefing is untrusted; resolve the listed risks before relying on this morning review bundle, and note that {cadence_summary}."
    elif status_pack.trust_status == "TRUST_RESTRICTED":
        summary_line = f"Canonical briefing is restricted; review inline provenance, strategic queues, thesis drift, and freshness warnings before relying on this bundle, and note that {cadence_summary}."
    else:
        summary_line = f"Canonical briefing is trusted and ready for operator review, and note that {cadence_summary}."
    operator_readiness, operator_readiness_summary_line, operator_readiness_reasons = assess_briefing_operator_readiness(
        trust_status=status_pack.trust_status,
        evidence_freshness_status=evidence_freshness_status,
        stale_artifact_count=stale_artifact_count,
        evidence_integrity_status=evidence_integrity_status,
        unverified_artifact_count=unverified_artifact_count,
        evidence_coverage_status=evidence_coverage_status,
        missing_expected_artifact_count=missing_expected_artifact_count,
        support_verification_status=support_verification_status,
    )

    governance_plane = assess_governance_plane(
        evidence_freshness_status=evidence_freshness_status,
        evidence_integrity_status=evidence_integrity_status,
        evidence_coverage_status=evidence_coverage_status,
        support_verification_status=support_verification_status,
        support_chain_trust_status=support_chain_trust_status,
        support_chain_remediation_status=support_chain_remediation_status,
        support_chain_remediation_actions=support_chain_remediation_actions,
        operator_readiness=operator_readiness,
        surface_label="this briefing pack",
    )
    operator_actions = _unique(operator_actions + governance_plane.governance_plane_actions)
    generated_at_utc = _utc_now()
    operator_queue_snapshot = materialize_operator_queue_snapshot(
        governance_plane=governance_plane,
        issued_at_utc=generated_at_utc,
    )

    operator_reliance_posture = governance_plane.operator_reliance_posture
    operator_reliance_summary_line = governance_plane.operator_reliance_summary_line
    operator_reliance_reasons = governance_plane.operator_reliance_reasons
    operator_escalation_lane = governance_plane.operator_escalation_lane
    operator_escalation_summary_line = governance_plane.operator_escalation_summary_line
    operator_escalation_reasons = governance_plane.operator_escalation_reasons
    propagation_posture = governance_plane.propagation_posture
    propagation_summary_line = governance_plane.propagation_summary_line
    propagation_reasons = governance_plane.propagation_reasons
    automation_posture = governance_plane.automation_posture
    automation_summary_line = governance_plane.automation_summary_line
    automation_reasons = governance_plane.automation_reasons
    governance_work_queue = operator_queue_snapshot.queue_state
    governance_review_envelope = governance_work_queue.governance_review_envelope
    governance_routing_envelope = governance_work_queue.governance_routing_envelope
    governance_dispatch_envelope = governance_work_queue.governance_dispatch_envelope
    governance_claim_envelope = governance_work_queue.governance_claim_envelope
    primary_work_item = operator_queue_snapshot.primary_work_item
    sections.append(
        build_operator_queue_briefing_section(
            operator_queue_snapshot=operator_queue_snapshot,
            governance_plane_status=governance_plane.governance_plane_status,
            governance_claim_sha256=governance_claim_envelope.governance_plane_claim_sha256,
            governance_dispatch_sha256=governance_dispatch_envelope.governance_plane_dispatch_sha256,
            status_pack_provenance_digest_sha256=status_pack.provenance_digest_sha256,
        )
    )
    report = OracleBriefingPackReport(
        generated_at_utc=generated_at_utc,
        repo_root=str(resolved_repo_root),
        search_root=str(resolved_search_root),
        oracle_policy_version=policy_version,
        oracle_policy_sha256=policy_sha256,
        oracle_policy_path=policy_path,
        operator_readiness=operator_readiness,
        operator_readiness_summary_line=operator_readiness_summary_line,
        operator_readiness_reasons=operator_readiness_reasons,
        evidence_freshness_status=evidence_freshness_status,
        stale_artifact_count=stale_artifact_count,
        freshness_summary_line=freshness_summary_line,
        artifact_freshness=artifact_freshness,
        artifact_lineage_summary_line=artifact_lineage_summary_line,
        artifact_lineage=artifact_lineage,
        evidence_integrity_status=evidence_integrity_status,
        unverified_artifact_count=unverified_artifact_count,
        integrity_summary_line=integrity_summary_line,
        evidence_coverage_status=evidence_coverage_status,
        missing_expected_artifact_count=missing_expected_artifact_count,
        evidence_coverage_summary_line=evidence_coverage_summary_line,
        missing_expected_artifact_labels=missing_expected_artifact_labels,
        support_verification_status=support_verification_status,
        support_verification_summary_line=support_verification_summary_line,
        support_verification_paths=support_verification_paths,
        support_chain_trust_status=support_chain_trust_status,
        support_chain_trust_summary_line=support_chain_trust_summary_line,
        support_chain_trust_reasons=support_chain_trust_reasons,
        support_chain_remediation_status=support_chain_remediation_status,
        support_chain_remediation_summary_line=support_chain_remediation_summary_line,
        support_chain_remediation_actions=support_chain_remediation_actions,
        trust_plane_summary_line=governance_plane.trust_plane_summary_line,
        operator_reliance_posture=operator_reliance_posture,
        operator_reliance_summary_line=operator_reliance_summary_line,
        operator_reliance_reasons=operator_reliance_reasons,
        operator_escalation_lane=operator_escalation_lane,
        operator_escalation_summary_line=operator_escalation_summary_line,
        operator_escalation_reasons=operator_escalation_reasons,
        propagation_posture=propagation_posture,
        propagation_summary_line=propagation_summary_line,
        propagation_reasons=propagation_reasons,
        automation_posture=automation_posture,
        automation_summary_line=automation_summary_line,
        automation_reasons=automation_reasons,
        control_plane_summary_line=governance_plane.control_plane_summary_line,
        governance_plane_status=governance_plane.governance_plane_status,
        governance_plane_summary_line=governance_plane.governance_plane_summary_line,
        governance_plane_reasons=governance_plane.governance_plane_reasons,
        governance_plane_codes=governance_plane.governance_plane_codes,
        governance_plane_blocking_dimensions=governance_plane.governance_plane_blocking_dimensions,
        governance_plane_restricted_dimensions=governance_plane.governance_plane_restricted_dimensions,
        governance_plane_actions=governance_plane.governance_plane_actions,
        governance_plane_action_items=governance_plane.governance_plane_action_items,
        governance_plane_primary_dimension=governance_plane.governance_plane_primary_dimension,
        governance_plane_primary_severity=governance_plane.governance_plane_primary_severity,
        governance_plane_primary_action_text=governance_plane.governance_plane_primary_action_text,
        governance_plane_priority_band=governance_plane.governance_plane_priority_band,
        governance_plane_priority_score=governance_plane.governance_plane_priority_score,
        governance_plane_priority_summary_line=governance_plane.governance_plane_priority_summary_line,
        governance_plane_review_target=governance_plane.governance_plane_review_target,
        governance_plane_review_sla_hours=governance_plane.governance_plane_review_sla_hours,
        governance_plane_review_summary_line=governance_plane.governance_plane_review_summary_line,
        governance_plane_review_due_by_utc=governance_review_envelope.governance_plane_review_due_by_utc,
        governance_plane_review_sort_key=governance_review_envelope.governance_plane_review_sort_key,
        governance_plane_review_envelope_vector=governance_review_envelope.governance_plane_review_envelope_vector,
        governance_plane_review_envelope_sha256=governance_review_envelope.governance_plane_review_envelope_sha256,
        governance_plane_routing_summary_line=governance_routing_envelope.governance_plane_routing_summary_line,
        governance_plane_routing_vector=governance_routing_envelope.governance_plane_routing_vector,
        governance_plane_routing_sha256=governance_routing_envelope.governance_plane_routing_sha256,
        governance_plane_dispatch_posture=primary_work_item.dispatch_posture,
        governance_plane_dispatch_permitted=primary_work_item.dispatch_permitted,
        governance_plane_dispatch_summary_line=governance_dispatch_envelope.governance_plane_dispatch_summary_line,
        governance_plane_dispatch_reasons=governance_dispatch_envelope.governance_plane_dispatch_reasons,
        governance_plane_dispatch_timeliness=governance_dispatch_envelope.governance_plane_dispatch_timeliness,
        governance_plane_dispatch_claim_permitted_now=primary_work_item.dispatch_claim_permitted_now,
        governance_plane_dispatch_timeliness_summary_line=governance_dispatch_envelope.governance_plane_dispatch_timeliness_summary_line,
        governance_plane_dispatch_claim_urgency=primary_work_item.dispatch_claim_urgency,
        governance_plane_dispatch_claim_score=primary_work_item.dispatch_claim_score,
        governance_plane_dispatch_claim_summary_line=primary_work_item.dispatch_claim_summary_line,
        governance_plane_dispatch_vector=governance_dispatch_envelope.governance_plane_dispatch_vector,
        governance_plane_dispatch_sha256=governance_dispatch_envelope.governance_plane_dispatch_sha256,
        governance_plane_dispatch_claim_key=primary_work_item.dispatch_claim_key,
        governance_plane_claim_summary_line=primary_work_item.claim_summary_line,
        governance_plane_claim_queue_key=primary_work_item.queue_key,
        governance_plane_claim_review_target=primary_work_item.review_target,
        governance_plane_claim_priority_band=primary_work_item.priority_band,
        governance_plane_claim_review_due_by_utc=primary_work_item.review_due_by_utc,
        governance_plane_claim_review_sort_key=primary_work_item.review_sort_key,
        governance_plane_claim_route_sha256=governance_claim_envelope.governance_plane_claim_route_sha256,
        governance_plane_claim_review_envelope_sha256=governance_claim_envelope.governance_plane_claim_review_envelope_sha256,
        governance_plane_claim_routing_envelope_sha256=governance_claim_envelope.governance_plane_claim_routing_envelope_sha256,
        governance_plane_claim_dispatch_claim_key=governance_claim_envelope.governance_plane_claim_dispatch_claim_key,
        governance_plane_claim_dispatch_sha256=governance_claim_envelope.governance_plane_claim_dispatch_sha256,
        governance_plane_claim_codes=governance_claim_envelope.governance_plane_claim_codes,
        governance_plane_claim_primary_code=governance_claim_envelope.governance_plane_claim_primary_code,
        governance_plane_claim_action_items=governance_claim_envelope.governance_plane_claim_action_items,
        governance_plane_claim_primary_action_text=primary_work_item.claim_primary_action_text,
        governance_plane_claim_worker_lane=primary_work_item.claim_worker_lane,
        governance_plane_claim_worker_summary_line=primary_work_item.claim_worker_summary_line,
        governance_plane_claim_worker_sort_key=primary_work_item.claim_worker_sort_key,
        governance_plane_claim_lease_key=primary_work_item.lease_key,
        governance_plane_claim_lease_mode=governance_claim_envelope.governance_plane_claim_lease_mode,
        governance_plane_claim_lease_ttl_seconds=governance_claim_envelope.governance_plane_claim_lease_ttl_seconds,
        governance_plane_claim_lease_expires_at_utc=governance_claim_envelope.governance_plane_claim_lease_expires_at_utc,
        governance_plane_claim_lease_active_now=primary_work_item.lease_active_now,
        governance_plane_claim_lease_summary_line=primary_work_item.lease_summary_line,
        governance_plane_claim_lease_coverage=governance_claim_envelope.governance_plane_claim_lease_coverage,
        governance_plane_claim_lease_coverage_summary_line=governance_claim_envelope.governance_plane_claim_lease_coverage_summary_line,
        governance_plane_claim_lease_health=governance_claim_envelope.governance_plane_claim_lease_health,
        governance_plane_claim_lease_health_summary_line=governance_claim_envelope.governance_plane_claim_lease_health_summary_line,
        governance_plane_claim_lease_renewal_posture=governance_claim_envelope.governance_plane_claim_lease_renewal_posture,
        governance_plane_claim_lease_renewal_permitted_now=governance_claim_envelope.governance_plane_claim_lease_renewal_permitted_now,
        governance_plane_claim_lease_renewal_summary_line=governance_claim_envelope.governance_plane_claim_lease_renewal_summary_line,
        governance_plane_claim_lease_action=primary_work_item.lease_action,
        governance_plane_claim_lease_action_summary_line=primary_work_item.lease_action_summary_line,
        governance_plane_claim_disposition=governance_claim_envelope.governance_plane_claim_disposition,
        governance_plane_claim_disposition_summary_line=governance_claim_envelope.governance_plane_claim_disposition_summary_line,
        governance_plane_claim_process_posture=governance_claim_envelope.governance_plane_claim_process_posture,
        governance_plane_claim_process_permitted_now=governance_claim_envelope.governance_plane_claim_process_permitted_now,
        governance_plane_claim_process_summary_line=governance_claim_envelope.governance_plane_claim_process_summary_line,
        governance_plane_claim_operability=primary_work_item.claim_operability,
        governance_plane_claim_operability_summary_line=primary_work_item.claim_operability_summary_line,
        governance_plane_claim_vector=governance_claim_envelope.governance_plane_claim_vector,
        governance_plane_claim_sha256=governance_claim_envelope.governance_plane_claim_sha256,
        governance_plane_queue_key=governance_plane.governance_plane_queue_key,
        governance_plane_route_vector=governance_plane.governance_plane_route_vector,
        governance_plane_route_sha256=governance_plane.governance_plane_route_sha256,
        governance_plane_vector=governance_plane.governance_plane_vector,
        governance_plane_sha256=governance_plane.governance_plane_sha256,
        trust_status=status_pack.trust_status,
        preferred_strategic_backing_source=status_pack.preferred_strategic_backing_source,
        exact_feedback_confirmation_count=status_pack.exact_feedback_confirmation_count,
        exact_feedback_relief_count=status_pack.exact_feedback_relief_count,
        exact_cadence_signal_classification=cadence_signal,
        preferred_strategic_backing_classification=status_pack.preferred_strategic_backing_classification,
        summary_line=summary_line,
        status_pack_digest_sha256=status_pack.provenance_digest_sha256,
        incident_pack_digest_sha256=(incident_pack.provenance_digest_sha256 if incident_pack is not None else None),
        sections=sections,
        operator_actions=operator_actions,
    )
    return _with_provenance_digest(report)


def build_oracle_briefing_pack(
    *,
    repo_root: Path,
    search_root: Path | None = None,
    derived_view_report_path: Path | None = None,
    constitutional_gate_report_path: Path | None = None,
    closure_snapshot_path: Path | None = None,
    closure_dsse_path: Path | None = None,
    closure_public_key_path: Path | None = None,
    governed_exception_memo_path: Path | None = None,
    governed_exception_dsse_path: Path | None = None,
    governed_exception_public_key_path: Path | None = None,
    strategic_briefing_report_path: Path | None = None,
    strategic_narrative_report_path: Path | None = None,
    strategic_memory_horizon_report_path: Path | None = None,
    contradiction_resolution_report_path: Path | None = None,
    strategic_intervention_report_path: Path | None = None,
    strategic_campaign_report_path: Path | None = None,
    strategic_campaign_execution_report_path: Path | None = None,
    thesis_memory_report_path: Path | None = None,
    strategy_cohort_report_path: Path | None = None,
    doctrine_adaptation_report_path: Path | None = None,
    research_priority_report_path: Path | None = None,
    research_execution_memory_report_path: Path | None = None,
    thesis_graph_report_path: Path | None = None,
    strategic_tension_report_path: Path | None = None,
) -> OracleBriefingPackReport:
    from strategy_validator.projections.operator_pack_assembly import assemble_oracle_briefing_pack

    return assemble_oracle_briefing_pack(
        repo_root=repo_root,
        search_root=search_root,
        derived_view_report_path=derived_view_report_path,
        constitutional_gate_report_path=constitutional_gate_report_path,
        closure_snapshot_path=closure_snapshot_path,
        closure_dsse_path=closure_dsse_path,
        closure_public_key_path=closure_public_key_path,
        governed_exception_memo_path=governed_exception_memo_path,
        governed_exception_dsse_path=governed_exception_dsse_path,
        governed_exception_public_key_path=governed_exception_public_key_path,
        strategic_briefing_report_path=strategic_briefing_report_path,
        strategic_narrative_report_path=strategic_narrative_report_path,
        strategic_memory_horizon_report_path=strategic_memory_horizon_report_path,
        contradiction_resolution_report_path=contradiction_resolution_report_path,
        strategic_intervention_report_path=strategic_intervention_report_path,
        strategic_campaign_report_path=strategic_campaign_report_path,
        strategic_campaign_execution_report_path=strategic_campaign_execution_report_path,
        thesis_memory_report_path=thesis_memory_report_path,
        strategy_cohort_report_path=strategy_cohort_report_path,
        doctrine_adaptation_report_path=doctrine_adaptation_report_path,
        research_priority_report_path=research_priority_report_path,
        research_execution_memory_report_path=research_execution_memory_report_path,
        thesis_graph_report_path=thesis_graph_report_path,
        strategic_tension_report_path=strategic_tension_report_path,
    )


def materialize_oracle_briefing_pack(
    pack_root: Path,
    report: OracleBriefingPackReport,
    *,
    markdown: str,
    html: str,
) -> OracleBriefingPackReport:
    return materialize_briefing_pack_bundle(pack_root, report, markdown=markdown, html=html)


from strategy_validator.validator.oracle_briefing_rendering import (
    render_oracle_briefing_pack_html,
    render_oracle_briefing_pack_markdown,
)
