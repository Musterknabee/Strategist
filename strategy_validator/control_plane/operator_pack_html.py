from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Iterable

from strategy_validator.contracts.oracle_operator_reports import (
    OracleBriefingPackReport,
    OracleIncidentPackReport,
    OracleStatusPackReport,
)
from strategy_validator.control_plane.operator_pack_headers import (
    OracleOperatorPackHeader,
    build_briefing_pack_header,
    build_incident_pack_header,
    build_status_pack_header,
)
from strategy_validator.control_plane.operator_section_registry import (
    OracleOperatorSectionComposition,
    compose_briefing_pack_sections,
    compose_incident_pack_sections,
    compose_status_pack_sections,
)


@dataclass(frozen=True)
class OracleOperatorPackHtmlDocument:
    pack_kind: str
    title: str
    body_html: str


def _metadata_lines_to_html(lines: Iterable[str]) -> str:
    items = [f'<li>{escape(line)}</li>' for line in lines if str(line).strip()]
    return '<ul>' + ''.join(items) + '</ul>' if items else ''


def _markdown_lines_to_html(lines: Iterable[str]) -> str:
    parts: list[str] = []
    in_list = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            parts.append('</ul>')
            in_list = False

    for raw_line in lines:
        line = str(raw_line)
        stripped = line.strip()
        if not stripped:
            close_list()
            continue
        if stripped.startswith('### '):
            close_list()
            parts.append(f'<h3>{escape(stripped[4:])}</h3>')
            continue
        if stripped.startswith('## '):
            close_list()
            parts.append(f'<h2>{escape(stripped[3:])}</h2>')
            continue
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                parts.append('<ul>')
                in_list = True
            parts.append(f'<li>{escape(stripped[2:])}</li>')
            continue
        close_list()
        parts.append(f'<p>{escape(stripped)}</p>')
    close_list()
    return ''.join(parts)



def render_operator_pack_html_document(*, header: OracleOperatorPackHeader, composition: OracleOperatorSectionComposition) -> str:
    body_parts = [
        f'<h1>{escape(header.title)}</h1>',
        _metadata_lines_to_html(header.metadata_lines),
        f'<p>{escape(header.summary_line)}</p>' if header.summary_line else '',
        _markdown_lines_to_html(header.trailing_lines),
    ]
    for entry in composition.entries:
        body_parts.append(f'<section data-section-key="{escape(entry.section_key)}">')
        body_parts.append(_markdown_lines_to_html(entry.markdown_lines))
        body_parts.append('</section>')
    body_html = ''.join(part for part in body_parts if part)
    document = OracleOperatorPackHtmlDocument(
        pack_kind=header.pack_kind,
        title=header.title,
        body_html=body_html,
    )
    return (
        '<html><head><meta charset="utf-8">'
        f'<title>{escape(document.title)}</title>'
        '</head><body>'
        f'{document.body_html}'
        '</body></html>'
    )



def build_status_pack_html(*, report: OracleStatusPackReport) -> str:
    return render_operator_pack_html_document(
        header=build_status_pack_header(report=report),
        composition=compose_status_pack_sections(report=report),
    )



def build_incident_pack_html(*, report: OracleIncidentPackReport) -> str:
    return render_operator_pack_html_document(
        header=build_incident_pack_header(report=report),
        composition=compose_incident_pack_sections(report=report),
    )



def build_briefing_pack_html(*, report: OracleBriefingPackReport) -> str:
    return render_operator_pack_html_document(
        header=build_briefing_pack_header(report=report),
        composition=compose_briefing_pack_sections(report=report),
    )


__all__ = [
    'OracleOperatorPackHtmlDocument',
    'build_briefing_pack_html',
    'build_incident_pack_html',
    'build_status_pack_html',
    'render_operator_pack_html_document',
]
