from __future__ import annotations

from pathlib import Path

from strategy_validator.contracts.oracle_operator_reports import OracleBriefingPackReport
from strategy_validator.control_plane.operator_queue_snapshot import materialize_operator_queue_snapshot
from strategy_validator.projections.operator_pack_service import materialize_briefing_pack_bundle
from strategy_validator.validator.oracle_briefing_io import (
    _briefing_pack_projection_inputs,
    emit_oracle_briefing_pack_projection_registry,
)
from strategy_validator.validator.oracle_briefing_pack_builders import _build_oracle_briefing_pack_impl
from strategy_validator.validator.oracle_briefing_rendering import (
    render_oracle_briefing_pack_html,
    render_oracle_briefing_pack_markdown,
)
from strategy_validator.validator.oracle_briefing_sections import (
    _briefing_sections,
    _exact_cadence_summary,
    _unique,
)


def build_oracle_briefing_pack(
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
    strategic_briefing_report_path: Path | None = None,
    strategic_narrative_report_path: Path | None = None,
    strategic_memory_horizon_report_path: Path | None = None,
    contradiction_resolution_report_path: Path | None = None,
    strategic_intervention_report_path: Path | None = None,
    strategic_campaign_report_path: Path | None = None,
    strategic_campaign_execution_report_path: Path | None = None,
    thesis_memory_report_path: Path | None = None,
    strategy_cohort_report_path: Path | None = None,
    doctrine_adaptation_report_path: Path | None = None,
    research_priority_report_path: Path | None = None,
    research_execution_memory_report_path: Path | None = None,
    thesis_graph_report_path: Path | None = None,
    strategic_tension_report_path: Path | None = None,
) -> OracleBriefingPackReport:
    from strategy_validator.projections.operator_pack_assembly import assemble_oracle_briefing_pack

    return assemble_oracle_briefing_pack(
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
        strategic_briefing_report_path=strategic_briefing_report_path,
        strategic_narrative_report_path=strategic_narrative_report_path,
        strategic_memory_horizon_report_path=strategic_memory_horizon_report_path,
        contradiction_resolution_report_path=contradiction_resolution_report_path,
        strategic_intervention_report_path=strategic_intervention_report_path,
        strategic_campaign_report_path=strategic_campaign_report_path,
        strategic_campaign_execution_report_path=strategic_campaign_execution_report_path,
        thesis_memory_report_path=thesis_memory_report_path,
        strategy_cohort_report_path=strategy_cohort_report_path,
        doctrine_adaptation_report_path=doctrine_adaptation_report_path,
        research_priority_report_path=research_priority_report_path,
        research_execution_memory_report_path=research_execution_memory_report_path,
        thesis_graph_report_path=thesis_graph_report_path,
        strategic_tension_report_path=strategic_tension_report_path,
    )


def materialize_oracle_briefing_pack(
    pack_root: Path,
    report: OracleBriefingPackReport,
    *,
    markdown: str,
    html: str,
) -> OracleBriefingPackReport:
    return materialize_briefing_pack_bundle(pack_root, report, markdown=markdown, html=html)


__all__ = [
    '_briefing_pack_projection_inputs',
    '_briefing_sections',
    '_build_oracle_briefing_pack_impl',
    '_exact_cadence_summary',
    '_unique',
    'build_oracle_briefing_pack',
    'emit_oracle_briefing_pack_projection_registry',
    'materialize_operator_queue_snapshot',
    'materialize_oracle_briefing_pack',
    'render_oracle_briefing_pack_html',
    'render_oracle_briefing_pack_markdown',
]
