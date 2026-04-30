from __future__ import annotations

from pathlib import Path

from strategy_validator.contracts.oracle_operator_reports import OracleBriefingPackReport
from strategy_validator.control_plane.operator_pack_headers import (
    build_briefing_pack_header,
    render_operator_pack_header_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_html import build_briefing_pack_html
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
from strategy_validator.control_plane.operator_pack_execution_force import (
    build_operator_pack_execution_force_request,
    materialize_operator_pack_execution_force,
    render_operator_pack_execution_force_markdown_lines,
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
from strategy_validator.control_plane.operator_section_registry import compose_briefing_pack_sections

def render_oracle_briefing_pack_markdown(report: OracleBriefingPackReport) -> str:
    lines = render_operator_pack_header_markdown_lines(header=build_briefing_pack_header(report=report))
    dashboard = materialize_operator_pack_dashboard(build_operator_pack_dashboard_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', preferred_pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_navigation_items=3, max_column_items=3)) if Path(report.search_root).exists() else None
    if dashboard is not None and (dashboard.columns or dashboard.navigation.items):
        lines.extend(render_operator_pack_dashboard_markdown_lines(dashboard))
    timeline = materialize_operator_pack_timeline(build_operator_pack_timeline_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=6)) if Path(report.search_root).exists() else None
    if timeline is not None and timeline.items:
        lines.extend(render_operator_pack_timeline_markdown_lines(timeline))
    comparison = materialize_operator_pack_comparison(build_operator_pack_comparison_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if comparison is not None and comparison.items:
        lines.extend(render_operator_pack_comparison_markdown_lines(comparison))
    drift = materialize_operator_pack_drift(build_operator_pack_drift_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if drift is not None and drift.items:
        lines.extend(render_operator_pack_drift_markdown_lines(drift))
    escalation = materialize_operator_pack_escalation(build_operator_pack_escalation_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if escalation is not None and escalation.items:
        lines.extend(render_operator_pack_escalation_markdown_lines(escalation))
    assignment = materialize_operator_pack_assignment(build_operator_pack_assignment_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if assignment is not None and assignment.items:
        lines.extend(render_operator_pack_assignment_markdown_lines(assignment))
    handoff = materialize_operator_pack_handoff(build_operator_pack_handoff_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if handoff is not None and handoff.items:
        lines.extend(render_operator_pack_handoff_markdown_lines(handoff))
    claim_lease = materialize_operator_pack_claim_lease(build_operator_pack_claim_lease_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if claim_lease is not None and claim_lease.items:
        lines.extend(render_operator_pack_claim_lease_markdown_lines(claim_lease))
    claim_lifecycle = materialize_operator_pack_claim_lifecycle(build_operator_pack_claim_lifecycle_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if claim_lifecycle is not None and claim_lifecycle.items:
        lines.extend(render_operator_pack_claim_lifecycle_markdown_lines(claim_lifecycle))
    lease_governance = materialize_operator_pack_lease_governance(build_operator_pack_lease_governance_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if lease_governance is not None and lease_governance.items:
        lines.extend(render_operator_pack_lease_governance_markdown_lines(lease_governance))
    claim_operability = materialize_operator_pack_claim_operability(build_operator_pack_claim_operability_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if claim_operability is not None and claim_operability.items:
        lines.extend(render_operator_pack_claim_operability_markdown_lines(claim_operability))
    execution_readiness = materialize_operator_pack_execution_readiness(build_operator_pack_execution_readiness_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if execution_readiness is not None and execution_readiness.items:
        lines.extend(render_operator_pack_execution_readiness_markdown_lines(execution_readiness))
    dispatch_permission = materialize_operator_pack_dispatch_permission(build_operator_pack_dispatch_permission_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if dispatch_permission is not None and dispatch_permission.items:
        lines.extend(render_operator_pack_dispatch_permission_markdown_lines(dispatch_permission))
    dispatch_outcome = materialize_operator_pack_dispatch_outcome(build_operator_pack_dispatch_outcome_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if dispatch_outcome is not None and dispatch_outcome.items:
        lines.extend(render_operator_pack_dispatch_outcome_markdown_lines(dispatch_outcome))
    execution_exception = materialize_operator_pack_execution_exception(build_operator_pack_execution_exception_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if execution_exception is not None and execution_exception.items:
        lines.extend(render_operator_pack_execution_exception_markdown_lines(execution_exception))
    approval_needed = materialize_operator_pack_approval_needed(build_operator_pack_approval_needed_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if approval_needed is not None and approval_needed.items:
        lines.extend(render_operator_pack_approval_needed_markdown_lines(approval_needed))
    approval_disposition = materialize_operator_pack_approval_disposition(build_operator_pack_approval_disposition_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if approval_disposition is not None and approval_disposition.items:
        lines.extend(render_operator_pack_approval_disposition_markdown_lines(approval_disposition))
    execution_authorization = materialize_operator_pack_execution_authorization(build_operator_pack_execution_authorization_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if execution_authorization is not None and execution_authorization.items:
        lines.extend(render_operator_pack_execution_authorization_markdown_lines(execution_authorization))
    execution_force = materialize_operator_pack_execution_force(build_operator_pack_execution_force_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if execution_force is not None and execution_force.items:
        lines.extend(render_operator_pack_execution_force_markdown_lines(execution_force))
    execution_finality = materialize_operator_pack_execution_finality(build_operator_pack_execution_finality_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if execution_finality is not None and execution_finality.items:
        lines.extend(render_operator_pack_execution_finality_markdown_lines(execution_finality))
    terminal_resolution = materialize_operator_pack_terminal_resolution(build_operator_pack_terminal_resolution_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if terminal_resolution is not None and terminal_resolution.items:
        lines.extend(render_operator_pack_terminal_resolution_markdown_lines(terminal_resolution))
    terminal_closure = materialize_operator_pack_terminal_closure(build_operator_pack_terminal_closure_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if terminal_closure is not None and terminal_closure.items:
        lines.extend(render_operator_pack_terminal_closure_markdown_lines(terminal_closure))
    terminal_archive = materialize_operator_pack_terminal_archive(build_operator_pack_terminal_archive_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if terminal_archive is not None and terminal_archive.items:
        lines.extend(render_operator_pack_terminal_archive_markdown_lines(terminal_archive))
    terminal_record = materialize_operator_pack_terminal_record(build_operator_pack_terminal_record_request(search_root=Path(report.search_root), repo_root=Path(report.repo_root), current_pack_kind='briefing_pack', pack_kinds=('incident_pack', 'status_pack', 'briefing_pack'), max_items=3)) if Path(report.search_root).exists() else None
    if terminal_record is not None and terminal_record.items:
        lines.extend(render_operator_pack_terminal_record_markdown_lines(terminal_record))
    composition = compose_briefing_pack_sections(report=report)
    for entry in composition.entries:
        lines.extend(entry.markdown_lines)
    return "\n".join(lines)


def render_oracle_briefing_pack_html(report: OracleBriefingPackReport) -> str:
    return build_briefing_pack_html(report=report)
