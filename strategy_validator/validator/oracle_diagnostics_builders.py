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
from strategy_validator.contracts.oracle_temporal import TemporalLaneStatus
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


def _build_oracle_status_pack_impl(
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
) -> OracleStatusPackReport:
    resolved_repo_root = repo_root.resolve()
    resolved_search_root = (search_root or (resolved_repo_root / "docs" / "artifacts")).resolve()
    sections: list[OracleStatusPackSection] = []
    operator_actions: list[str] = []
    active_governed_exception_ids: list[str] = []
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: str | None = None

    if resolved_search_root.exists():
        lineage = verify_oracle_doctrine_lineage(repo_root=resolved_repo_root, search_root=resolved_search_root)
        lineage_banner = trust_banner_for_lineage_verification(lineage)
        lineage_explanation = explain_lineage_verification(lineage, subject_path=str(resolved_search_root))
        sections.append(
            OracleStatusPackSection(
                section_id="lineage",
                status=lineage.seal_status,
                summary_line=lineage.summary_line,
                preferred_strategic_backing_source=getattr(lineage, "preferred_strategic_backing_source", None),
                preferred_strategic_backing_classification=getattr(lineage, "preferred_strategic_backing_classification", None),
                exact_feedback_confirmation_count=getattr(lineage, "exact_feedback_confirmation_count", 0),
                exact_feedback_relief_count=getattr(lineage, "exact_feedback_relief_count", 0),
                exact_cadence_signal_classification=_exact_cadence_signal_classification(
                    exact_feedback_confirmation_count=getattr(lineage, "exact_feedback_confirmation_count", 0),
                    exact_feedback_relief_count=getattr(lineage, "exact_feedback_relief_count", 0),
                ),
                facts=[
                    f"trust_status={lineage_banner.trust_status}",
                    f"completeness_percent={lineage.completeness_percent}",
                    f"valid_required_layer_count={lineage.valid_required_layer_count}",
                    f"required_layer_count={lineage.required_layer_count}",
                    f"exact_evidence_support_score={getattr(lineage, 'exact_evidence_support_score', 0.0):.2f}",
                    f"exact_feedback_confirmation_count={getattr(lineage, 'exact_feedback_confirmation_count', 0)}",
                    f"exact_feedback_relief_count={getattr(lineage, 'exact_feedback_relief_count', 0)}",
                ] + [f"missing_required_layer={item}" for item in lineage.missing_required_layers],
                operator_actions=list(lineage.operator_actions),
                explanation=lineage_explanation,
            )
        )
        preferred_strategic_backing_source = getattr(lineage, "preferred_strategic_backing_source", None) or preferred_strategic_backing_source
        preferred_strategic_backing_classification = getattr(lineage, "preferred_strategic_backing_classification", None) or preferred_strategic_backing_classification
        operator_actions.extend(lineage.operator_actions)

    derived_path = derived_view_report_path
    if derived_path is None and resolved_search_root.exists():
        projection_selection = select_latest_canonical_event_projection(search_root=resolved_search_root, repo_root=resolved_repo_root)
        derived_path = (projection_selection.output_artifact_path if projection_selection is not None else None) or _find_latest(resolved_search_root, ["ORACLE_ROLLING_REVIEW.json", "ORACLE_HORIZON_VIEW.json", "ORACLE_DERIVED_VIEW.json"])
    if derived_path is not None and derived_path.exists():
        payload, explanation = _resolve_explanation_from_report(derived_path, repo_root=resolved_repo_root)
        sections.append(
            OracleStatusPackSection(
                section_id="oracle_posture",
                status=explanation.trust_status,
                summary_line=payload.get("summary_line") or explanation.summary_line,
                facts=_unique([
                    f"view_label={payload.get('view_label', '')}",
                    f"window_entry_count={payload.get('window_entry_count', 0)}",
                    f"derived_classification={payload.get('derived_classification', '')}",
                    f"subject_path={derived_path}",
                ] + _facts_from_explanation(explanation, categories={"trust", "evidence", "warning"})),
                operator_actions=_actions_from_explanation(explanation),
                explanation=explanation,
            )
        )
        operator_actions.extend(_actions_from_explanation(explanation))

    gate_path = constitutional_gate_report_path
    if gate_path is None and resolved_search_root.exists():
        gate_path = _find_latest(resolved_search_root, ["ORACLE_CONSTITUTIONAL_GATE_REPORT.json"])
    temporal_path = temporal_lane_status_path
    if temporal_path is None and resolved_search_root.exists():
        temporal_path = _find_latest(resolved_search_root, ["ORACLE_TEMPORAL_LANE_STATUS.json"])
    if temporal_path is not None and temporal_path.exists():
        temporal_status = _load_temporal_lane_status(temporal_path)
        temporal_facts = [
            f"provider_id={temporal_status.provider_id}",
            f"model_name={temporal_status.model_name}",
            f"batch_window={temporal_status.batch_start_date.isoformat()}..{temporal_status.batch_end_date.isoformat()}",
            f"extraction_days={temporal_status.extraction_days}",
            f"verified_days={temporal_status.verified_days}",
            f"rejected_days={temporal_status.rejected_days}",
            f"canonicalized_days={temporal_status.canonicalized_days}",
            f"canonicalization_skipped_days={temporal_status.canonicalization_skipped_days}",
            f"appended_days={temporal_status.appended_days}",
            f"append_skipped_days={temporal_status.append_skipped_days}",
            f"verification_status={temporal_status.verification_status}",
            f"canonicalization_verification_status={temporal_status.canonicalization_verification_status}",
            f"subject_path={temporal_path}",
        ]
        if temporal_status.append_lane_path:
            temporal_facts.append(f"append_lane_path={temporal_status.append_lane_path}")
        temporal_actions = list(temporal_status.operator_lines[1:] or [temporal_status.summary_line])
        temporal_trust = "TRUSTED" if temporal_status.appended_days > 0 and temporal_status.append_skipped_days == 0 else ("TRUST_RESTRICTED" if temporal_status.verified_days > 0 else "UNTRUSTED")
        sections.append(
            OracleStatusPackSection(
                section_id="temporal_lane",
                status=temporal_status.verification_status,
                summary_line=temporal_status.summary_line,
                facts=_unique(temporal_facts),
                operator_actions=_unique(temporal_actions),
                explanation=None,
            )
        )
        operator_actions.extend(temporal_actions)

    if gate_path is not None and gate_path.exists():
        payload, explanation = _resolve_explanation_from_report(gate_path, repo_root=resolved_repo_root)
        gate_report = OracleConstitutionalGateReport.model_validate(payload)
        sections.append(
            OracleStatusPackSection(
                section_id="constitutional_gate",
                status=gate_report.trust_status,
                summary_line=gate_report.summary_line,
                preferred_strategic_backing_source=gate_report.preferred_strategic_backing_source,
                preferred_strategic_backing_classification=gate_report.preferred_strategic_backing_classification,
                exact_feedback_confirmation_count=gate_report.exact_feedback_confirmation_count,
                exact_feedback_relief_count=gate_report.exact_feedback_relief_count,
                exact_cadence_signal_classification=_exact_cadence_signal_classification(
                    exact_feedback_confirmation_count=gate_report.exact_feedback_confirmation_count,
                    exact_feedback_relief_count=gate_report.exact_feedback_relief_count,
                ),
                facts=_unique([
                    f"lineage_seal_status={gate_report.lineage_seal_status}",
                    f"minimum_required_seal_status={gate_report.minimum_required_seal_status}",
                    f"manifest_verification_status={gate_report.manifest_verification_status}",
                    f"trusted_for_constitutional_use={gate_report.trusted_for_constitutional_use}",
                    f"exact_evidence_support_score={gate_report.exact_evidence_support_score:.2f}",
                    f"exact_feedback_confirmation_count={gate_report.exact_feedback_confirmation_count}",
                    f"exact_feedback_relief_count={gate_report.exact_feedback_relief_count}",
                ] + [f"blocking_reason={item}" for item in gate_report.blocking_reasons]),
                operator_actions=list(gate_report.operator_actions),
                explanation=explanation,
            )
        )
        preferred_strategic_backing_source = gate_report.preferred_strategic_backing_source or preferred_strategic_backing_source
        preferred_strategic_backing_classification = gate_report.preferred_strategic_backing_classification or preferred_strategic_backing_classification
        operator_actions.extend(gate_report.operator_actions)

    snapshot_path = closure_snapshot_path
    if snapshot_path is None and resolved_search_root.exists():
        snapshot_path = _find_latest(resolved_search_root, ["CLOSURE_SNAPSHOT.json"])
    if snapshot_path is not None and snapshot_path.exists():
        snapshot_path = snapshot_path.resolve()
        if closure_dsse_path is None:
            candidate = snapshot_path.with_name("CLOSURE_SNAPSHOT.dsse.json")
            closure_dsse_path = candidate if candidate.exists() else None
        if closure_public_key_path is None:
            closure_public_key_path = _default_public_key(resolved_repo_root)
        closure_verification = verify_closure_snapshot(
            snapshot_path=snapshot_path,
            repo_root=resolved_repo_root,
            dsse_path=closure_dsse_path,
            public_key_path=closure_public_key_path,
        )
        governed_memo: GovernedExceptionMemo | None = None
        governed_verification: GovernedExceptionVerification | None = None
        memo_path = governed_exception_memo_path
        if memo_path is None and resolved_search_root.exists():
            memo_path = _find_latest(resolved_search_root, ["GOVERNED_EXCEPTION_MEMO.json"])
        if memo_path is not None and memo_path.exists():
            memo_path = memo_path.resolve()
            if governed_exception_dsse_path is None:
                candidate = memo_path.with_name("GOVERNED_EXCEPTION_MEMO.dsse.json")
                governed_exception_dsse_path = candidate if candidate.exists() else None
            if governed_exception_public_key_path is None:
                governed_exception_public_key_path = closure_public_key_path or _default_public_key(resolved_repo_root)
            governed_memo = GovernedExceptionMemo.model_validate(_load_json(memo_path))
            governed_verification = verify_governed_exception_memo(
                memo_path=memo_path,
                repo_root=resolved_repo_root,
                dsse_path=governed_exception_dsse_path,
                public_key_path=governed_exception_public_key_path,
            )
            sections.append(
                OracleStatusPackSection(
                    section_id="governed_exception",
                    status=governed_verification.status,
                    summary_line=f"Governed exception `{governed_memo.exception_id}` verification is {governed_verification.status}.",
                    facts=_unique([
                        f"closure_id={governed_memo.closure_id}",
                        f"governed_exception_code={governed_memo.governed_exception_code}",
                        f"approved_by={governed_memo.approved_by}",
                        f"valid_until_utc={governed_memo.valid_until_utc.isoformat()}",
                    ] + [f"verification_note={item}" for item in governed_verification.notes]),
                    operator_actions=[
                        "Re-verify or renew the governed exception before its validity window ends."
                    ] if governed_verification.status != "VERIFIED" else [
                        "Re-evaluate the closure snapshot before the governed exception expires."
                    ],
                )
            )
            if governed_verification.status == "VERIFIED":
                active_governed_exception_ids.append(governed_memo.exception_id)
            operator_actions.extend(sections[-1].operator_actions)
        attestation, _ = build_closure_release_attestation(
            snapshot_path=snapshot_path,
            repo_root=resolved_repo_root,
            verification=closure_verification,
            verification_path=snapshot_path.with_name("CLOSURE_SNAPSHOT.verification.json") if snapshot_path.with_name("CLOSURE_SNAPSHOT.verification.json").exists() else None,
            review_path=snapshot_path.parent / "RUNTIME_REVIEW.json",
            governed_exception_memo=governed_memo,
            governed_exception_verification=governed_verification,
        )
        sections.append(_closure_section(snapshot_path=snapshot_path, verification=closure_verification, attestation=attestation))
        operator_actions.extend(attestation.required_operator_actions)
        if attestation.applied_governed_exception_id:
            active_governed_exception_ids.append(attestation.applied_governed_exception_id)

    if sections:
        trust_status = max(
            (
                section.explanation.trust_status
                for section in sections
                if section.explanation is not None
            ),
            default="TRUST_RESTRICTED",
            key=lambda status: _TRUST_RANK.get(status, 1),
        )
    else:
        trust_status = "TRUST_RESTRICTED"
    exact_feedback_confirmation_count = max((section.exact_feedback_confirmation_count for section in sections), default=0)
    exact_feedback_relief_count = max((section.exact_feedback_relief_count for section in sections), default=0)
    exact_cadence_signal_classification = _exact_cadence_signal_classification(
        exact_feedback_confirmation_count=exact_feedback_confirmation_count,
        exact_feedback_relief_count=exact_feedback_relief_count,
    )
    cadence_summary = _exact_cadence_summary(
        exact_feedback_confirmation_count=exact_feedback_confirmation_count,
        exact_feedback_relief_count=exact_feedback_relief_count,
    )
    if trust_status == "UNTRUSTED":
        summary_line = f"One or more canonical oracle/governance surfaces are untrusted or blocked; operator remediation is required before relying on the pack, and {cadence_summary}."
    elif trust_status == "TRUST_RESTRICTED":
        summary_line = f"Canonical oracle/governance surfaces are replayable but still restricted; review lineage and policy explanations before relying on them, and {cadence_summary}."
    else:
        summary_line = f"Canonical oracle/governance surfaces are fully trusted in the current pack context, and {cadence_summary}."
    generated_at_utc = _utc_now()
    memo_path = governed_exception_memo_path
    if memo_path is None and resolved_search_root.exists():
        memo_path = _find_latest(resolved_search_root, ["GOVERNED_EXCEPTION_MEMO.json"])
    workboard_timestamp_candidates = [
        path.stat().st_mtime
        for path in (derived_path, gate_path, snapshot_path, memo_path)
        if path is not None and path.exists()
    ]
    workboard_issued_at_utc = datetime.fromtimestamp(max(workboard_timestamp_candidates), tz=timezone.utc) if workboard_timestamp_candidates else generated_at_utc.replace(microsecond=0)
    operator_workboard = _status_pack_workboard_from_trust(
        trust_status=trust_status,
        issued_at_utc=workboard_issued_at_utc,
        surface_label='oracle status pack',
    )
    return _with_provenance_digest(
        OracleStatusPackReport(
            generated_at_utc=generated_at_utc,
            repo_root=str(resolved_repo_root),
            search_root=str(resolved_search_root),
            trust_status=trust_status,
            preferred_strategic_backing_source=preferred_strategic_backing_source,
            preferred_strategic_backing_classification=preferred_strategic_backing_classification,
            exact_feedback_confirmation_count=exact_feedback_confirmation_count,
            exact_feedback_relief_count=exact_feedback_relief_count,
            exact_cadence_signal_classification=exact_cadence_signal_classification,
            active_governed_exception_ids=_unique(active_governed_exception_ids),
            summary_line=summary_line,
            operator_actions=_unique(operator_actions),
            sections=sections,
        operator_workboard=operator_workboard,
        )
    )


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


