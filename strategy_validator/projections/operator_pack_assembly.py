from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from strategy_validator.contracts.oracle import OracleBriefingPackReport, OracleIncidentPackReport, OracleStatusPackReport


@dataclass(frozen=True)
class OracleStatusPackAssemblyRequest:
    repo_root: Path
    search_root: Path | None = None
    derived_view_report_path: Path | None = None
    constitutional_gate_report_path: Path | None = None
    closure_snapshot_path: Path | None = None
    closure_dsse_path: Path | None = None
    closure_public_key_path: Path | None = None
    governed_exception_memo_path: Path | None = None
    governed_exception_dsse_path: Path | None = None
    governed_exception_public_key_path: Path | None = None
    temporal_lane_status_path: Path | None = None


@dataclass(frozen=True)
class OracleIncidentPackAssemblyRequest:
    repo_root: Path
    search_root: Path | None = None
    derived_view_report_path: Path | None = None
    constitutional_gate_report_path: Path | None = None
    closure_snapshot_path: Path | None = None
    closure_dsse_path: Path | None = None
    closure_public_key_path: Path | None = None
    governed_exception_memo_path: Path | None = None
    governed_exception_dsse_path: Path | None = None
    governed_exception_public_key_path: Path | None = None
    temporal_lane_status_path: Path | None = None


@dataclass(frozen=True)
class OracleBriefingPackAssemblyRequest:
    repo_root: Path
    search_root: Path | None = None
    derived_view_report_path: Path | None = None
    constitutional_gate_report_path: Path | None = None
    closure_snapshot_path: Path | None = None
    closure_dsse_path: Path | None = None
    closure_public_key_path: Path | None = None
    governed_exception_memo_path: Path | None = None
    governed_exception_dsse_path: Path | None = None
    governed_exception_public_key_path: Path | None = None
    temporal_lane_status_path: Path | None = None
    strategic_briefing_report_path: Path | None = None
    strategic_narrative_report_path: Path | None = None
    strategic_memory_horizon_report_path: Path | None = None
    contradiction_resolution_report_path: Path | None = None
    strategic_intervention_report_path: Path | None = None
    strategic_campaign_report_path: Path | None = None
    strategic_campaign_execution_report_path: Path | None = None
    thesis_memory_report_path: Path | None = None
    strategy_cohort_report_path: Path | None = None
    doctrine_adaptation_report_path: Path | None = None
    research_priority_report_path: Path | None = None
    research_execution_memory_report_path: Path | None = None
    thesis_graph_report_path: Path | None = None
    strategic_tension_report_path: Path | None = None


def build_status_pack_assembly_request(**kwargs) -> OracleStatusPackAssemblyRequest:
    return OracleStatusPackAssemblyRequest(**kwargs)


def build_incident_pack_assembly_request(**kwargs) -> OracleIncidentPackAssemblyRequest:
    return OracleIncidentPackAssemblyRequest(**kwargs)


def build_briefing_pack_assembly_request(**kwargs) -> OracleBriefingPackAssemblyRequest:
    return OracleBriefingPackAssemblyRequest(**kwargs)


def assemble_oracle_status_pack(request: OracleStatusPackAssemblyRequest | None = None, **kwargs) -> OracleStatusPackReport:
    request = request or OracleStatusPackAssemblyRequest(**kwargs)
    from strategy_validator.validator.oracle_diagnostics import _build_oracle_status_pack_impl

    return _build_oracle_status_pack_impl(
        repo_root=request.repo_root,
        search_root=request.search_root,
        derived_view_report_path=request.derived_view_report_path,
        constitutional_gate_report_path=request.constitutional_gate_report_path,
        closure_snapshot_path=request.closure_snapshot_path,
        closure_dsse_path=request.closure_dsse_path,
        closure_public_key_path=request.closure_public_key_path,
        governed_exception_memo_path=request.governed_exception_memo_path,
        governed_exception_dsse_path=request.governed_exception_dsse_path,
        governed_exception_public_key_path=request.governed_exception_public_key_path,
        temporal_lane_status_path=request.temporal_lane_status_path,
    )


def assemble_oracle_incident_pack(request: OracleIncidentPackAssemblyRequest | None = None, **kwargs) -> OracleIncidentPackReport:
    request = request or OracleIncidentPackAssemblyRequest(**kwargs)
    from strategy_validator.validator.oracle_diagnostics import _build_oracle_incident_pack_impl

    return _build_oracle_incident_pack_impl(
        repo_root=request.repo_root,
        search_root=request.search_root,
        derived_view_report_path=request.derived_view_report_path,
        constitutional_gate_report_path=request.constitutional_gate_report_path,
        closure_snapshot_path=request.closure_snapshot_path,
        closure_dsse_path=request.closure_dsse_path,
        closure_public_key_path=request.closure_public_key_path,
        governed_exception_memo_path=request.governed_exception_memo_path,
        governed_exception_dsse_path=request.governed_exception_dsse_path,
        governed_exception_public_key_path=request.governed_exception_public_key_path,
        temporal_lane_status_path=request.temporal_lane_status_path,
    )


def assemble_oracle_briefing_pack(request: OracleBriefingPackAssemblyRequest | None = None, **kwargs) -> OracleBriefingPackReport:
    request = request or OracleBriefingPackAssemblyRequest(**kwargs)
    from strategy_validator.validator.oracle_briefing import _build_oracle_briefing_pack_impl

    return _build_oracle_briefing_pack_impl(
        repo_root=request.repo_root,
        search_root=request.search_root,
        derived_view_report_path=request.derived_view_report_path,
        constitutional_gate_report_path=request.constitutional_gate_report_path,
        closure_snapshot_path=request.closure_snapshot_path,
        closure_dsse_path=request.closure_dsse_path,
        closure_public_key_path=request.closure_public_key_path,
        governed_exception_memo_path=request.governed_exception_memo_path,
        governed_exception_dsse_path=request.governed_exception_dsse_path,
        governed_exception_public_key_path=request.governed_exception_public_key_path,
        strategic_briefing_report_path=request.strategic_briefing_report_path,
        strategic_narrative_report_path=request.strategic_narrative_report_path,
        strategic_memory_horizon_report_path=request.strategic_memory_horizon_report_path,
        contradiction_resolution_report_path=request.contradiction_resolution_report_path,
        strategic_intervention_report_path=request.strategic_intervention_report_path,
        strategic_campaign_report_path=request.strategic_campaign_report_path,
        strategic_campaign_execution_report_path=request.strategic_campaign_execution_report_path,
        thesis_memory_report_path=request.thesis_memory_report_path,
        strategy_cohort_report_path=request.strategy_cohort_report_path,
        doctrine_adaptation_report_path=request.doctrine_adaptation_report_path,
        research_priority_report_path=request.research_priority_report_path,
        research_execution_memory_report_path=request.research_execution_memory_report_path,
        thesis_graph_report_path=request.thesis_graph_report_path,
        strategic_tension_report_path=request.strategic_tension_report_path,
    )
