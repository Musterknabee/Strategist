from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from strategy_validator.contracts.operational import (
    ClosureReleaseAttestation,
    ClosureSnapshotVerification,
    GovernedExceptionMemo,
    GovernedExceptionVerification,
)
from strategy_validator.contracts.oracle import (
    OracleConstitutionalGateReport,
    OracleDoctrineLineageVerification,
    OracleIncidentPackArtifact,
    OracleIncidentPackReport,
    OracleOperatorDiagnosticReport,
    OracleOperatorWorkboardItemReport,
    OracleOperatorWorkboardReport,
    OracleStatusPackReport,
    OracleStatusPackSection,
    OracleTrustExplanationReport,
)
from strategy_validator.projections.operator_materialization import with_report_provenance_digest
from strategy_validator.projections.operator_pack_service import (
    materialize_incident_pack_bundle,
    materialize_status_pack_bundle,
)
from strategy_validator.projections.service import select_latest_canonical_event_projection
from strategy_validator.control_plane import (
    assess_governance_plane,
    build_incident_pack_header,
    build_incident_pack_html,
    build_operator_pack_comparison_request,
    build_operator_pack_dashboard_request,
    build_operator_pack_timeline_request,
    build_operator_pack_drift_request,
    build_operator_pack_assignment_request,
    build_operator_pack_claim_lease_request,
    build_operator_pack_claim_operability_request,
    build_operator_pack_claim_lifecycle_request,
    build_operator_pack_lease_governance_request,
    build_operator_pack_execution_readiness_request,
    build_operator_pack_dispatch_permission_request,
    build_operator_pack_dispatch_outcome_request,
    build_operator_pack_execution_exception_request,
    build_operator_pack_approval_needed_request,
    build_operator_pack_approval_disposition_request,
    build_operator_pack_execution_authorization_request,
    build_operator_pack_execution_force_request,
    build_operator_pack_execution_finality_request,
    build_operator_pack_terminal_resolution_request,
    build_operator_pack_terminal_closure_request,
    build_operator_pack_terminal_archive_request,
    build_operator_pack_terminal_record_request,
    build_operator_pack_handoff_request,
    build_operator_pack_escalation_request,
    build_operator_workboard_report,
    build_status_pack_header,
    build_status_pack_html,
    compose_incident_pack_sections,
    compose_status_pack_sections,
    materialize_operator_pack_comparison,
    materialize_operator_pack_dashboard,
    materialize_operator_pack_timeline,
    materialize_operator_pack_drift,
    materialize_operator_pack_assignment,
    materialize_operator_pack_claim_lease,
    materialize_operator_pack_claim_operability,
    materialize_operator_pack_claim_lifecycle,
    materialize_operator_pack_lease_governance,
    materialize_operator_pack_execution_readiness,
    materialize_operator_pack_dispatch_permission,
    materialize_operator_pack_dispatch_outcome,
    materialize_operator_pack_execution_exception,
    materialize_operator_pack_approval_needed,
    materialize_operator_pack_approval_disposition,
    materialize_operator_pack_execution_authorization,
    materialize_operator_pack_execution_force,
    materialize_operator_pack_execution_finality,
    materialize_operator_pack_terminal_resolution,
    materialize_operator_pack_terminal_closure,
    materialize_operator_pack_terminal_archive,
    materialize_operator_pack_terminal_record,
    materialize_operator_pack_handoff,
    materialize_operator_pack_escalation,
    materialize_operator_workboard,
    render_operator_pack_comparison_markdown_lines,
    render_operator_pack_dashboard_markdown_lines,
    render_operator_pack_timeline_markdown_lines,
    render_operator_pack_drift_markdown_lines,
    render_operator_pack_assignment_markdown_lines,
    render_operator_pack_claim_lease_markdown_lines,
    render_operator_pack_claim_operability_markdown_lines,
    render_operator_pack_claim_lifecycle_markdown_lines,
    render_operator_pack_lease_governance_markdown_lines,
    render_operator_pack_execution_readiness_markdown_lines,
    render_operator_pack_dispatch_permission_markdown_lines,
    render_operator_pack_dispatch_outcome_markdown_lines,
    render_operator_pack_execution_exception_markdown_lines,
    render_operator_pack_approval_needed_markdown_lines,
    render_operator_pack_approval_disposition_markdown_lines,
    render_operator_pack_execution_authorization_markdown_lines,
    render_operator_pack_execution_force_markdown_lines,
    render_operator_pack_execution_finality_markdown_lines,
    render_operator_pack_terminal_resolution_markdown_lines,
    render_operator_pack_terminal_closure_markdown_lines,
    render_operator_pack_terminal_archive_markdown_lines,
    render_operator_pack_terminal_record_markdown_lines,
    render_operator_pack_handoff_markdown_lines,
    render_operator_pack_escalation_markdown_lines,
    render_operator_pack_header_markdown_lines,
)
from strategy_validator.validator.oracle_explain import (
    explain_checkpoint_from_paths,
    explain_lineage_verification,
    explain_report_from_path,
)
from strategy_validator.validator.oracle_schema_registry import validate_registered_schema
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.oracle_trust import (
    trust_banner_for_lineage_verification,
)
from strategy_validator.validator.oracle_strategic_artifact_evidence import discover_preferred_strategic_artifact_evidence
from strategy_validator.validator.rollout_ops import (
    build_closure_release_attestation,
    verify_closure_snapshot,
    verify_governed_exception_memo,
)
from strategy_validator.validator.oracle_constitutional import verify_oracle_doctrine_lineage
from strategy_validator.validator.oracle_diagnostics_rendering import (
    render_oracle_incident_pack_html,
    render_oracle_operator_diagnostic_markdown,
    render_oracle_status_pack_html,
)
from strategy_validator.validator.oracle_diagnostics_pack_rendering import (
    render_oracle_incident_pack_markdown,
    render_oracle_status_pack_markdown,
)

