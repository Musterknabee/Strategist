from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from strategy_validator.contracts.oracle import (
    OracleAdvisoryInput,
    OracleDoctrineAdaptationReport,
    OracleResearchExecutionMemoryReport,
    OracleResearchPriorityReport,
    OracleStrategicFusionReport,
    OracleStrategyCohortReport,
    OracleThesisGraphEdge,
    OracleThesisGraphNode,
    OracleThesisGraphReport,
    OracleThesisMemoryReport,
)
from strategy_validator.validator.oracle_doctrine_adaptation import build_oracle_doctrine_adaptation_report
from strategy_validator.validator.oracle_research_planner import build_oracle_research_priority_report
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report
from strategy_validator.validator.oracle_strategy_cohort import build_oracle_strategy_cohort_report
from strategy_validator.validator.oracle_thesis_memory import build_oracle_thesis_memory_report
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.oracle_run_identity import assert_matching_strategic_epoch
from strategy_validator.validator.strategy_health_posterior import build_strategy_health_posterior_report
from strategy_validator.validator.oracle_strategic_artifact_evidence import (
    discover_preferred_strategic_artifact_evidence,
    preferred_artifact_evidence_fact,
    strategic_artifact_evidence_support_score,
)


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _unique(items: list[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if normalized and normalized not in output:
            output.append(normalized)
    return output


def _thesis_risk(state: str, evolution: str) -> float:
    base = {
        "SUPPORTIVE": 0.16,
        "NEUTRAL": 0.32,
        "CAUTIONARY": 0.56,
        "AT_RISK": 0.78,
        "BROKEN": 0.94,
    }.get(state, 0.40)
    if evolution in {"WEAKENING", "REVERSING"}:
        base += 0.08
    elif evolution in {"STRENGTHENING", "EMERGING"}:
        base -= 0.05
    return round(_clamp(base), 6)


def _priority_risk(kind: str, urgency: float) -> float:
    bonus = {
        "DOCTRINE_REVIEW": 0.10,
        "THESIS_REVIEW": 0.08,
        "SCENARIO_PROBE": 0.06,
        "STRATEGY_VALIDATION": 0.06,
        "REGIME_INVESTIGATION": 0.05,
    }.get(kind, 0.04)
    return round(_clamp(urgency + bonus), 6)


def _outcome_risk(disposition: str | None, urgency_impact: float) -> float:
    base = {
        "ESCALATED": 0.86,
        "REFUTED": 0.76,
        "MIXED": 0.62,
        "INCONCLUSIVE": 0.52,
        "CONFIRMED": 0.34,
        None: 0.40,
    }.get(disposition, 0.40)
    return round(_clamp(base + 0.20 * max(urgency_impact, 0.0)), 6)


def _strategy_node_risk(item) -> float:
    return round(_clamp(0.42 * (1.0 - item.cohort_rank_score) + 0.24 * (1.0 - item.scenario_downside_floor) + 0.18 * item.transition_sensitivity_score + 0.16 * item.thesis_pressure_score), 6)


def _relation_from_thesis(item) -> str:
    if item.current_state in {"AT_RISK", "BROKEN"} or item.evolution_state in {"WEAKENING", "REVERSING"}:
        return "WEAKENS"
    return "SUPPORTS"


def _relation_from_outcome_to_strategy(effect: str) -> str:
    return {"PROMOTES": "PROMOTES", "DEMOTES": "DEMOTES", "WATCH": "PRESSURES", "NO_CHANGE": "DEPENDS_ON"}.get(effect, "DEPENDS_ON")


def _relation_from_outcome_to_thesis(effect: str) -> str:
    return {"STRENGTHENS": "SUPPORTS", "WEAKENS": "WEAKENS", "REVIEW_REQUIRED": "PRESSURES", "NO_CHANGE": "DEPENDS_ON"}.get(effect, "DEPENDS_ON")


def _relation_from_outcome_to_doctrine(effect: str) -> str:
    return {"RELIEVES": "RELIEVES", "PRESSURES": "PRESSURES", "FREEZE_CANDIDATE": "PRESSURES", "NO_CHANGE": "DEPENDS_ON"}.get(effect, "DEPENDS_ON")


def build_oracle_thesis_graph_report(
    payload: OracleAdvisoryInput,
    *,
    fusion_report: OracleStrategicFusionReport | None = None,
    thesis_memory_report: OracleThesisMemoryReport | None = None,
    strategy_cohort_report: OracleStrategyCohortReport | None = None,
    doctrine_adaptation_report: OracleDoctrineAdaptationReport | None = None,
    research_priority_report: OracleResearchPriorityReport | None = None,
    research_execution_memory_report: OracleResearchExecutionMemoryReport | None = None,
    doctrine_adaptation_report_path: Path | None = None,
    research_priority_report_path: Path | None = None,
    repo_root: Path | None = None,
    search_root: Path | None = None,
    now_utc: datetime | None = None,
) -> OracleThesisGraphReport:
    issued_at = now_utc or _utc_now()
    fusion = fusion_report or build_oracle_strategic_fusion_report(payload, now_utc=issued_at)
    posterior = build_strategy_health_posterior_report(payload, fusion, now_utc=issued_at)
    thesis = thesis_memory_report or build_oracle_thesis_memory_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        execution_memory_report=research_execution_memory_report,
        now_utc=issued_at,
    )
    cohorts = strategy_cohort_report or build_oracle_strategy_cohort_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        thesis_memory_report=thesis,
        execution_memory_report=research_execution_memory_report,
        now_utc=issued_at,
    )
    doctrine = doctrine_adaptation_report or build_oracle_doctrine_adaptation_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        thesis_memory_report=thesis,
        strategy_cohort_report=cohorts,
        execution_memory_report=research_execution_memory_report,
        now_utc=issued_at,
    )
    priorities = research_priority_report or build_oracle_research_priority_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        thesis_memory_report=thesis,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        now_utc=issued_at,
    )

    oracle_run_id, input_timestamp_utc, _ = assert_matching_strategic_epoch(fusion, thesis, cohorts, doctrine, priorities, research_execution_memory_report)

    resolved_repo_root = (repo_root or Path.cwd()).resolve()
    resolved_search_root = (search_root or resolved_repo_root).resolve()
    doctrine_artifact_evidence = discover_preferred_strategic_artifact_evidence(
        report_path=Path(doctrine_adaptation_report_path), repo_root=resolved_repo_root, search_root=resolved_search_root
    ) if doctrine_adaptation_report_path is not None and Path(doctrine_adaptation_report_path).exists() else None
    research_artifact_evidence = discover_preferred_strategic_artifact_evidence(
        report_path=Path(research_priority_report_path), repo_root=resolved_repo_root, search_root=resolved_search_root
    ) if research_priority_report_path is not None and Path(research_priority_report_path).exists() else None
    doctrine_exact_support = strategic_artifact_evidence_support_score(doctrine_artifact_evidence)
    research_exact_support = strategic_artifact_evidence_support_score(research_artifact_evidence)
    exact_evidence_support_score = max(doctrine_exact_support, research_exact_support, thesis.exact_evidence_support_score)
    preferred_backing_source = (
        doctrine_artifact_evidence.get("preferred_strategic_backing_source") if doctrine_artifact_evidence and doctrine_exact_support >= research_exact_support else None
    ) or (
        research_artifact_evidence.get("preferred_strategic_backing_source") if research_artifact_evidence else None
    ) or thesis.preferred_strategic_backing_source or doctrine.preferred_strategic_backing_source or priorities.preferred_strategic_backing_source
    preferred_backing_classification = (
        doctrine_artifact_evidence.get("preferred_strategic_backing_classification") if doctrine_artifact_evidence and doctrine_exact_support >= research_exact_support else None
    ) or (
        research_artifact_evidence.get("preferred_strategic_backing_classification") if research_artifact_evidence else None
    ) or thesis.preferred_strategic_backing_classification or doctrine.preferred_strategic_backing_classification or priorities.preferred_strategic_backing_classification

    nodes: dict[str, OracleThesisGraphNode] = {}
    edges: list[OracleThesisGraphEdge] = []

    def add_node(node_id: str, node_kind: str, label: str, status: str, base_risk: float, evidence: list[str], summary_line: str, exact_support: float = 0.0) -> None:
        if node_id in nodes:
            return
        nodes[node_id] = OracleThesisGraphNode(
            node_id=node_id,
            node_kind=node_kind,
            label=label,
            status=status,
            cascade_risk_score=round(_clamp(base_risk), 6),
            exact_evidence_support_score=round(_clamp(exact_support), 6),
            connected_node_ids=[],
            evidence=_unique(evidence)[:8],
            summary_line=summary_line,
        )

    def add_edge(source: str, target: str, relation: str, influence: float, summary_line: str) -> None:
        if source not in nodes or target not in nodes or source == target:
            return
        edge_id = f"{source}->{target}:{relation}"
        if any(item.edge_id == edge_id for item in edges):
            return
        edges.append(OracleThesisGraphEdge(
            edge_id=edge_id,
            source_node_id=source,
            target_node_id=target,
            relation_kind=relation,
            influence_score=round(_clamp(influence), 6),
            summary_line=summary_line,
        ))

    for item in thesis.items:
        add_node(
            item.thesis_id,
            "THESIS",
            item.thesis_label,
            item.current_state,
            _thesis_risk(item.current_state, item.evolution_state),
            item.evidence_against + item.evidence_for + preferred_artifact_evidence_fact("graph_support", doctrine_artifact_evidence if item.thesis_kind == "DOCTRINE" else research_artifact_evidence if item.thesis_kind == "STRATEGY" else (doctrine_artifact_evidence if doctrine_exact_support >= research_exact_support else research_artifact_evidence)),
            item.summary_line,
            item.exact_evidence_support_score,
        )

    for item in cohorts.items:
        add_node(
            f"strategy:{item.strategy_id}",
            "STRATEGY_COHORT",
            item.strategy_id,
            item.cohort_bucket,
            _strategy_node_risk(item),
            item.evidence + preferred_artifact_evidence_fact("graph_support", research_artifact_evidence),
            item.summary_line,
            research_exact_support,
        )

    for item in doctrine.items:
        add_node(
            item.clause_id,
            "DOCTRINE_CLAUSE",
            item.clause_label,
            item.adaptation_state,
            item.stress_score,
            item.pressure_sources + item.weakening_assumptions + preferred_artifact_evidence_fact("graph_support", doctrine_artifact_evidence),
            item.summary_line,
            doctrine_exact_support,
        )

    for item in priorities.items:
        add_node(
            item.priority_id,
            "RESEARCH_PRIORITY",
            item.title,
            item.priority_kind,
            _priority_risk(item.priority_kind, item.urgency_score),
            item.evidence,
            item.summary_line,
        )

    if research_execution_memory_report is not None:
        for item in research_execution_memory_report.items:
            add_node(
                f"outcome:{item.execution_id}",
                "INVESTIGATION_OUTCOME",
                item.priority_id,
                item.outcome_disposition or item.execution_state,
                _outcome_risk(item.outcome_disposition, item.urgency_impact),
                item.evidence + [item.finding_summary],
                item.summary_line,
            )

    doctrine_thesis = next((item for item in thesis.items if item.thesis_id == "doctrine:coherence"), None)
    if doctrine_thesis is not None:
        for clause in doctrine.items:
            relation = "PRESSURES" if doctrine_thesis.current_state in {"AT_RISK", "BROKEN"} or clause.stress_score >= 0.54 else "SUPPORTS"
            add_edge(doctrine_thesis.thesis_id, clause.clause_id, relation, max(clause.stress_score, 1.0 - doctrine_thesis.confidence_score), f"Doctrine coherence {'pressures' if relation == 'PRESSURES' else 'supports'} {clause.clause_label.lower()}.")

    for item in thesis.items:
        if item.thesis_kind == "STRATEGY":
            for strategy_id in item.strategy_ids:
                strategy_node_id = f"strategy:{strategy_id}"
                if strategy_node_id in nodes:
                    relation = _relation_from_thesis(item)
                    add_edge(item.thesis_id, strategy_node_id, relation, max(_thesis_risk(item.current_state, item.evolution_state), 0.35), f"{item.thesis_label} {relation.lower()} {strategy_id} under the current strategic stack.")
        elif item.thesis_kind == "REGIME":
            for priority in priorities.items:
                if priority.priority_kind == "REGIME_INVESTIGATION":
                    add_edge(priority.priority_id, item.thesis_id, "INVESTIGATES", priority.urgency_score, f"{priority.title} investigates the current regime thesis.")
        elif item.thesis_kind == "DOCTRINE":
            for clause in doctrine.items[:2]:
                relation = "PRESSURES" if item.current_state in {"AT_RISK", "BROKEN"} else "SUPPORTS"
                add_edge(item.thesis_id, clause.clause_id, relation, max(clause.stress_score, 1.0 - item.confidence_score), f"{item.thesis_label} {relation.lower()} {clause.clause_label.lower()}.")

    alignment_clause = next((item for item in doctrine.items if item.clause_id == "doctrine:strategy-alignment"), None)
    if alignment_clause is not None:
        for item in cohorts.items:
            relation = "PRESSURES" if item.cohort_bucket in {"PRESSURED", "RESEARCH_ONLY"} else "SUPPORTS"
            influence = max(item.transition_sensitivity_score, 1.0 - item.cohort_rank_score)
            add_edge(f"strategy:{item.strategy_id}", alignment_clause.clause_id, relation, influence, f"{item.strategy_id} {relation.lower()} doctrine strategy alignment through its cohort pressure profile.")

    weakening_theses = [item for item in thesis.items if item.evolution_state in {"WEAKENING", "REVERSING"}] or thesis.items[:1]
    for priority in priorities.items:
        if priority.related_strategy_ids:
            for strategy_id in priority.related_strategy_ids[:3]:
                add_edge(priority.priority_id, f"strategy:{strategy_id}", "INVESTIGATES", priority.urgency_score, f"{priority.title} investigates {strategy_id}.")
        if priority.priority_kind == "DOCTRINE_REVIEW":
            for clause in doctrine.items[:2]:
                add_edge(priority.priority_id, clause.clause_id, "INVESTIGATES", priority.urgency_score, f"{priority.title} investigates {clause.clause_label.lower()}.")
        elif priority.priority_kind == "THESIS_REVIEW":
            for item in weakening_theses[:2]:
                add_edge(priority.priority_id, item.thesis_id, "INVESTIGATES", priority.urgency_score, f"{priority.title} investigates {item.thesis_label.lower()}.")

    if research_execution_memory_report is not None:
        for item in research_execution_memory_report.items:
            outcome_id = f"outcome:{item.execution_id}"
            if item.priority_id in nodes:
                add_edge(outcome_id, item.priority_id, "DEPENDS_ON", _outcome_risk(item.outcome_disposition, item.urgency_impact), f"{item.priority_id} produced execution memory outcome {item.execution_id}.")
            for thesis_id in item.thesis_ids:
                add_edge(outcome_id, thesis_id, _relation_from_outcome_to_thesis(item.thesis_effect), max(abs(item.confidence_impact), 0.35), f"Investigation outcome {item.execution_id} {item.thesis_effect.lower()} {thesis_id}.")
            for clause_id in item.doctrine_clause_ids:
                add_edge(outcome_id, clause_id, _relation_from_outcome_to_doctrine(item.doctrine_effect), max(abs(item.urgency_impact), 0.35), f"Investigation outcome {item.execution_id} {item.doctrine_effect.lower()} {clause_id}.")
            for strategy_id in item.related_strategy_ids:
                add_edge(outcome_id, f"strategy:{strategy_id}", _relation_from_outcome_to_strategy(item.cohort_effect), max(abs(item.confidence_impact), 0.35), f"Investigation outcome {item.execution_id} {item.cohort_effect.lower()} {strategy_id} in the active cohort map.")

    incoming: dict[str, list[OracleThesisGraphEdge]] = defaultdict(list)
    outgoing: dict[str, list[OracleThesisGraphEdge]] = defaultdict(list)
    for edge in edges:
        incoming[edge.target_node_id].append(edge)
        outgoing[edge.source_node_id].append(edge)

    pressure_relations = {"PRESSURES", "WEAKENS", "DEMOTES"}
    support_relations = {"SUPPORTS", "RELIEVES", "PROMOTES"}
    updated_nodes: list[OracleThesisGraphNode] = []
    for node in nodes.values():
        in_edges = incoming.get(node.node_id, [])
        out_edges = outgoing.get(node.node_id, [])
        pressure = sum(edge.influence_score for edge in in_edges + out_edges if edge.relation_kind in pressure_relations)
        support = sum(edge.influence_score for edge in in_edges + out_edges if edge.relation_kind in support_relations)
        degree = len(in_edges) + len(out_edges)
        cascade = _clamp(node.cascade_risk_score + 0.12 * min(1.0, pressure / 2.0) - 0.07 * min(1.0, support / 2.0) + 0.05 * min(1.0, degree / 6.0) - 0.08 * node.exact_evidence_support_score)
        connected_ids = _unique([edge.target_node_id for edge in out_edges] + [edge.source_node_id for edge in in_edges])[:10]
        summary_line = f"{node.label} has cascade risk {cascade:.2f} across {len(connected_ids)} connected node(s)."
        if node.exact_evidence_support_score > 0:
            summary_line = f"{node.label} has cascade risk {cascade:.2f} across {len(connected_ids)} connected node(s) with exact support {node.exact_evidence_support_score:.2f}."
        updated_nodes.append(node.model_copy(update={
            "cascade_risk_score": round(cascade, 6),
            "connected_node_ids": connected_ids,
            "summary_line": summary_line,
        }))

    updated_nodes.sort(key=lambda item: (-item.cascade_risk_score, item.node_kind, item.node_id))
    highest_ids = [item.node_id for item in updated_nodes[:5]]
    operator_actions = []
    if highest_ids:
        top = updated_nodes[0]
        operator_actions.append(f"Investigate cascade risk around {top.label.lower()} before widening conviction.")
    for item in updated_nodes[:3]:
        if item.node_kind == "DOCTRINE_CLAUSE":
            operator_actions.append(f"Review doctrine clause {item.label.lower()} because it sits on a high-risk dependency path.")
        elif item.node_kind == "STRATEGY_COHORT":
            operator_actions.append(f"Re-check strategy cohort {item.label} because its dependencies are carrying elevated cascade risk.")
        elif item.node_kind == "THESIS":
            operator_actions.append(f"Refresh thesis evidence for {item.label.lower()} before treating it as stable.")
    operator_actions = _unique(operator_actions)[:6]
    top_label = updated_nodes[0].label if updated_nodes else 'none'
    return OracleThesisGraphReport(
        generated_at_utc=issued_at,
        universe_label=payload.universe_label,
        oracle_run_id=oracle_run_id,
        input_timestamp_utc=input_timestamp_utc,
        dominant_regime=fusion.dominant_regime,
        strategic_posture=fusion.strategic_posture,
        preferred_strategic_backing_source=preferred_backing_source,
        preferred_strategic_backing_classification=preferred_backing_classification,
        exact_evidence_support_score=round(exact_evidence_support_score, 6),
        summary_line=(
            f"Thesis graph for {payload.universe_label}: {len(updated_nodes)} nodes and {len(edges)} edges, "
            f"highest cascade risk concentrated around {top_label}."
        ),
        highest_cascade_risk_node_ids=highest_ids,
        nodes=updated_nodes,
        edges=sorted(edges, key=lambda item: (-item.influence_score, item.source_node_id, item.target_node_id)),
        operator_actions=operator_actions,
    )


