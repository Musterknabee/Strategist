from __future__ import annotations

import hashlib
import json
from pathlib import Path

from strategy_validator.contracts.oracle_operator_reports import OracleBriefingPackReport
from strategy_validator.contracts.oracle_strategic_memory import (
    OracleContradictionResolutionReport,
    OracleDoctrineAdaptationReport,
    OracleResearchExecutionMemoryReport,
    OracleResearchPriorityReport,
    OracleStrategicInterventionReport,
    OracleStrategicMemoryHorizonReport,
    OracleStrategicNarrativeReport,
    OracleStrategicTensionReport,
    OracleThesisGraphReport,
    OracleThesisMemoryReport,
)
from strategy_validator.contracts.oracle_evidence_events import OracleDerivedViewReport
from strategy_validator.contracts.oracle_strategic_programs import (
    OracleScenarioLabReport,
    OracleStrategicBriefingReport,
    OracleStrategicCampaignExecutionReport,
    OracleStrategicCampaignReport,
    OracleStrategyCohortReport,
)
from strategy_validator.projections.artifact_registry import write_projection_artifact_registry_with_index
from strategy_validator.projections.briefing_pack import build_briefing_pack_projection_registry
from strategy_validator.projections.service import select_latest_canonical_event_projection
from strategy_validator.validator.oracle_schema_registry import validate_registered_schema

def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_json(payload: dict) -> str:
    stable = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(stable).hexdigest()


def _with_provenance_digest(report: OracleBriefingPackReport) -> OracleBriefingPackReport:
    payload = report.model_dump(mode="json")
    payload.pop("generated_at_utc", None)
    payload.pop("provenance_digest_sha256", None)
    return report.model_copy(update={"provenance_digest_sha256": _sha256_json(payload)})


def _load_derived_view(path: Path | None) -> OracleDerivedViewReport | None:
    if path is None or not path.exists():
        return None
    payload = _load_json(path)
    validate_registered_schema(payload, expected_families={"oracle"})
    if payload.get("schema_version") != "oracle_derived_view_report/v1":
        return None
    return OracleDerivedViewReport.model_validate(payload)


def _load_strategic_briefing(path: Path | None) -> OracleStrategicBriefingReport | None:
    if path is None or not path.exists():
        return None
    payload = _load_json(path)
    validate_registered_schema(payload, expected_families={"oracle"})
    if payload.get("schema_version") != "oracle_strategic_briefing_report/v1":
        return None
    return OracleStrategicBriefingReport.model_validate(payload)


def _load_scenario_lab(path: Path | None) -> OracleScenarioLabReport | None:
    if path is None or not path.exists():
        return None
    payload = _load_json(path)
    validate_registered_schema(payload, expected_families={"oracle"})
    if payload.get("schema_version") != "oracle_scenario_lab_report/v1":
        return None
    return OracleScenarioLabReport.model_validate(payload)


def _load_thesis_memory(path: Path | None) -> OracleThesisMemoryReport | None:
    if path is None or not path.exists():
        return None
    payload = _load_json(path)
    validate_registered_schema(payload, expected_families={"oracle"})
    if payload.get("schema_version") != "oracle_thesis_memory_report/v1":
        return None
    return OracleThesisMemoryReport.model_validate(payload)


def _load_strategy_cohort(path: Path | None) -> OracleStrategyCohortReport | None:
    if path is None or not path.exists():
        return None
    payload = _load_json(path)
    validate_registered_schema(payload, expected_families={"oracle"})
    if payload.get("schema_version") != "oracle_strategy_cohort_report/v1":
        return None
    return OracleStrategyCohortReport.model_validate(payload)

def _load_doctrine_adaptation(path: Path | None) -> OracleDoctrineAdaptationReport | None:
    if path is None or not path.exists():
        return None
    payload = _load_json(path)
    validate_registered_schema(payload, expected_families={"oracle"})
    if payload.get("schema_version") != "oracle_doctrine_adaptation_report/v1":
        return None
    return OracleDoctrineAdaptationReport.model_validate(payload)


