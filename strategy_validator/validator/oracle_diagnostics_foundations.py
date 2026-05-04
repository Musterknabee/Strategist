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


_TRUST_RANK = {
    "TRUSTED": 0,
    "TRUST_RESTRICTED": 1,
    "UNTRUSTED": 2,
}



def _exact_cadence_signal_classification(*, exact_feedback_confirmation_count: int, exact_feedback_relief_count: int) -> str:
    if exact_feedback_confirmation_count > 0 and exact_feedback_confirmation_count >= exact_feedback_relief_count:
        return "EXACT_CONFIRMED_PRESSURE"
    if exact_feedback_relief_count > 0:
        return "EXACT_RELIEF_PRESSURE"
    return "AMBIENT_DRIFT"


def _exact_cadence_summary(*, exact_feedback_confirmation_count: int, exact_feedback_relief_count: int) -> str:
    classification = _exact_cadence_signal_classification(
        exact_feedback_confirmation_count=exact_feedback_confirmation_count,
        exact_feedback_relief_count=exact_feedback_relief_count,
    )
    if classification == "EXACT_CONFIRMED_PRESSURE":
        return f"pressure is being driven by repeated exact sealed confirmations ({exact_feedback_confirmation_count})"
    if classification == "EXACT_RELIEF_PRESSURE":
        return f"pressure is being softened by repeated exact sealed relief signals ({exact_feedback_relief_count})"
    return "pressure is currently explained by broader ambient doctrine drift rather than repeated exact sealed cadence signals"

def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_json(payload: dict) -> str:
    stable = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return _sha256_bytes(stable)


def _with_provenance_digest(report: OracleStatusPackReport | OracleIncidentPackReport):
    return with_report_provenance_digest(report)


def _artifact_sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())




def _load_temporal_lane_status(path: Path) -> TemporalLaneStatus:
    return TemporalLaneStatus.model_validate(_load_json(path))

