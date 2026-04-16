from __future__ import annotations

from pathlib import Path

from strategy_validator.contracts.oracle import OracleBriefingPackReport, OracleIncidentPackArtifact, OracleIncidentPackReport, OracleStatusPackReport
from strategy_validator.projections.operator_pack_registry import build_operator_pack_manifest, write_operator_pack_manifest_with_index

from strategy_validator.projections.operator_materialization import (
    OperatorBundleArtifactCopy,
    OperatorBundleMaterializationRequest,
    materialize_operator_bundle,
    with_report_provenance_digest,
)


def materialize_status_pack_bundle(pack_root: Path, report: OracleStatusPackReport, *, markdown: str, html: str | None = None) -> OracleStatusPackReport:
    updated_report, result = materialize_operator_bundle(
        OperatorBundleMaterializationRequest(
            pack_root=pack_root,
            json_filename="ORACLE_STATUS_PACK_REPORT.json",
            markdown_filename="ORACLE_STATUS_PACK_REPORT.md",
            html_filename="ORACLE_STATUS_PACK_REPORT.html",
        ),
        report=report,
        markdown=markdown,
        html=html,
    )
    write_operator_pack_manifest_with_index(
        pack_root / 'ORACLE_OPERATOR_PACK_MANIFEST.json',
        build_operator_pack_manifest(pack_kind='status_pack', report=updated_report, result=result, repo_root=Path(updated_report.repo_root)),
        repo_root=Path(updated_report.repo_root),
    )
    return updated_report



def materialize_incident_pack_bundle(
    pack_root: Path,
    report: OracleIncidentPackReport,
    *,
    markdown: str,
    html: str | None = None,
    render_markdown,
    render_html=None,
) -> OracleIncidentPackReport:
    artifact_copies = tuple(
        OperatorBundleArtifactCopy(artifact_kind=artifact.artifact_kind, source_path=Path(artifact.source_path))
        for artifact in report.artifacts
    )
    _, result = materialize_operator_bundle(
        OperatorBundleMaterializationRequest(
            pack_root=pack_root,
            json_filename="ORACLE_INCIDENT_PACK_REPORT.json",
            markdown_filename="ORACLE_INCIDENT_PACK_REPORT.md",
            html_filename="ORACLE_INCIDENT_PACK_REPORT.html",
            artifact_copies=artifact_copies,
        ),
        report=report,
        markdown=markdown,
        html=html,
    )
    updated_artifacts: list[OracleIncidentPackArtifact] = []
    for artifact in report.artifacts:
        updated_artifacts.append(
            artifact.model_copy(update={"pack_path": result.artifact_pack_paths.get(str(Path(artifact.source_path)))})
        )
    updated_report = with_report_provenance_digest(report.model_copy(update={"artifacts": updated_artifacts}))
    _, final_result = materialize_operator_bundle(
        OperatorBundleMaterializationRequest(
            pack_root=pack_root,
            json_filename="ORACLE_INCIDENT_PACK_REPORT.json",
            markdown_filename="ORACLE_INCIDENT_PACK_REPORT.md",
            html_filename="ORACLE_INCIDENT_PACK_REPORT.html",
        ),
        report=updated_report,
        markdown=render_markdown(updated_report),
        html=render_html(updated_report) if render_html is not None else None,
    )
    write_operator_pack_manifest_with_index(
        pack_root / 'ORACLE_OPERATOR_PACK_MANIFEST.json',
        build_operator_pack_manifest(pack_kind='incident_pack', report=updated_report, result=final_result, repo_root=Path(updated_report.repo_root)),
        repo_root=Path(updated_report.repo_root),
    )
    return updated_report



def materialize_briefing_pack_bundle(
    pack_root: Path,
    report: OracleBriefingPackReport,
    *,
    markdown: str,
    html: str,
) -> OracleBriefingPackReport:
    updated_report, result = materialize_operator_bundle(
        OperatorBundleMaterializationRequest(
            pack_root=pack_root,
            json_filename="ORACLE_BRIEFING_PACK_REPORT.json",
            markdown_filename="ORACLE_BRIEFING_PACK_REPORT.md",
            html_filename="ORACLE_BRIEFING_PACK_REPORT.html",
        ),
        report=report,
        markdown=markdown,
        html=html,
    )
    write_operator_pack_manifest_with_index(
        pack_root / 'ORACLE_OPERATOR_PACK_MANIFEST.json',
        build_operator_pack_manifest(pack_kind='briefing_pack', report=updated_report, result=result, repo_root=Path(updated_report.repo_root)),
        repo_root=Path(updated_report.repo_root),
    )
    return updated_report