def _load_research_priorities(path: Path | None) -> OracleResearchPriorityReport | None:
    if path is None or not path.exists():
        return None
    payload = _load_json(path)
    validate_registered_schema(payload, expected_families={"oracle"})
    if payload.get("schema_version") != "oracle_research_priority_report/v1":
        return None
    return OracleResearchPriorityReport.model_validate(payload)


def _load_research_execution_memory(path: Path | None) -> OracleResearchExecutionMemoryReport | None:
    if path is None or not path.exists():
        return None
    payload = _load_json(path)
    validate_registered_schema(payload, expected_families={"oracle"})
    if payload.get("schema_version") != "oracle_research_execution_memory_report/v1":
        return None
    return OracleResearchExecutionMemoryReport.model_validate(payload)


def _load_thesis_graph(path: Path | None) -> OracleThesisGraphReport | None:
    if path is None or not path.exists():
        return None
    payload = _load_json(path)
    validate_registered_schema(payload, expected_families={"oracle"})
    if payload.get("schema_version") != "oracle_thesis_graph_report/v1":
        return None
    return OracleThesisGraphReport.model_validate(payload)


def _load_strategic_tensions(path: Path | None) -> OracleStrategicTensionReport | None:
    if path is None or not path.exists():
        return None
    payload = _load_json(path)
    validate_registered_schema(payload, expected_families={"oracle"})
    if payload.get("schema_version") != "oracle_strategic_tension_report/v1":
        return None
    return OracleStrategicTensionReport.model_validate(payload)


def _load_strategic_narrative(path: Path | None) -> OracleStrategicNarrativeReport | None:
    if path is None or not path.exists():
        return None
    payload = _load_json(path)
    validate_registered_schema(payload, expected_families={"oracle"})
    if payload.get("schema_version") != "oracle_strategic_narrative_report/v1":
        return None
    return OracleStrategicNarrativeReport.model_validate(payload)


def _load_strategic_memory_horizon(path: Path | None) -> OracleStrategicMemoryHorizonReport | None:
    if path is None or not path.exists():
        return None
    payload = _load_json(path)
    validate_registered_schema(payload, expected_families={"oracle"})
    if payload.get("schema_version") != "oracle_strategic_memory_horizon_report/v1":
        return None
    return OracleStrategicMemoryHorizonReport.model_validate(payload)


def _load_strategic_intervention(path: Path | None) -> OracleStrategicInterventionReport | None:
    if path is None or not path.exists():
        return None
    payload = _load_json(path)
    validate_registered_schema(payload, expected_families={"oracle"})
    if payload.get("schema_version") != "oracle_strategic_intervention_report/v1":
        return None
    return OracleStrategicInterventionReport.model_validate(payload)

def _load_strategic_campaign(path: Path | None) -> OracleStrategicCampaignReport | None:
    if path is None or not path.exists():
        return None
    payload = _load_json(path)
    validate_registered_schema(payload, expected_families={"oracle"})
    if payload.get("schema_version") != "oracle_strategic_campaign_report/v1":
        return None
    return OracleStrategicCampaignReport.model_validate(payload)




def _load_strategic_campaign_execution(path: Path | None) -> OracleStrategicCampaignExecutionReport | None:
    if path is None or not path.exists():
        return None
    payload = _load_json(path)
    validate_registered_schema(payload, expected_families={"oracle"})
    if payload.get("schema_version") != "oracle_strategic_campaign_execution_report/v1":
        return None
    return OracleStrategicCampaignExecutionReport.model_validate(payload)



def _discover_latest_canonical_event_projection(
    *,
    search_root: Path,
    repo_root: Path,
) -> Path | None:
    selection = select_latest_canonical_event_projection(search_root=search_root, repo_root=repo_root)
    return selection.output_artifact_path if selection is not None else None


