from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from pathlib import Path

from strategy_validator.contracts.oracle_core import OracleAdvisoryInput
from strategy_validator.contracts.oracle_strategic_memory import (
    OracleContradictionResolutionItem,
    OracleContradictionResolutionReport,
    OracleDoctrineAdaptationReport,
    OracleResearchExecutionMemoryReport,
    OracleResearchPriorityReport,
    OracleStrategicMemoryHorizonReport,
    OracleStrategicNarrativeReport,
    OracleStrategicTensionReport,
    OracleThesisGraphReport,
    OracleThesisMemoryReport,
)
from strategy_validator.contracts.oracle_strategic_programs import (
    OracleScenarioLabReport,
    OracleStrategyCohortReport,
)
from strategy_validator.contracts.oracle_strategic_fusion import (
    OracleStrategicFusionReport,
    StrategyHealthPosteriorReport,
)
from strategy_validator.validator.oracle_doctrine_adaptation import build_oracle_doctrine_adaptation_report
from strategy_validator.validator.oracle_research_planner import build_oracle_research_priority_report
from strategy_validator.validator.oracle_scenario_lab import build_oracle_scenario_lab_report
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report
from strategy_validator.validator.oracle_strategy_cohort import build_oracle_strategy_cohort_report
from strategy_validator.validator.oracle_strategic_memory_horizon import build_oracle_strategic_memory_horizon_report
from strategy_validator.validator.oracle_strategic_narrative import build_oracle_strategic_narrative_report
from strategy_validator.validator.oracle_strategic_tension import build_oracle_strategic_tension_report
from strategy_validator.validator.oracle_thesis_graph import build_oracle_thesis_graph_report
from strategy_validator.validator.oracle_thesis_memory import build_oracle_thesis_memory_report
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.oracle_strategic_artifact_evidence import (
    discover_preferred_strategic_artifact_evidence,
    preferred_artifact_evidence_fact,
    strategic_artifact_evidence_support_score,
)

