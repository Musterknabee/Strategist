from __future__ import annotations

from dataclasses import dataclass

from strategy_validator.contracts.oracle_operator_reports import (
    OracleBriefingPackReport,
    OracleIncidentPackArtifact,
    OracleIncidentPackReport,
    OracleStatusPackReport,
)
from strategy_validator.control_plane.operator_board_sections import render_operator_workboard_markdown_lines


@dataclass(frozen=True)
class OracleOperatorSectionEntry:
    section_key: str
    title: str
    markdown_lines: list[str]


@dataclass(frozen=True)
class OracleOperatorSectionComposition:
    pack_kind: str
    entries: list[OracleOperatorSectionEntry]


def _status_section_markdown_lines(report: OracleStatusPackReport) -> list[OracleOperatorSectionEntry]:
    entries: list[OracleOperatorSectionEntry] = []
    for section in report.sections:
        lines = [
            f"### {section.section_id.replace('_', ' ').title()}",
            f"- Status: `{section.status}`",
            f"- Summary: {section.summary_line}",
            f"- Exact cadence signal: `{section.exact_cadence_signal_classification}`",
            f"- Exact feedback confirmations: `{section.exact_feedback_confirmation_count}`",
            f"- Exact feedback relief signals: `{section.exact_feedback_relief_count}`",
        ]
        if section.facts:
            lines.append('- Facts:')
            lines.extend([f"  - {item}" for item in section.facts])
        if section.operator_actions:
            lines.append('- Operator actions:')
            lines.extend([f"  - {item}" for item in section.operator_actions])
        if section.explanation is not None:
            lines.append(f"- Explanation kind: `{section.explanation.explanation_kind}`")
        lines.append('')
        entries.append(OracleOperatorSectionEntry(section_key=f'status:{section.section_id}', title=section.section_id.replace('_',' ').title(), markdown_lines=lines))
    workboard_lines = render_operator_workboard_markdown_lines(workboard=report.operator_workboard)
    if workboard_lines:
        entries.append(OracleOperatorSectionEntry(section_key='status:operator_workboard', title='Operator Workboard', markdown_lines=workboard_lines))
    next_action_lines = ['## Next Actions']
    next_action_lines.extend([f"- {item}" for item in report.operator_actions] or ['- No additional operator actions recorded.'])
    next_action_lines.append('')
    entries.append(OracleOperatorSectionEntry(section_key='status:next_actions', title='Next Actions', markdown_lines=next_action_lines))
    return entries


def compose_status_pack_sections(*, report: OracleStatusPackReport) -> OracleOperatorSectionComposition:
    return OracleOperatorSectionComposition(pack_kind='status_pack', entries=_status_section_markdown_lines(report))


def _incident_artifact_lines(artifact: OracleIncidentPackArtifact) -> list[str]:
    return [
        f"### {artifact.artifact_kind}",
        f"- Source path: `{artifact.source_path}`",
        f"- Pack path: `{artifact.pack_path or 'not materialized'}`",
        f"- SHA256: `{artifact.sha256}`",
        f"- Summary: {artifact.summary_line}",
        '',
    ]


