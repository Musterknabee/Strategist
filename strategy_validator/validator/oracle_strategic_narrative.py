from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from strategy_validator.contracts.oracle_core import OracleAdvisoryInput
from strategy_validator.contracts.oracle_strategic_memory import (
    OracleDoctrineAdaptationReport,
    OracleResearchExecutionMemoryReport,
    OracleResearchPriorityReport,
    OracleStrategicNarrativeItem,
    OracleStrategicNarrativeReport,
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
from strategy_validator.validator.oracle_strategic_tension import build_oracle_strategic_tension_report
from strategy_validator.validator.oracle_thesis_graph import build_oracle_thesis_graph_report
from strategy_validator.validator.oracle_thesis_memory import build_oracle_thesis_memory_report
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.strategy_health_posterior import build_strategy_health_posterior_report
from strategy_validator.validator.oracle_run_identity import assert_matching_strategic_epoch
from strategy_validator.validator.oracle_strategic_artifact_evidence import discover_preferred_strategic_artifact_evidence, preferred_artifact_evidence_fact, strategic_artifact_evidence_support_score
from strategy_validator.validator.oracle_cadence_feedback import summarize_exact_cadence_feedback, classify_exact_cadence_signal


SupportivePostures = {"OPPORTUNITY_BIASED", "BALANCED_OBSERVATION"}
DefensivePostures = {"CAUTION_BIASED", "DEFENSIVE_RESEARCH", "RESEARCH_FREEZE"}


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _unique(items: list[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if normalized and normalized not in output:
            output.append(normalized)
    return output


def _conviction_state(conviction_score: float, fragility_score: float) -> str:
    if conviction_score >= 0.72 and fragility_score <= 0.35:
        return "HIGH_CONVICTION"
    if conviction_score >= 0.54 and fragility_score <= 0.58:
        return "GUARDED_CONVICTION"
    if conviction_score >= 0.32:
        return "FRAGILE_CONVICTION"
    return "BROKEN_CONVICTION"


def _sort_items(items: list[OracleStrategicNarrativeItem]) -> list[OracleStrategicNarrativeItem]:
    return sorted(items, key=lambda item: (-item.rank_score, item.driver_kind, item.title))


def build_oracle_strategic_narrative_report(
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
    strategic_tension_report: OracleStrategicTensionReport | None = None,
    doctrine_adaptation_report_path: Path | None = None,
    research_priority_report_path: Path | None = None,
    repo_root: Path | None = None,
    search_root: Path | None = None,
    now_utc: datetime | None = None,
) -> OracleStrategicNarrativeReport:
    issued_at = now_utc or _utc_now()
    fusion = fusion_report or build_oracle_strategic_fusion_report(payload, now_utc=issued_at)
    posterior = posterior_report or build_strategy_health_posterior_report(payload, fusion, now_utc=issued_at)
    queue = queue_report or build_oracle_opportunity_queue_report(payload, fusion_report=fusion, posterior_report=posterior, now_utc=issued_at)
    thesis = thesis_memory_report or build_oracle_thesis_memory_report(payload, fusion_report=fusion, posterior_report=posterior, execution_memory_report=research_execution_memory_report, now_utc=issued_at)
    scenario_lab = scenario_lab_report or build_oracle_scenario_lab_report(payload, baseline_fusion_report=fusion, now_utc=issued_at)
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
    thesis_graph = thesis_graph_report or build_oracle_thesis_graph_report(
        payload,
        fusion_report=fusion,
        thesis_memory_report=thesis,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        research_execution_memory_report=research_execution_memory_report,
        now_utc=issued_at,
    )
    tensions = strategic_tension_report or build_oracle_strategic_tension_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        queue_report=queue,
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        research_execution_memory_report=research_execution_memory_report,
        thesis_graph_report=thesis_graph,
        now_utc=issued_at,
    )

    downside = next((item for item in scenario_lab.scenarios if item.scenario_id == scenario_lab.highest_downside_scenario_id), None)
    upside = next((item for item in scenario_lab.scenarios if item.scenario_id == scenario_lab.highest_upside_scenario_id), None)
    top_tension = next((item for item in tensions.items if item.alignment_state != "CONSENSUS"), tensions.items[0] if tensions.items else None)
    top_graph = thesis_graph.nodes[0] if thesis_graph.nodes else None
    lead = cohorts.items[0] if cohorts.items else None
    top_priority = priorities.items[0] if priorities.items else None
    top_queue = queue.items[0] if queue.items else None
    execution_alerts = [
        item for item in (research_execution_memory_report.items if research_execution_memory_report is not None else [])
        if item.outcome_disposition in {"REFUTED", "ESCALATED"} or item.doctrine_effect in {"PRESSURES", "FREEZE_CANDIDATE"} or item.cohort_effect in {"DEMOTES", "WATCH"}
    ]

    resolved_repo_root = repo_root.resolve() if repo_root is not None else None
    resolved_search_root = search_root.resolve() if search_root is not None else resolved_repo_root
    doctrine_artifact_evidence = discover_preferred_strategic_artifact_evidence(
        report_path=Path(doctrine_adaptation_report_path),
        repo_root=resolved_repo_root,
        search_root=resolved_search_root,
    ) if doctrine_adaptation_report_path is not None and Path(doctrine_adaptation_report_path).exists() and resolved_repo_root is not None else None
    cadence = summarize_exact_cadence_feedback(repo_root=resolved_repo_root, search_root=resolved_search_root, window_size=6)
    exact_cadence_signal_classification = classify_exact_cadence_signal(
        exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
        exact_feedback_relief_count=cadence.exact_feedback_relief_count,
    )
    research_artifact_evidence = discover_preferred_strategic_artifact_evidence(
        report_path=Path(research_priority_report_path),
        repo_root=resolved_repo_root,
        search_root=resolved_search_root,
    ) if research_priority_report_path is not None and Path(research_priority_report_path).exists() and resolved_repo_root is not None else None
    doctrine_exact_support = strategic_artifact_evidence_support_score(doctrine_artifact_evidence)
    research_exact_support = strategic_artifact_evidence_support_score(research_artifact_evidence)
    exact_evidence_support_score = round(max(doctrine_exact_support, research_exact_support, cadence.exact_evidence_support_score), 6)

    conviction = (
        0.48
        + 0.25 * fusion.opportunity_score
        - 0.22 * fusion.caution_score
        - 0.16 * fusion.doctrine_stress_score
        + 0.10 * posterior.average_posterior_edge_confidence
        + (0.08 if fusion.strategic_posture in SupportivePostures else -0.08 if fusion.strategic_posture in DefensivePostures else 0.0)
        + (0.08 if lead is not None and lead.cohort_bucket == "LEAD" else -0.06 if lead is not None and lead.cohort_bucket in {"PRESSURED", "RESEARCH_ONLY"} else 0.0)
        - (0.16 if doctrine.freeze_recommended else 0.0)
        - (0.12 if top_tension is not None and top_tension.alignment_state == "SEVERE_TENSION" else 0.06 if top_tension is not None and top_tension.alignment_state == "TENSION" else 0.0)
        - 0.12 * min(len(thesis.weakening_thesis_ids), 3) / 3.0
        - 0.08 * len(execution_alerts[:2])
        + 0.10 * max(doctrine_exact_support, research_exact_support)
    )
    fragility = (
        0.28 * fusion.caution_score
        + 0.20 * fusion.doctrine_stress_score
        + 0.18 * (downside.caution_delta if downside is not None else 0.0)
        + 0.18 * (top_graph.cascade_risk_score if top_graph is not None else 0.0)
        + 0.16 * ((top_tension.severity_score if top_tension is not None else 0.0))
        + 0.10 * min(len(thesis.weakening_thesis_ids), 3) / 3.0
        + (0.08 if doctrine.freeze_recommended else 0.0)
        - 0.08 * max(doctrine_exact_support, research_exact_support)
    )
    conviction_score = round(_clamp(conviction), 6)
    fragility_score = round(_clamp(fragility), 6)
    conviction_state = _conviction_state(conviction_score, fragility_score)

    oracle_run_id, input_timestamp_utc, _ = assert_matching_strategic_epoch(fusion, posterior, queue, thesis, scenario_lab, cohorts, doctrine, priorities, research_execution_memory_report, thesis_graph, tensions)
    items: list[OracleStrategicNarrativeItem] = []

    def add_item(
        narrative_id: str,
        driver_kind: str,
        rank_score: float,
        title: str,
        summary_line: str,
        evidence: list[str],
        related_strategy_ids: list[str],
        trust_bias: str,
        operator_guidance: str,
        evidence_support: float = 0.0,
    ) -> None:
        items.append(
            OracleStrategicNarrativeItem(
                narrative_id=narrative_id,
                conviction_state=conviction_state,
                driver_kind=driver_kind,
                exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
                exact_feedback_relief_count=cadence.exact_feedback_relief_count,
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                exact_evidence_support_score=round(evidence_support, 6),
                rank_score=round(_clamp(rank_score + 0.08 * evidence_support), 6),
                title=title,
                summary_line=summary_line,
                evidence=_unique(evidence + preferred_artifact_evidence_fact("narrative_support", doctrine_artifact_evidence if driver_kind == "DOCTRINE_DRIVER" else research_artifact_evidence if driver_kind == "INVESTIGATION_DRIVER" else (research_artifact_evidence or doctrine_artifact_evidence if driver_kind in {"CONTRADICTION_DRIVER", "STRATEGY_DRIVER"} else None)) + [f"exact_cadence_signal_classification={exact_cadence_signal_classification}", f"exact_feedback_confirmation_count={cadence.exact_feedback_confirmation_count}", f"exact_feedback_relief_count={cadence.exact_feedback_relief_count}"])[:10],
                related_strategy_ids=_unique(related_strategy_ids)[:6],
                trust_bias=trust_bias,
                operator_guidance=operator_guidance,
            )
        )

    add_item(
        "narrative:regime-driver",
        "REGIME_DRIVER",
        max(0.45, 0.32 + fusion.regime_confidence * 0.42 + abs(fusion.opportunity_score - fusion.caution_score) * 0.18),
        f"{fusion.dominant_regime} is the headline driver of the current map",
        f"The dominant regime and fused posture are setting the main conviction tone, with {fusion.strategic_posture.lower()} carrying the current headline bias.",
        [
            f"dominant_regime={fusion.dominant_regime}",
            f"regime_confidence={fusion.regime_confidence:.2f}",
            f"strategic_posture={fusion.strategic_posture}",
            f"opportunity_score={fusion.opportunity_score:.2f}",
            f"caution_score={fusion.caution_score:.2f}",
        ],
        [item.strategy_id for item in cohorts.items[:3]],
        "TRUST_MORE" if conviction_state in {"HIGH_CONVICTION", "GUARDED_CONVICTION"} else "HOLD",
        queue.operator_actions[0] if queue.operator_actions else "Validate whether the headline regime still matches the most recent sensor mix before increasing conviction.",
        max(doctrine_exact_support, research_exact_support),
    )

    if top_tension is not None or (top_graph is not None and top_graph.cascade_risk_score >= 0.55):
        add_item(
            "narrative:contradiction-driver",
            "CONTRADICTION_DRIVER",
            max(
                0.52,
                (top_tension.severity_score if top_tension is not None else 0.0) * 0.62
                + (top_graph.cascade_risk_score if top_graph is not None else 0.0) * 0.28
                + (0.10 if doctrine.freeze_recommended else 0.0),
            ),
            "Contradiction pressure is shaping conviction more than the headline posture suggests",
            "The strongest tensions, cascade-risk nodes, or doctrine freeze pressure imply that confidence should be discounted until the contradiction chain is resolved.",
            _unique([
                *([f"top_tension={top_tension.tension_kind}:{top_tension.alignment_state}:severity={top_tension.severity_score:.2f}"] if top_tension is not None else []),
                *([f"top_cascade_node={top_graph.node_id}:risk={top_graph.cascade_risk_score:.2f}"] if top_graph is not None else []),
                f"freeze_recommended={doctrine.freeze_recommended}",
            ]),
            [item.strategy_id for item in cohorts.items if item.cohort_bucket in {"PRESSURED", "RESEARCH_ONLY"}][:4],
            "TRUST_LESS" if conviction_state in {"FRAGILE_CONVICTION", "BROKEN_CONVICTION"} else "HOLD",
            (top_tension.resolution_guidance if top_tension is not None else doctrine.operator_actions[0] if doctrine.operator_actions else "Resolve the highest contradiction before broadening strategic trust.") if max(doctrine_exact_support, research_exact_support) < 0.85 else "Exact sealed support exists for the underlying strategist subject, so resolve the contradiction chain directly instead of globally discounting conviction.",
            max(doctrine_exact_support, research_exact_support),
        )

    if lead is not None:
        add_item(
            "narrative:cohort-driver",
            "STRATEGY_DRIVER",
            max(0.42, lead.cohort_rank_score * 0.60 + lead.resilience_score * 0.25 + (1.0 - lead.thesis_pressure_score) * 0.15),
            f"{lead.strategy_id} is the current cohort anchor",
            f"The top cohort strategy is influencing the map through its resilience, downside floor, and transition sensitivity, which makes it the clearest current strategy-level anchor.",
            [
                f"strategy_id={lead.strategy_id}",
                f"cohort_bucket={lead.cohort_bucket}",
                f"rank_score={lead.cohort_rank_score:.2f}",
                f"resilience_score={lead.resilience_score:.2f}",
                f"scenario_downside_floor={lead.scenario_downside_floor:.2f}",
            ],
            [lead.strategy_id],
            "TRUST_MORE" if lead.cohort_bucket == "LEAD" and lead.scenario_downside_floor >= 0.50 else "HOLD" if lead.cohort_bucket == "WATCH" else "TRUST_LESS",
            lead.operator_action,
        )

    if downside is not None or upside is not None:
        key = downside if downside is not None and downside.caution_delta >= max((upside.opportunity_delta if upside is not None else 0.0), 0.0) else upside
        if key is not None:
            add_item(
                "narrative:scenario-driver",
                "SCENARIO_DRIVER",
                max(0.44, abs(key.caution_delta if downside is key else key.opportunity_delta) * 0.60 + abs(key.average_posterior_delta) * 0.25 + abs(key.doctrine_stress_delta) * 0.15),
                f"{key.scenario_id} is the strongest counterfactual driver",
                f"Scenario analysis shows that {key.scenario_id} would most materially shift posture, queue pressure, or confidence, making it the most informative future lens on the current map.",
                [
                    f"scenario_id={key.scenario_id}",
                    f"transition_classification={key.transition_classification}",
                    f"caution_delta={key.caution_delta:+.2f}",
                    f"opportunity_delta={key.opportunity_delta:+.2f}",
                    f"average_posterior_delta={key.average_posterior_delta:+.2f}",
                ],
                [item.strategy_id for item in cohorts.items[:4]],
                "TRUST_LESS" if key is downside and key.caution_delta > 0.12 else "TRUST_MORE" if key is upside and key.opportunity_delta > 0.10 else "HOLD",
                key.operator_action,
            )

    if doctrine.freeze_recommended or doctrine.items:
        clause = doctrine.items[0] if doctrine.items else None
        add_item(
            "narrative:doctrine-driver",
            "DOCTRINE_DRIVER",
            max(0.40, (clause.review_priority_score if clause is not None else 0.0) * 0.50 + fusion.doctrine_stress_score * 0.30 + (0.20 if doctrine.freeze_recommended else 0.0)),
            "Doctrine pressure is contributing directly to conviction sizing",
            "Clause-level doctrine stress is now materially shaping how much confidence the operator should place in the current strategic picture.",
            _unique([
                *([f"clause={clause.clause_id}:{clause.adaptation_state}:stress={clause.stress_score:.2f}"] if clause is not None else []),
                f"freeze_recommended={doctrine.freeze_recommended}",
                f"doctrine_stress_score={fusion.doctrine_stress_score:.2f}",
            ]),
            [],
            "TRUST_LESS" if doctrine.freeze_recommended else "HOLD",
            doctrine.operator_actions[0] if doctrine.operator_actions else "Review the highest-pressure doctrine clause before expanding confidence.",
        )

    if execution_alerts or top_priority is not None:
        anchor = execution_alerts[0] if execution_alerts else None
        add_item(
            "narrative:investigation-driver",
            "INVESTIGATION_DRIVER",
            max(0.38, (abs(anchor.confidence_impact) if anchor is not None else 0.0) * 0.40 + (anchor.urgency_impact if anchor is not None else 0.0) * 0.30 + (top_priority.urgency_score if top_priority is not None else 0.0) * 0.30),
            "Investigation feedback is actively rewriting conviction",
            "The ranked investigation plan and its latest completed outcomes are now changing the map enough to deserve explicit inclusion in the operator's conviction story.",
            _unique([
                *([f"execution={anchor.priority_id}:{anchor.outcome_disposition or anchor.execution_state}:confidence_impact={anchor.confidence_impact:+.2f}"] if anchor is not None else []),
                *([f"next_priority={top_priority.priority_kind}:{top_priority.title}:urgency={top_priority.urgency_score:.2f}"] if top_priority is not None else []),
            ]),
            _unique([
                *(anchor.related_strategy_ids if anchor is not None else []),
                *(top_priority.related_strategy_ids if top_priority is not None else []),
            ])[:4],
            "TRUST_LESS" if anchor is not None and anchor.confidence_impact < -0.12 else "HOLD",
            (anchor.next_action if anchor is not None else top_priority.recommended_investigation if top_priority is not None else "Record investigation outcomes so conviction changes stay replayable."),
        )

    items = _sort_items(items)
    top = items[0] if items else None
    summary_line = (
        f"Strategic conviction is {conviction_state.lower().replace('_', ' ')} at {conviction_score:.2f}, with fragility {fragility_score:.2f}; "
        f"the main driver is {top.title.lower() if top is not None else 'insufficient narrative evidence'}"
        f" and the strongest trust bias is {top.trust_bias.lower().replace('_', ' ') if top is not None else 'hold'}; "
        f"cadence={exact_cadence_signal_classification}, exact_confirm={cadence.exact_feedback_confirmation_count}, exact_relief={cadence.exact_feedback_relief_count}."
    )
    operator_actions = _unique([
        *(item.operator_guidance for item in items[:4]),
        *(tensions.operator_actions[:2]),
        *(priorities.operator_actions[:2]),
        *(queue.operator_actions[:2]),
    ])[:8]
    return OracleStrategicNarrativeReport(
        generated_at_utc=issued_at,
        universe_label=payload.universe_label,
        oracle_run_id=oracle_run_id,
        input_timestamp_utc=input_timestamp_utc,
        dominant_regime=fusion.dominant_regime,
        strategic_posture=fusion.strategic_posture,
        preferred_strategic_backing_source=getattr(doctrine, "preferred_strategic_backing_source", None) or getattr(priorities, "preferred_strategic_backing_source", None),
        preferred_strategic_backing_classification=getattr(doctrine, "preferred_strategic_backing_classification", None) or getattr(priorities, "preferred_strategic_backing_classification", None),
        exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
        exact_feedback_relief_count=cadence.exact_feedback_relief_count,
        exact_cadence_signal_classification=exact_cadence_signal_classification,
        exact_evidence_support_score=round(exact_evidence_support_score, 6),
        conviction_state=conviction_state,
        conviction_score=conviction_score,
        fragility_score=fragility_score,
        summary_line=summary_line,
        highest_ranked_narrative_id=(top.narrative_id if top is not None else None),
        items=items,
        operator_actions=operator_actions,
    )


def render_oracle_strategic_narrative_markdown(report: OracleStrategicNarrativeReport) -> str:
    lines = [
        "# ORACLE STRATEGIC NARRATIVE REPORT",
        "",
        f"- Generated at UTC: {report.generated_at_utc.isoformat()}",
        f"- Universe: {report.universe_label}",
        f"- Dominant regime: {report.dominant_regime}",
        f"- Strategic posture: {report.strategic_posture}",
        f"- Preferred strategic backing source: {report.preferred_strategic_backing_source or 'none'}",
        f"- Preferred strategic backing classification: {report.preferred_strategic_backing_classification or 'none'}",
        f"- Exact evidence support: {report.exact_evidence_support_score:.2f}",
        f"- Exact cadence signal: {report.exact_cadence_signal_classification}",
        f"- Exact feedback confirmation count: {report.exact_feedback_confirmation_count}",
        f"- Exact feedback relief count: {report.exact_feedback_relief_count}",
        f"- Conviction state: {report.conviction_state}",
        f"- Conviction score: {report.conviction_score:.2f}",
        f"- Fragility score: {report.fragility_score:.2f}",
        f"- Highest-ranked narrative: {report.highest_ranked_narrative_id or 'none'}",
        "",
        "## Summary",
        "",
        report.summary_line,
        "",
        "## Narrative Drivers",
        "",
    ]
    for item in report.items:
        lines.extend([
            f"### {item.title}",
            "",
            f"- Narrative ID: `{item.narrative_id}`",
            f"- Driver kind: `{item.driver_kind}`",
            f"- Conviction state: `{item.conviction_state}`",
            f"- Exact evidence support: `{item.exact_evidence_support_score:.2f}`",
            f"- Exact cadence signal: `{item.exact_cadence_signal_classification}`",
            f"- Rank score: `{item.rank_score:.2f}`",
            f"- Trust bias: `{item.trust_bias}`",
            f"- Summary: {item.summary_line}",
            "",
            "#### Evidence",
            "",
        ])
        lines.extend([f"- {evidence}" for evidence in item.evidence] or ["- none"])
        lines.extend([
            "",
            "#### Related strategies",
            "",
        ])
        lines.extend([f"- {strategy_id}" for strategy_id in item.related_strategy_ids] or ["- none"])
        lines.extend([
            "",
            "#### Operator guidance",
            "",
            f"- {item.operator_guidance}",
            "",
        ])
    lines.extend([
        "## Recommended operator actions",
        "",
    ])
    lines.extend([f"- {action}" for action in report.operator_actions] or ["- none"])
    lines.append("")
    return "\n".join(lines)


def load_strategic_narrative_report(path: Path) -> OracleStrategicNarrativeReport:
    return OracleStrategicNarrativeReport.model_validate(json.loads(path.read_text(encoding="utf-8")))
