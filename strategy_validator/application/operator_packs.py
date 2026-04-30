from __future__ import annotations

from pathlib import Path

from strategy_validator.contracts.oracle_operator_reports import (
    OracleBriefingPackReport,
    OracleIncidentPackReport,
    OracleStatusPackReport,
)
from strategy_validator.projections.operator_pack_service import (
    materialize_briefing_pack_bundle,
    materialize_incident_pack_bundle,
    materialize_status_pack_bundle,
)


def materialize_status_operator_pack(
    pack_root: Path,
    report: OracleStatusPackReport,
    *,
    markdown: str,
    html: str | None = None,
) -> OracleStatusPackReport:
    return materialize_status_pack_bundle(pack_root, report, markdown=markdown, html=html)


def materialize_incident_operator_pack(
    pack_root: Path,
    report: OracleIncidentPackReport,
    *,
    markdown: str,
    html: str | None = None,
    render_markdown,
    render_html=None,
) -> OracleIncidentPackReport:
    return materialize_incident_pack_bundle(
        pack_root,
        report,
        markdown=markdown,
        html=html,
        render_markdown=render_markdown,
        render_html=render_html,
    )


def materialize_briefing_operator_pack(
    pack_root: Path,
    report: OracleBriefingPackReport,
    *,
    markdown: str,
    html: str,
) -> OracleBriefingPackReport:
    return materialize_briefing_pack_bundle(pack_root, report, markdown=markdown, html=html)


__all__ = [
    'materialize_status_operator_pack',
    'materialize_incident_operator_pack',
    'materialize_briefing_operator_pack',
]
