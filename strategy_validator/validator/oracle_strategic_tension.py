from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from strategy_validator.contracts.oracle_core import OracleAdvisoryInput
from strategy_validator.contracts.oracle_strategic_memory import (
    OracleDoctrineAdaptationReport,
    OracleResearchExecutionMemoryReport,
    OracleResearchPriorityReport,
    OracleStrategicTensionItem,
    OracleStrategicTensionReport,
    OracleThesisGraphReport,
    OracleThesisMemoryReport,
)
from strategy_validator.contracts.oracle_strategic_fusion import (
    OracleOpportunityQueueReport,
    OracleStrategicFusionReport,
    StrategyHealthPosteriorReport,
)
from strategy_validator.contracts.oracle_strategic_programs import (
    OracleScenarioLabReport,
    OracleStrategyCohortReport,
)
from strategy_validator.validator.oracle_doctrine_adaptation import build_oracle_doctrine_adaptation_report
from strategy_validator.validator.oracle_opportunity_queue import build_oracle_opportunity_queue_report
from strategy_validator.validator.oracle_research_planner import build_oracle_research_priority_report
from strategy_validator.validator.oracle_scenario_lab import build_oracle_scenario_lab_report
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report
from strategy_validator.validator.oracle_strategy_cohort import build_oracle_strategy_cohort_report
from strategy_validator.validator.oracle_thesis_graph import build_oracle_thesis_graph_report
from strategy_validator.validator.oracle_thesis_memory import build_oracle_thesis_memory_report
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.strategy_health_posterior import build_strategy_health_posterior_report
from strategy_validator.validator.oracle_run_identity import assert_matching_strategic_epoch
from strategy_validator.validator.oracle_history_integrity import preferred_strategic_backing_source, preferred_strategic_backing_classification
from strategy_validator.validator.oracle_strategic_artifact_evidence import discover_preferred_strategic_artifact_evidence, preferred_artifact_evidence_fact, strategic_artifact_evidence_support_score


