from __future__ import annotations

from datetime import datetime
from pathlib import Path

from strategy_validator.contracts.oracle import (
    OracleAdvisoryInput,
    OracleStrategicFusionReport,
    StrategyHealthPosteriorReport,
    StrategyPosteriorState,
)
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.oracle_run_identity import assert_matching_strategic_epoch
from strategy_validator.validator.oracle_strategic_artifact_evidence import discover_preferred_strategic_artifact_evidence, preferred_artifact_evidence_fact, strategic_artifact_evidence_support_score


def _resolve_preferred_artifact_evidence(*artifact_evidences: dict[str, str] | None) -> dict[str, str] | None:
    candidates = [item for item in artifact_evidences if item is not None]
    if not candidates:
        return None
    return max(candidates, key=strategic_artifact_evidence_support_score)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def build_strategy_health_posterior_report(
    payload: OracleAdvisoryInput,
    fusion_report: OracleStrategicFusionReport,
    now_utc: datetime | None = None,
    doctrine_adaptation_report=None,
    research_priority_report=None,
    doctrine_adaptation_report_path: Path | None = None,
    research_priority_report_path: Path | None = None,
    repo_root: Path | None = None,
    search_root: Path | None = None,
) -> StrategyHealthPosteriorReport:
    issued_at = now_utc or _utc_now()
    oracle_run_id, input_timestamp_utc, _ = assert_matching_strategic_epoch(fusion_report)
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
    preferred_artifact_evidence = _resolve_preferred_artifact_evidence(doctrine_artifact_evidence, research_artifact_evidence)
    states: list[StrategyPosteriorState] = []
    degraded_ids: list[str] = []
    recovering_ids: list[str] = []

    for strategy in payload.strategies:
        sharpe_gap = strategy.realized_live_sharpe - strategy.cpcv_lower_bound
        regime_fit = "NEUTRAL"
        regime_penalty = 0.0
        if strategy.expected_regimes:
            if fusion_report.dominant_regime in strategy.expected_regimes:
                regime_fit = "ALIGNED"
            else:
                regime_fit = "MISMATCH"
                regime_penalty = 0.18

        strategy_support = 0.0
        if research_priority_report is not None and any(strategy.strategy_id in item.related_strategy_ids for item in getattr(research_priority_report, "items", [])):
            strategy_support = max(strategy_support, research_exact_support)
        if doctrine_adaptation_report is not None:
            strategy_support = max(strategy_support, doctrine_exact_support * 0.6)
        degradation = _clamp(
            max(-sharpe_gap, 0.0) * 0.22
            + strategy.drawdown_fraction * 0.90
            + max(0.50 - strategy.recent_win_rate, 0.0) * 0.70
            + regime_penalty
            + fusion_report.caution_score * 0.20
            + fusion_report.doctrine_stress_score * 0.18
            - 0.10 * strategy_support,
            0.0,
            1.0,
        )
        recovery = _clamp(
            max(sharpe_gap, 0.0) * 0.20
            + max(strategy.recent_win_rate - 0.50, 0.0) * 0.85
            + max(0.08 - strategy.drawdown_fraction, 0.0) * 0.90
            + (0.12 if regime_fit == "ALIGNED" else 0.0)
            + fusion_report.opportunity_score * 0.18
            + 0.10 * strategy_support,
            0.0,
            1.0,
        )
        posterior = _clamp(
            strategy.prior_edge_confidence
            + 0.30 * recovery
            - 0.34 * degradation,
            0.0,
            1.0,
        )
        delta = round(posterior - strategy.prior_edge_confidence, 6)
        reasons: list[str] = []
        if regime_fit == "MISMATCH":
            reasons.append(f"dominant_regime={fusion_report.dominant_regime} is outside expected_regimes={strategy.expected_regimes}")
        if sharpe_gap < 0:
            reasons.append(f"realized_live_sharpe trails cpcv_lower_bound by {abs(sharpe_gap):.2f}")
        elif sharpe_gap > 0:
            reasons.append(f"realized_live_sharpe exceeds cpcv_lower_bound by {sharpe_gap:.2f}")
        if strategy.drawdown_fraction >= 0.12:
            reasons.append(f"drawdown_fraction elevated at {strategy.drawdown_fraction:.1%}")
        if fusion_report.caution_score >= 0.60:
            reasons.append("fused caution pressure is materially elevated")
        if fusion_report.opportunity_score >= 0.60:
            reasons.append("fused opportunity pressure is supportive")
        reasons.extend(preferred_artifact_evidence_fact("posterior_support", doctrine_artifact_evidence if strategy_support == doctrine_exact_support * 0.6 and doctrine_exact_support > research_exact_support else research_artifact_evidence if strategy_support == research_exact_support and research_exact_support > 0 else preferred_artifact_evidence))

        action = "MAINTAIN"
        if posterior < 0.28 or degradation >= 0.72:
            action = "HIBERNATE"
            degraded_ids.append(strategy.strategy_id)
        elif posterior < 0.48 or degradation >= 0.48:
            action = "CANARY"
            degraded_ids.append(strategy.strategy_id)
        elif delta >= 0.08 and recovery >= 0.35:
            recovering_ids.append(strategy.strategy_id)

        states.append(
            StrategyPosteriorState(
                strategy_id=strategy.strategy_id,
                strategy_type=strategy.strategy_type,
                exact_evidence_support_score=round(strategy_support, 6),
                prior_edge_confidence=round(strategy.prior_edge_confidence, 6),
                posterior_edge_confidence=round(posterior, 6),
                confidence_delta=delta,
                degradation_score=round(degradation, 6),
                recovery_score=round(recovery, 6),
                regime_fit=regime_fit,
                recommended_action=action,
                reasons=reasons,
            )
        )

    avg_posterior = round(_mean([state.posterior_edge_confidence for state in states]), 6)
    operator_actions = [
        "Use posterior shifts to prioritize research attention, not execution authority.",
    ]
    if degraded_ids:
        operator_actions.append("Review degraded strategies for regime mismatch, drawdown clustering, and doctrine pressure before trusting recovery narratives.")
    if recovering_ids:
        operator_actions.append("Validate recovering strategies with fresh evidence before broadening research confidence.")

    return StrategyHealthPosteriorReport(
        generated_at_utc=issued_at,
        universe_label=payload.universe_label,
        oracle_run_id=oracle_run_id,
        input_timestamp_utc=input_timestamp_utc,
        dominant_regime=fusion_report.dominant_regime,
        strategic_posture=fusion_report.strategic_posture,
        preferred_strategic_backing_source=(preferred_artifact_evidence.get("manifest_path") if preferred_artifact_evidence is not None else None) and "strategic_artifact_evidence_manifest" or None,
        preferred_strategic_backing_classification=(preferred_artifact_evidence.get("preferred_strategic_backing_classification") if preferred_artifact_evidence is not None else None) or None,
        exact_evidence_support_score=exact_evidence_support_score,
        average_posterior_edge_confidence=avg_posterior,
        degraded_strategy_ids=degraded_ids,
        recovering_strategy_ids=recovering_ids,
        operator_actions=operator_actions,
        strategies=states,
        summary_line=(
            f"Average posterior edge confidence is {avg_posterior:.1%} under {fusion_report.strategic_posture}; "
            f"degraded={len(degraded_ids)} recovering={len(recovering_ids)}."
        ),
    )


def render_strategy_health_posterior_markdown(report: StrategyHealthPosteriorReport) -> str:
    strategy_lines = "\n".join(
        f"- {item.strategy_id} [{item.strategy_type}] -> {item.recommended_action} "
        f"(prior={item.prior_edge_confidence:.1%}; posterior={item.posterior_edge_confidence:.1%}; "
        f"delta={item.confidence_delta:+.1%}; regime_fit={item.regime_fit}; exact_support={item.exact_evidence_support_score:.2f})"
        for item in report.strategies
    ) or "- none"
    return f"""# STRATEGY HEALTH POSTERIOR REPORT

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Universe: {report.universe_label}
- Dominant regime: {report.dominant_regime}
- Strategic posture: {report.strategic_posture}
- Preferred strategic backing source: {report.preferred_strategic_backing_source or "none"}
- Preferred strategic backing classification: {report.preferred_strategic_backing_classification or "none"}

## Summary

{report.summary_line}

## Strategy states

{strategy_lines}

## Report trust

- exact_evidence_support_score={report.exact_evidence_support_score:.2f}

## Operator actions

{"\n".join(f"- {item}" for item in report.operator_actions) or '- none'}
"""