def _resolve_briefing_derived_view_path(
    *,
    search_root: Path,
    repo_root: Path,
    explicit_path: Path | None,
) -> Path | None:
    if explicit_path is not None:
        return explicit_path
    return _discover_latest_canonical_event_projection(search_root=search_root, repo_root=repo_root) or _find_latest(
        search_root, {"ORACLE_DERIVED_VIEW.json", "ORACLE_ROLLING_REVIEW.json", "ORACLE_HORIZON_VIEW.json"}
    )


def _briefing_pack_projection_inputs(
    *,
    repo_root: Path,
    search_root: Path | None = None,
    derived_view_report_path: Path | None = None,
    constitutional_gate_report_path: Path | None = None,
    closure_snapshot_path: Path | None = None,
    closure_dsse_path: Path | None = None,
    governed_exception_memo_path: Path | None = None,
    governed_exception_dsse_path: Path | None = None,
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
) -> tuple[dict[str, Path | None], dict[str, object | None]]:
    resolved_repo_root = repo_root.resolve()
    resolved_search_root = (search_root or (resolved_repo_root / "docs" / "artifacts")).resolve()
    source_paths: dict[str, Path | None] = {
        "derived_view": _resolve_briefing_derived_view_path(search_root=resolved_search_root, repo_root=resolved_repo_root, explicit_path=derived_view_report_path),
        "constitutional_gate": constitutional_gate_report_path,
        "closure_snapshot": closure_snapshot_path,
        "closure_dsse": closure_dsse_path,
        "governed_exception": governed_exception_memo_path,
        "governed_exception_dsse": governed_exception_dsse_path,
        "strategic_briefing": strategic_briefing_report_path or _find_latest(resolved_search_root, {"ORACLE_STRATEGIC_BRIEFING_REPORT.json"}),
        "strategic_narrative": strategic_narrative_report_path or _find_latest(resolved_search_root, {"ORACLE_STRATEGIC_NARRATIVE_REPORT.json"}),
        "strategic_memory_horizon": strategic_memory_horizon_report_path or _find_latest(resolved_search_root, {"ORACLE_STRATEGIC_MEMORY_HORIZON_REPORT.json"}),
        "contradiction_resolution": contradiction_resolution_report_path or _find_latest(resolved_search_root, {"ORACLE_CONTRADICTION_RESOLUTION_REPORT.json"}),
        "strategic_intervention": strategic_intervention_report_path or _find_latest(resolved_search_root, {"ORACLE_STRATEGIC_INTERVENTION_REPORT.json"}),
        "strategic_campaign": strategic_campaign_report_path or _find_latest(resolved_search_root, {"ORACLE_STRATEGIC_CAMPAIGN_REPORT.json"}),
        "strategic_campaign_execution": strategic_campaign_execution_report_path or _find_latest(resolved_search_root, {"ORACLE_STRATEGIC_CAMPAIGN_EXECUTION_REPORT.json"}),
        "thesis_memory": thesis_memory_report_path or _find_latest(resolved_search_root, {"ORACLE_THESIS_MEMORY_REPORT.json"}),
        "strategy_cohort": strategy_cohort_report_path or _find_latest(resolved_search_root, {"ORACLE_STRATEGY_COHORT_REPORT.json"}),
        "doctrine_adaptation": doctrine_adaptation_report_path or _find_latest(resolved_search_root, {"ORACLE_DOCTRINE_ADAPTATION_REPORT.json"}),
        "research_priorities": research_priority_report_path or _find_latest(resolved_search_root, {"ORACLE_RESEARCH_PRIORITY_REPORT.json"}),
        "research_execution_memory": research_execution_memory_report_path or _find_latest(resolved_search_root, {"ORACLE_RESEARCH_EXECUTION_MEMORY_REPORT.json"}),
        "thesis_graph": thesis_graph_report_path or _find_latest(resolved_search_root, {"ORACLE_THESIS_GRAPH_REPORT.json"}),
        "strategic_tensions": strategic_tension_report_path or _find_latest(resolved_search_root, {"ORACLE_STRATEGIC_TENSION_REPORT.json"}),
        "scenario_lab": _find_latest(resolved_search_root, {"ORACLE_SCENARIO_LAB_REPORT.json"}),
    }
    source_payloads: dict[str, object | None] = {
        "derived_view": _load_derived_view(source_paths["derived_view"]),
        "strategic_briefing": _load_strategic_briefing(source_paths["strategic_briefing"]),
        "strategic_narrative": _load_strategic_narrative(source_paths["strategic_narrative"]),
        "strategic_memory_horizon": _load_strategic_memory_horizon(source_paths["strategic_memory_horizon"]),
        "contradiction_resolution": _load_contradiction_resolution(source_paths["contradiction_resolution"]),
        "strategic_intervention": _load_strategic_intervention(source_paths["strategic_intervention"]),
        "strategic_campaign": _load_strategic_campaign(source_paths["strategic_campaign"]),
        "strategic_campaign_execution": _load_strategic_campaign_execution(source_paths["strategic_campaign_execution"]),
        "thesis_memory": _load_thesis_memory(source_paths["thesis_memory"]),
        "strategy_cohort": _load_strategy_cohort(source_paths["strategy_cohort"]),
        "doctrine_adaptation": _load_doctrine_adaptation(source_paths["doctrine_adaptation"]),
        "research_priorities": _load_research_priorities(source_paths["research_priorities"]),
        "research_execution_memory": _load_research_execution_memory(source_paths["research_execution_memory"]),
        "thesis_graph": _load_thesis_graph(source_paths["thesis_graph"]),
        "strategic_tensions": _load_strategic_tensions(source_paths["strategic_tensions"]),
        "scenario_lab": _load_scenario_lab(source_paths["scenario_lab"]),
    }
    return source_paths, source_payloads