def _closure_section(
    *,
    snapshot_path: Path,
    verification: ClosureSnapshotVerification,
    attestation: ClosureReleaseAttestation,
) -> OracleStatusPackSection:
    return OracleStatusPackSection(
        section_id="closure_attestation",
        status=attestation.signoff_status,
        summary_line=attestation.summary_line,
        facts=_unique([
            f"closure_id={attestation.closure_id}",
            f"verification_status={verification.status}",
            f"machine_decision={attestation.machine_decision}",
            f"primary_classification={attestation.primary_classification}",
            f"final_release_stance={attestation.final_release_stance}",
            f"snapshot_path={snapshot_path}",
        ] + [f"reason={item}" for item in attestation.reasons]),
        operator_actions=list(attestation.required_operator_actions),
    )


def build_oracle_status_pack(
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
) -> OracleStatusPackReport:
    from strategy_validator.projections.operator_pack_assembly import assemble_oracle_status_pack

    return assemble_oracle_status_pack(
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


def materialize_oracle_status_pack(pack_root: Path, report: OracleStatusPackReport, *, markdown: str, html: str | None = None) -> OracleStatusPackReport:
    return materialize_status_pack_bundle(pack_root, report, markdown=markdown, html=html)


def materialize_oracle_incident_pack(pack_root: Path, report: OracleIncidentPackReport, *, markdown: str, html: str | None = None) -> OracleIncidentPackReport:
    return materialize_incident_pack_bundle(
        pack_root,
        report,
        markdown=markdown,
        html=html,
        render_markdown=render_oracle_incident_pack_markdown,
        render_html=render_oracle_incident_pack_html,
    )