DefensivePostures = {"CAUTION_BIASED", "DEFENSIVE_RESEARCH", "RESEARCH_FREEZE"}
OpportunityPostures = {"OPPORTUNITY_BIASED", "BALANCED_OBSERVATION"}


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _unique(items: list[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if normalized and normalized not in output:
            output.append(normalized)
    return output


def _sort_items(items: list[OracleStrategicTensionItem]) -> list[OracleStrategicTensionItem]:
    return sorted(items, key=lambda item: (-item.severity_score, item.alignment_state, item.tension_kind, item.title))


def build_oracle_strategic_tension_report(
    payload: OracleAdvisoryInput,
    *,
    fusion_report: OracleStrategicFusionReport | None = None,
    posterior_report: StrategyHealthPosteriorReport | None = None,
    queue_report: OracleOpportunityQueueReport | None = None,
    thesis_memory_report: OracleThesisMemoryReport | None = None,
    scenario_lab_report: OracleScenarioLabReport | None = None,
    strategy_cohort_report: OracleStrategyCohortReport | None = None,
    doctrine_adaptation_report: OracleDoctrineAdaptationReport | None = None,
    research_priority_report: OracleResearchPriorityReport | None = None,
    research_execution_memory_report: OracleResearchExecutionMemoryReport | None = None,
    thesis_graph_report: OracleThesisGraphReport | None = None,
    doctrine_adaptation_report_path: Path | None = None,
    research_priority_report_path: Path | None = None,
    repo_root: Path | None = None,
    search_root: Path | None = None,
    now_utc: datetime | None = None,
) -> OracleStrategicTensionReport:
    issued_at = now_utc or _utc_now()
    fusion = fusion_report or build_oracle_strategic_fusion_report(payload, now_utc=issued_at)
    posterior = posterior_report or build_strategy_health_posterior_report(payload, fusion, now_utc=issued_at)
    queue = queue_report or build_oracle_opportunity_queue_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        now_utc=issued_at,
    )
    thesis = thesis_memory_report or build_oracle_thesis_memory_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        execution_memory_report=research_execution_memory_report,
        now_utc=issued_at,
    )
    scenario_lab = scenario_lab_report or build_oracle_scenario_lab_report(
        payload,
        baseline_fusion_report=fusion,
        now_utc=issued_at,
    )
    cohorts = strategy_cohort_report or build_oracle_strategy_cohort_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        queue_report=queue,
        thesis_memory_report=thesis,
        execution_memory_report=research_execution_memory_report,
        now_utc=issued_at,
    )
    doctrine = doctrine_adaptation_report or build_oracle_doctrine_adaptation_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=cohorts,
        execution_memory_report=research_execution_memory_report,
        now_utc=issued_at,
    )
    priorities = research_priority_report or build_oracle_research_priority_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        queue_report=queue,
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        now_utc=issued_at,
    )
    graph = thesis_graph_report or build_oracle_thesis_graph_report(
        payload,
        fusion_report=fusion,
        thesis_memory_report=thesis,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        research_execution_memory_report=research_execution_memory_report,
        now_utc=issued_at,
    )

    oracle_run_id, input_timestamp_utc, _ = assert_matching_strategic_epoch(fusion, posterior, queue, thesis, scenario_lab, cohorts, doctrine, priorities, research_execution_memory_report, graph)
    resolved_repo_root = repo_root.resolve() if repo_root is not None else None
    resolved_search_root = search_root.resolve() if search_root is not None else resolved_repo_root
    doctrine_artifact_evidence = discover_preferred_strategic_artifact_evidence(
        report_path=Path(doctrine_adaptation_report_path),
        repo_root=resolved_repo_root,
        search_root=resolved_search_root,
    ) if doctrine_adaptation_report_path is not None and Path(doctrine_adaptation_report_path).exists() and resolved_repo_root is not None else None
    research_artifact_evidence = discover_preferred_strategic_artifact_evidence(
        report_path=Path(research_priority_report_path),
        repo_root=resolved_repo_root,
        search_root=resolved_search_root,
    ) if research_priority_report_path is not None and Path(research_priority_report_path).exists() and resolved_repo_root is not None else None
    doctrine_exact_support = strategic_artifact_evidence_support_score(doctrine_artifact_evidence)
    research_exact_support = strategic_artifact_evidence_support_score(research_artifact_evidence)
    exact_evidence_support_score = round(max(doctrine_exact_support, research_exact_support), 6)
    preferred_backing_source = preferred_strategic_backing_source(getattr(doctrine, 'strategic_memory_horizon_report', None) if hasattr(doctrine, 'strategic_memory_horizon_report') else None) or getattr(doctrine, 'preferred_strategic_backing_source', None) or getattr(priorities, 'preferred_strategic_backing_source', None)
    preferred_backing_classification = preferred_strategic_backing_classification(getattr(doctrine, 'strategic_memory_horizon_report', None) if hasattr(doctrine, 'strategic_memory_horizon_report') else None) or getattr(doctrine, 'preferred_strategic_backing_classification', None) or getattr(priorities, 'preferred_strategic_backing_classification', None)
    items: list[OracleStrategicTensionItem] = []

    def add_item(
        tension_id: str,
        tension_kind: str,
        alignment_state: str,
        severity: float,
        title: str,
        summary_line: str,
        evidence: list[str],
        related_strategy_ids: list[str],
        resolution_guidance: str,
        evidence_support: float = 0.0,
    ) -> None:
        items.append(
            OracleStrategicTensionItem(
                tension_id=tension_id,
                tension_kind=tension_kind,
                alignment_state=alignment_state,
                exact_evidence_support_score=round(evidence_support, 6),
                severity_score=round(_clamp(severity + 0.08 * evidence_support), 6),
                title=title,
                summary_line=summary_line,
                evidence=_unique(evidence + preferred_artifact_evidence_fact("tension_support", doctrine_artifact_evidence if tension_kind in {"POSTURE_VS_RISK_STACK", "OPPORTUNITY_CONSENSUS", "POSTURE_CONSENSUS"} else research_artifact_evidence if tension_kind in {"RESEARCH_PRIORITY_VS_POSTURE", "EXECUTION_OUTCOME_FEEDBACK"} else (research_artifact_evidence or doctrine_artifact_evidence)))[:10],
                related_strategy_ids=_unique(related_strategy_ids)[:6],
                resolution_guidance=resolution_guidance,
            )
        )

    caution_items = [item for item in queue.items if item.queue_kind != "OPPORTUNITY"]
    top_caution = caution_items[0] if caution_items else None
    downside = next((item for item in scenario_lab.scenarios if item.scenario_id == scenario_lab.highest_downside_scenario_id), None)
    top_graph = graph.nodes[0] if graph.nodes else None
    top_priority = priorities.items[0] if priorities.items else None
    lead_items = [item for item in cohorts.items if item.cohort_bucket == "LEAD"]
    pressured_items = [item for item in cohorts.items if item.cohort_bucket in {"PRESSURED", "RESEARCH_ONLY"}]
    execution_alerts = [
        item for item in (research_execution_memory_report.items if research_execution_memory_report is not None else [])
        if item.outcome_disposition in {"ESCALATED", "REFUTED"} or item.cohort_effect in {"DEMOTES", "WATCH"} or item.doctrine_effect in {"PRESSURES", "FREEZE_CANDIDATE"}
    ]

    if fusion.strategic_posture in DefensivePostures and (
        doctrine.freeze_recommended
        or (downside is not None and downside.transition_classification in {"HIGH_UNCERTAINTY", "STRUCTURAL_BREAK_CANDIDATE"})
        or pressured_items
    ):
        add_item(
            "consensus:defensive-stack",
            "POSTURE_CONSENSUS",
            "CONSENSUS",
            0.58 + 0.12 * float(doctrine.freeze_recommended) + 0.10 * min(len(pressured_items), 2),
            "Defensive consensus across posture, doctrine, and strategy cohorts",
            "Multiple strategic layers agree that the active stack should remain defensive until pressure is relieved.",
            [
                f"strategic_posture={fusion.strategic_posture}",
                f"freeze_recommended={doctrine.freeze_recommended}",
                *( [f"downside_transition={downside.transition_classification}"] if downside is not None else [] ),
                f"pressured_cohort_count={len(pressured_items)}",
            ],
            [item.strategy_id for item in pressured_items[:4]],
            doctrine.operator_actions[0] if doctrine.operator_actions else "Maintain defensive posture and investigate the highest-pressure clause before expanding risk.",
            doctrine_exact_support,
        )

    if fusion.strategic_posture in OpportunityPostures and lead_items and not doctrine.freeze_recommended and not thesis.weakening_thesis_ids:
        add_item(
            "consensus:opportunity-stack",
            "OPPORTUNITY_CONSENSUS",
            "CONSENSUS",
            0.52 + 0.18 * fusion.opportunity_score,
            "Opportunity consensus across posture, theses, and lead cohorts",
            "Supportive posture, intact theses, and lead cohorts are aligned enough to justify focused opportunity review.",
            [
                f"strategic_posture={fusion.strategic_posture}",
                f"opportunity_score={fusion.opportunity_score:.2f}",
                f"lead_cohort_count={len(lead_items)}",
                f"weakening_thesis_count={len(thesis.weakening_thesis_ids)}",
            ],
            [item.strategy_id for item in lead_items[:4]],
            queue.operator_actions[0] if queue.operator_actions else "Validate the lead opportunity queue items before increasing confidence.",
            max(doctrine_exact_support, research_exact_support),
        )

    if fusion.strategic_posture in OpportunityPostures and (
        doctrine.freeze_recommended
        or (top_caution is not None and top_caution.priority_score >= max(0.62, fusion.opportunity_score))
        or (downside is not None and (downside.caution_delta >= 0.18 or downside.transition_classification == "STRUCTURAL_BREAK_CANDIDATE"))
    ):
        add_item(
            "tension:posture-vs-risk-stack",
            "POSTURE_VS_RISK_STACK",
            "SEVERE_TENSION" if doctrine.freeze_recommended or (downside is not None and downside.transition_classification == "STRUCTURAL_BREAK_CANDIDATE") else "TENSION",
            0.62 + 0.16 * float(doctrine.freeze_recommended) + 0.10 * ((downside.caution_delta if downside is not None else 0.0)),
            "Opportunity posture conflicts with hidden downside pressure",
            "The baseline posture still leans opportunity-biased, but doctrine, queue, or scenario analysis implies stronger downside pressure than the headline posture suggests.",
            [
                f"strategic_posture={fusion.strategic_posture}",
                *( [f"top_caution={top_caution.title}:score={top_caution.priority_score:.2f}"] if top_caution is not None else [] ),
                *( [f"downside_scenario={downside.scenario_id}:{downside.transition_classification}:caution_delta={downside.caution_delta:+.2f}"] if downside is not None else [] ),
                f"freeze_recommended={doctrine.freeze_recommended}",
            ],
            [item.strategy_id for item in lead_items[:4]],
            doctrine.operator_actions[0] if doctrine.operator_actions else "Resolve doctrine and downside tensions before treating the current stack as broad opportunity.",
            doctrine_exact_support,
        )

    fragile_leads = [item for item in lead_items if item.scenario_downside_floor <= 0.45 or item.thesis_pressure_score >= 0.58 or item.transition_sensitivity_score >= 0.55]
    if fragile_leads:
        add_item(
            "tension:lead-cohort-fragility",
            "LEAD_COHORT_FRAGILITY",
            "SEVERE_TENSION" if any(item.scenario_downside_floor <= 0.32 for item in fragile_leads) else "TENSION",
            max(0.56, max((1.0 - item.scenario_downside_floor) * 0.55 + item.thesis_pressure_score * 0.25 + item.transition_sensitivity_score * 0.20 for item in fragile_leads)),
            "Lead cohort ranking conflicts with downside resilience",
            "One or more lead strategies still rank highly even though their downside floor, thesis pressure, or transition sensitivity suggests fragility.",
            [
                f"{item.strategy_id}:floor={item.scenario_downside_floor:.2f}:thesis_pressure={item.thesis_pressure_score:.2f}:transition_sensitivity={item.transition_sensitivity_score:.2f}"
                for item in fragile_leads[:6]
            ],
            [item.strategy_id for item in fragile_leads[:6]],
            "Demote or revalidate fragile lead cohorts before treating them as structurally resilient.",
            research_exact_support,
        )

    if top_graph is not None and top_graph.cascade_risk_score >= 0.72 and fusion.strategic_posture in OpportunityPostures:
        add_item(
            "tension:hidden-cascade-fragility",
            "GRAPH_CASCADE_VS_POSTURE",
            "TENSION",
            0.50 + 0.36 * top_graph.cascade_risk_score,
            "Dependency-cascade fragility conflicts with headline posture",
            "The thesis graph shows elevated cascade risk even though the baseline posture still looks supportive enough to tempt overconfidence.",
            [
                f"highest_cascade_node={top_graph.node_id}",
                f"cascade_risk_score={top_graph.cascade_risk_score:.2f}",
                f"strategic_posture={fusion.strategic_posture}",
            ],
            lead_items[0:1] and [lead_items[0].strategy_id] or [],
            graph.operator_actions[0] if graph.operator_actions else "Reduce conviction around the highest cascade-risk node before broadening confidence.",
            max(doctrine_exact_support, research_exact_support),
        )

    if top_priority is not None and top_priority.priority_kind in {"DOCTRINE_REVIEW", "THESIS_REVIEW"} and fusion.strategic_posture == "OPPORTUNITY_BIASED":
        add_item(
            "tension:research-priority-vs-posture",
            "RESEARCH_PRIORITY_VS_POSTURE",
            "TENSION",
            0.46 + 0.42 * top_priority.urgency_score,
            "Highest research priority contradicts the headline opportunity posture",
            "The most urgent investigation is not expansionary; it is trying to resolve doctrine or thesis instability that still sits under the current posture.",
            [
                f"highest_priority={top_priority.priority_id}",
                f"priority_kind={top_priority.priority_kind}",
                f"urgency={top_priority.urgency_score:.2f}",
                f"strategic_posture={fusion.strategic_posture}",
            ],
            top_priority.related_strategy_ids[:4],
            top_priority.recommended_investigation if research_exact_support < 0.85 else f"{top_priority.recommended_investigation.rstrip('.')} Exact sealed support exists for the research/doctrine subject, so prioritize direct resolution over blanket caution.",
            research_exact_support,
        )

    if execution_alerts:
        affected_strategies = _unique([strategy_id for item in execution_alerts for strategy_id in item.related_strategy_ids])
        add_item(
            "tension:execution-feedback",
            "EXECUTION_OUTCOME_FEEDBACK",
            "SEVERE_TENSION" if any(item.outcome_disposition == "ESCALATED" for item in execution_alerts) else "TENSION",
            max(0.58, max(0.46 + max(item.urgency_impact, 0.0) * 0.20 + max(-item.confidence_impact, 0.0) * 0.20 for item in execution_alerts)),
            "Executed investigations disagree with prior strategic confidence",
            "Recent investigation outcomes escalated or refuted assumptions that were still carrying strategic weight elsewhere in the stack.",
            [
                f"{item.priority_id}:{item.outcome_disposition or item.execution_state}:confidence_impact={item.confidence_impact:+.2f}:urgency_impact={item.urgency_impact:+.2f}"
                for item in execution_alerts[:6]
            ],
            affected_strategies[:6],
            research_execution_memory_report.operator_actions[0] if research_execution_memory_report and research_execution_memory_report.operator_actions else "Feed the latest investigation outcomes back into theses, cohorts, and doctrine before treating prior rankings as current.",
            research_exact_support,
        )

    items = _sort_items(items)
    tension_item_ids = [item.tension_id for item in items if item.alignment_state != "CONSENSUS"]
    consensus_item_ids = [item.tension_id for item in items if item.alignment_state == "CONSENSUS"]
    highest_tension = next((item for item in items if item.alignment_state != "CONSENSUS"), None)
    avg_tension = (sum(item.severity_score for item in items if item.alignment_state != "CONSENSUS") / max(1, len(tension_item_ids))) if tension_item_ids else 0.0
    avg_consensus = (sum(item.severity_score for item in items if item.alignment_state == "CONSENSUS") / max(1, len(consensus_item_ids))) if consensus_item_ids else 0.0
    consensus_strength = _clamp(0.50 + 0.30 * avg_consensus - 0.28 * avg_tension + 0.04 * len(consensus_item_ids) - 0.03 * len(tension_item_ids))

    operator_actions = []
    if highest_tension is not None:
        operator_actions.append(highest_tension.resolution_guidance)
    if doctrine.freeze_recommended:
        operator_actions.append("Do not let supportive headline posture override a current doctrine freeze recommendation.")
    if fragile_leads:
        operator_actions.append("Re-rank fragile lead cohorts against downside floors before promoting them as robust opportunities.")
    if execution_alerts:
        operator_actions.append("Treat recent investigation outcomes as first-class feedback, not as side notes outside the strategic stack.")
    if not operator_actions and items:
        operator_actions.append(items[0].resolution_guidance)
    if not items:
        operator_actions.append("No major contradictions surfaced; maintain monitoring cadence and refresh the strategic stack on the next cycle.")
    operator_actions = _unique(operator_actions)[:6]

    if not items:
        summary_line = f"Strategic tension engine for {payload.universe_label}: no major contradiction or consensus tension dominated the current stack."
    else:
        summary_line = (
            f"Strategic tension engine for {payload.universe_label}: {len(tension_item_ids)} contradiction(s) and {len(consensus_item_ids)} consensus signal(s); "
            f"highest-severity focus is {highest_tension.title.lower() if highest_tension is not None else 'none'} with consensus strength {consensus_strength:.2f}; exact_evidence_support={exact_evidence_support_score:.2f}."
        )

    return OracleStrategicTensionReport(
        generated_at_utc=issued_at,
        universe_label=payload.universe_label,
        oracle_run_id=oracle_run_id,
        input_timestamp_utc=input_timestamp_utc,
        dominant_regime=fusion.dominant_regime,
        strategic_posture=fusion.strategic_posture,
        preferred_strategic_backing_source=preferred_backing_source,
        preferred_strategic_backing_classification=preferred_backing_classification,
        exact_evidence_support_score=round(exact_evidence_support_score, 6),
        summary_line=summary_line,
        consensus_strength_score=round(consensus_strength, 6),
        highest_severity_tension_id=(highest_tension.tension_id if highest_tension is not None else None),
        tension_item_ids=tension_item_ids,
        consensus_item_ids=consensus_item_ids,
        items=items,
        operator_actions=operator_actions,
    )


