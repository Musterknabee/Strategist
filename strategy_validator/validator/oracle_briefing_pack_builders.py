from __future__ import annotations

from pathlib import Path

from strategy_validator.contracts.oracle_operator_reports import OracleBriefingPackReport
from strategy_validator.validator.oracle_diagnostics import (
    build_oracle_incident_pack,
    build_oracle_status_pack,
)
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.oracle_strategic_artifact_evidence import discover_preferred_strategic_artifact_evidence
from strategy_validator.validator.oracle_policy import load_oracle_policy, oracle_policy_sha256
from strategy_validator.validator.oracle_artifact_freshness import build_freshness_item, summarize_freshness
from strategy_validator.validator.oracle_artifact_lineage import (
    build_lineage_item,
    build_lineage_item_from_model,
    build_lineage_item_from_registered_artifact,
    summarize_lineage,
)
from strategy_validator.validator.oracle_artifact_integrity import summarize_artifact_integrity
from strategy_validator.validator.oracle_artifact_coverage import summarize_artifact_coverage
from strategy_validator.validator.oracle_operator_readiness import assess_briefing_operator_readiness
from strategy_validator.validator.oracle_support_verification import summarize_support_verification
from strategy_validator.validator.oracle_support_chain_trust import assess_support_chain_trust
from strategy_validator.validator.oracle_support_chain_remediation import assess_support_chain_remediation
from strategy_validator.validator.oracle_governance_plane import assess_governance_plane
from strategy_validator.control_plane.operator_board_sections import build_operator_queue_briefing_section
from strategy_validator.validator.oracle_briefing_io import (
    _find_latest,
    _load_contradiction_resolution,
    _load_doctrine_adaptation,
    _load_derived_view,
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
    _with_provenance_digest,
)
from strategy_validator.validator.oracle_briefing_sections import (
    _briefing_sections,
    _exact_cadence_summary,
    _unique,
)


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
    from strategy_validator.validator import oracle_briefing as oracle_briefing_module

    operator_queue_snapshot = oracle_briefing_module.materialize_operator_queue_snapshot(
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

__all__ = ['_build_oracle_briefing_pack_impl']
