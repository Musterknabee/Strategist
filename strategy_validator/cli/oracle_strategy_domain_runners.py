from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from strategy_validator.cli.oracle_cli_common import write_json
from strategy_validator.cli.application_strategy_surfaces import (
    build_contradiction_resolution_payload,
    build_doctrine_adaptation_payload,
    build_morning_attestation_payload,
    build_opportunity_queue_payload,
    build_oracle_evidence_bundle_payload,
    build_regime_transition_payload,
    build_replay_audit_payload,
    build_research_execution_memory_payload,
    build_research_priority_payload,
    build_scenario_lab_payload,
    build_status_pack_payload,
    build_strategic_artifact_evidence_bundle_payload,
    build_strategic_briefing_payload,
    build_strategic_campaign_execution_payload,
    build_strategic_campaign_payload,
    build_strategic_fusion_payload,
    build_strategic_intervention_payload,
    build_strategic_memory_horizon_payload,
    build_strategic_narrative_payload,
    build_strategic_stack_evidence_bundle_payload,
    build_strategic_tension_payload,
    build_strategy_cohort_payload,
    build_strategy_health_posterior_payload,
    build_thesis_graph_payload,
    build_thesis_memory_payload,
    load_contradiction_resolution_report_payload,
    load_doctrine_adaptation_report_payload,
    load_doctrine_adaptation_report_payload,
    load_fusion_report_payload,
    load_investigation_outcome_input_payload,
    load_oracle_input_payload,
    load_research_execution_memory_report_payload,
    load_research_priority_report_payload,
    load_scenario_plan_input_payload,
    load_sensor_ingestion_input_payload,
    load_strategic_campaign_execution_input_payload,
    load_strategic_campaign_execution_report_payload,
    load_strategic_campaign_report_payload,
    load_strategic_memory_horizon_report_payload,
    load_strategic_narrative_report_payload,
    load_strategic_tension_report_payload,
    load_strategy_cohort_report_payload,
    load_thesis_graph_report_payload,
    load_thesis_memory_report_payload,
    load_verified_strategic_stack_history_bundle_payload,
    materialize_briefing_pack_payload,
    materialize_incident_pack_payload,
    materialize_status_pack_payload,
    normalize_sensor_ingestion_payload,
    render_contradiction_resolution_markdown_payload,
    render_doctrine_adaptation_markdown_payload,
    render_morning_attestation_markdown_payload,
    render_opportunity_queue_markdown_payload,
    render_operator_diagnostic_markdown_payload,
    render_incident_pack_html_payload,
    render_incident_pack_markdown_payload,
    render_research_execution_memory_markdown_payload,
    render_replay_audit_markdown_payload,
    render_scenario_lab_markdown_payload,
    render_sensor_ingestion_markdown_payload,
    render_status_pack_html_payload,
    render_status_pack_markdown_payload,
    render_strategic_briefing_markdown_payload,
    render_strategic_campaign_execution_markdown_payload,
    render_strategic_campaign_markdown_payload,
    render_strategic_fusion_markdown_payload,
    render_strategic_intervention_markdown_payload,
    render_strategic_memory_horizon_markdown_payload,
    render_strategic_narrative_markdown_payload,
    render_strategic_tension_markdown_payload,
    render_strategy_cohort_markdown_payload,
    render_strategy_health_posterior_markdown_payload,
    render_regime_transition_markdown_payload,
    render_research_priority_markdown_payload,
    render_thesis_graph_markdown_payload,
    render_thesis_memory_markdown_payload,
    build_operator_diagnostic_from_checkpoint_payload,
    build_operator_diagnostic_from_report_payload,
    build_incident_pack_payload,
    verify_oracle_evidence_bundle_payload,
    verify_strategic_artifact_evidence_bundle_payload,
    verify_strategic_stack_evidence_bundle_payload,
)


