from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from strategy_validator.contracts.oracle import (
    OracleAdvisoryInput,
    OracleDoctrineAdaptationReport,
    OracleOpportunityQueueReport,
    OracleRegimeTransitionSignalReport,
    OracleResearchPriorityItem,
    OracleResearchPriorityReport,
    OracleScenarioLabReport,
    OracleStrategicFusionReport,
    OracleStrategyCohortReport,
    OracleThesisMemoryReport,
    StrategyHealthPosteriorReport,
)
from strategy_validator.validator.oracle_doctrine_adaptation import build_oracle_doctrine_adaptation_report
from strategy_validator.validator.oracle_opportunity_queue import build_oracle_opportunity_queue_report
from strategy_validator.validator.oracle_regime_transition import compare_strategic_fusion_reports
from strategy_validator.validator.oracle_scenario_lab import build_oracle_scenario_lab_report
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report
from strategy_validator.validator.oracle_strategy_cohort import build_oracle_strategy_cohort_report
from strategy_validator.validator.oracle_thesis_memory import build_oracle_thesis_memory_report
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.strategy_health_posterior import build_strategy_health_posterior_report
from strategy_validator.validator.oracle_run_identity import assert_matching_strategic_epoch
from strategy_validator.validator.oracle_history_integrity import integrity_operator_action, preferred_strategic_backing_source, preferred_strategic_backing_classification
from strategy_validator.validator.oracle_strategic_artifact_evidence import discover_preferred_strategic_artifact_evidence, strategic_artifact_evidence_support_score, preferred_artifact_evidence_fact
from strategy_validator.validator.oracle_cadence_feedback import summarize_exact_cadence_feedback, classify_exact_cadence_signal, cadence_operator_action, cadence_recommendation_suffix
from strategy_validator.contracts.oracle import OracleStrategicMemoryHorizonReport


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _unique(items: list[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if normalized and normalized not in output:
            output.append(normalized)
    return output


def _sort_items(items: list[OracleResearchPriorityItem]) -> list[OracleResearchPriorityItem]:
    return sorted(items, key=lambda item: (-item.urgency_score, item.priority_kind, item.title))


def build_oracle_research_priority_report(
    payload: OracleAdvisoryInput,
    fusion_report: OracleStrategicFusionReport | None = None,
    posterior_report: StrategyHealthPosteriorReport | None = None,
    transition_report: OracleRegimeTransitionSignalReport | None = None,
    previous_fusion_report: OracleStrategicFusionReport | None = None,
    queue_report: OracleOpportunityQueueReport | None = None,
    thesis_memory_report: OracleThesisMemoryReport | None = None,
    scenario_lab_report: OracleScenarioLabReport | None = None,
    strategy_cohort_report: OracleStrategyCohortReport | None = None,
    doctrine_adaptation_report: OracleDoctrineAdaptationReport | None = None,
    strategic_memory_horizon_report: OracleStrategicMemoryHorizonReport | None = None,
    repo_root: Path | None = None,
    search_root: Path | None = None,
    doctrine_adaptation_report_path: Path | None = None,
    now_utc: datetime | None = None,
) -> OracleResearchPriorityReport:
    issued_at = now_utc or _utc_now()
    fusion = fusion_report or build_oracle_strategic_fusion_report(payload, now_utc=issued_at)
    posterior = posterior_report or build_strategy_health_posterior_report(payload, fusion, now_utc=issued_at)
    transition = transition_report
    if transition is None and previous_fusion_report is not None:
        transition = compare_strategic_fusion_reports(previous_fusion_report, fusion, now_utc=issued_at)
    queue = queue_report or build_oracle_opportunity_queue_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        strategic_memory_horizon_report=strategic_memory_horizon_report,
        now_utc=issued_at,
    )
    thesis = thesis_memory_report or build_oracle_thesis_memory_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
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
        transition_report=transition,
        queue_report=queue,
        thesis_memory_report=thesis,
        now_utc=issued_at,
    )
    doctrine = doctrine_adaptation_report or build_oracle_doctrine_adaptation_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        transition_report=transition,
        previous_fusion_report=previous_fusion_report,
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=cohorts,
        now_utc=issued_at,
    )

    oracle_run_id, input_timestamp_utc, _ = assert_matching_strategic_epoch(fusion, posterior, transition, queue, thesis, scenario_lab, cohorts, doctrine)
    integrity_status = getattr(queue, "history_integrity_status", "CURRENT_ONLY")
    resolved_repo_root = (repo_root or Path.cwd()).resolve()
    resolved_search_root = (search_root or resolved_repo_root / "docs" / "artifacts").resolve()
    doctrine_artifact_evidence = discover_preferred_strategic_artifact_evidence(report_path=Path(doctrine_adaptation_report_path), repo_root=resolved_repo_root, search_root=resolved_search_root) if doctrine_adaptation_report_path is not None and Path(doctrine_adaptation_report_path).exists() else None
    exact_evidence_support_score = strategic_artifact_evidence_support_score(doctrine_artifact_evidence)
    preferred_backing_source = preferred_strategic_backing_source(strategic_memory_horizon_report)
    preferred_backing_classification = preferred_strategic_backing_classification(strategic_memory_horizon_report)
    sealed_history_count = int(getattr(queue, "sealed_history_observation_count", 0) or 0)
    unsealed_history_count = int(getattr(queue, "unsealed_history_excluded_count", 0) or 0)
    cadence_summary = summarize_exact_cadence_feedback(repo_root=resolved_repo_root, search_root=resolved_search_root)
    exact_feedback_confirmation_count = cadence_summary.exact_feedback_confirmation_count
    exact_feedback_relief_count = cadence_summary.exact_feedback_relief_count
    exact_cadence_signal_classification = classify_exact_cadence_signal(
        exact_feedback_confirmation_count=exact_feedback_confirmation_count,
        exact_feedback_relief_count=exact_feedback_relief_count,
    )
    integrity_penalty = 0.0 if integrity_status == "SEALED_HISTORY" else 0.12 if integrity_status == "MIXED_HISTORY" else 0.18

    def _priority_penalty(kind: str) -> float:
        base_penalty = 0.0
        if integrity_status != "SEALED_HISTORY":
            if kind == "STRATEGY_VALIDATION":
                base_penalty = integrity_penalty
            elif kind == "DOCTRINE_REVIEW":
                base_penalty = round(integrity_penalty * 0.85, 6)
            elif kind == "THESIS_REVIEW":
                base_penalty = round(integrity_penalty * 0.45, 6)
        if base_penalty <= 0.0:
            return 0.0
        if kind in {"STRATEGY_VALIDATION", "DOCTRINE_REVIEW"}:
            return round(_clamp(max(0.0, base_penalty - (0.12 * exact_evidence_support_score))), 6)
        if kind == "THESIS_REVIEW":
            return round(_clamp(max(0.0, base_penalty - (0.06 * exact_evidence_support_score))), 6)
        return round(base_penalty, 6)

    def _adjust_urgency(base_score: float, kind: str) -> float:
        adjusted = base_score - _priority_penalty(kind)
        if kind in {"STRATEGY_VALIDATION", "DOCTRINE_REVIEW"}:
            adjusted += 0.10 * exact_evidence_support_score
        if exact_cadence_signal_classification == "EXACT_CONFIRMED_PRESSURE" and kind in {"STRATEGY_VALIDATION", "DOCTRINE_REVIEW"}:
            adjusted += 0.05
        elif exact_cadence_signal_classification == "EXACT_RELIEF_PRESSURE" and kind in {"STRATEGY_VALIDATION", "DOCTRINE_REVIEW"}:
            adjusted -= 0.03
        if integrity_status != "SEALED_HISTORY" and kind == "REGIME_INVESTIGATION":
            adjusted += 0.25 * integrity_penalty
        elif integrity_status != "SEALED_HISTORY" and kind == "SCENARIO_PROBE":
            adjusted += 0.10 * integrity_penalty
        return round(_clamp(adjusted), 6)

    def _priority_evidence(entries: list[str], kind: str) -> list[str]:
        extras = [
            f"history_integrity={integrity_status}",
            f"integrity_penalty={_priority_penalty(kind):.2f}",
        ] + preferred_artifact_evidence_fact("doctrine", doctrine_artifact_evidence)
        if _priority_penalty(kind) > 0:
            extras.append("ranking is intentionally constrained until prior strategic history is sealed and replayable")
        elif integrity_status != "SEALED_HISTORY" and kind in {"REGIME_INVESTIGATION", "SCENARIO_PROBE"}:
            extras.append("cautionary investigation is allowed to rise because weak history should slow expansion")
        return _unique(entries + extras)

    def _priority_action(action: str, kind: str) -> str:
        if _priority_penalty(kind) > 0 and exact_evidence_support_score >= 0.85 and kind in {"STRATEGY_VALIDATION", "DOCTRINE_REVIEW"}:
            action = f"{action.rstrip('.')} Advance with the exact sealed doctrine subject, but keep broader expansion constrained until more prior strategic history is sealed."
        elif _priority_penalty(kind) > 0:
            action = f"{action.rstrip('.')} Delay doctrine-changing or expansion-forward action until at least one prior strategic stack is sealed."
        elif integrity_status != "SEALED_HISTORY" and kind in {"REGIME_INVESTIGATION", "SCENARIO_PROBE"}:
            action = f"{action.rstrip('.')} Treat this as a higher-confidence next move than expansion while strategic history remains unsealed."
        return f"{action.rstrip('.')}" + cadence_recommendation_suffix(exact_cadence_signal_classification=exact_cadence_signal_classification, exact_evidence_support_score=exact_evidence_support_score)

    items: list[OracleResearchPriorityItem] = []

    if transition is not None and transition.transition_classification in {"TRANSITIONING", "HIGH_UNCERTAINTY", "STRUCTURAL_BREAK_CANDIDATE"}:
        urgency = _clamp(0.58 + max(transition.confidence_delta, 0.0) + (0.12 if transition.transition_classification == "STRUCTURAL_BREAK_CANDIDATE" else 0.0))
        items.append(
            OracleResearchPriorityItem(
                priority_id=f"regime:{transition.transition_classification.lower()}",
                priority_kind="REGIME_INVESTIGATION",
                exact_feedback_confirmation_count=exact_feedback_confirmation_count,
                exact_feedback_relief_count=exact_feedback_relief_count,
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                urgency_score=_adjust_urgency(urgency, "REGIME_INVESTIGATION"),
                exact_evidence_support_score=round(exact_evidence_support_score, 6),
                integrity_penalty_score=_priority_penalty("REGIME_INVESTIGATION"),
                title=f"Investigate {transition.transition_classification.replace('_', ' ').lower()} regime shift",
                summary_line=transition.summary_line,
                evidence=_priority_evidence(transition.drivers[:6], "REGIME_INVESTIGATION"),
                recommended_investigation=_priority_action((
                    transition.operator_actions[0]
                    if transition.operator_actions
                    else "Reconstruct the regime shift drivers before trusting current strategic posture."
                ), "REGIME_INVESTIGATION"),
            )
        )

    doctrine_candidates = [item for item in doctrine.items if item.adaptation_state in {"FREEZE", "ADAPT", "REVIEW"}] or doctrine.items[:1]
    for item in doctrine_candidates[:2]:
        items.append(
            OracleResearchPriorityItem(
                priority_id=f"doctrine:{item.clause_id}",
                priority_kind="DOCTRINE_REVIEW",
                exact_feedback_confirmation_count=exact_feedback_confirmation_count,
                exact_feedback_relief_count=exact_feedback_relief_count,
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                urgency_score=_adjust_urgency(0.48 * item.review_priority_score + 0.42 * item.stress_score + 0.10 * fusion.doctrine_stress_score, "DOCTRINE_REVIEW"),
                exact_evidence_support_score=round(exact_evidence_support_score, 6),
                integrity_penalty_score=_priority_penalty("DOCTRINE_REVIEW"),
                title=f"{item.adaptation_state.title()} doctrine clause {item.clause_label.lower()}",
                summary_line=item.summary_line,
                evidence=_priority_evidence(_unique(item.weakening_assumptions + item.pressure_sources)[:6], "DOCTRINE_REVIEW"),
                recommended_investigation=_priority_action(item.recommended_adaptation, "DOCTRINE_REVIEW"),
            )
        )

    thesis_candidates = [
        item for item in thesis.items
        if item.evolution_state in {"REVERSING", "WEAKENING"} or item.current_state in {"AT_RISK", "BROKEN"}
    ] or thesis.items[:1]
    for item in thesis_candidates[:2]:
        evidence = _unique(item.evidence_against[:3] + item.evidence_for[:1])
        urgency = 0.38 + (0.24 if item.evolution_state == "REVERSING" else 0.16 if item.evolution_state == "WEAKENING" else 0.0)
        urgency += 0.18 if item.current_state == "BROKEN" else 0.10 if item.current_state == "AT_RISK" else 0.0
        urgency += 0.15 * (1.0 - item.confidence_score)
        items.append(
            OracleResearchPriorityItem(
                priority_id=f"thesis:{item.thesis_id}",
                priority_kind="THESIS_REVIEW",
                exact_feedback_confirmation_count=exact_feedback_confirmation_count,
                exact_feedback_relief_count=exact_feedback_relief_count,
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                urgency_score=_adjust_urgency(urgency, "THESIS_REVIEW"),
                integrity_penalty_score=_priority_penalty("THESIS_REVIEW"),
                title=f"Review thesis {item.thesis_label.lower()}",
                summary_line=item.summary_line,
                related_strategy_ids=item.strategy_ids[:4],
                evidence=_priority_evidence(evidence[:6], "THESIS_REVIEW"),
                recommended_investigation=_priority_action(item.recommended_research_action, "THESIS_REVIEW"),
            )
        )

    downside = next((item for item in scenario_lab.scenarios if item.scenario_id == scenario_lab.highest_downside_scenario_id), None)
    if downside is not None:
        items.append(
            OracleResearchPriorityItem(
                priority_id=f"scenario:{downside.scenario_id}",
                priority_kind="SCENARIO_PROBE",
                exact_feedback_confirmation_count=exact_feedback_confirmation_count,
                exact_feedback_relief_count=exact_feedback_relief_count,
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                urgency_score=_adjust_urgency(0.42 + 0.33 * max(downside.caution_delta + downside.doctrine_stress_delta, 0.0) + 0.10 * max(-downside.average_posterior_delta, 0.0), "SCENARIO_PROBE"),
                exact_evidence_support_score=round(exact_evidence_support_score, 6),
                integrity_penalty_score=_priority_penalty("SCENARIO_PROBE"),
                title=f"Probe downside scenario {downside.title.lower()}",
                summary_line=downside.summary_line,
                evidence=_priority_evidence(_unique(downside.evidence + [f"leading_queue_kind={downside.leading_queue_kind or 'NONE'}"])[:6], "SCENARIO_PROBE"),
                recommended_investigation=_priority_action(downside.operator_action, "SCENARIO_PROBE"),
            )
        )

    cohort_candidates = [item for item in cohorts.items if item.cohort_bucket in {"PRESSURED", "RESEARCH_ONLY", "LEAD"}] or cohorts.items[:1]
    for item in cohort_candidates[:2]:
        title_prefix = "Validate" if item.cohort_bucket == "LEAD" else "Investigate"
        items.append(
            OracleResearchPriorityItem(
                priority_id=f"strategy:{item.strategy_id}",
                priority_kind="STRATEGY_VALIDATION",
                exact_feedback_confirmation_count=exact_feedback_confirmation_count,
                exact_feedback_relief_count=exact_feedback_relief_count,
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                urgency_score=_adjust_urgency(0.36 * (1.0 - item.scenario_downside_floor) + 0.24 * item.transition_sensitivity_score + 0.22 * item.queue_pressure_score + 0.18 * item.thesis_pressure_score, "STRATEGY_VALIDATION"),
                exact_evidence_support_score=round(exact_evidence_support_score, 6),
                integrity_penalty_score=_priority_penalty("STRATEGY_VALIDATION"),
                title=f"{title_prefix} strategy {item.strategy_id}",
                summary_line=item.summary_line,
                related_strategy_ids=[item.strategy_id],
                evidence=_priority_evidence(item.evidence[:6], "STRATEGY_VALIDATION"),
                recommended_investigation=_priority_action(item.operator_action, "STRATEGY_VALIDATION"),
            )
        )

    top_queue = queue.items[0] if queue.items else None
    if top_queue is not None and top_queue.strategy_id and all(top_queue.strategy_id not in item.related_strategy_ids for item in items):
        items.append(
            OracleResearchPriorityItem(
                priority_id=f"queue:{top_queue.queue_id}",
                priority_kind="STRATEGY_VALIDATION" if top_queue.queue_kind == "OPPORTUNITY" else "REGIME_INVESTIGATION",
                exact_feedback_confirmation_count=exact_feedback_confirmation_count,
                exact_feedback_relief_count=exact_feedback_relief_count,
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                urgency_score=_adjust_urgency(0.35 + 0.55 * top_queue.priority_score, "STRATEGY_VALIDATION" if top_queue.queue_kind == "OPPORTUNITY" else "REGIME_INVESTIGATION"),
                exact_evidence_support_score=round(exact_evidence_support_score, 6),
                integrity_penalty_score=_priority_penalty("STRATEGY_VALIDATION" if top_queue.queue_kind == "OPPORTUNITY" else "REGIME_INVESTIGATION"),
                title=f"Resolve queue priority {top_queue.title.lower()}",
                summary_line=top_queue.summary_line,
                related_strategy_ids=[top_queue.strategy_id],
                evidence=_priority_evidence(top_queue.evidence[:6], "STRATEGY_VALIDATION" if top_queue.queue_kind == "OPPORTUNITY" else "REGIME_INVESTIGATION"),
                recommended_investigation=_priority_action(top_queue.operator_action, "STRATEGY_VALIDATION" if top_queue.queue_kind == "OPPORTUNITY" else "REGIME_INVESTIGATION"),
            )
        )

    if not items:
        items.append(
            OracleResearchPriorityItem(
                priority_id="research:baseline-monitoring",
                priority_kind="REGIME_INVESTIGATION",
                exact_feedback_confirmation_count=exact_feedback_confirmation_count,
                exact_feedback_relief_count=exact_feedback_relief_count,
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                urgency_score=_adjust_urgency(max(fusion.caution_score, fusion.opportunity_score, 0.34), "REGIME_INVESTIGATION"),
                exact_evidence_support_score=round(exact_evidence_support_score, 6),
                integrity_penalty_score=_priority_penalty("REGIME_INVESTIGATION"),
                title="Maintain one baseline strategic investigation",
                summary_line="The current stack is relatively contained, but one live investigation should remain open so strategic drift is noticed early.",
                evidence=_priority_evidence(_unique([
                    f"dominant_regime={fusion.dominant_regime}",
                    f"strategic_posture={fusion.strategic_posture}",
                    f"avg_posterior={posterior.average_posterior_edge_confidence:.2f}",
                ]), "REGIME_INVESTIGATION"),
                recommended_investigation=_priority_action("Keep a lightweight regime and strategy validation probe active until a more directional edge or caution cluster forms.", "REGIME_INVESTIGATION"),
            )
        )

    items = _sort_items(items)[:8]
    operator_actions = _unique([cadence_operator_action(exact_cadence_signal_classification=exact_cadence_signal_classification, exact_feedback_confirmation_count=exact_feedback_confirmation_count, exact_feedback_relief_count=exact_feedback_relief_count)] + [item.recommended_investigation for item in items] + doctrine.operator_actions + scenario_lab.operator_actions + queue.operator_actions + [integrity_operator_action(strategic_memory_horizon_report)])[:8]
    highest_priority_id = items[0].priority_id if items else None
    summary_line = (
        f"Research planner ranked {len(items)} investigations for {payload.universe_label}; "
        f"top_priority={highest_priority_id or 'none'}, doctrine_freeze={'yes' if doctrine.freeze_recommended else 'no'}, "
        f"downside_scenario={scenario_lab.highest_downside_scenario_id or 'none'}, history_integrity={integrity_status.lower()}, "
        f"cadence={exact_cadence_signal_classification}, exact_confirmations={exact_feedback_confirmation_count}, exact_relief={exact_feedback_relief_count}, "
        f"exact_evidence_support={exact_evidence_support_score:.2f}, integrity_penalty={max((item.integrity_penalty_score for item in items), default=integrity_penalty):.2f}."
    )
    return OracleResearchPriorityReport(
        generated_at_utc=issued_at,
        universe_label=payload.universe_label,
        oracle_run_id=oracle_run_id,
        input_timestamp_utc=input_timestamp_utc,
        dominant_regime=fusion.dominant_regime,
        strategic_posture=fusion.strategic_posture,
        transition_classification=(transition.transition_classification if transition else None),
        history_integrity_status=integrity_status,
        sealed_history_observation_count=sealed_history_count,
        unsealed_history_excluded_count=unsealed_history_count,
        preferred_strategic_backing_source=preferred_backing_source,
        preferred_strategic_backing_classification=preferred_backing_classification,
        exact_feedback_confirmation_count=exact_feedback_confirmation_count,
        exact_feedback_relief_count=exact_feedback_relief_count,
        exact_cadence_signal_classification=exact_cadence_signal_classification,
        exact_evidence_support_score=round(exact_evidence_support_score, 6),
        integrity_penalty_score=round(max((item.integrity_penalty_score for item in items), default=integrity_penalty), 6),
        summary_line=summary_line,
        highest_priority_id=highest_priority_id,
        items=items,
        operator_actions=operator_actions,
    )


