from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategy_validator.cli.oracle_cli_common import write_json
from strategy_validator.application import (
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


def cmd_oracle_advisory(ns: argparse.Namespace) -> int:
    payload = load_oracle_input_payload(Path(ns.input))
    attestation = build_morning_attestation_payload(payload=payload)
    attestation_output = Path(ns.output) if ns.output else Path(ns.input).with_name("ORACLE_MORNING_ATTESTATION.json")
    write_json(attestation_output, attestation.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else attestation_output.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_morning_attestation_markdown_payload(attestation), encoding="utf-8")
    sys.stdout.write(json.dumps(attestation.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_sensor_ingest(ns: argparse.Namespace) -> int:
    payload = load_sensor_ingestion_input_payload(Path(ns.input))
    report = normalize_sensor_ingestion_payload(payload)
    output_path = Path(ns.output) if ns.output else Path(ns.input).with_name("ORACLE_SENSOR_INGESTION_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    advisory_input_output = Path(ns.advisory_input_output) if ns.advisory_input_output else output_path.with_name("ORACLE_ADVISORY_INPUT.json")
    write_json(advisory_input_output, report.advisory_input.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_sensor_ingestion_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_signal_fusion(ns: argparse.Namespace) -> int:
    payload = load_oracle_input_payload(Path(ns.input))
    report = build_strategic_fusion_payload(
        payload=payload,
        doctrine_adaptation_report_path=(Path(ns.doctrine_adaptation_report) if getattr(ns, "doctrine_adaptation_report", "") else None),
        research_priority_report_path=(Path(ns.research_priority_report) if getattr(ns, "research_priority_report", "") else None),
        repo_root=(Path(ns.repo_root) if getattr(ns, "repo_root", "") else None),
        search_root=(Path(ns.search_root) if getattr(ns, "search_root", "") else None),
    )
    output_path = Path(ns.output) if ns.output else Path(ns.input).with_name("ORACLE_STRATEGIC_FUSION_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_strategic_fusion_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_strategy_health_posterior(ns: argparse.Namespace) -> int:
    payload = load_oracle_input_payload(Path(ns.input))
    fusion = load_fusion_report_payload(Path(ns.fusion_report)) if ns.fusion_report else build_strategic_fusion_payload(payload=payload)
    doctrine = load_doctrine_adaptation_report_payload(Path(ns.doctrine_adaptation_report)) if getattr(ns, "doctrine_adaptation_report", "") else None
    priorities = load_research_priority_report_payload(Path(ns.research_priority_report)) if getattr(ns, "research_priority_report", "") else None
    report = build_strategy_health_posterior_payload(
        payload=payload,
        fusion_report=fusion,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        doctrine_adaptation_report_path=(Path(ns.doctrine_adaptation_report) if getattr(ns, "doctrine_adaptation_report", "") else None),
        research_priority_report_path=(Path(ns.research_priority_report) if getattr(ns, "research_priority_report", "") else None),
        repo_root=(Path(ns.repo_root) if getattr(ns, "repo_root", "") else None),
        search_root=(Path(ns.search_root) if getattr(ns, "search_root", "") else None),
    )
    output_path = Path(ns.output) if ns.output else Path(ns.input).with_name("ORACLE_STRATEGY_HEALTH_POSTERIOR_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_strategy_health_posterior_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_regime_transition_signal(ns: argparse.Namespace) -> int:
    previous = load_fusion_report_payload(Path(ns.previous_fusion_report))
    current = load_fusion_report_payload(Path(ns.current_fusion_report))
    report = build_regime_transition_payload(
        previous=previous,
        current=current,
        doctrine_adaptation_report_path=(Path(ns.doctrine_adaptation_report) if getattr(ns, "doctrine_adaptation_report", "") else None),
        research_priority_report_path=(Path(ns.research_priority_report) if getattr(ns, "research_priority_report", "") else None),
        repo_root=(Path(ns.repo_root) if getattr(ns, "repo_root", "") else None),
        search_root=(Path(ns.search_root) if getattr(ns, "search_root", "") else None),
    )
    output_path = Path(ns.output) if ns.output else Path(ns.current_fusion_report).with_name("ORACLE_REGIME_TRANSITION_SIGNAL_REPORT.json")
    write_json(output_path, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else output_path.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_regime_transition_markdown_payload(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_strategic_stack_evidence(ns: argparse.Namespace) -> int:
    try:
        manifest, envelope = build_strategic_stack_evidence_bundle_payload(
            input_path=Path(ns.input),
            briefing_report_path=Path(ns.briefing_report),
            repo_root=Path(ns.repo_root) if ns.repo_root else None,
            markdown_path=Path(ns.markdown_path) if ns.markdown_path else None,
            artifact_paths=[Path(path) for path in getattr(ns, "artifact", [])],
            signing_private_key_path=Path(ns.signing_private_key) if ns.signing_private_key else None,
        )
    except (FileNotFoundError, ValueError) as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    output = Path(ns.output) if ns.output else Path(ns.briefing_report).with_name("ORACLE_STRATEGIC_STACK_EVIDENCE.json")
    write_json(output, manifest.model_dump(mode="json"))
    if envelope is not None:
        dsse_output = Path(ns.dsse_output) if ns.dsse_output else output.with_suffix(".dsse.json")
        write_json(dsse_output, envelope.model_dump(mode="json"))
    sys.stdout.write(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_verify_oracle_strategic_stack_evidence(ns: argparse.Namespace) -> int:
    try:
        verification = verify_strategic_stack_evidence_bundle_payload(
            manifest_path=Path(ns.manifest),
            repo_root=Path(ns.repo_root) if ns.repo_root else None,
            dsse_path=Path(ns.dsse) if ns.dsse else None,
            public_key_path=Path(ns.public_key) if ns.public_key else None,
        )
    except ValueError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    output = Path(ns.output) if ns.output else Path(ns.manifest).with_name("ORACLE_STRATEGIC_STACK_EVIDENCE.verification.json")
    write_json(output, verification.model_dump(mode="json"))
    sys.stdout.write(json.dumps(verification.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0 if verification.status == "VERIFIED" else 2


def cmd_oracle_strategic_artifact_evidence(ns: argparse.Namespace) -> int:
    try:
        manifest, envelope = build_strategic_artifact_evidence_bundle_payload(
            report_path=Path(ns.report),
            repo_root=Path(ns.repo_root) if ns.repo_root else None,
            markdown_path=Path(ns.markdown_path) if ns.markdown_path else None,
            artifact_paths=[Path(path) for path in getattr(ns, "artifact", [])],
            signing_private_key_path=Path(ns.signing_private_key) if ns.signing_private_key else None,
        )
    except (FileNotFoundError, ValueError) as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    output = Path(ns.output) if ns.output else Path(ns.report).with_name("ORACLE_STRATEGIC_ARTIFACT_EVIDENCE.json")
    write_json(output, manifest.model_dump(mode="json"))
    if envelope is not None:
        dsse_output = Path(ns.dsse_output) if ns.dsse_output else output.with_suffix(".dsse.json")
        write_json(dsse_output, envelope.model_dump(mode="json"))
    sys.stdout.write(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_verify_oracle_strategic_artifact_evidence(ns: argparse.Namespace) -> int:
    try:
        verification = verify_strategic_artifact_evidence_bundle_payload(
            manifest_path=Path(ns.manifest),
            repo_root=Path(ns.repo_root) if ns.repo_root else None,
            dsse_path=Path(ns.dsse) if ns.dsse else None,
            public_key_path=Path(ns.public_key) if ns.public_key else None,
        )
    except ValueError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    output = Path(ns.output) if ns.output else Path(ns.manifest).with_name("ORACLE_STRATEGIC_ARTIFACT_EVIDENCE.verification.json")
    write_json(output, verification.model_dump(mode="json"))
    sys.stdout.write(json.dumps(verification.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0 if verification.status == "VERIFIED" else 2


def cmd_oracle_evidence(ns: argparse.Namespace) -> int:
    payload = load_oracle_input_payload(Path(ns.input))
    attestation = build_morning_attestation_payload(payload=payload)
    attestation_output = Path(ns.attestation_output) if ns.attestation_output else Path(ns.input).with_name("ORACLE_MORNING_ATTESTATION.json")
    write_json(attestation_output, attestation.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else attestation_output.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_morning_attestation_markdown_payload(attestation), encoding="utf-8")
    manifest, envelope = build_oracle_evidence_bundle_payload(
        input_path=Path(ns.input),
        attestation_path=attestation_output,
        markdown_path=markdown_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        closure_snapshot_path=Path(ns.closure_snapshot) if ns.closure_snapshot else None,
        signing_private_key_path=Path(ns.signing_private_key) if ns.signing_private_key else None,
    )
    manifest_output = Path(ns.output) if ns.output else attestation_output.with_name("ORACLE_EVIDENCE.json")
    write_json(manifest_output, manifest.model_dump(mode="json"))
    if envelope is not None:
        dsse_output = Path(ns.dsse_output) if ns.dsse_output else manifest_output.with_suffix(".dsse.json")
        write_json(dsse_output, envelope.model_dump(mode="json"))
    sys.stdout.write(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0 if manifest.integrity_status == "VERIFIED" else 2


def cmd_verify_oracle_evidence(ns: argparse.Namespace) -> int:
    verification = verify_oracle_evidence_bundle_payload(
        manifest_path=Path(ns.manifest),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        dsse_path=Path(ns.dsse) if ns.dsse else None,
        public_key_path=Path(ns.public_key) if ns.public_key else None,
    )
    payload = verification.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    return 0 if verification.status == "VERIFIED" else 2