def render_oracle_thesis_graph_markdown(report: OracleThesisGraphReport) -> str:
    node_lines = []
    for item in report.nodes[:10]:
        node_lines.append(
            "\n".join([
                f"### {item.label}",
                "",
                f"- Node ID: {item.node_id}",
                f"- Kind: {item.node_kind}",
                f"- Status: {item.status}",
                f"- Cascade risk score: {item.cascade_risk_score:.2f}",
                f"- Exact evidence support score: {item.exact_evidence_support_score:.2f}",
                f"- Connected nodes: {', '.join(item.connected_node_ids) if item.connected_node_ids else 'none'}",
                f"- Summary: {item.summary_line}",
                f"- Evidence: {', '.join(item.evidence) if item.evidence else 'none'}",
            ])
        )
    edge_lines = []
    for item in report.edges[:14]:
        edge_lines.append(f"- {item.source_node_id} -> {item.target_node_id} [{item.relation_kind}] influence={item.influence_score:.2f} :: {item.summary_line}")
    action_lines = "\n".join(f"- {item}" for item in report.operator_actions) or "- none"
    top_lines = "\n".join(f"- {item}" for item in report.highest_cascade_risk_node_ids) or "- none"
    node_block = "\n\n".join(node_lines) if node_lines else "No graph nodes were available."
    edge_block = "\n".join(edge_lines) if edge_lines else "- none"
    return f"""# ORACLE THESIS GRAPH REPORT

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Universe: {report.universe_label}
- Dominant regime: {report.dominant_regime}
- Strategic posture: {report.strategic_posture}
- Preferred strategic backing source: {report.preferred_strategic_backing_source or 'none'}
- Preferred strategic backing classification: {report.preferred_strategic_backing_classification or 'none'}
- Exact evidence support score: {report.exact_evidence_support_score:.2f}

## Summary

{report.summary_line}

## Highest Cascade Risk Nodes

{top_lines}

## Nodes

{node_block}

## Edges

{edge_block}

## Recommended operator actions

{action_lines}
"""


def load_thesis_graph_report(path: Path) -> OracleThesisGraphReport:
    return OracleThesisGraphReport.model_validate(json.loads(path.read_text(encoding="utf-8")))
