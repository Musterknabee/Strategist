from __future__ import annotations

from datetime import datetime
from pathlib import Path

from strategy_validator.contracts.oracle import (
    OracleAdvisoryInput,
    OracleDoctrineAdaptationReport,
    OracleOpportunityQueueItem,
    OracleOpportunityQueueReport,
    OracleRegimeTransitionSignalReport,
    OracleResearchPriorityReport,
    OracleStrategicFusionReport,
    StrategyHealthPosteriorReport,
)
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.strategy_health_posterior import build_strategy_health_posterior_report
from strategy_validator.validator.oracle_run_identity import assert_matching_strategic_epoch
from strategy_validator.validator.oracle_history_integrity import (
    history_integrity_status,
    integrity_operator_action,
    queue_operator_friction,
    sealed_history_observation_count,
    unsealed_history_excluded_count,
)
from strategy_validator.contracts.oracle import OracleStrategicMemoryHorizonReport
from strategy_validator.validator.oracle_strategic_artifact_evidence import (
    discover_preferred_strategic_artifact_evidence,
    preferred_artifact_evidence_fact,
    strategic_artifact_evidence_support_score,
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


def _sort_items(items: list[OracleOpportunityQueueItem]) -> list[OracleOpportunityQueueItem]:
    return sorted(items, key=lambda item: (-item.priority_score, item.queue_kind, item.title))


def build_oracle_opportunity_queue_report(
    payload: OracleAdvisoryInput,
    fusion_report: OracleStrategicFusionReport | None = None,
    posterior_report: StrategyHealthPosteriorReport | None = None,
    transition_report: OracleRegimeTransitionSignalReport | None = None,
    strategic_memory_horizon_report: OracleStrategicMemoryHorizonReport | None = None,
    doctrine_adaptation_report: OracleDoctrineAdaptationReport | None = None,
    research_priority_report: OracleResearchPriorityReport | None = None,
    doctrine_adaptation_report_path: Path | None = None,
    research_priority_report_path: Path | None = None,
    repo_root: Path | None = None,
    search_root: Path | None = None,
    now_utc: datetime | None = None,
) -> OracleOpportunityQueueReport:
    issued_at = now_utc or _utc_now()
    fusion = fusion_report or build_oracle_strategic_fusion_report(payload, now_utc=issued_at)
    posterior = posterior_report or build_strategy_health_posterior_report(payload, fusion, now_utc=issued_at)
    oracle_run_id, input_timestamp_utc, _ = assert_matching_strategic_epoch(fusion, posterior, transition_report, doctrine_adaptation_report, research_priority_report)
    integrity_status = history_integrity_status(strategic_memory_horizon_report)
    integrity_friction = queue_operator_friction(strategic_memory_horizon_report)
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

    def _queue_priority(base_score: float, queue_kind: str, evidence_support: float) -> float:
        if queue_kind == "OPPORTUNITY":
            adjusted = base_score - integrity_friction + 0.22 * evidence_support
        elif queue_kind == "CAUTION":
            adjusted = base_score + 0.45 * integrity_friction + 0.08 * doctrine_exact_support
        else:
            adjusted = base_score + 0.65 * integrity_friction + 0.06 * max(doctrine_exact_support, research_exact_support)
        return round(_clamp(adjusted), 6)

    def _queue_evidence(entries: list[str], queue_kind: str, evidence_support: float) -> list[str]:
        extras = [
            f"history_integrity={integrity_status}",
            f"integrity_friction={integrity_friction:.2f}",
            f"exact_evidence_support={evidence_support:.2f}",
        ]
        if queue_kind == "OPPORTUNITY" and integrity_status != "SEALED_HISTORY":
            extras.append("opportunity ranking is intentionally damped until historical drift is sealed")
        if queue_kind != "OPPORTUNITY" and integrity_status != "SEALED_HISTORY":
            extras.append("caution/review ranking is slightly elevated because weak history should not accelerate expansion")
        if queue_kind == "OPPORTUNITY":
            extras.extend(preferred_artifact_evidence_fact("queue_support", research_artifact_evidence or doctrine_artifact_evidence))
        elif queue_kind == "CAUTION":
            extras.extend(preferred_artifact_evidence_fact("queue_support", doctrine_artifact_evidence))
        else:
            extras.extend(preferred_artifact_evidence_fact("queue_support", research_artifact_evidence or doctrine_artifact_evidence))
        return _unique(entries + extras)

    def _queue_action(action: str, queue_kind: str, evidence_support: float) -> str:
        if queue_kind == "OPPORTUNITY" and integrity_status != "SEALED_HISTORY" and evidence_support < 0.85:
            action = f"{action.rstrip('.')} Only advance beyond canary scale after sealing prior strategic stack history."
        elif queue_kind == "OPPORTUNITY" and evidence_support >= 0.85:
            action = f"{action.rstrip('.')} Exact sealed support exists for the supporting strategist subject, so this queue can advance while broader historical sealing catches up."
        elif queue_kind != "OPPORTUNITY" and integrity_status != "SEALED_HISTORY" and evidence_support < 0.85:
            action = f"{action.rstrip('.')} Treat this review as higher priority until historical drift is sealed and replayable."
        return f"{action.rstrip('.')}" + cadence_recommendation_suffix(exact_cadence_signal_classification=exact_cadence_signal_classification, exact_evidence_support_score=evidence_support)

    items: list[OracleOpportunityQueueItem] = []

    if fusion.opportunity_score >= 0.35 or fusion.strategic_posture in {"OPPORTUNITY_BIASED", "BALANCED_OBSERVATION"}:
        items.append(
            OracleOpportunityQueueItem(
                queue_id=f"opportunity:regime:{fusion.dominant_regime.lower()}",
                queue_kind="OPPORTUNITY",
                priority_score=_queue_priority(fusion.opportunity_score, "OPPORTUNITY", max(research_exact_support, doctrine_exact_support)),
                exact_feedback_confirmation_count=exact_feedback_confirmation_count,
                exact_feedback_relief_count=exact_feedback_relief_count,
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                operator_friction_score=round(max(0.0, integrity_friction - 0.18 * max(research_exact_support, doctrine_exact_support)), 6),
                exact_evidence_support_score=round(max(research_exact_support, doctrine_exact_support), 6),
                title=f"Validate {fusion.dominant_regime.lower()} opportunity cluster",
                summary_line=f"Current fusion stack suggests opportunity-biased research under {fusion.dominant_regime} with score {fusion.opportunity_score:.2f}.",
                evidence=_queue_evidence(fusion.opportunity_factors + [f"regime_confidence={fusion.regime_confidence:.2f}", f"strategic_posture={fusion.strategic_posture}"], "OPPORTUNITY", max(research_exact_support, doctrine_exact_support)),
                operator_action=_queue_action("Prioritize canary-sized research validation on the most aligned strategy cohort.", "OPPORTUNITY", max(research_exact_support, doctrine_exact_support)),
            )
        )

    if fusion.caution_score >= 0.35 or fusion.strategic_posture in {"CAUTION_BIASED", "DEFENSIVE_RESEARCH", "RESEARCH_FREEZE"}:
        items.append(
            OracleOpportunityQueueItem(
                queue_id="caution:fusion-stack",
                queue_kind="CAUTION",
                priority_score=_queue_priority(max(fusion.caution_score, fusion.doctrine_stress_score), "CAUTION", doctrine_exact_support),
                exact_feedback_confirmation_count=exact_feedback_confirmation_count,
                exact_feedback_relief_count=exact_feedback_relief_count,
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                operator_friction_score=round(max(0.0, integrity_friction - 0.08 * doctrine_exact_support), 6),
                exact_evidence_support_score=round(doctrine_exact_support, 6),
                title="Resolve fused caution pressure before expansion",
                summary_line=f"Fused caution pressure is elevated at {fusion.caution_score:.2f} with doctrine stress {fusion.doctrine_stress_score:.2f}.",
                evidence=_queue_evidence(fusion.caution_factors + fusion.doctrine_pressure_points + [f"epistemic_status={fusion.epistemic_status}"], "CAUTION", doctrine_exact_support),
                operator_action=_queue_action("Validate whether caution drivers are transient before broadening strategy-selection confidence.", "CAUTION", doctrine_exact_support),
            )
        )

    for state in posterior.strategies:
        if state.posterior_edge_confidence >= 0.55 and state.confidence_delta >= 0.01:
            items.append(
                OracleOpportunityQueueItem(
                    queue_id=f"opportunity:strategy:{state.strategy_id}",
                    queue_kind="OPPORTUNITY",
                    priority_score=_queue_priority(0.55 * state.posterior_edge_confidence + 0.45 * max(state.confidence_delta, 0.0), "OPPORTUNITY", research_exact_support),
                    exact_feedback_confirmation_count=exact_feedback_confirmation_count,
                exact_feedback_relief_count=exact_feedback_relief_count,
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                operator_friction_score=round(max(0.0, integrity_friction - 0.18 * research_exact_support), 6),
                    exact_evidence_support_score=round(research_exact_support, 6),
                    title=f"{state.strategy_id} is showing recovery evidence",
                    strategy_id=state.strategy_id,
                    summary_line=f"Posterior confidence for {state.strategy_id} improved to {state.posterior_edge_confidence:.2f} with {state.regime_fit.lower()} regime fit.",
                    evidence=_queue_evidence(state.reasons[:5], "OPPORTUNITY", research_exact_support),
                    operator_action=_queue_action("Review the recovery evidence and confirm it persists across the next fused window.", "OPPORTUNITY", research_exact_support),
                )
            )
        if state.recommended_action in {"CANARY", "HIBERNATE"}:
            kind = "CAUTION" if state.recommended_action == "CANARY" else "RESEARCH_REVIEW"
            items.append(
                OracleOpportunityQueueItem(
                    queue_id=f"caution:strategy:{state.strategy_id}",
                    queue_kind=kind,
                    priority_score=_queue_priority(max(state.degradation_score, 1.0 - state.posterior_edge_confidence), kind, doctrine_exact_support),
                    exact_feedback_confirmation_count=exact_feedback_confirmation_count,
                exact_feedback_relief_count=exact_feedback_relief_count,
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                operator_friction_score=round(max(0.0, integrity_friction - 0.08 * doctrine_exact_support), 6),
                    exact_evidence_support_score=round(doctrine_exact_support, 6),
                    title=f"{state.strategy_id} needs {state.recommended_action.lower()} handling",
                    strategy_id=state.strategy_id,
                    summary_line=f"{state.strategy_id} is flagged for {state.recommended_action.lower()} with posterior {state.posterior_edge_confidence:.2f}.",
                    evidence=_queue_evidence(state.reasons[:5], kind, doctrine_exact_support),
                    operator_action=_queue_action((
                        "Reduce confidence in this strategy until new evidence resolves the degradation cluster."
                        if state.recommended_action == "HIBERNATE"
                        else "Keep this strategy in canary-style review until posterior stability improves."
                    ), kind, doctrine_exact_support),
                )
            )

    if transition_report is not None and transition_report.transition_classification in {"TRANSITIONING", "HIGH_UNCERTAINTY", "STRUCTURAL_BREAK_CANDIDATE"}:
        items.append(
            OracleOpportunityQueueItem(
                queue_id=f"transition:{transition_report.transition_classification.lower()}",
                queue_kind="RESEARCH_REVIEW",
                priority_score=_queue_priority(0.65 + max(transition_report.confidence_delta, 0.0), "RESEARCH_REVIEW", max(doctrine_exact_support, research_exact_support)),
                exact_feedback_confirmation_count=exact_feedback_confirmation_count,
                exact_feedback_relief_count=exact_feedback_relief_count,
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                operator_friction_score=round(max(0.0, integrity_friction - 0.08 * max(doctrine_exact_support, research_exact_support)), 6),
                exact_evidence_support_score=round(max(doctrine_exact_support, research_exact_support), 6),
                title=f"{transition_report.transition_classification.replace('_', ' ').title()} review",
                summary_line=transition_report.summary_line,
                evidence=_queue_evidence(transition_report.drivers[:6], "RESEARCH_REVIEW", max(doctrine_exact_support, research_exact_support)),
                operator_action=_queue_action(transition_report.operator_actions[1] if len(transition_report.operator_actions) > 1 else transition_report.operator_actions[0], "RESEARCH_REVIEW", max(doctrine_exact_support, research_exact_support)),
            )
        )

    if not items:
        items.append(
            OracleOpportunityQueueItem(
                queue_id="opportunity:observation-balance",
                queue_kind="OPPORTUNITY" if fusion.opportunity_score >= fusion.caution_score else "RESEARCH_REVIEW",
                priority_score=_queue_priority(max(fusion.opportunity_score, fusion.caution_score, 0.35), "OPPORTUNITY" if fusion.opportunity_score >= fusion.caution_score else "RESEARCH_REVIEW"),
                exact_feedback_confirmation_count=exact_feedback_confirmation_count,
                exact_feedback_relief_count=exact_feedback_relief_count,
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                operator_friction_score=round(integrity_friction, 6),
                title="Maintain observation queue coverage",
                summary_line=f"The current stack is quiet but still worth monitoring under {fusion.strategic_posture}.",
                evidence=_queue_evidence([
                    f"opportunity_score={fusion.opportunity_score:.2f}",
                    f"caution_score={fusion.caution_score:.2f}",
                    f"dominant_regime={fusion.dominant_regime}",
                ], "OPPORTUNITY" if fusion.opportunity_score >= fusion.caution_score else "RESEARCH_REVIEW"),
                operator_action=_queue_action("Keep one lightweight research queue item open so strategic drift is noticed early rather than after conditions worsen.", "OPPORTUNITY" if fusion.opportunity_score >= fusion.caution_score else "RESEARCH_REVIEW"),
            )
        )

    items = _sort_items(items)
    operator_actions = _unique([cadence_operator_action(exact_cadence_signal_classification=exact_cadence_signal_classification, exact_feedback_confirmation_count=exact_feedback_confirmation_count, exact_feedback_relief_count=exact_feedback_relief_count)] + [item.operator_action for item in items] + fusion.operator_actions + posterior.operator_actions + [integrity_operator_action(strategic_memory_horizon_report)])[:8]
    summary_line = (
        f"Strategic queue contains {sum(item.queue_kind == 'OPPORTUNITY' for item in items)} opportunity items, "
        f"{sum(item.queue_kind == 'CAUTION' for item in items)} caution items, and "
        f"{sum(item.queue_kind == 'RESEARCH_REVIEW' for item in items)} research-review items; "
        f"history_integrity={integrity_status.lower()}, cadence={exact_cadence_signal_classification}, exact_confirmations={exact_feedback_confirmation_count}, exact_relief={exact_feedback_relief_count}, and integrity_friction={integrity_friction:.2f}."
    )
    return OracleOpportunityQueueReport(
        generated_at_utc=issued_at,
        universe_label=payload.universe_label,
        oracle_run_id=oracle_run_id,
        input_timestamp_utc=input_timestamp_utc,
        dominant_regime=fusion.dominant_regime,
        strategic_posture=fusion.strategic_posture,
        history_integrity_status=integrity_status,
        sealed_history_observation_count=sealed_history_observation_count(strategic_memory_horizon_report),
        unsealed_history_excluded_count=unsealed_history_excluded_count(strategic_memory_horizon_report),
        exact_feedback_confirmation_count=exact_feedback_confirmation_count,
        exact_feedback_relief_count=exact_feedback_relief_count,
        exact_cadence_signal_classification=exact_cadence_signal_classification,
        exact_evidence_support_score=round(exact_evidence_support_score, 6),
        integrity_operator_friction_score=round(max(0.0, integrity_friction - 0.08 * exact_evidence_support_score), 6),
        summary_line=summary_line,
        items=items,
        operator_actions=operator_actions,
    )


def render_oracle_opportunity_queue_markdown(report: OracleOpportunityQueueReport) -> str:
    blocks: list[str] = []
    for item in report.items:
        evidence = "\n".join(f"- {entry}" for entry in item.evidence) or "- none"
        blocks.append(
            f"## {item.title}\n\n"
            f"- Kind: {item.queue_kind}\n"
            f"- Priority score: {item.priority_score:.2f}\n"
            f"- Exact evidence support: {item.exact_evidence_support_score:.2f}\n"
            f"- Strategy: {item.strategy_id or 'n/a'}\n"
            f"- Summary: {item.summary_line}\n\n"
            f"### Evidence\n\n{evidence}\n\n"
            f"### Operator action\n\n- {item.operator_action}"
        )
    action_lines = "\n".join(f"- {item}" for item in report.operator_actions) or "- none"
    return f"""# ORACLE OPPORTUNITY QUEUE REPORT

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Universe: {report.universe_label}
- Dominant regime: {report.dominant_regime}
- Strategic posture: {report.strategic_posture}
- History integrity: {report.history_integrity_status}
- Exact cadence classification: {report.exact_cadence_signal_classification}
- Exact feedback confirmations: {report.exact_feedback_confirmation_count}
- Exact feedback relief: {report.exact_feedback_relief_count}
- Integrity operator friction: {report.integrity_operator_friction_score:.2f}

## Summary

{report.summary_line}

{"\n\n".join(blocks) if blocks else 'No active queue items were surfaced.'}

## Operator actions

{action_lines}
"""