def cmd_oracle_opportunity_queue(ns: argparse.Namespace) -> int:
    payload = load_oracle_input_payload(Path(ns.input))
    fusion = load_fusion_report_payload(Path(ns.fusion_report)) if ns.fusion_report else build_strategic_fusion_payload(payload=payload)
    posterior = build_strategy_health_posterior_payload(payload=payload, fusion_report=fusion)
    strategic_memory = load_strategic_memory_horizon_report_payload(Path(ns.strategic_memory_horizon_report)) if getattr(ns, "strategic_memory_horizon_report", "") else None
    doctrine = load_doctrine_adaptation_report_payload(Path(ns.doctrine_adaptation_report)) if getattr(ns, "doctrine_adaptation_report", "") else None
    priorities = load_research_priority_report_payload(Path(ns.research_priority_report)) if getattr(ns, "research_priority_report", "") else None
    transition = None
    if ns.previous_fusion_report:
        transition = build_regime_transition_payload(
            previous=load_fusion_report_payload(Path(ns.previous_fusion_report)),
            current=fusion,
        )
    report = build_opportunity_queue_payload(
        payload=payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        strategic_memory_horizon_report=strategic_memory,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        doctrine_adaptation_report_path=Path(ns.doctrine_adaptation_report) if getattr(ns, "doctrine_adaptation_report", "") else None,
        research_priority_report_path=Path(ns.research_priority_report) if getattr(ns, "research_priority_report", "") else None,
        repo_root=Path(ns.repo_root) if getattr(ns, "repo_root", "") else None,
        search_root=Path(ns.search_root) if getattr(ns, "search_root", "") else None,
    )
    output_path = Path(ns.output) if ns.output else Path(ns.input).with_name("ORACLE_OPPORTUNITY_QUEUE_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_opportunity_queue_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_thesis_memory(ns: argparse.Namespace) -> int:
    payload = load_oracle_input_payload(Path(ns.input))
    fusion = load_fusion_report_payload(Path(ns.fusion_report)) if ns.fusion_report else build_strategic_fusion_payload(payload=payload)
    posterior = build_strategy_health_posterior_payload(payload=payload, fusion_report=fusion)
    previous_thesis = load_thesis_memory_report_payload(Path(ns.previous_thesis_memory_report)) if ns.previous_thesis_memory_report else None
    transition = None
    if ns.previous_fusion_report:
        transition = build_regime_transition_payload(
            previous=load_fusion_report_payload(Path(ns.previous_fusion_report)),
            current=fusion,
        )
    report = build_thesis_memory_payload(
        payload=payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        previous_report=previous_thesis,
        execution_memory_report=(load_research_execution_memory_report_payload(Path(ns.research_execution_memory_report)) if getattr(ns, "research_execution_memory_report", "") else None),
        doctrine_adaptation_report=(load_doctrine_adaptation_report_payload(Path(ns.doctrine_adaptation_report)) if getattr(ns, "doctrine_adaptation_report", "") else None),
        research_priority_report=(load_research_priority_report_payload(Path(ns.research_priority_report)) if getattr(ns, "research_priority_report", "") else None),
        doctrine_adaptation_report_path=(Path(ns.doctrine_adaptation_report) if getattr(ns, "doctrine_adaptation_report", "") else None),
        research_priority_report_path=(Path(ns.research_priority_report) if getattr(ns, "research_priority_report", "") else None),
        repo_root=(Path(ns.repo_root) if getattr(ns, "repo_root", "") else None),
        search_root=(Path(ns.search_root) if getattr(ns, "search_root", "") else None),
    )
    output_path = Path(ns.output) if ns.output else Path(ns.input).with_name("ORACLE_THESIS_MEMORY_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_thesis_memory_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_strategic_briefing(ns: argparse.Namespace) -> int:
    payload = load_oracle_input_payload(Path(ns.input))
    previous_fusion = load_fusion_report_payload(Path(ns.previous_fusion_report)) if ns.previous_fusion_report else None
    previous_thesis = load_thesis_memory_report_payload(Path(ns.previous_thesis_memory_report)) if ns.previous_thesis_memory_report else None
    execution_memory = load_research_execution_memory_report_payload(Path(ns.research_execution_memory_report)) if getattr(ns, "research_execution_memory_report", "") else None
    report = build_strategic_briefing_payload(
        payload=payload,
        previous_fusion_report=previous_fusion,
        previous_thesis_memory_report=previous_thesis,
        research_execution_memory_report=execution_memory,
        thesis_graph_report=(load_thesis_graph_report_payload(Path(ns.thesis_graph_report)) if getattr(ns, "thesis_graph_report", "") else None),
        strategic_tension_report=(load_strategic_tension_report_payload(Path(ns.strategic_tension_report)) if getattr(ns, "strategic_tension_report", "") else None),
        strategic_narrative_report=(load_strategic_narrative_report_payload(Path(ns.strategic_narrative_report)) if getattr(ns, "strategic_narrative_report", "") else None),
        strategic_memory_horizon_report=(load_strategic_memory_horizon_report_payload(Path(ns.strategic_memory_horizon_report)) if getattr(ns, "strategic_memory_horizon_report", "") else None),
        contradiction_resolution_report=(load_contradiction_resolution_report_payload(Path(ns.contradiction_resolution_report)) if getattr(ns, "contradiction_resolution_report", "") else None),
        intervention_simulation_report=(load_strategic_intervention_report_payload(Path(ns.strategic_intervention_report)) if getattr(ns, "strategic_intervention_report", "") else None),
        strategic_campaign_report=(load_strategic_campaign_report_payload(Path(ns.strategic_campaign_report)) if getattr(ns, "strategic_campaign_report", "") else None),
        campaign_execution_report=(load_strategic_campaign_execution_report_payload(Path(ns.strategic_campaign_execution_report)) if getattr(ns, "strategic_campaign_execution_report", "") else None),
    )
    output_path = Path(ns.output) if ns.output else Path(ns.input).with_name("ORACLE_STRATEGIC_BRIEFING_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_strategic_briefing_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_strategic_memory_horizon(ns: argparse.Namespace) -> int:
    current_report = load_strategic_narrative_report_payload(Path(ns.current_report))
    history_reports = [load_strategic_narrative_report_payload(Path(path)) for path in getattr(ns, "history_report", [])]
    sealed_history_reports = []
    sealed_history_manifest_paths = []
    for bundle in getattr(ns, "verified_history_bundle", []):
        narrative_raw = manifest_raw = verification_raw = ""
        # Windows drive letters introduce ":" characters into absolute paths, so parse using
        # a Windows-absolute-path extractor when possible.
        windows_paths = re.findall(r"[A-Za-z]:\\[^:]+", bundle)
        if len(windows_paths) == 3:
            narrative_raw, manifest_raw, verification_raw = windows_paths
        else:
            parts = bundle.split(":", 2)
            if len(parts) != 3:
                raise ValueError("verified history bundles must use narrative_path:manifest_path:verification_path")
            narrative_raw, manifest_raw, verification_raw = parts
        narrative, manifest, _ = load_verified_strategic_stack_history_bundle_payload(
            narrative_report_path=Path(narrative_raw),
            manifest_path=Path(manifest_raw),
            verification_path=Path(verification_raw),
        )
        sealed_history_reports.append(narrative)
        sealed_history_manifest_paths.append(str(Path(manifest_raw)))
    report = build_strategic_memory_horizon_payload(
        current_report=current_report,
        history_reports=history_reports,
        sealed_history_reports=sealed_history_reports,
        sealed_history_manifest_paths=sealed_history_manifest_paths,
        require_sealed_history=bool(getattr(ns, "require_sealed_history", False) or sealed_history_reports),
    )
    output_path = Path(ns.output) if ns.output else Path(ns.current_report).with_name("ORACLE_STRATEGIC_MEMORY_HORIZON_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_strategic_memory_horizon_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_contradiction_resolution(ns: argparse.Namespace) -> int:
    payload = load_oracle_input_payload(Path(ns.input))
    fusion = load_fusion_report_payload(Path(ns.fusion_report)) if getattr(ns, "fusion_report", "") else build_strategic_fusion_payload(payload=payload)
    thesis = load_thesis_memory_report_payload(Path(ns.thesis_memory_report)) if getattr(ns, "thesis_memory_report", "") else None
    cohorts = load_strategy_cohort_report_payload(Path(ns.strategy_cohort_report)) if getattr(ns, "strategy_cohort_report", "") else None
    doctrine = load_doctrine_adaptation_report_payload(Path(ns.doctrine_adaptation_report)) if getattr(ns, "doctrine_adaptation_report", "") else None
    priorities = load_research_priority_report_payload(Path(ns.research_priority_report)) if getattr(ns, "research_priority_report", "") else None
    execution_memory = load_research_execution_memory_report_payload(Path(ns.research_execution_memory_report)) if getattr(ns, "research_execution_memory_report", "") else None
    thesis_graph = load_thesis_graph_report_payload(Path(ns.thesis_graph_report)) if getattr(ns, "thesis_graph_report", "") else None
    strategic_tension = load_strategic_tension_report_payload(Path(ns.strategic_tension_report)) if getattr(ns, "strategic_tension_report", "") else None
    strategic_narrative = load_strategic_narrative_report_payload(Path(ns.strategic_narrative_report)) if getattr(ns, "strategic_narrative_report", "") else None
    strategic_memory = load_strategic_memory_horizon_report_payload(Path(ns.strategic_memory_horizon_report)) if getattr(ns, "strategic_memory_horizon_report", "") else None
    report = build_contradiction_resolution_payload(
        payload=payload,
        fusion_report=fusion,
        thesis_memory_report=thesis,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        research_execution_memory_report=execution_memory,
        thesis_graph_report=thesis_graph,
        strategic_tension_report=strategic_tension,
        strategic_narrative_report=strategic_narrative,
        strategic_memory_horizon_report=strategic_memory,
        doctrine_adaptation_report_path=Path(ns.doctrine_adaptation_report) if getattr(ns, "doctrine_adaptation_report", "") else None,
        research_priority_report_path=Path(ns.research_priority_report) if getattr(ns, "research_priority_report", "") else None,
        repo_root=Path(ns.repo_root) if getattr(ns, "repo_root", "") else None,
        search_root=Path(ns.search_root) if getattr(ns, "search_root", "") else None,
    )
    output_path = Path(ns.output) if ns.output else Path(ns.input).with_name("ORACLE_CONTRADICTION_RESOLUTION_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_contradiction_resolution_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_strategic_intervention(ns: argparse.Namespace) -> int:
    payload = load_oracle_input_payload(Path(ns.input))
    fusion = load_fusion_report_payload(Path(ns.fusion_report)) if getattr(ns, "fusion_report", "") else build_strategic_fusion_payload(payload=payload)
    thesis = load_thesis_memory_report_payload(Path(ns.thesis_memory_report)) if getattr(ns, "thesis_memory_report", "") else None
    cohorts = load_strategy_cohort_report_payload(Path(ns.strategy_cohort_report)) if getattr(ns, "strategy_cohort_report", "") else None
    doctrine = load_doctrine_adaptation_report_payload(Path(ns.doctrine_adaptation_report)) if getattr(ns, "doctrine_adaptation_report", "") else None
    priorities = load_research_priority_report_payload(Path(ns.research_priority_report)) if getattr(ns, "research_priority_report", "") else None
    execution_memory = load_research_execution_memory_report_payload(Path(ns.research_execution_memory_report)) if getattr(ns, "research_execution_memory_report", "") else None
    thesis_graph = load_thesis_graph_report_payload(Path(ns.thesis_graph_report)) if getattr(ns, "thesis_graph_report", "") else None
    strategic_tension = load_strategic_tension_report_payload(Path(ns.strategic_tension_report)) if getattr(ns, "strategic_tension_report", "") else None
    strategic_narrative = load_strategic_narrative_report_payload(Path(ns.strategic_narrative_report)) if getattr(ns, "strategic_narrative_report", "") else None
    strategic_memory = load_strategic_memory_horizon_report_payload(Path(ns.strategic_memory_horizon_report)) if getattr(ns, "strategic_memory_horizon_report", "") else None
    contradiction = load_contradiction_resolution_report_payload(Path(ns.contradiction_resolution_report)) if getattr(ns, "contradiction_resolution_report", "") else None
    report = build_strategic_intervention_payload(
        payload=payload,
        fusion_report=fusion,
        thesis_memory_report=thesis,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        research_execution_memory_report=execution_memory,
        thesis_graph_report=thesis_graph,
        strategic_tension_report=strategic_tension,
        strategic_narrative_report=strategic_narrative,
        strategic_memory_horizon_report=strategic_memory,
        contradiction_resolution_report=contradiction,
        doctrine_adaptation_report_path=Path(ns.doctrine_adaptation_report) if getattr(ns, "doctrine_adaptation_report", "") else None,
        research_priority_report_path=Path(ns.research_priority_report) if getattr(ns, "research_priority_report", "") else None,
        repo_root=Path(ns.repo_root) if getattr(ns, "repo_root", "") else None,
        search_root=Path(ns.search_root) if getattr(ns, "search_root", "") else None,
    )
    output_path = Path(ns.output) if ns.output else Path(ns.input).with_name("ORACLE_STRATEGIC_INTERVENTION_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_strategic_intervention_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_strategic_campaign_execution(ns: argparse.Namespace) -> int:
    campaign_report = load_strategic_campaign_report_payload(Path(ns.campaign_report))
    execution_input = load_strategic_campaign_execution_input_payload(Path(ns.execution_input)) if getattr(ns, "execution_input", "") else None
    execution_memory = load_research_execution_memory_report_payload(Path(ns.research_execution_memory_report)) if getattr(ns, "research_execution_memory_report", "") else None
    doctrine = load_doctrine_adaptation_report_payload(Path(ns.doctrine_adaptation_report)) if getattr(ns, "doctrine_adaptation_report", "") else None
    strategic_memory = load_strategic_memory_horizon_report_payload(Path(ns.strategic_memory_horizon_report)) if getattr(ns, "strategic_memory_horizon_report", "") else None
    report = build_strategic_campaign_execution_payload(
        campaign_report=campaign_report,
        execution_input=execution_input,
        research_execution_memory_report=execution_memory,
        doctrine_adaptation_report=doctrine,
        strategic_memory_horizon_report=strategic_memory,
        campaign_report_path=Path(ns.campaign_report),
        repo_root=Path(ns.repo_root) if getattr(ns, "repo_root", "") else None,
        search_root=Path(ns.search_root) if getattr(ns, "search_root", "") else None,
    )
    output_path = Path(ns.output) if ns.output else Path(ns.campaign_report).with_name("ORACLE_STRATEGIC_CAMPAIGN_EXECUTION_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_strategic_campaign_execution_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_strategic_campaign(ns: argparse.Namespace) -> int:
    payload = load_oracle_input_payload(Path(ns.input))
    fusion = load_fusion_report_payload(Path(ns.fusion_report)) if getattr(ns, "fusion_report", "") else build_strategic_fusion_payload(payload=payload)
    thesis = load_thesis_memory_report_payload(Path(ns.thesis_memory_report)) if getattr(ns, "thesis_memory_report", "") else None
    cohorts = load_strategy_cohort_report_payload(Path(ns.strategy_cohort_report)) if getattr(ns, "strategy_cohort_report", "") else None
    doctrine = load_doctrine_adaptation_report_payload(Path(ns.doctrine_adaptation_report)) if getattr(ns, "doctrine_adaptation_report", "") else None
    priorities = load_research_priority_report_payload(Path(ns.research_priority_report)) if getattr(ns, "research_priority_report", "") else None
    execution_memory = load_research_execution_memory_report_payload(Path(ns.research_execution_memory_report)) if getattr(ns, "research_execution_memory_report", "") else None
    thesis_graph = load_thesis_graph_report_payload(Path(ns.thesis_graph_report)) if getattr(ns, "thesis_graph_report", "") else None
    strategic_tension = load_strategic_tension_report_payload(Path(ns.strategic_tension_report)) if getattr(ns, "strategic_tension_report", "") else None
    strategic_narrative = load_strategic_narrative_report_payload(Path(ns.strategic_narrative_report)) if getattr(ns, "strategic_narrative_report", "") else None
    strategic_memory = load_strategic_memory_horizon_report_payload(Path(ns.strategic_memory_horizon_report)) if getattr(ns, "strategic_memory_horizon_report", "") else None
    contradiction = load_contradiction_resolution_report_payload(Path(ns.contradiction_resolution_report)) if getattr(ns, "contradiction_resolution_report", "") else None
    intervention = load_strategic_intervention_report_payload(Path(ns.strategic_intervention_report)) if getattr(ns, "strategic_intervention_report", "") else None
    report = build_strategic_campaign_payload(
        payload=payload,
        fusion_report=fusion,
        thesis_memory_report=thesis,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        research_execution_memory_report=execution_memory,
        thesis_graph_report=thesis_graph,
        strategic_tension_report=strategic_tension,
        strategic_narrative_report=strategic_narrative,
        strategic_memory_horizon_report=strategic_memory,
        contradiction_resolution_report=contradiction,
        intervention_report=intervention,
        repo_root=Path(ns.repo_root) if getattr(ns, "repo_root", "") else None,
        search_root=Path(ns.search_root) if getattr(ns, "search_root", "") else None,
        doctrine_adaptation_report_path=Path(ns.doctrine_adaptation_report) if getattr(ns, "doctrine_adaptation_report", "") else None,
        research_priority_report_path=Path(ns.research_priority_report) if getattr(ns, "research_priority_report", "") else None,
        intervention_report_path=Path(ns.strategic_intervention_report) if getattr(ns, "strategic_intervention_report", "") else None,
    )
    output_path = Path(ns.output) if ns.output else Path(ns.input).with_name("ORACLE_STRATEGIC_CAMPAIGN_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_strategic_campaign_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_scenario_lab(ns: argparse.Namespace) -> int:
    payload = load_oracle_input_payload(Path(ns.input))
    fusion = load_fusion_report_payload(Path(ns.fusion_report)) if ns.fusion_report else None
    plan = load_scenario_plan_input_payload(Path(ns.scenario_plan)) if ns.scenario_plan else None
    doctrine = load_doctrine_adaptation_report_payload(Path(ns.doctrine_adaptation_report)) if getattr(ns, "doctrine_adaptation_report", "") else None
    priorities = load_research_priority_report_payload(Path(ns.research_priority_report)) if getattr(ns, "research_priority_report", "") else None
    report = build_scenario_lab_payload(
        payload=payload,
        plan=plan,
        baseline_fusion_report=fusion,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        doctrine_adaptation_report_path=(Path(ns.doctrine_adaptation_report) if getattr(ns, "doctrine_adaptation_report", "") else None),
        research_priority_report_path=(Path(ns.research_priority_report) if getattr(ns, "research_priority_report", "") else None),
        repo_root=(Path(ns.repo_root) if getattr(ns, "repo_root", "") else None),
        search_root=(Path(ns.search_root) if getattr(ns, "search_root", "") else None),
    )
    output_path = Path(ns.output) if ns.output else Path(ns.input).with_name("ORACLE_SCENARIO_LAB_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_scenario_lab_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_strategy_cohort(ns: argparse.Namespace) -> int:
    payload = load_oracle_input_payload(Path(ns.input))
    strategic_memory = load_strategic_memory_horizon_report_payload(Path(ns.strategic_memory_horizon_report)) if getattr(ns, "strategic_memory_horizon_report", "") else None
    fusion = load_fusion_report_payload(Path(ns.fusion_report)) if ns.fusion_report else build_strategic_fusion_payload(payload=payload)
    posterior = build_strategy_health_posterior_payload(payload=payload, fusion_report=fusion)
    previous_fusion = load_fusion_report_payload(Path(ns.previous_fusion_report)) if ns.previous_fusion_report else None
    transition = build_regime_transition_payload(previous=previous_fusion, current=fusion) if previous_fusion is not None else None
    thesis = build_thesis_memory_payload(
        payload=payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        previous_report=(load_thesis_memory_report_payload(Path(ns.previous_thesis_memory_report)) if ns.previous_thesis_memory_report else None),
        execution_memory_report=(load_research_execution_memory_report_payload(Path(ns.research_execution_memory_report)) if getattr(ns, "research_execution_memory_report", "") else None),
    )
    queue = build_opportunity_queue_payload(
        payload=payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        strategic_memory_horizon_report=strategic_memory,
    )
    plan = load_scenario_plan_input_payload(Path(ns.scenario_plan)) if ns.scenario_plan else None
    doctrine = load_doctrine_adaptation_report_payload(Path(ns.doctrine_adaptation_report)) if getattr(ns, "doctrine_adaptation_report", "") else None
    priorities = load_research_priority_report_payload(Path(ns.research_priority_report)) if getattr(ns, "research_priority_report", "") else None
    report = build_strategy_cohort_payload(
        payload=payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        queue_report=queue,
        thesis_memory_report=thesis,
        scenario_plan=plan,
        previous_fusion_report=previous_fusion,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        doctrine_adaptation_report_path=(Path(ns.doctrine_adaptation_report) if getattr(ns, "doctrine_adaptation_report", "") else None),
        research_priority_report_path=(Path(ns.research_priority_report) if getattr(ns, "research_priority_report", "") else None),
        repo_root=(Path(ns.repo_root) if getattr(ns, "repo_root", "") else None),
        search_root=(Path(ns.search_root) if getattr(ns, "search_root", "") else None),
    )
    output_path = Path(ns.output) if ns.output else Path(ns.input).with_name("ORACLE_STRATEGY_COHORT_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_strategy_cohort_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_doctrine_adaptation(ns: argparse.Namespace) -> int:
    payload = load_oracle_input_payload(Path(ns.input))
    fusion = load_fusion_report_payload(Path(ns.fusion_report)) if ns.fusion_report else build_strategic_fusion_payload(payload=payload)
    posterior = build_strategy_health_posterior_payload(payload=payload, fusion_report=fusion)
    previous_fusion = load_fusion_report_payload(Path(ns.previous_fusion_report)) if ns.previous_fusion_report else None
    transition = build_regime_transition_payload(previous=previous_fusion, current=fusion) if previous_fusion is not None else None
    thesis = build_thesis_memory_payload(
        payload=payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        previous_report=(load_thesis_memory_report_payload(Path(ns.previous_thesis_memory_report)) if ns.previous_thesis_memory_report else None),
    )
    plan = load_scenario_plan_input_payload(Path(ns.scenario_plan)) if ns.scenario_plan else None
    scenario_lab = build_scenario_lab_payload(
        payload=payload,
        plan=plan,
        baseline_fusion_report=fusion,
    )
    cohorts = build_strategy_cohort_payload(
        payload=payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        thesis_memory_report=thesis,
        scenario_plan=plan,
        previous_fusion_report=previous_fusion,
    )
    strategic_memory = load_strategic_memory_horizon_report_payload(Path(ns.strategic_memory_horizon_report)) if getattr(ns, "strategic_memory_horizon_report", "") else None
    execution_memory = load_research_execution_memory_report_payload(Path(ns.research_execution_memory_report)) if getattr(ns, "research_execution_memory_report", "") else None
    report = build_doctrine_adaptation_payload(
        payload=payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        previous_fusion_report=previous_fusion,
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=cohorts,
        execution_memory_report=execution_memory,
        strategic_memory_horizon_report=strategic_memory,
    )
    output_path = Path(ns.output) if ns.output else Path(ns.input).with_name("ORACLE_DOCTRINE_ADAPTATION_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_doctrine_adaptation_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_research_planner(ns: argparse.Namespace) -> int:
    payload = load_oracle_input_payload(Path(ns.input))
    fusion = load_fusion_report_payload(Path(ns.fusion_report)) if ns.fusion_report else build_strategic_fusion_payload(payload=payload)
    previous_fusion = load_fusion_report_payload(Path(ns.previous_fusion_report)) if ns.previous_fusion_report else None
    strategic_memory = load_strategic_memory_horizon_report_payload(Path(ns.strategic_memory_horizon_report)) if getattr(ns, "strategic_memory_horizon_report", "") else None
    transition = build_regime_transition_payload(previous_fusion, fusion) if previous_fusion is not None else None
    posterior = build_strategy_health_posterior_payload(payload=payload, fusion_report=fusion)
    thesis = build_thesis_memory_payload(
        payload=payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        previous_report=(load_thesis_memory_report_payload(Path(ns.previous_thesis_memory_report)) if ns.previous_thesis_memory_report else None),
    )
    queue = build_opportunity_queue_payload(
        payload=payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        strategic_memory_horizon_report=strategic_memory,
    )
    plan = load_scenario_plan_input_payload(Path(ns.scenario_plan)) if ns.scenario_plan else None
    scenario_lab = build_scenario_lab_payload(
        payload=payload,
        baseline_fusion_report=fusion,
        plan=plan,
    )
    cohorts = build_strategy_cohort_payload(
        payload=payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        queue_report=queue,
        thesis_memory_report=thesis,
        scenario_plan=plan,
        previous_fusion_report=previous_fusion,
        repo_root=(Path(ns.repo_root) if getattr(ns, "repo_root", "") else None),
        search_root=(Path(ns.search_root) if getattr(ns, "search_root", "") else None),
    )
    doctrine = build_doctrine_adaptation_payload(
        payload=payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        previous_fusion_report=previous_fusion,
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=cohorts,
        strategic_memory_horizon_report=strategic_memory,
    )
    report = build_research_priority_payload(
        payload=payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        previous_fusion_report=previous_fusion,
        queue_report=queue,
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        strategic_memory_horizon_report=strategic_memory,
        repo_root=Path(ns.repo_root) if getattr(ns, "repo_root", "") else None,
        search_root=Path(ns.search_root) if getattr(ns, "search_root", "") else None,
        doctrine_adaptation_report_path=Path(ns.doctrine_adaptation_report) if getattr(ns, "doctrine_adaptation_report", "") else None,
    )
    output_path = Path(ns.output) if ns.output else Path(ns.input).with_name("ORACLE_RESEARCH_PRIORITY_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_research_priority_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_research_execution_memory(ns: argparse.Namespace) -> int:
    priority_report = load_research_priority_report_payload(Path(ns.research_priority_report))
    outcome_input = load_investigation_outcome_input_payload(Path(ns.outcome_input))
    report = build_research_execution_memory_payload(
        priority_report=priority_report,
        outcome_input=outcome_input,
        doctrine_adaptation_report_path=(Path(ns.doctrine_adaptation_report) if getattr(ns, "doctrine_adaptation_report", "") else None),
        research_priority_report_path=Path(ns.research_priority_report),
        repo_root=(Path(ns.repo_root) if getattr(ns, "repo_root", "") else None),
        search_root=(Path(ns.search_root) if getattr(ns, "search_root", "") else None),
    )
    output_path = Path(ns.output) if ns.output else Path(ns.research_priority_report).with_name("ORACLE_RESEARCH_EXECUTION_MEMORY_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_research_execution_memory_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_thesis_graph(ns: argparse.Namespace) -> int:
    payload = load_oracle_input_payload(Path(ns.input))
    fusion = load_fusion_report_payload(Path(ns.fusion_report)) if ns.fusion_report else build_strategic_fusion_payload(payload=payload)
    thesis = load_thesis_memory_report_payload(Path(ns.thesis_memory_report)) if getattr(ns, "thesis_memory_report", "") else None
    cohorts = load_strategy_cohort_report_payload(Path(ns.strategy_cohort_report)) if getattr(ns, "strategy_cohort_report", "") else None
    doctrine = load_doctrine_adaptation_report_payload(Path(ns.doctrine_adaptation_report)) if getattr(ns, "doctrine_adaptation_report", "") else None
    priorities = load_research_priority_report_payload(Path(ns.research_priority_report)) if getattr(ns, "research_priority_report", "") else None
    execution_memory = load_research_execution_memory_report_payload(Path(ns.research_execution_memory_report)) if getattr(ns, "research_execution_memory_report", "") else None
    report = build_thesis_graph_payload(
        payload=payload,
        fusion_report=fusion,
        thesis_memory_report=thesis,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        research_execution_memory_report=execution_memory,
        doctrine_adaptation_report_path=(Path(ns.doctrine_adaptation_report) if getattr(ns, "doctrine_adaptation_report", "") else None),
        research_priority_report_path=(Path(ns.research_priority_report) if getattr(ns, "research_priority_report", "") else None),
        repo_root=(Path(ns.repo_root) if getattr(ns, "repo_root", "") else None),
        search_root=(Path(ns.search_root) if getattr(ns, "search_root", "") else None),
    )
    output_path = Path(ns.output) if ns.output else Path(ns.input).with_name("ORACLE_THESIS_GRAPH_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_thesis_graph_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_strategic_narrative(ns: argparse.Namespace) -> int:
    payload = load_oracle_input_payload(Path(ns.input))
    fusion = load_fusion_report_payload(Path(ns.fusion_report)) if getattr(ns, "fusion_report", "") else build_strategic_fusion_payload(payload=payload)
    thesis = load_thesis_memory_report_payload(Path(ns.thesis_memory_report)) if getattr(ns, "thesis_memory_report", "") else None
    cohorts = load_strategy_cohort_report_payload(Path(ns.strategy_cohort_report)) if getattr(ns, "strategy_cohort_report", "") else None
    doctrine = load_doctrine_adaptation_report_payload(Path(ns.doctrine_adaptation_report)) if getattr(ns, "doctrine_adaptation_report", "") else None
    priorities = load_research_priority_report_payload(Path(ns.research_priority_report)) if getattr(ns, "research_priority_report", "") else None
    execution_memory = load_research_execution_memory_report_payload(Path(ns.research_execution_memory_report)) if getattr(ns, "research_execution_memory_report", "") else None
    thesis_graph = load_thesis_graph_report_payload(Path(ns.thesis_graph_report)) if getattr(ns, "thesis_graph_report", "") else None
    strategic_tension = load_strategic_tension_report_payload(Path(ns.strategic_tension_report)) if getattr(ns, "strategic_tension_report", "") else None
    report = build_strategic_narrative_payload(
        payload=payload,
        fusion_report=fusion,
        thesis_memory_report=thesis,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        research_execution_memory_report=execution_memory,
        thesis_graph_report=thesis_graph,
        strategic_tension_report=strategic_tension,
        doctrine_adaptation_report_path=Path(ns.doctrine_adaptation_report) if getattr(ns, "doctrine_adaptation_report", "") else None,
        research_priority_report_path=Path(ns.research_priority_report) if getattr(ns, "research_priority_report", "") else None,
        repo_root=Path(ns.repo_root) if getattr(ns, "repo_root", "") else None,
        search_root=Path(ns.search_root) if getattr(ns, "search_root", "") else None,
    )
    output_path = Path(ns.output) if ns.output else Path(ns.input).with_name("ORACLE_STRATEGIC_NARRATIVE_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_strategic_narrative_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_strategic_tension(ns: argparse.Namespace) -> int:
    payload = load_oracle_input_payload(Path(ns.input))
    fusion = load_fusion_report_payload(Path(ns.fusion_report)) if getattr(ns, "fusion_report", "") else build_strategic_fusion_payload(payload=payload)
    thesis = load_thesis_memory_report_payload(Path(ns.thesis_memory_report)) if getattr(ns, "thesis_memory_report", "") else None
    cohorts = load_strategy_cohort_report_payload(Path(ns.strategy_cohort_report)) if getattr(ns, "strategy_cohort_report", "") else None
    doctrine = load_doctrine_adaptation_report_payload(Path(ns.doctrine_adaptation_report)) if getattr(ns, "doctrine_adaptation_report", "") else None
    priorities = load_research_priority_report_payload(Path(ns.research_priority_report)) if getattr(ns, "research_priority_report", "") else None
    execution_memory = load_research_execution_memory_report_payload(Path(ns.research_execution_memory_report)) if getattr(ns, "research_execution_memory_report", "") else None
    thesis_graph = load_thesis_graph_report_payload(Path(ns.thesis_graph_report)) if getattr(ns, "thesis_graph_report", "") else None
    report = build_strategic_tension_payload(
        payload=payload,
        fusion_report=fusion,
        thesis_memory_report=thesis,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        research_execution_memory_report=execution_memory,
        thesis_graph_report=thesis_graph,
        doctrine_adaptation_report_path=Path(ns.doctrine_adaptation_report) if getattr(ns, "doctrine_adaptation_report", "") else None,
        research_priority_report_path=Path(ns.research_priority_report) if getattr(ns, "research_priority_report", "") else None,
        repo_root=Path(ns.repo_root) if getattr(ns, "repo_root", "") else None,
        search_root=Path(ns.search_root) if getattr(ns, "search_root", "") else None,
    )
    output_path = Path(ns.output) if ns.output else Path(ns.input).with_name("ORACLE_STRATEGIC_TENSION_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_strategic_tension_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0
