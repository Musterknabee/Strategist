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
from strategy_validator.contracts.oracle_cadence_reviews import (
    OracleConstitutionalGateReport,
    OracleDoctrineLineageVerification,
)
from strategy_validator.contracts.oracle_operator_reports import (
    OracleIncidentPackArtifact,
    OracleIncidentPackReport,
    OracleOperatorDiagnosticReport,
    OracleOperatorWorkboardItemReport,
    OracleOperatorWorkboardReport,
    OracleStatusPackReport,
    OracleStatusPackSection,
    OracleTrustExplanationReport,
)
from strategy_validator.contracts.oracle_temporal_results import TemporalLaneStatus
from strategy_validator.projections.operator_materialization import with_report_provenance_digest
from strategy_validator.projections.operator_pack_service import (
    materialize_incident_pack_bundle,
    materialize_status_pack_bundle,
)
from strategy_validator.projections.service import select_latest_canonical_event_projection
from strategy_validator.control_plane.governance_plane import assess_governance_plane
from strategy_validator.control_plane.operator_pack_headers import (
    build_incident_pack_header,
    build_status_pack_header,
    render_operator_pack_header_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_html import build_incident_pack_html, build_status_pack_html
from strategy_validator.control_plane.operator_section_registry import (
    compose_incident_pack_sections,
    compose_status_pack_sections,
)
from strategy_validator.control_plane.operator_board_sections import build_operator_workboard_report
from strategy_validator.control_plane.operator_pack_comparison import (
    build_operator_pack_comparison_request,
    materialize_operator_pack_comparison,
    render_operator_pack_comparison_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_dashboard import (
    build_operator_pack_dashboard_request,
    materialize_operator_pack_dashboard,
    render_operator_pack_dashboard_markdown_lines,
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
from strategy_validator.control_plane.operator_pack_claim_lease import (
    build_operator_pack_claim_lease_request,
    materialize_operator_pack_claim_lease,
    render_operator_pack_claim_lease_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_claim_operability import (
    build_operator_pack_claim_operability_request,
    materialize_operator_pack_claim_operability,
    render_operator_pack_claim_operability_markdown_lines,
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
from strategy_validator.control_plane.operator_pack_handoff import (
    build_operator_pack_handoff_request,
    materialize_operator_pack_handoff,
    render_operator_pack_handoff_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_escalation import (
    build_operator_pack_escalation_request,
    materialize_operator_pack_escalation,
    render_operator_pack_escalation_markdown_lines,
)
from strategy_validator.control_plane.operator_workboard import materialize_operator_workboard
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



from strategy_validator.validator.oracle_diagnostics_foundations import (
    _TRUST_RANK,
    _actions_from_explanation,
    _artifact_sha256,
    _default_public_key,
    _exact_cadence_signal_classification,
    _exact_cadence_summary,
    _facts_from_explanation,
    _find_latest,
    _load_temporal_lane_status,
    _resolve_explanation_from_report,
    _status_pack_workboard_from_trust,
    _unique,
    _with_provenance_digest,
    build_oracle_operator_diagnostic_from_report,
)

from strategy_validator.validator.oracle_diagnostics_status_pack import build_oracle_status_pack

def _build_oracle_incident_pack_impl(
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
    temporal_lane_status_path: Path | None = None,
) -> OracleIncidentPackReport:
    resolved_repo_root = repo_root.resolve()
    resolved_search_root = (search_root or (resolved_repo_root / "docs" / "artifacts")).resolve()
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
        temporal_lane_status_path=temporal_lane_status_path,
    )

    gate_path = constitutional_gate_report_path
    if gate_path is None and resolved_search_root.exists():
        gate_path = _find_latest(resolved_search_root, ["ORACLE_CONSTITUTIONAL_GATE_REPORT.json"])
    derived_path = derived_view_report_path
    if derived_path is None and resolved_search_root.exists():
        projection_selection = select_latest_canonical_event_projection(search_root=resolved_search_root, repo_root=resolved_repo_root)
        derived_path = (projection_selection.output_artifact_path if projection_selection is not None else None) or _find_latest(resolved_search_root, ["ORACLE_ROLLING_REVIEW.json", "ORACLE_HORIZON_VIEW.json", "ORACLE_DERIVED_VIEW.json"])

    primary_diagnostic: OracleOperatorDiagnosticReport | None = None
    if gate_path is not None and gate_path.exists():
        primary_diagnostic = build_oracle_operator_diagnostic_from_report(gate_path, repo_root=resolved_repo_root)
    elif derived_path is not None and derived_path.exists():
        primary_diagnostic = build_oracle_operator_diagnostic_from_report(derived_path, repo_root=resolved_repo_root)

    blocked = bool(primary_diagnostic.blocked) if primary_diagnostic is not None else False
    cadence_summary = _exact_cadence_summary(
        exact_feedback_confirmation_count=status_pack.exact_feedback_confirmation_count,
        exact_feedback_relief_count=status_pack.exact_feedback_relief_count,
    )
    if blocked:
        incident_kind = "blocked"
        summary_line = f"Canonical trust is blocked; an incident pack has been assembled for operator remediation, and {cadence_summary}."
    elif status_pack.trust_status == "UNTRUSTED":
        incident_kind = "untrusted"
        summary_line = f"Canonical trust is untrusted; review the incident pack before relying on this context, and {cadence_summary}."
    elif status_pack.trust_status == "TRUST_RESTRICTED":
        incident_kind = "restricted"
        summary_line = f"Canonical trust is restricted; review the incident pack before relying on this context, and {cadence_summary}."
    else:
        incident_kind = "trusted_context"
        summary_line = f"Canonical trust is currently healthy; this incident pack captures the current context for auditability, and {cadence_summary}."

    artifacts: list[OracleIncidentPackArtifact] = []
    lineage_path = _find_latest(resolved_search_root, ["ORACLE_DOCTRINE_LINEAGE_VERIFICATION.json"]) if resolved_search_root.exists() else None
    snapshot_path = closure_snapshot_path
    if snapshot_path is None and resolved_search_root.exists():
        snapshot_path = _find_latest(resolved_search_root, ["CLOSURE_SNAPSHOT.json"])
    memo_path = governed_exception_memo_path
    if memo_path is None and resolved_search_root.exists():
        memo_path = _find_latest(resolved_search_root, ["GOVERNED_EXCEPTION_MEMO.json"])
    candidate_artifacts = [
        ("derived_view_report", derived_path, False, "Canonical derived oracle posture used in the incident context."),
        ("constitutional_gate_report", gate_path, False, "Constitutional gate report explaining whether oracle trust is blocked."),
        ("lineage_verification", lineage_path, False, "Doctrine lineage verification that anchors the trust state."),
        ("closure_snapshot", snapshot_path, False, "Release closure snapshot associated with the current incident context."),
        ("closure_snapshot_dsse", closure_dsse_path, False, "DSSE envelope for the closure snapshot."),
        ("governed_exception_memo", memo_path, False, "Governed exception memo active in the current context."),
        ("governed_exception_dsse", governed_exception_dsse_path, False, "DSSE envelope for the governed exception memo."),
    ]
    for artifact_kind, path, required, summary in candidate_artifacts:
        if path is None:
            continue
        resolved = Path(path)
        if not resolved.exists():
            continue
        artifacts.append(
            OracleIncidentPackArtifact(
                artifact_kind=artifact_kind,
                source_path=str(resolved.resolve()),
                sha256=_artifact_sha256(resolved),
                summary_line=summary,
                required=required,
            )
        )

    recommended_next_actions = list(status_pack.operator_actions)
    if primary_diagnostic is not None:
        recommended_next_actions.extend(primary_diagnostic.operator_actions)
    report = OracleIncidentPackReport(
        generated_at_utc=_utc_now(),
        repo_root=str(resolved_repo_root),
        search_root=str(resolved_search_root),
        trust_status=status_pack.trust_status,
        incident_kind=incident_kind,
        blocked=blocked,
        exact_feedback_confirmation_count=status_pack.exact_feedback_confirmation_count,
        exact_feedback_relief_count=status_pack.exact_feedback_relief_count,
        exact_cadence_signal_classification=status_pack.exact_cadence_signal_classification,
        summary_line=summary_line,
        recommended_next_actions=_unique(recommended_next_actions),
        primary_diagnostic=primary_diagnostic,
        status_pack=status_pack,
        artifacts=artifacts,
        operator_workboard=status_pack.operator_workboard,
    )
    return _with_provenance_digest(report)

def build_oracle_incident_pack(
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
    temporal_lane_status_path: Path | None = None,
) -> OracleIncidentPackReport:
    from strategy_validator.projections.operator_pack_assembly import assemble_oracle_incident_pack

    return assemble_oracle_incident_pack(
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
        temporal_lane_status_path=temporal_lane_status_path,
    )

def materialize_oracle_incident_pack(pack_root: Path, report: OracleIncidentPackReport, *, markdown: str, html: str | None = None) -> OracleIncidentPackReport:
    return materialize_incident_pack_bundle(
        pack_root,
        report,
        markdown=markdown,
        html=html,
        render_markdown=render_oracle_incident_pack_markdown,
        render_html=render_oracle_incident_pack_html,
    )