def render_oracle_strategic_tension_markdown(report: OracleStrategicTensionReport) -> str:
    item_blocks: list[str] = []
    for item in report.items[:10]:
        evidence_lines = "\n".join(f"- {entry}" for entry in item.evidence) or "- none"
        strategies = ", ".join(item.related_strategy_ids) if item.related_strategy_ids else "none"
        item_blocks.append(
            "\n".join([
                f"## {item.title}",
                "",
                f"- Tension ID: {item.tension_id}",
                f"- Kind: {item.tension_kind}",
                f"- Alignment state: {item.alignment_state}",
                f"- Exact evidence support: {item.exact_evidence_support_score:.2f}",
                f"- Severity score: {item.severity_score:.2f}",
                f"- Related strategies: {strategies}",
                f"- Summary: {item.summary_line}",
                "",
                "### Evidence",
                "",
                evidence_lines,
                "",
                "### Resolution guidance",
                "",
                f"- {item.resolution_guidance}",
            ])
        )
    item_block = "\n\n".join(item_blocks) if item_blocks else "No major contradiction or consensus items were emitted."
    action_lines = "\n".join(f"- {item}" for item in report.operator_actions) or "- none"
    tension_lines = "\n".join(f"- {item}" for item in report.tension_item_ids) or "- none"
    consensus_lines = "\n".join(f"- {item}" for item in report.consensus_item_ids) or "- none"
    return f"""# ORACLE STRATEGIC TENSION REPORT

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Universe: {report.universe_label}
- Dominant regime: {report.dominant_regime}
- Strategic posture: {report.strategic_posture}
- Preferred strategic backing source: {report.preferred_strategic_backing_source or 'none'}
- Preferred strategic backing classification: {report.preferred_strategic_backing_classification or 'none'}
- Exact evidence support score: {report.exact_evidence_support_score:.2f}
- Consensus strength score: {report.consensus_strength_score:.2f}
- Highest severity tension: {report.highest_severity_tension_id or 'none'}

## Summary

{report.summary_line}

## Contradiction items

{tension_lines}

## Consensus items

{consensus_lines}

{item_block}

## Recommended operator actions

{action_lines}
"""


def load_strategic_tension_report(path: Path) -> OracleStrategicTensionReport:
    return OracleStrategicTensionReport.model_validate(json.loads(path.read_text(encoding="utf-8")))