def _unique(items: Iterable[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if normalized and normalized not in output:
            output.append(normalized)
    return output


def _facts_from_explanation(explanation: OracleTrustExplanationReport, *, categories: set[str] | None = None) -> list[str]:
    facts: list[str] = []
    for node in explanation.nodes:
        if categories is not None and node.category not in categories:
            continue
        if node.detail:
            facts.append(node.detail)
        facts.extend(node.facts)
    return _unique(facts)


def _actions_from_explanation(explanation: OracleTrustExplanationReport) -> list[str]:
    actions: list[str] = []
    for node in explanation.nodes:
        if node.category == "operator_action":
            actions.extend(node.facts)
    return _unique(actions)


def _find_latest(search_root: Path, candidates: Iterable[str]) -> Path | None:
    discovered: list[Path] = []
    candidate_set = set(candidates)
    for path in search_root.rglob("*"):
        if path.is_file() and path.name in candidate_set:
            discovered.append(path)
    if not discovered:
        return None
    discovered.sort(key=lambda path: (path.stat().st_mtime, str(path)))
    return discovered[-1]




def _status_pack_workboard_from_trust(*, trust_status: str, issued_at_utc: datetime, surface_label: str) -> OracleOperatorWorkboardReport:
    if trust_status == "UNTRUSTED":
        support_chain_trust_status = "UNTRUSTED"
        support_chain_remediation_status = "REMEDIATION_REQUIRED"
        operator_readiness = "HOLD_FOR_REFRESH"
        remediation_actions = ["Repair constitutional trust blockers before claiming this surface for downstream use."]
    elif trust_status == "TRUST_RESTRICTED":
        support_chain_trust_status = "TRUST_RESTRICTED"
        support_chain_remediation_status = "REMEDIATION_RECOMMENDED"
        operator_readiness = "REVIEW_WITH_CAUTION"
        remediation_actions = ["Review restricted trust findings before treating this surface as routine operator context."]
    else:
        support_chain_trust_status = "TRUSTED"
        support_chain_remediation_status = "NO_REMEDIATION"
        operator_readiness = "READY_FOR_REVIEW"
        remediation_actions = []
    governance_plane = assess_governance_plane(
        evidence_freshness_status='EVIDENCE_CURRENT',
        evidence_integrity_status='INTEGRITY_VERIFIED',
        evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED',
        support_chain_trust_status=support_chain_trust_status,
        support_chain_remediation_status=support_chain_remediation_status,
        support_chain_remediation_actions=remediation_actions,
        operator_readiness=operator_readiness,
        surface_label=surface_label,
    )
    workboard = materialize_operator_workboard(
        governance_plane=governance_plane,
        issued_at_utc=issued_at_utc,
        board_label='status_pack_workboard',
    )
    return build_operator_workboard_report(workboard=workboard)
def _default_public_key(repo_root: Path) -> Path | None:
    for candidate in (
        repo_root / ".keys" / "closure_snapshot_public.pem",
        repo_root / "keys" / "closure_snapshot_public.pem",
    ):
        if candidate.exists():
            return candidate
    return None


def _resolve_explanation_from_report(report_path: Path, *, repo_root: Path | None) -> tuple[dict, OracleTrustExplanationReport]:
    payload = _load_json(report_path)
    validate_registered_schema(payload, expected_families={"oracle"})
    explanation = explain_report_from_path(report_path, repo_root=repo_root)
    return payload, explanation


def build_oracle_operator_diagnostic_from_report(
    report_path: Path,
    *,
    repo_root: Path | None = None,
) -> OracleOperatorDiagnosticReport:
    payload, explanation = _resolve_explanation_from_report(report_path, repo_root=repo_root)
    resolved_repo_root = (repo_root or report_path.parent).resolve()
    artifact_evidence = discover_preferred_strategic_artifact_evidence(report_path=report_path, repo_root=resolved_repo_root, search_root=resolved_repo_root / 'docs' / 'artifacts')
    registration = validate_registered_schema(payload, expected_families={"oracle"})
    reasons = _facts_from_explanation(explanation, categories={"trust", "lineage", "evidence", "policy", "warning"})
    actions = _actions_from_explanation(explanation)
    blocked = False
    diagnostic_kind = "why_restricted"
    if registration.schema_version == "oracle_constitutional_gate_report/v1":
        report = OracleConstitutionalGateReport.model_validate(payload)
        blocked = (not report.trusted_for_constitutional_use) or explanation.trust_status != "TRUSTED"
        diagnostic_kind = "why_blocked"
        reasons = _unique(list(report.blocking_reasons) + reasons) or [explanation.summary_line]
        actions = _unique(list(report.operator_actions) + actions)
    elif registration.schema_version == "oracle_doctrine_lineage_verification/v1":
        report = OracleDoctrineLineageVerification.model_validate(payload)
        reasons = _unique(
            [
                explanation.summary_line,
                *report.missing_required_layers,
                *report.parse_failures,
                *report.integrity_warnings,
            ]
        )
        actions = _unique(list(report.operator_actions) + actions)
    else:
        reasons = reasons or [explanation.summary_line]
    if artifact_evidence is not None:
        reasons = _unique([
            *reasons,
            f"sealed_strategic_evidence_manifest={artifact_evidence.get('manifest_path')}",
            f"sealed_strategic_evidence_kind={artifact_evidence.get('artifact_kind')}",
            f"sealed_strategic_evidence_status={artifact_evidence.get('evidence_status')}",
        ])
    if explanation.trust_status == "TRUSTED" and not blocked:
        trusted_reasons = [f"Subject is currently fully trusted: {explanation.summary_line}"]
        if artifact_evidence is not None:
            trusted_reasons.append(f"sealed_strategic_evidence_manifest={artifact_evidence.get('manifest_path')}")
        if explanation.exact_feedback_confirmation_count:
            trusted_reasons.append(f"exact_feedback_confirmation_count={explanation.exact_feedback_confirmation_count}")
        if explanation.exact_feedback_relief_count:
            trusted_reasons.append(f"exact_feedback_relief_count={explanation.exact_feedback_relief_count}")
        reasons = trusted_reasons
    summary = (
        explanation.summary_line
        if explanation.trust_status != "TRUSTED" or blocked
        else f"No active restriction or block is present. {explanation.summary_line}"
    )
    return OracleOperatorDiagnosticReport(
        generated_at_utc=_utc_now(),
        diagnostic_kind=diagnostic_kind,
        subject_path=str(report_path),
        trust_status=explanation.trust_status,
        blocked=blocked,
        preferred_strategic_backing_source=explanation.preferred_strategic_backing_source,
        preferred_strategic_backing_classification=explanation.preferred_strategic_backing_classification,
        exact_feedback_confirmation_count=explanation.exact_feedback_confirmation_count,
        exact_feedback_relief_count=explanation.exact_feedback_relief_count,
        summary_line=summary,
        reasons=reasons,
        operator_actions=actions,
        explanation=explanation,
    )


def build_oracle_operator_diagnostic_from_checkpoint(
    manifest_path: Path,
    verification_path: Path,
    *,
    repo_root: Path | None = None,
) -> OracleOperatorDiagnosticReport:
    explanation = explain_checkpoint_from_paths(manifest_path, verification_path, repo_root=repo_root)
    reasons = _facts_from_explanation(explanation, categories={"trust", "lineage", "evidence", "warning"}) or [explanation.summary_line]
    actions = _actions_from_explanation(explanation)
    if explanation.trust_status == "TRUSTED":
        reasons = [f"Checkpoint is currently fully trusted: {explanation.summary_line}"]
    return OracleOperatorDiagnosticReport(
        generated_at_utc=_utc_now(),
        diagnostic_kind="why_restricted",
        subject_path=str(manifest_path),
        trust_status=explanation.trust_status,
        blocked=False,
        preferred_strategic_backing_source=explanation.preferred_strategic_backing_source,
        preferred_strategic_backing_classification=explanation.preferred_strategic_backing_classification,
        exact_feedback_confirmation_count=explanation.exact_feedback_confirmation_count,
        exact_feedback_relief_count=explanation.exact_feedback_relief_count,
        summary_line=explanation.summary_line,
        reasons=reasons,
        operator_actions=actions,
        explanation=explanation,
    )


