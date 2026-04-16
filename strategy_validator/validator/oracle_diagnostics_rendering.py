from __future__ import annotations

from strategy_validator.contracts.oracle import (
    OracleIncidentPackReport,
    OracleOperatorDiagnosticReport,
    OracleStatusPackReport,
)
from strategy_validator.control_plane import build_incident_pack_html, build_status_pack_html


def render_oracle_operator_diagnostic_markdown(report: OracleOperatorDiagnosticReport) -> str:
    lines = [
        "# Oracle Operator Diagnostic",
        "",
        f"- Diagnostic kind: `{report.diagnostic_kind}`",
        f"- Trust status: `{report.trust_status}`",
        f"- Blocked: `{report.blocked}`",
    ]
    if report.subject_path:
        lines.append(f"- Subject path: `{report.subject_path}`")
    if report.preferred_strategic_backing_source:
        lines.append(f"- Preferred strategic backing source: `{report.preferred_strategic_backing_source}`")
    if report.preferred_strategic_backing_classification:
        lines.append(f"- Preferred strategic backing classification: `{report.preferred_strategic_backing_classification}`")
    lines.append(f"- Exact feedback confirmations: `{report.exact_feedback_confirmation_count}`")
    lines.append(f"- Exact feedback relief signals: `{report.exact_feedback_relief_count}`")
    lines.extend(["", report.summary_line, "", "## Reasons"])
    lines.extend([f"- {item}" for item in report.reasons] or ["- No active restriction or block reasons are present."])
    lines.extend(["", "## Operator Actions"])
    lines.extend([f"- {item}" for item in report.operator_actions] or ["- No additional operator actions recorded."])
    if report.explanation is not None:
        lines.extend([
            "",
            "## Explanation Summary",
            f"- Explanation kind: `{report.explanation.explanation_kind}`",
            f"- Subject schema: `{report.explanation.subject_schema_version}`",
        ])
    lines.append("")
    return "\n".join(lines)


def render_oracle_status_pack_html(report: OracleStatusPackReport) -> str:
    return build_status_pack_html(report=report)


def render_oracle_incident_pack_html(report: OracleIncidentPackReport) -> str:
    return build_incident_pack_html(report=report)
