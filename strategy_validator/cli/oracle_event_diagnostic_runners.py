"""Diagnostic, replay, and pack CLI runners for oracle event surfaces."""
from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

from strategy_validator.application import (
    build_briefing_pack_payload,
    build_incident_pack_payload,
    build_operator_diagnostic_from_checkpoint_payload,
    build_operator_diagnostic_from_report_payload,
    build_replay_audit_payload,
    build_status_pack_payload,
    emit_briefing_pack_projection_registry_payload,
    inspect_compacted_state_payload,
    materialize_briefing_pack_payload,
    materialize_incident_pack_payload,
    materialize_status_pack_payload,
    rebuild_compacted_state_payload,
    render_briefing_pack_html_payload,
    render_briefing_pack_markdown_payload,
    render_compacted_state_inspection_markdown_payload,
    render_compacted_state_rebuild_markdown_payload,
    render_incident_pack_html_payload,
    render_incident_pack_markdown_payload,
    render_operator_diagnostic_markdown_payload,
    render_replay_audit_markdown_payload,
    render_status_pack_html_payload,
    render_status_pack_markdown_payload,
)
from strategy_validator.cli.oracle_event_constitutional_runner_common import *

def cmd_oracle_diagnose(ns: argparse.Namespace) -> int:
    repo_root = Path(ns.repo_root) if ns.repo_root else None
    try:
        if ns.manifest and ns.verification:
            report = build_operator_diagnostic_from_checkpoint_payload(
                Path(ns.manifest),
                Path(ns.verification),
                repo_root=repo_root,
            )
        elif ns.report:
            report = build_operator_diagnostic_from_report_payload(Path(ns.report), repo_root=repo_root)
        else:
            sys.stderr.write("oracle-diagnose requires either --report or both --manifest and --verification.\n")
            return 2
    except (FileNotFoundError, ValueError) as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    payload = report.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    if ns.markdown_output:
        Path(ns.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        write_markdown(Path(ns.markdown_output), render_operator_diagnostic_markdown_payload(report))
    return 0

def cmd_oracle_status_pack(ns: argparse.Namespace) -> int:
    try:
        report = build_status_pack_payload(
            repo_root=Path(ns.repo_root),
            search_root=Path(ns.search_root) if ns.search_root else None,
            derived_view_report_path=Path(ns.derived_view_report) if ns.derived_view_report else None,
            constitutional_gate_report_path=Path(ns.constitutional_gate_report) if ns.constitutional_gate_report else None,
            closure_snapshot_path=Path(ns.closure_snapshot) if ns.closure_snapshot else None,
            closure_dsse_path=Path(ns.closure_dsse) if ns.closure_dsse else None,
            closure_public_key_path=Path(ns.closure_public_key) if ns.closure_public_key else None,
            governed_exception_memo_path=Path(ns.governed_exception) if ns.governed_exception else None,
            governed_exception_dsse_path=Path(ns.governed_exception_dsse) if ns.governed_exception_dsse else None,
            governed_exception_public_key_path=Path(ns.governed_exception_public_key) if ns.governed_exception_public_key else None,
        )
    except (FileNotFoundError, ValueError) as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    markdown = render_status_pack_markdown_payload(report)
    html = render_status_pack_html_payload(report)
    if ns.pack_root:
        report = materialize_status_pack_payload(Path(ns.pack_root), report, markdown=markdown, html=html)
        markdown = render_status_pack_markdown_payload(report)
        html = render_status_pack_html_payload(report)
    payload = report.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    if ns.markdown_output:
        Path(ns.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        write_markdown(Path(ns.markdown_output), markdown)
    if getattr(ns, 'html_output', ''):
        _write_text_output(ns.html_output, html)
    return 0

def cmd_oracle_incident_pack(ns: argparse.Namespace) -> int:
    try:
        report = build_incident_pack_payload(
            repo_root=Path(ns.repo_root),
            search_root=Path(ns.search_root) if ns.search_root else None,
            derived_view_report_path=Path(ns.derived_view_report) if ns.derived_view_report else None,
            constitutional_gate_report_path=Path(ns.constitutional_gate_report) if ns.constitutional_gate_report else None,
            closure_snapshot_path=Path(ns.closure_snapshot) if ns.closure_snapshot else None,
            closure_dsse_path=Path(ns.closure_dsse) if ns.closure_dsse else None,
            closure_public_key_path=Path(ns.closure_public_key) if ns.closure_public_key else None,
            governed_exception_memo_path=Path(ns.governed_exception) if ns.governed_exception else None,
            governed_exception_dsse_path=Path(ns.governed_exception_dsse) if ns.governed_exception_dsse else None,
            governed_exception_public_key_path=Path(ns.governed_exception_public_key) if ns.governed_exception_public_key else None,
        )
    except (FileNotFoundError, ValueError) as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    markdown = render_incident_pack_markdown_payload(report)
    html = render_incident_pack_html_payload(report)
    if ns.pack_root:
        report = materialize_incident_pack_payload(Path(ns.pack_root), report, markdown=markdown, html=html)
        markdown = render_incident_pack_markdown_payload(report)
        html = render_incident_pack_html_payload(report)
    payload = report.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    if ns.markdown_output:
        Path(ns.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        write_markdown(Path(ns.markdown_output), markdown)
    if getattr(ns, 'html_output', ''):
        _write_text_output(ns.html_output, html)
    return 0

def cmd_oracle_compacted_state_inspect(ns: argparse.Namespace) -> int:
    try:
        report = inspect_compacted_state_payload(
            lane_path=Path(ns.log_path),
            checkpoint_metadata_path=Path(ns.checkpoint_metadata),
        )
    except (FileNotFoundError, ValueError) as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    payload = report.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    if ns.markdown_output:
        Path(ns.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        write_markdown(Path(ns.markdown_output), render_compacted_state_inspection_markdown_payload(report))
    return 0 if report.replay_status in {"CURRENT", "STALE"} else 2

def cmd_oracle_compacted_state_rebuild(ns: argparse.Namespace) -> int:
    try:
        report = rebuild_compacted_state_payload(
            lane_path=Path(ns.log_path),
            checkpoint_metadata_path=Path(ns.checkpoint_metadata),
        )
    except (FileNotFoundError, ValueError) as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    payload = report.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    if ns.markdown_output:
        Path(ns.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        write_markdown(Path(ns.markdown_output), render_compacted_state_rebuild_markdown_payload(report))
    return 0

def cmd_oracle_briefing_pack(ns: argparse.Namespace) -> int:
    try:
        report = build_briefing_pack_payload(
            repo_root=Path(ns.repo_root),
            search_root=Path(ns.search_root) if ns.search_root else None,
            derived_view_report_path=Path(ns.derived_view_report) if ns.derived_view_report else None,
            constitutional_gate_report_path=Path(ns.constitutional_gate_report) if ns.constitutional_gate_report else None,
            closure_snapshot_path=Path(ns.closure_snapshot) if ns.closure_snapshot else None,
            closure_dsse_path=Path(ns.closure_dsse) if ns.closure_dsse else None,
            closure_public_key_path=Path(ns.closure_public_key) if ns.closure_public_key else None,
            governed_exception_memo_path=Path(ns.governed_exception) if ns.governed_exception else None,
            governed_exception_dsse_path=Path(ns.governed_exception_dsse) if ns.governed_exception_dsse else None,
            governed_exception_public_key_path=Path(ns.governed_exception_public_key) if ns.governed_exception_public_key else None,
            strategic_briefing_report_path=Path(ns.strategic_briefing_report) if ns.strategic_briefing_report else None,
            strategic_narrative_report_path=Path(ns.strategic_narrative_report) if getattr(ns, "strategic_narrative_report", "") else None,
            strategic_memory_horizon_report_path=Path(ns.strategic_memory_horizon_report) if getattr(ns, "strategic_memory_horizon_report", "") else None,
            contradiction_resolution_report_path=Path(ns.contradiction_resolution_report) if getattr(ns, "contradiction_resolution_report", "") else None,
            strategic_intervention_report_path=Path(ns.strategic_intervention_report) if getattr(ns, "strategic_intervention_report", "") else None,
            strategic_campaign_report_path=Path(ns.strategic_campaign_report) if getattr(ns, "strategic_campaign_report", "") else None,
            strategic_campaign_execution_report_path=Path(ns.strategic_campaign_execution_report) if getattr(ns, "strategic_campaign_execution_report", "") else None,
            thesis_memory_report_path=Path(ns.thesis_memory_report) if ns.thesis_memory_report else None,
            research_priority_report_path=Path(ns.research_priority_report) if ns.research_priority_report else None,
            research_execution_memory_report_path=Path(ns.research_execution_memory_report) if getattr(ns, "research_execution_memory_report", "") else None,
            thesis_graph_report_path=Path(ns.thesis_graph_report) if getattr(ns, "thesis_graph_report", "") else None,
            strategic_tension_report_path=Path(ns.strategic_tension_report) if getattr(ns, "strategic_tension_report", "") else None,
        )
    except (FileNotFoundError, ValueError) as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    markdown = render_briefing_pack_markdown_payload(report)
    html = render_briefing_pack_html_payload(report)
    pack_root_path: Path | None = None
    if ns.pack_root:
        pack_root_path = Path(ns.pack_root)
        report = materialize_briefing_pack_payload(pack_root_path, report, markdown=markdown, html=html)
        markdown = render_briefing_pack_markdown_payload(report)
        html = render_briefing_pack_html_payload(report)
    payload = report.model_dump(mode="json")
    output_paths: list[Path] = []
    if ns.output:
        output_path = Path(ns.output)
        write_json(output_path, payload)
        output_paths.append(output_path)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    if ns.markdown_output:
        markdown_path = Path(ns.markdown_output)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        write_markdown(markdown_path, markdown)
        output_paths.append(markdown_path)
    if ns.html_output:
        html_path = Path(ns.html_output)
        _write_text_output(ns.html_output, html)
        output_paths.append(html_path)
    registry_output_path: Path | None = None
    if pack_root_path is not None:
        output_paths.extend([
            pack_root_path / 'ORACLE_BRIEFING_PACK_REPORT.json',
            pack_root_path / 'ORACLE_BRIEFING_PACK_REPORT.md',
            pack_root_path / 'ORACLE_BRIEFING_PACK_REPORT.html',
        ])
        deduped_output_paths: list[Path] = []
        for candidate in output_paths:
            if candidate not in deduped_output_paths:
                deduped_output_paths.append(candidate)
        output_paths = deduped_output_paths
    if output_paths:
        if ns.output:
            registry_output_path = Path(ns.output).with_suffix('.projection.registry.json')
        elif ns.pack_root:
            registry_output_path = Path(ns.pack_root) / 'ORACLE_BRIEFING_PACK_REPORT.projection.registry.json'
        else:
            registry_output_path = output_paths[0].with_suffix('.projection.registry.json')
    if registry_output_path is not None:
        emit_briefing_pack_projection_registry_payload(
            registry_output_path=registry_output_path,
            repo_root=Path(ns.repo_root),
            generated_at_utc=report.generated_at_utc,
            output_paths=output_paths,
            search_root=Path(ns.search_root) if ns.search_root else None,
            derived_view_report_path=Path(ns.derived_view_report) if ns.derived_view_report else None,
            constitutional_gate_report_path=Path(ns.constitutional_gate_report) if ns.constitutional_gate_report else None,
            closure_snapshot_path=Path(ns.closure_snapshot) if ns.closure_snapshot else None,
            closure_dsse_path=Path(ns.closure_dsse) if ns.closure_dsse else None,
            governed_exception_memo_path=Path(ns.governed_exception) if ns.governed_exception else None,
            governed_exception_dsse_path=Path(ns.governed_exception_dsse) if ns.governed_exception_dsse else None,
            strategic_briefing_report_path=Path(ns.strategic_briefing_report) if ns.strategic_briefing_report else None,
            strategic_narrative_report_path=Path(ns.strategic_narrative_report) if getattr(ns, 'strategic_narrative_report', '') else None,
            strategic_memory_horizon_report_path=Path(ns.strategic_memory_horizon_report) if getattr(ns, 'strategic_memory_horizon_report', '') else None,
            contradiction_resolution_report_path=Path(ns.contradiction_resolution_report) if getattr(ns, 'contradiction_resolution_report', '') else None,
            strategic_intervention_report_path=Path(ns.strategic_intervention_report) if getattr(ns, 'strategic_intervention_report', '') else None,
            strategic_campaign_report_path=Path(ns.strategic_campaign_report) if getattr(ns, 'strategic_campaign_report', '') else None,
            strategic_campaign_execution_report_path=Path(ns.strategic_campaign_execution_report) if getattr(ns, 'strategic_campaign_execution_report', '') else None,
            thesis_memory_report_path=Path(ns.thesis_memory_report) if ns.thesis_memory_report else None,
            strategy_cohort_report_path=Path(ns.strategy_cohort_report) if getattr(ns, 'strategy_cohort_report', '') else None,
            doctrine_adaptation_report_path=Path(ns.doctrine_adaptation_report) if getattr(ns, 'doctrine_adaptation_report', '') else None,
            research_priority_report_path=Path(ns.research_priority_report) if ns.research_priority_report else None,
            research_execution_memory_report_path=Path(ns.research_execution_memory_report) if getattr(ns, 'research_execution_memory_report', '') else None,
            thesis_graph_report_path=Path(ns.thesis_graph_report) if getattr(ns, 'thesis_graph_report', '') else None,
            strategic_tension_report_path=Path(ns.strategic_tension_report) if getattr(ns, 'strategic_tension_report', '') else None,
        )
    return 0

def cmd_oracle_replay_audit(ns: argparse.Namespace) -> int:
    try:
        report = build_replay_audit_payload(
            lane_path=Path(ns.log_path),
            checkpoint_metadata_path=Path(ns.checkpoint_metadata),
            checkpoint_manifest_path=Path(ns.checkpoint_manifest) if ns.checkpoint_manifest else None,
            checkpoint_verification_path=Path(ns.checkpoint_verification) if ns.checkpoint_verification else None,
            rebuild_parity=ns.rebuild_parity,
        )
    except (FileNotFoundError, ValueError) as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    payload = report.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    if ns.markdown_output:
        Path(ns.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        write_markdown(Path(ns.markdown_output), render_replay_audit_markdown_payload(report))
    return 0 if report.replay_status == "CONSISTENT" else 2

