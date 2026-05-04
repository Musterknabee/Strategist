from __future__ import annotations

from strategy_validator.contracts.oracle_operator_reports import (
    OracleCompactedStateInspectionReport,
    OracleCompactedStateRebuildReport,
    OracleReplayAuditReport,
)


def render_oracle_compacted_state_rebuild_markdown(report: OracleCompactedStateRebuildReport) -> str:
    lines = [
        "# Oracle Compacted State Rebuild",
        "",
        f"- View label: `{report.view_label}`",
        f"- Lane path: `{report.lane_path}`",
        f"- Checkpoint metadata: `{report.checkpoint_metadata_path}`",
        f"- Previous replay status: `{report.previous_replay_status or 'unknown'}`",
        f"- Rebuilt window entry count: `{report.rebuilt_window_entry_count}`",
        f"- Rebuilt file offset: `{report.rebuilt_file_offset_bytes}`",
        f"- Compacted window digest: `{report.compacted_window_digest_sha256}`",
        "",
        report.summary_line,
        "",
    ]
    if report.findings:
        lines.append("## Prior Findings")
        lines.extend([f"- {item}" for item in report.findings])
        lines.append("")
    lines.append("## Next Actions")
    lines.extend([f"- {item}" for item in report.operator_actions] or ["- No additional operator actions recorded."])
    lines.append("")
    return "\n".join(lines)


def render_oracle_compacted_state_inspection_markdown(report: OracleCompactedStateInspectionReport) -> str:
    lines = [
        "# Oracle Compacted State Inspection",
        "",
        f"- Replay status: `{report.replay_status}`",
        f"- View label: `{report.view_label}`",
        f"- Lane path: `{report.lane_path}`",
        f"- Checkpoint metadata: `{report.checkpoint_metadata_path}`",
        f"- Current file size: `{report.current_file_size_bytes}`",
        f"- Metadata offset: `{report.metadata_file_offset_bytes}`",
        f"- Cached window entries: `{report.cached_window_entry_count}`",
        f"- Compacted window digest: `{report.compacted_window_digest_sha256}`",
        "",
        report.summary_line,
        "",
    ]
    if report.findings:
        lines.extend(["## Findings", *[f"- {item}" for item in report.findings], ""])
    if report.operator_actions:
        lines.extend(["## Operator Actions", *[f"- {item}" for item in report.operator_actions], ""])
    return "\n".join(lines)



def render_oracle_replay_audit_markdown(report: OracleReplayAuditReport) -> str:
    lines = [
        "# Oracle Replay Audit",
        "",
        f"- Replay status: `{report.replay_status}`",
        f"- Lane path: `{report.lane_path}`",
        f"- Checkpoint metadata: `{report.checkpoint_metadata_path}`",
        f"- Canonical window digest: `{report.canonical_window_digest_sha256}`",
        f"- Compacted window digest: `{report.compacted_window_digest_sha256}`",
        f"- Rebuilt window digest: `{report.rebuilt_window_digest_sha256 or 'not requested'}`",
        f"- Derived report path: `{report.report_path or 'none'}`",
        "",
        report.summary_line,
        "",
        "## Sources",
    ]
    for source in report.sources:
        lines.extend([
            f"### {source.source_id}",
            f"- Status: `{source.status}`",
            f"- Summary: {source.summary_line}",
        ])
        if source.details:
            lines.extend([f"- Detail: {detail}" for detail in source.details])
        lines.append("")
    if report.findings:
        lines.extend(["## Findings", *[f"- {item}" for item in report.findings], ""])
    if report.operator_actions:
        lines.extend(["## Operator Actions", *[f"- {item}" for item in report.operator_actions], ""])
    return "\n".join(lines)