from strategy_validator.validator.strategy_health_posterior import build_strategy_health_posterior_report
from strategy_validator.validator.oracle_run_identity import assert_matching_strategic_epoch
from strategy_validator.validator.oracle_history_integrity import (
    contradiction_penalty,
    history_integrity_status,
    integrity_fact,
    integrity_operator_action,
    sealed_history_observation_count,
    unsealed_history_excluded_count,
)
from strategy_validator.validator.oracle_cadence_feedback import summarize_exact_cadence_feedback, classify_exact_cadence_signal, cadence_operator_action, cadence_recommendation_suffix


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _unique(items: list[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if normalized and normalized not in output:
            output.append(normalized)
    return output


def _sort_items(items: list[OracleContradictionResolutionItem]) -> list[OracleContradictionResolutionItem]:
    return sorted(items, key=lambda item: (-item.resolution_priority_score, -item.expected_conviction_gain_score, item.resolution_kind, item.title))


def _resolution_kind(tension_kind: str) -> str:
    mapping = {
        "POSTURE_VS_RISK_STACK": "POSTURE_RISK_CONTRADICTION",
        "LEAD_COHORT_FRAGILITY": "COHORT_CONTRADICTION",
        "GRAPH_CASCADE_VS_POSTURE": "CASCADE_CONTRADICTION",
        "RESEARCH_PRIORITY_VS_POSTURE": "INVESTIGATION_CONTRADICTION",
        "EXECUTION_OUTCOME_FEEDBACK": "INVESTIGATION_CONTRADICTION",
        "POSTURE_CONSENSUS": "CONSENSUS_VALIDATION",
        "OPPORTUNITY_CONSENSUS": "CONSENSUS_VALIDATION",
    }
    return mapping.get(tension_kind, "DOCTRINE_CONTRADICTION")


def build_oracle_contradiction_resolution_report(
    payload: OracleAdvisoryInput,
    *,
    fusion_report: OracleStrategicFusionReport | None = None,
    posterior_report: StrategyHealthPosteriorReport | None = None,
    thesis_memory_report: OracleThesisMemoryReport | None = None,
    scenario_lab_report: OracleScenarioLabReport | None = None,
    strategy_cohort_report: OracleStrategyCohortReport | None = None,
    doctrine_adaptation_report: OracleDoctrineAdaptationReport | None = None,
    research_priority_report: OracleResearchPriorityReport | None = None,
    research_execution_memory_report: OracleResearchExecutionMemoryReport | None = None,
    thesis_graph_report: OracleThesisGraphReport | None = None,
    strategic_tension_report: OracleStrategicTensionReport | None = None,
    strategic_narrative_report: OracleStrategicNarrativeReport | None = None,
    strategic_memory_horizon_report: OracleStrategicMemoryHorizonReport | None = None,
    doctrine_adaptation_report_path: Path | None = None,
    research_priority_report_path: Path | None = None,
    repo_root: Path | None = None,
    search_root: Path | None = None,
    now_utc: datetime | None = None,
) -> OracleContradictionResolutionReport:
    issued_at = now_utc or _utc_now()
    fusion = fusion_report or build_oracle_strategic_fusion_report(payload, now_utc=issued_at)
    posterior = posterior_report or build_strategy_health_posterior_report(payload, fusion, now_utc=issued_at)
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
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        research_execution_memory_report=research_execution_memory_report,
        thesis_graph_report=thesis_graph,
        now_utc=issued_at,
    )
    narrative = strategic_narrative_report or build_oracle_strategic_narrative_report(
        payload,
        fusion_report=fusion,
        posterior_report=posterior,
        thesis_memory_report=thesis,
        scenario_lab_report=scenario_lab,
        strategy_cohort_report=cohorts,
        doctrine_adaptation_report=doctrine,
        research_priority_report=priorities,
        research_execution_memory_report=research_execution_memory_report,
        thesis_graph_report=thesis_graph,
        strategic_tension_report=tensions,
        now_utc=issued_at,
    )
    memory = strategic_memory_horizon_report or build_oracle_strategic_memory_horizon_report(
        narrative,
        history_reports=[],
        now_utc=issued_at,
    )

    top_graph = thesis_graph.nodes[0] if thesis_graph.nodes else None
    top_priority = priorities.items[0] if priorities.items else None
    top_doctrine = doctrine.items[0] if doctrine.items else None
    top_outcomes = [
        item
        for item in (research_execution_memory_report.items if research_execution_memory_report is not None else [])
        if item.outcome_disposition in {"ESCALATED", "REFUTED"}
        or item.doctrine_effect in {"PRESSURES", "FREEZE_CANDIDATE"}
        or item.cohort_effect in {"DEMOTES", "WATCH"}
    ]
    drift_bonus = {
        "REVERSING": 0.22,
        "VOLATILE": 0.16,
        "SOFTENING": 0.12,
        "STRENGTHENING": -0.04,
        "STABLE": 0.02,
        "FIRST_OBSERVATION": 0.05,
    }.get(memory.drift_state, 0.05)

    oracle_run_id, input_timestamp_utc, _ = assert_matching_strategic_epoch(fusion, posterior, thesis, scenario_lab, cohorts, doctrine, priorities, research_execution_memory_report, thesis_graph, tensions, narrative, memory)
    integrity_status = history_integrity_status(memory)
    integrity_penalty = contradiction_penalty(memory)
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
    cadence_summary = summarize_exact_cadence_feedback(repo_root=resolved_repo_root, search_root=resolved_search_root)
    exact_feedback_confirmation_count = cadence_summary.exact_feedback_confirmation_count
    exact_feedback_relief_count = cadence_summary.exact_feedback_relief_count
    exact_cadence_signal_classification = classify_exact_cadence_signal(
        exact_feedback_confirmation_count=exact_feedback_confirmation_count,
        exact_feedback_relief_count=exact_feedback_relief_count,
    )
    exact_evidence_support_score = round(max(doctrine_exact_support, research_exact_support), 6)
    items: list[OracleContradictionResolutionItem] = []

    def add_item(
        resolution_id: str,
        resolution_kind: str,
        title: str,
        summary_line: str,
        evidence: list[str],
        related_strategy_ids: list[str],
        recommended_resolution: str,
        severity: float,
        matching_priority_urgency: float,
        cascade_risk: float,
    ) -> None:
        evidence_support = round(
            research_exact_support if resolution_kind == "INVESTIGATION_CONTRADICTION" else (
                doctrine_exact_support if resolution_kind in {"DOCTRINE_CONTRADICTION", "CONSENSUS_VALIDATION"} else max(doctrine_exact_support, research_exact_support)
            ),
            6,
        )
        resolution_penalty = max(0.0, integrity_penalty + (0.05 if integrity_status != "SEALED_HISTORY" and resolution_kind == "CONSENSUS_VALIDATION" else 0.0) - 0.28 * evidence_support)
        expected_gain = _clamp(
            0.40 * severity
            + 0.26 * narrative.fragility_score
            + 0.18 * cascade_risk
            + 0.10 * matching_priority_urgency
            + 0.06 * max(drift_bonus, 0.0)
            - resolution_penalty
            + 0.12 * evidence_support
        )
        fragility_reduction = _clamp(
            0.46 * severity
            + 0.24 * narrative.fragility_score
            + 0.16 * float(doctrine.freeze_recommended)
            + 0.14 * max(drift_bonus, 0.0)
            - 0.70 * resolution_penalty
            + 0.08 * evidence_support
        )
        cascade_relief = _clamp(
            0.58 * cascade_risk
            + 0.18 * severity
            + 0.12 * min(len(related_strategy_ids), 3) / 3.0
            + 0.12 * min(len(thesis.weakening_thesis_ids), 3) / 3.0
        )
        resolution_priority = _clamp(
            0.34 * severity
            + 0.22 * expected_gain
            + 0.18 * fragility_reduction
            + 0.16 * cascade_relief
            + 0.10 * matching_priority_urgency
            - 0.85 * resolution_penalty
            + 0.14 * evidence_support
        )
        items.append(
            OracleContradictionResolutionItem(
                resolution_id=resolution_id,
                resolution_kind=resolution_kind,
                source_tension_id=(resolution_id.split(":", 1)[1] if resolution_id.startswith("resolve:") else None),
                exact_feedback_confirmation_count=exact_feedback_confirmation_count,
                exact_feedback_relief_count=exact_feedback_relief_count,
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                exact_evidence_support_score=round(evidence_support, 6),
                resolution_priority_score=round(resolution_priority, 6),
                expected_conviction_gain_score=round(expected_gain, 6),
                fragility_reduction_score=round(fragility_reduction, 6),
                cascade_relief_score=round(cascade_relief, 6),
                title=title,
                summary_line=summary_line,
                evidence=_unique(
                    evidence
                    + [integrity_fact(memory), f"integrity_penalty={resolution_penalty:.2f}", f"exact_evidence_support={evidence_support:.2f}"]
                    + (preferred_artifact_evidence_fact("contradiction_support", doctrine_artifact_evidence) if resolution_kind in {"DOCTRINE_CONTRADICTION", "CONSENSUS_VALIDATION"} else [])
                    + (preferred_artifact_evidence_fact("contradiction_support", research_artifact_evidence) if resolution_kind == "INVESTIGATION_CONTRADICTION" else [])
                )[:10],
                related_strategy_ids=_unique(related_strategy_ids)[:6],
                recommended_resolution=(
                    (
                        f"{recommended_resolution.rstrip('.')} Advance with the exact sealed supporting subject while broader strategic history continues sealing."
                        if evidence_support >= 0.85 and integrity_status != "SEALED_HISTORY"
                        else recommended_resolution.rstrip('.')
                    ) + cadence_recommendation_suffix(
                        exact_cadence_signal_classification=exact_cadence_signal_classification,
                        exact_evidence_support_score=evidence_support,
                    )
                ),
            )
        )

    tension_candidates = [item for item in tensions.items if item.alignment_state != "CONSENSUS"]
    if not tension_candidates and tensions.items:
        consensus = tensions.items[0]
        add_item(
            f"resolve:{consensus.tension_id}",
            _resolution_kind(consensus.tension_kind),
            f"Validate consensus integrity for {consensus.title.lower()}",
            "The stack is aligned, so the highest-leverage move is to validate that the apparent consensus is backed by durable evidence rather than stale alignment.",
            consensus.evidence + [f"conviction_state={narrative.conviction_state}", f"drift_state={memory.drift_state}"],
            consensus.related_strategy_ids,
            consensus.resolution_guidance,
            max(0.18, consensus.severity_score * 0.45),
            top_priority.urgency_score if top_priority is not None else 0.34,
            top_graph.cascade_risk_score if top_graph is not None else 0.24,
        )
    else:
        for tension in tension_candidates[:6]:
            matching_priority = next((item for item in priorities.items if set(item.related_strategy_ids) & set(tension.related_strategy_ids)), None)
            matching_cohorts = [item for item in cohorts.items if item.strategy_id in tension.related_strategy_ids]
            matching_outcome = next((item for item in top_outcomes if set(item.related_strategy_ids) & set(tension.related_strategy_ids)), None)
            cascade_risk = max(
                top_graph.cascade_risk_score if top_graph is not None else 0.0,
                max((item.queue_pressure_score for item in matching_cohorts), default=0.0) * 0.5,
            )
            summary_bits = [
                f"Resolving {tension.title.lower()} would likely raise conviction by ~{(0.22 + 0.55 * tension.severity_score):.2f} and reduce fragility driven by {memory.drift_state.lower().replace('_', ' ')} belief drift."
            ]
            if matching_priority is not None:
                summary_bits.append(f"It is reinforced by research priority {matching_priority.priority_id}.")
            if matching_outcome is not None:
                summary_bits.append(f"Recent investigation outcome {matching_outcome.execution_id} also points at the same contradiction chain.")
            recommendation = matching_priority.recommended_investigation if matching_priority is not None else tension.resolution_guidance
            if matching_outcome is not None and matching_outcome.next_action:
                next_action = matching_outcome.next_action
                next_action = next_action[0].lower() + next_action[1:] if len(next_action) > 1 else next_action.lower()
                recommendation = f"{recommendation} Then {next_action}"
            evidence = tension.evidence + [
                f"conviction_state={narrative.conviction_state}",
                f"fragility_score={narrative.fragility_score:.2f}",
                f"drift_state={memory.drift_state}",
                *([f"matching_priority={matching_priority.priority_id}:urgency={matching_priority.urgency_score:.2f}"] if matching_priority is not None else []),
                *([f"matching_outcome={matching_outcome.execution_id}:{matching_outcome.outcome_disposition}"] if matching_outcome is not None else []),
                *([f"top_cascade_node={top_graph.node_id}:risk={top_graph.cascade_risk_score:.2f}"] if top_graph is not None else []),
                *([f"top_doctrine_clause={top_doctrine.clause_id}:{top_doctrine.adaptation_state}"] if top_doctrine is not None else []),
            ]
            add_item(
                f"resolve:{tension.tension_id}",
                _resolution_kind(tension.tension_kind),
                f"Resolve {tension.title.lower()}",
                " ".join(summary_bits),
                evidence,
                tension.related_strategy_ids,
                recommendation,
                tension.severity_score,
                matching_priority.urgency_score if matching_priority is not None else (top_priority.urgency_score if top_priority is not None else 0.42),
                cascade_risk,
            )

    items = _sort_items(items)[:6]
    highest_priority_resolution_id = items[0].resolution_id if items else None
    operator_actions = _unique([cadence_operator_action(exact_cadence_signal_classification=exact_cadence_signal_classification, exact_feedback_confirmation_count=exact_feedback_confirmation_count, exact_feedback_relief_count=exact_feedback_relief_count), integrity_operator_action(memory)] + [item.recommended_resolution for item in items] + narrative.operator_actions + memory.operator_actions + tensions.operator_actions)[:8]
    summary_line = (
        f"Contradiction-resolution planner ranked {len(items)} contradiction chains for {payload.universe_label}; "
        f"top_resolution={highest_priority_resolution_id or 'none'}, conviction_state={narrative.conviction_state}, "
        f"drift_state={memory.drift_state}, history_integrity={integrity_status}, "
        f"cadence={exact_cadence_signal_classification}, exact_confirmations={exact_feedback_confirmation_count}, exact_relief={exact_feedback_relief_count}, "
        f"exact_evidence_support={exact_evidence_support_score:.2f}, highest_tension={tensions.highest_severity_tension_id or 'none'}."
    )
    return OracleContradictionResolutionReport(
        generated_at_utc=issued_at,
        universe_label=payload.universe_label,
        oracle_run_id=oracle_run_id,
        input_timestamp_utc=input_timestamp_utc,
        dominant_regime=fusion.dominant_regime,
        strategic_posture=fusion.strategic_posture,
        conviction_state=narrative.conviction_state,
        conviction_score=narrative.conviction_score,
        fragility_score=narrative.fragility_score,
        drift_state=memory.drift_state,
        history_integrity_status=integrity_status,
        sealed_history_observation_count=sealed_history_observation_count(memory),
        unsealed_history_excluded_count=unsealed_history_excluded_count(memory),
        exact_feedback_confirmation_count=exact_feedback_confirmation_count,
        exact_feedback_relief_count=exact_feedback_relief_count,
        exact_cadence_signal_classification=exact_cadence_signal_classification,
        exact_evidence_support_score=round(exact_evidence_support_score, 6),
        integrity_penalty_score=round(max(0.0, integrity_penalty - 0.22 * exact_evidence_support_score), 6),
        summary_line=summary_line,
        highest_priority_resolution_id=highest_priority_resolution_id,
        items=items,
        operator_actions=operator_actions,
    )


def render_oracle_contradiction_resolution_markdown(report: OracleContradictionResolutionReport) -> str:
    blocks: list[str] = []
    for item in report.items:
        evidence = "\n".join(f"- {entry}" for entry in item.evidence) or "- none"
        strategies = ", ".join(item.related_strategy_ids) if item.related_strategy_ids else "n/a"
        blocks.append(
            f"## {item.title}\n\n"
            f"- Resolution kind: {item.resolution_kind}\n"
            f"- Priority score: {item.resolution_priority_score:.2f}\n"
            f"- Exact evidence support: {item.exact_evidence_support_score:.2f}\n"
            f"- Expected conviction gain: {item.expected_conviction_gain_score:.2f}\n"
            f"- Fragility reduction: {item.fragility_reduction_score:.2f}\n"
            f"- Cascade relief: {item.cascade_relief_score:.2f}\n"
            f"- Related strategies: {strategies}\n"
            f"- Summary: {item.summary_line}\n\n"
            f"### Evidence\n\n{evidence}\n\n"
            f"### Recommended resolution\n\n- {item.recommended_resolution}"
        )
    action_lines = "\n".join(f"- {item}" for item in report.operator_actions) or "- none"
    body = "\n\n".join(blocks) if blocks else "No contradiction chains were surfaced."
    return (
        "# ORACLE CONTRADICTION RESOLUTION REPORT\n\n"
        f"- Generated at UTC: {report.generated_at_utc.isoformat()}\n"
        f"- Universe: {report.universe_label}\n"
        f"- Dominant regime: {report.dominant_regime}\n"
        f"- Strategic posture: {report.strategic_posture}\n"
        f"- Conviction state: {report.conviction_state}\n"
        f"- Conviction score: {report.conviction_score:.2f}\n"
        f"- Fragility score: {report.fragility_score:.2f}\n"
        f"- Drift state: {report.drift_state}\n"
        f"- Exact evidence support: {report.exact_evidence_support_score:.2f}\n\n"
        "## Summary\n\n"
        f"{report.summary_line}\n\n"
        f"{body}\n\n"
        "## Recommended operator actions\n\n"
        f"{action_lines}\n"
    )


def load_contradiction_resolution_report(path: Path) -> OracleContradictionResolutionReport:
    return OracleContradictionResolutionReport.model_validate(json.loads(path.read_text(encoding="utf-8")))
