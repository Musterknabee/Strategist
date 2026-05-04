from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.contracts.oracle_operator_reports import OracleStatusPackReport
from strategy_validator.projections.operator_pack_service import materialize_status_pack_bundle
from strategy_validator.projections.service import select_latest_canonical_event_projection
from strategy_validator.validator.oracle_diagnostics_foundations import (
    _TRUST_RANK,
    _exact_cadence_signal_classification,
    _exact_cadence_summary,
    _find_latest,
    _status_pack_workboard_from_trust,
    _unique,
    _with_provenance_digest,
)
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.oracle_diagnostics_pack_rendering import render_oracle_status_pack_markdown
from strategy_validator.validator.oracle_diagnostics_rendering import render_oracle_status_pack_html
from strategy_validator.validator.oracle_diagnostics_status_pack_sections import (
    _build_constitutional_gate_section,
    _build_governed_exception_and_closure_sections,
    _build_lineage_section,
    _build_oracle_posture_section,
    _build_temporal_lane_section,
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
    sections = []
    operator_actions: list[str] = []
    active_governed_exception_ids: list[str] = []
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: str | None = None

    if resolved_search_root.exists():
        section, actions, preferred_source, preferred_classification = _build_lineage_section(
            resolved_repo_root=resolved_repo_root,
            resolved_search_root=resolved_search_root,
        )
        sections.append(section)
        operator_actions.extend(actions)
        preferred_strategic_backing_source = preferred_source or preferred_strategic_backing_source
        preferred_strategic_backing_classification = preferred_classification or preferred_strategic_backing_classification

    derived_path = derived_view_report_path
    if derived_path is None and resolved_search_root.exists():
        projection_selection = select_latest_canonical_event_projection(search_root=resolved_search_root, repo_root=resolved_repo_root)
        derived_path = (projection_selection.output_artifact_path if projection_selection is not None else None) or _find_latest(
            resolved_search_root,
            ["ORACLE_ROLLING_REVIEW.json", "ORACLE_HORIZON_VIEW.json", "ORACLE_DERIVED_VIEW.json"],
        )
    if derived_path is not None and derived_path.exists():
        section, actions = _build_oracle_posture_section(derived_path=derived_path, repo_root=resolved_repo_root)
        sections.append(section)
        operator_actions.extend(actions)

    gate_path = constitutional_gate_report_path
    if gate_path is None and resolved_search_root.exists():
        gate_path = _find_latest(resolved_search_root, ["ORACLE_CONSTITUTIONAL_GATE_REPORT.json"])
    temporal_path = temporal_lane_status_path
    if temporal_path is None and resolved_search_root.exists():
        temporal_path = _find_latest(resolved_search_root, ["ORACLE_TEMPORAL_LANE_STATUS.json"])
    if temporal_path is not None and temporal_path.exists():
        section, actions = _build_temporal_lane_section(temporal_path=temporal_path)
        sections.append(section)
        operator_actions.extend(actions)

    if gate_path is not None and gate_path.exists():
        section, actions, preferred_source, preferred_classification = _build_constitutional_gate_section(
            gate_path=gate_path,
            repo_root=resolved_repo_root,
        )
        sections.append(section)
        operator_actions.extend(actions)
        preferred_strategic_backing_source = preferred_source or preferred_strategic_backing_source
        preferred_strategic_backing_classification = preferred_classification or preferred_strategic_backing_classification

    snapshot_path = closure_snapshot_path
    if snapshot_path is None and resolved_search_root.exists():
        snapshot_path = _find_latest(resolved_search_root, ["CLOSURE_SNAPSHOT.json"])
    if snapshot_path is not None and snapshot_path.exists():
        closure_sections, closure_actions, active_ids = _build_governed_exception_and_closure_sections(
            resolved_repo_root=resolved_repo_root,
            resolved_search_root=resolved_search_root,
            snapshot_path=snapshot_path,
            closure_dsse_path=closure_dsse_path,
            closure_public_key_path=closure_public_key_path,
            governed_exception_memo_path=governed_exception_memo_path,
            governed_exception_dsse_path=governed_exception_dsse_path,
            governed_exception_public_key_path=governed_exception_public_key_path,
        )
        sections.extend(closure_sections)
        operator_actions.extend(closure_actions)
        active_governed_exception_ids.extend(active_ids)

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


def materialize_oracle_status_pack(pack_root: Path, report: OracleStatusPackReport, *, markdown: str, html: str | None = None) -> OracleStatusPackReport:
    pack_root.mkdir(parents=True, exist_ok=True)
    status_bundle = materialize_status_pack_bundle(report, output_dir=pack_root)
    status_bundle.report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    status_bundle.markdown_path.write_text(markdown, encoding="utf-8")
    if html:
        status_bundle.html_path.write_text(html, encoding="utf-8")
    return report.model_copy(update={
        "artifact_paths": tuple(
            str(path)
            for path in (
                status_bundle.report_path,
                status_bundle.markdown_path,
                status_bundle.html_path if html else None,
            )
            if path is not None
        )
    })


__all__ = [name for name in globals() if not name.startswith("__")]