from strategy_validator.validator.oracle_diagnostics_builders import (
    _build_oracle_incident_pack_impl,
    _build_oracle_status_pack_impl,
    _status_pack_workboard_from_trust,
    build_oracle_incident_pack,
    build_oracle_operator_diagnostic_from_checkpoint,
    build_oracle_operator_diagnostic_from_report,
    build_oracle_status_pack,
    materialize_oracle_incident_pack,
    materialize_oracle_status_pack,
)


from strategy_validator.validator.oracle_diagnostics_pack_lines import (
    _closure_section,
    _operator_pack_approval_disposition_lines,
    _operator_pack_approval_needed_lines,
    _operator_pack_assignment_lines,
    _operator_pack_claim_lease_lines,
    _operator_pack_claim_lifecycle_lines,
    _operator_pack_claim_operability_lines,
    _operator_pack_comparison_lines,
    _operator_pack_dashboard_lines,
    _operator_pack_dispatch_outcome_lines,
    _operator_pack_dispatch_permission_lines,
    _operator_pack_drift_lines,
    _operator_pack_escalation_lines,
    _operator_pack_execution_authorization_lines,
    _operator_pack_execution_exception_lines,
    _operator_pack_execution_finality_lines,
    _operator_pack_execution_force_lines,
    _operator_pack_execution_readiness_lines,
    _operator_pack_handoff_lines,
    _operator_pack_lease_governance_lines,
    _operator_pack_terminal_archive_lines,
    _operator_pack_terminal_closure_lines,
    _operator_pack_terminal_record_lines,
    _operator_pack_terminal_resolution_lines,
    _operator_pack_timeline_lines,
)

def render_oracle_status_pack_markdown(report: OracleStatusPackReport) -> str:
    lines = render_operator_pack_header_markdown_lines(header=build_status_pack_header(report=report))
    lines.extend(_operator_pack_dashboard_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', preferred_pack_kinds=('incident_pack', 'briefing_pack', 'status_pack')))
    lines.extend(_operator_pack_timeline_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', preferred_pack_kinds=('incident_pack', 'briefing_pack', 'status_pack')))
    lines.extend(_operator_pack_comparison_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack')))
    lines.extend(_operator_pack_drift_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack')))
    lines.extend(_operator_pack_escalation_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_operator_pack_assignment_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_operator_pack_handoff_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_operator_pack_claim_lease_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_operator_pack_claim_operability_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_operator_pack_claim_lifecycle_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_operator_pack_lease_governance_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_operator_pack_execution_readiness_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_operator_pack_dispatch_permission_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_operator_pack_dispatch_outcome_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_operator_pack_execution_exception_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_operator_pack_approval_needed_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_operator_pack_approval_disposition_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_operator_pack_execution_authorization_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_operator_pack_execution_force_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_operator_pack_execution_finality_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_operator_pack_terminal_resolution_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_operator_pack_terminal_closure_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_operator_pack_terminal_archive_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    lines.extend(_operator_pack_terminal_record_lines(report_search_root=report.search_root, report_repo_root=report.repo_root, current_pack_kind='status_pack', pack_kinds=('incident_pack', 'briefing_pack', 'status_pack'), operator_workboard=report.operator_workboard))
    composition = compose_status_pack_sections(report=report)
    for entry in composition.entries:
        lines.extend(entry.markdown_lines)
    return "\n".join(lines)