def compose_incident_pack_sections(*, report: OracleIncidentPackReport) -> OracleOperatorSectionComposition:
    entries: list[OracleOperatorSectionEntry] = []
    if report.primary_diagnostic is not None:
        lines = [
            '## Primary Diagnostic',
            f"- Trust status: `{report.primary_diagnostic.trust_status}`",
            f"- Summary: {report.primary_diagnostic.summary_line}",
        ]
        if report.primary_diagnostic.reasons:
            lines.append('- Reasons:')
            lines.extend([f"  - {item}" for item in report.primary_diagnostic.reasons])
        lines.append('')
        entries.append(OracleOperatorSectionEntry(section_key='incident:primary_diagnostic', title='Primary Diagnostic', markdown_lines=lines))
    action_lines = ['## Recommended Next Actions']
    action_lines.extend([f"- {item}" for item in report.recommended_next_actions] or ['- No additional operator actions recorded.'])
    action_lines.append('')
    entries.append(OracleOperatorSectionEntry(section_key='incident:recommended_next_actions', title='Recommended Next Actions', markdown_lines=action_lines))
    artifact_lines = ['## Referenced Artifacts']
    for artifact in report.artifacts:
        artifact_lines.extend(_incident_artifact_lines(artifact))
    entries.append(OracleOperatorSectionEntry(section_key='incident:referenced_artifacts', title='Referenced Artifacts', markdown_lines=artifact_lines))
    workboard_lines = render_operator_workboard_markdown_lines(workboard=report.operator_workboard)
    if workboard_lines:
        entries.append(OracleOperatorSectionEntry(section_key='incident:operator_workboard', title='Operator Workboard', markdown_lines=workboard_lines))
    status_lines = [
        '## Embedded Status Pack',
        f"- Trust status: `{report.status_pack.trust_status}`",
        f"- Summary: {report.status_pack.summary_line}",
    ]
    if report.status_pack.preferred_strategic_backing_source:
        status_lines.append(f"- Preferred strategic backing source: `{report.status_pack.preferred_strategic_backing_source}`")
    status_lines.append(f"- Exact cadence signal: `{report.status_pack.exact_cadence_signal_classification}`")
    status_lines.append(f"- Exact feedback confirmations: `{report.status_pack.exact_feedback_confirmation_count}`")
    status_lines.append(f"- Exact feedback relief signals: `{report.status_pack.exact_feedback_relief_count}`")
    if report.status_pack.preferred_strategic_backing_classification:
        status_lines.append(f"- Preferred strategic backing classification: `{report.status_pack.preferred_strategic_backing_classification}`")
    status_lines.append('')
    entries.append(OracleOperatorSectionEntry(section_key='incident:embedded_status_pack', title='Embedded Status Pack', markdown_lines=status_lines))
    return OracleOperatorSectionComposition(pack_kind='incident_pack', entries=entries)


def compose_briefing_pack_sections(*, report: OracleBriefingPackReport) -> OracleOperatorSectionComposition:
    entries: list[OracleOperatorSectionEntry] = []
    for section in report.sections:
        lines = [
            f"## {section.title}",
            f"- Status: `{section.status}`",
            f"- Summary: {section.summary_line}",
        ]
        if section.preferred_strategic_backing_source:
            lines.append(f"- Preferred strategic backing source: `{section.preferred_strategic_backing_source}`")
        if section.preferred_strategic_backing_classification:
            lines.append(f"- Preferred strategic backing classification: `{section.preferred_strategic_backing_classification}`")
        lines.append(f"- Exact cadence signal: `{section.exact_cadence_signal_classification}`")
        lines.append(f"- Exact feedback confirmations: `{section.exact_feedback_confirmation_count}`")
        lines.append(f"- Exact feedback relief signals: `{section.exact_feedback_relief_count}`")
        if section.facts:
            lines.append('- Facts:')
            lines.extend([f"  - {item}" for item in section.facts])
        if section.operator_actions:
            lines.append('- Operator actions:')
            lines.extend([f"  - {item}" for item in section.operator_actions])
        if section.provenance_refs:
            lines.append('- Provenance:')
            lines.extend([f"  - {item}" for item in section.provenance_refs])
        lines.append('')
        entries.append(OracleOperatorSectionEntry(section_key=f'briefing:{section.section_id}', title=section.title, markdown_lines=lines))
    next_action_lines = ['## Next Actions']
    next_action_lines.extend([f"- {item}" for item in report.operator_actions] or ['- No additional operator actions recorded.'])
    next_action_lines.append('')
    entries.append(OracleOperatorSectionEntry(section_key='briefing:next_actions', title='Next Actions', markdown_lines=next_action_lines))
    return OracleOperatorSectionComposition(pack_kind='briefing_pack', entries=entries)


__all__ = [
    'OracleOperatorSectionComposition',
    'OracleOperatorSectionEntry',
    'compose_briefing_pack_sections',
    'compose_incident_pack_sections',
    'compose_status_pack_sections',
]