def render_oracle_research_priority_markdown(report: OracleResearchPriorityReport) -> str:
    blocks: list[str] = []
    for item in report.items:
        evidence = "\n".join(f"- {entry}" for entry in item.evidence) or "- none"
        strategies = ", ".join(item.related_strategy_ids) if item.related_strategy_ids else "n/a"
        blocks.append(
            f"## {item.title}\n\n"
            f"- Kind: {item.priority_kind}\n"
            f"- Urgency score: {item.urgency_score:.2f}\n"
            f"- Exact evidence support: {item.exact_evidence_support_score:.2f}\n"
            f"- Related strategies: {strategies}\n"
            f"- Summary: {item.summary_line}\n\n"
            f"### Evidence\n\n{evidence}\n\n"
            f"### Recommended investigation\n\n- {item.recommended_investigation}"
        )
    action_lines = "\n".join(f"- {item}" for item in report.operator_actions) or "- none"
    return f"""# ORACLE RESEARCH PRIORITY REPORT

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Universe: {report.universe_label}
- Dominant regime: {report.dominant_regime}
- Strategic posture: {report.strategic_posture}
- Transition classification: {report.transition_classification or 'N/A'}
- History integrity: {report.history_integrity_status}
- Preferred strategic backing source: {report.preferred_strategic_backing_source or 'none'}
- Preferred strategic backing classification: {report.preferred_strategic_backing_classification or 'none'}
- Exact cadence classification: {report.exact_cadence_signal_classification}
- Exact feedback confirmations: {report.exact_feedback_confirmation_count}
- Exact feedback relief: {report.exact_feedback_relief_count}
- Exact evidence support: {report.exact_evidence_support_score:.2f}
- Integrity penalty: {report.integrity_penalty_score:.2f}

## Summary

{report.summary_line}

{"\n\n".join(blocks) if blocks else 'No research priorities were surfaced.'}

## Operator actions

{action_lines}
"""


def load_research_priority_report(path: Path) -> OracleResearchPriorityReport:
    return OracleResearchPriorityReport.model_validate(json.loads(path.read_text(encoding="utf-8")))
