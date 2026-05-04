from __future__ import annotations

from strategy_validator.contracts.oracle_operator_reports import OracleIncidentPackReport, OracleStatusPackReport
from strategy_validator.control_plane.operator_pack_headers import (
    build_incident_pack_header,
    build_status_pack_header,
    render_operator_pack_header_markdown_lines,
)
from strategy_validator.control_plane.operator_section_registry import (
    compose_incident_pack_sections,
    compose_status_pack_sections,
)


def render_oracle_incident_pack_markdown(report: OracleIncidentPackReport) -> str:
    from strategy_validator.validator import oracle_diagnostics_pack_lines as _lines

    lines = render_operator_pack_header_markdown_lines(header=build_incident_pack_header(report=report))
    if report.primary_diagnostic is not None:
        lines.extend([
            "## Primary Diagnostic",
            f"- Trust status: `{report.primary_diagnostic.trust_status}`",
            f"- Summary: {report.primary_diagnostic.summary_line}",
        ])
        if report.primary_diagnostic.reasons:
            lines.append("- Reasons:")
            lines.extend([f"  - {item}" for item in report.primary_diagnostic.reasons])
        lines.append("")
    lines.extend(_lines._operator_pack_dashboard_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', preferred_pack_kinds=('briefing_pack', 'status_pack', 'incident_pack')))
    lines.extend(_lines._operator_pack_timeline_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', preferred_pack_kinds=('briefing_pack', 'status_pack', 'incident_pack')))
    lines.extend(_lines._operator_pack_comparison_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack')))
    lines.extend(_lines._operator_pack_drift_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack')))
    lines.extend(_lines._operator_pack_escalation_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_assignment_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_handoff_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_claim_lease_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_claim_operability_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_claim_lifecycle_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_lease_governance_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_execution_readiness_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_dispatch_permission_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_dispatch_outcome_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_execution_exception_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_approval_needed_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_approval_disposition_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_execution_authorization_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_execution_force_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_execution_finality_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_terminal_resolution_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_terminal_closure_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_terminal_archive_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_terminal_record_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='incident_pack', pack_kinds=('briefing_pack', 'status_pack', 'incident_pack'), operator_workboard=report.operator_workboard))
    lines.extend(["## Recommended Next Actions"])
    lines.extend([f"- {item}" for item in report.recommended_next_actions] or ["- No additional operator actions recorded."])
    lines.extend(["", "## Referenced Artifacts"])
    for artifact in report.artifacts:
        lines.extend([
            f"### {artifact.artifact_kind}",
            f"- Source path: `{artifact.source_path}`",
            f"- Pack path: `{artifact.pack_path or 'not materialized'}`",
            f"- SHA256: `{artifact.sha256}`",
            f"- Summary: {artifact.summary_line}",
        ])
        lines.append("")
    composition = compose_incident_pack_sections(report=report)
    for entry in composition.entries:
        lines.extend(entry.markdown_lines)
    return "\n".join(lines)


def render_oracle_status_pack_markdown(report: OracleStatusPackReport) -> str:
    from strategy_validator.validator import oracle_diagnostics_pack_lines as _lines

    lines = render_operator_pack_header_markdown_lines(header=build_status_pack_header(report=report))
    lines.extend(_lines._operator_pack_dashboard_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', preferred_pack_kinds=('incident_pack', 'briefing_pack', 'status_pack')))
    lines.extend(_lines._operator_pack_timeline_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', preferred_pack_kinds=('incident_pack', 'briefing_pack', 'status_pack')))
    lines.extend(_lines._operator_pack_comparison_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack')))
    lines.extend(_lines._operator_pack_drift_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack')))
    lines.extend(_lines._operator_pack_escalation_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_assignment_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_handoff_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_claim_lease_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_claim_operability_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_claim_lifecycle_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_lease_governance_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_execution_readiness_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_dispatch_permission_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_dispatch_outcome_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_execution_exception_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_approval_needed_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_approval_disposition_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_execution_authorization_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_execution_force_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_execution_finality_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_terminal_resolution_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_terminal_closure_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_terminal_archive_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_lines._operator_pack_terminal_record_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    composition = compose_status_pack_sections(report=report)
    for entry in composition.entries:
        lines.extend(entry.markdown_lines)
    return "\n".join(lines)