def emit_oracle_briefing_pack_projection_registry(
    *,
    registry_output_path: Path,
    repo_root: Path,
    generated_at_utc,
    output_paths: list[Path],
    search_root: Path | None = None,
    derived_view_report_path: Path | None = None,
    constitutional_gate_report_path: Path | None = None,
    closure_snapshot_path: Path | None = None,
    closure_dsse_path: Path | None = None,
    governed_exception_memo_path: Path | None = None,
    governed_exception_dsse_path: Path | None = None,
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
) -> dict[str, object]:
    source_paths, source_payloads = _briefing_pack_projection_inputs(
        repo_root=repo_root,
        search_root=search_root,
        derived_view_report_path=derived_view_report_path,
        constitutional_gate_report_path=constitutional_gate_report_path,
        closure_snapshot_path=closure_snapshot_path,
        closure_dsse_path=closure_dsse_path,
        governed_exception_memo_path=governed_exception_memo_path,
        governed_exception_dsse_path=governed_exception_dsse_path,
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
    registry = build_briefing_pack_projection_registry(
        repo_root=repo_root.resolve(),
        generated_at_utc=generated_at_utc,
        source_paths=source_paths,
        source_payloads=source_payloads,
        output_paths=output_paths,
    )
    write_projection_artifact_registry_with_index(
        registry_output_path,
        registry,
        repo_root=repo_root.resolve(),
        generated_at_utc=generated_at_utc,
    )
    return registry


def _load_contradiction_resolution(path: Path | None) -> OracleContradictionResolutionReport | None:
    if path is None or not path.exists():
        return None
    payload = _load_json(path)
    validate_registered_schema(payload, expected_families={"oracle"})
    if payload.get("schema_version") != "oracle_contradiction_resolution_report/v1":
        return None
    return OracleContradictionResolutionReport.model_validate(payload)



def _find_latest(search_root: Path, candidates):
    discovered: list[Path] = []
    candidate_set = set(candidates)
    if not search_root.exists():
        return None
    for path in search_root.rglob("*"):
        if path.is_file() and path.name in candidate_set:
            discovered.append(path)
    if not discovered:
        return None
    discovered.sort(key=lambda p: (p.stat().st_mtime, str(p)), reverse=True)
    return discovered[0]
