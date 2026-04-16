from __future__ import annotations

from dataclasses import dataclass

from strategy_validator.contracts.oracle import (
    OracleBriefingPackReport,
    OracleIncidentPackReport,
    OracleStatusPackReport,
)


@dataclass(frozen=True)
class OracleOperatorPackHeader:
    pack_kind: str
    title: str
    metadata_lines: list[str]
    summary_line: str
    trailing_lines: list[str]


def render_operator_pack_header_markdown_lines(*, header: OracleOperatorPackHeader) -> list[str]:
    lines = [
        f"# {header.title}",
        "",
        *header.metadata_lines,
        "",
        header.summary_line,
        "",
        *header.trailing_lines,
    ]
    return lines


def build_status_pack_header(*, report: OracleStatusPackReport) -> OracleOperatorPackHeader:
    return OracleOperatorPackHeader(
        pack_kind='status_pack',
        title='Oracle Status Pack',
        metadata_lines=[
            f"- Trust status: `{report.trust_status}`",
            f"- Repo root: `{report.repo_root}`",
            f"- Search root: `{report.search_root}`",
            f"- Active governed exceptions: `{', '.join(report.active_governed_exception_ids) if report.active_governed_exception_ids else 'None'}`",
            f"- Provenance digest: `{report.provenance_digest_sha256}`",
            f"- Exact cadence signal: `{report.exact_cadence_signal_classification}`",
            f"- Exact feedback confirmations: `{report.exact_feedback_confirmation_count}`",
            f"- Exact feedback relief signals: `{report.exact_feedback_relief_count}`",
        ],
        summary_line=report.summary_line,
        trailing_lines=['## Sections'],
    )


def build_incident_pack_header(*, report: OracleIncidentPackReport) -> OracleOperatorPackHeader:
    return OracleOperatorPackHeader(
        pack_kind='incident_pack',
        title='Oracle Incident Pack',
        metadata_lines=[
            f"- Trust status: `{report.trust_status}`",
            f"- Incident kind: `{report.incident_kind}`",
            f"- Blocked: `{report.blocked}`",
            f"- Repo root: `{report.repo_root}`",
            f"- Search root: `{report.search_root}`",
            f"- Provenance digest: `{report.provenance_digest_sha256}`",
            f"- Exact cadence signal: `{report.exact_cadence_signal_classification}`",
            f"- Exact feedback confirmations: `{report.exact_feedback_confirmation_count}`",
            f"- Exact feedback relief signals: `{report.exact_feedback_relief_count}`",
        ],
        summary_line=report.summary_line,
        trailing_lines=[],
    )


def build_briefing_pack_header(*, report: OracleBriefingPackReport) -> OracleOperatorPackHeader:
    return OracleOperatorPackHeader(
        pack_kind='briefing_pack',
        title='Oracle Briefing Pack',
        metadata_lines=[
            f"- Trust status: `{report.trust_status}`",
            f"- Preferred strategic backing source: `{report.preferred_strategic_backing_source or 'none'}`",
            f"- Preferred strategic backing classification: `{report.preferred_strategic_backing_classification or 'none'}`",
            f"- Exact cadence signal: `{report.exact_cadence_signal_classification}`",
            f"- Exact feedback confirmations: `{report.exact_feedback_confirmation_count}`",
            f"- Exact feedback relief signals: `{report.exact_feedback_relief_count}`",
            f"- Repo root: `{report.repo_root}`",
            f"- Search root: `{report.search_root}`",
            f"- Status pack digest: `{report.status_pack_digest_sha256}`",
            f"- Incident pack digest: `{report.incident_pack_digest_sha256 or 'none'}`",
            f"- Evidence freshness status: `{report.evidence_freshness_status}`",
            f"- Support-chain trust: `{report.support_chain_trust_status}`",
            f"- Support-chain remediation: `{report.support_chain_remediation_status}`",
            f"- Escalation lane: `{report.operator_escalation_lane}`",
            f"- Propagation posture: `{report.propagation_posture}`",
            f"- Automation posture: `{report.automation_posture}`",
            f"- {report.control_plane_summary_line}",
            f"- {report.governance_plane_summary_line}",
            f"- Governance primary dimension: {report.governance_plane_primary_dimension or 'none'}",
            f"- Governance primary severity: {report.governance_plane_primary_severity}",
            f"- Governance primary action: {report.governance_plane_primary_action_text or 'none'}",
            f"- Governance priority: {report.governance_plane_priority_band} (score={report.governance_plane_priority_score})",
            f"- {report.governance_plane_priority_summary_line}",
            f"- {report.governance_plane_routing_summary_line}",
            f"- Governance routing vector: `{report.governance_plane_routing_vector}`",
            f"- Governance routing sha256: `{report.governance_plane_routing_sha256}`",
            f"- Governance queue key: `{report.governance_plane_queue_key}`",
            f"- Governance vector: `{report.governance_plane_vector}`",
            f"- Governance sha256: `{report.governance_plane_sha256}`",
            f"- Stale artifact count: `{report.stale_artifact_count}`",
            f"- Provenance digest: `{report.provenance_digest_sha256}`",
        ],
        summary_line=report.summary_line,
        trailing_lines=[
            f"Artifact lineage: {report.artifact_lineage_summary_line}",
            f"Artifact integrity: {report.integrity_summary_line}",
            f"Artifact coverage: {report.evidence_coverage_summary_line}",
            f"Support verification: {report.support_verification_summary_line}",
            f"Support-chain trust: {report.support_chain_trust_summary_line}",
            f"Support-chain remediation: {report.support_chain_remediation_summary_line}",
            f"Escalation lane: {report.operator_escalation_summary_line}",
            f"Propagation posture: {report.propagation_summary_line}",
            f"Automation posture: {report.automation_summary_line}",
            f"Missing expected artifacts: {', '.join(report.missing_expected_artifact_labels) if report.missing_expected_artifact_labels else 'none'}",
            '',
            'Trust reasons:',
            *([f"- {item}" for item in report.support_chain_trust_reasons] or ['- none']),
            '',
            'Remediation actions:',
            *([f"- {item}" for item in report.support_chain_remediation_actions] or ['- none']),
            '',
            'Governance codes:',
            *([f"- {item}" for item in report.governance_plane_codes] or ['- none']),
            '',
            'Governance blocking dimensions:',
            *([f"- {item}" for item in report.governance_plane_blocking_dimensions] or ['- none']),
            '',
            'Governance restricted dimensions:',
            *([f"- {item}" for item in report.governance_plane_restricted_dimensions] or ['- none']),
            '',
            'Governance actions:',
            *([f"- [{item.dimension}/{item.severity}] {item.action_text}" for item in report.governance_plane_action_items] or ['- none']),
            '',
            'Governance fingerprint:',
            f"- Vector: `{report.governance_plane_vector}`",
            f"- SHA-256: `{report.governance_plane_sha256}`",
            '',
            'Escalation reasons:',
            *([f"- {item}" for item in report.operator_escalation_reasons] or ['- none']),
            '',
            f"Freshness: {report.freshness_summary_line}",
            '',
        ],
    )


__all__ = [
    'OracleOperatorPackHeader',
    'build_briefing_pack_header',
    'build_incident_pack_header',
    'build_status_pack_header',
    'render_operator_pack_header_markdown_lines',
]
