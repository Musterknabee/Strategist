from __future__ import annotations

from strategy_validator.validator.oracle_transition_common import (
    OracleMemoryLaneSummary,
    OracleMemoryReviewReport,
    OracleStateTransitionReport,
    OracleWeeklyDigestReport,
)


def render_oracle_state_transition_markdown(report: OracleStateTransitionReport) -> str:
    strategy_lines = "\n".join(
        f"- {item.strategy_id} [{item.strategy_type}] -> {item.previous_action} → {item.current_action} "
        f"(delta={item.posterior_delta:+.1%}; drift={item.drift_level}; {'; '.join(item.reasons)})"
        for item in report.strategy_transitions
    ) or "- No shared strategy advisories to compare."
    action_lines = "\n".join(f"- {item}" for item in report.operator_actions)
    introduced = ", ".join(report.introduced_strategy_ids) if report.introduced_strategy_ids else "none"
    removed = ", ".join(report.removed_strategy_ids) if report.removed_strategy_ids else "none"
    return f"""# ORACLE STATE TRANSITION REPORT

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Universe: {report.universe_label}
- Execution authority: {report.execution_authority}
- Previous evidence id: {report.previous_evidence_id}
- Current evidence id: {report.current_evidence_id}
- Comparison status: {report.comparison_status}
- Transition classification: {report.transition_classification}
- Drift score: {report.drift_score:.1%}

## Summary

{report.summary_line}

## Regime transition

- Previous dominant regime: {report.regime_transition.previous_dominant_regime} ({report.regime_transition.previous_dominant_probability:.1%})
- Current dominant regime: {report.regime_transition.current_dominant_regime} ({report.regime_transition.current_dominant_probability:.1%})
- Dominant changed: {report.regime_transition.dominant_changed}
- Drift level: {report.regime_transition.drift_level}
- Drivers: {', '.join(report.regime_transition.drivers) if report.regime_transition.drivers else 'none'}

## Global advisory shift

- Previous global action: {report.previous_recommended_global_action}
- Current global action: {report.current_recommended_global_action}
- Previous epistemic status: {report.previous_epistemic_status}
- Current epistemic status: {report.current_epistemic_status}

## Strategy transitions

{strategy_lines}

## Strategy set changes

- Introduced strategies: {introduced}
- Removed strategies: {removed}

## Operator actions

{action_lines}
"""


def render_oracle_memory_review_markdown(review: OracleMemoryReviewReport) -> str:
    triggers = "\n".join(f"- {item}" for item in review.triggers) or "- none"
    actions = "\n".join(f"- {item}" for item in review.operator_actions) or "- none"
    candidates = ", ".join(review.strategy_retrain_candidate_ids) if review.strategy_retrain_candidate_ids else "none"
    return f"""# ORACLE MEMORY REVIEW REPORT

- Generated at UTC: {review.generated_at_utc.isoformat()}
- Lane id: {review.lane_id}
- Window entry count: {review.window_entry_count}
- Window start sequence: {review.window_start_sequence_number if review.window_start_sequence_number is not None else 'n/a'}
- Window end sequence: {review.window_end_sequence_number if review.window_end_sequence_number is not None else 'n/a'}
- Latest transition classification: {review.latest_transition_classification or 'n/a'}
- Latest global action: {review.latest_global_action or 'n/a'}
- Latest epistemic status: {review.latest_epistemic_status or 'n/a'}
- Review classification: {review.review_classification}

## Summary

{review.summary_line}

## Trigger counts

- Evidence gaps: {review.evidence_gap_count}
- Epistemic escalations: {review.epistemic_escalation_count}
- Global action escalations: {review.global_action_escalation_count}
- Severe/material drift count: {review.severe_or_material_drift_count}
- Strategy retrain candidates: {candidates}

## Trigger interpretation

{triggers}

## Operator actions

{actions}
"""


def render_oracle_memory_lane_summary_markdown(summary: OracleMemoryLaneSummary) -> str:
    counts = "\n".join(f"- {key}: {value}" for key, value in sorted(summary.classification_counts.items())) or "- none"
    actions = "\n".join(f"- {item}" for item in summary.operator_actions) or "- none"
    return f"""# ORACLE MEMORY LANE SUMMARY

- Generated at UTC: {summary.generated_at_utc.isoformat()}
- Lane id: {summary.lane_id}
- Entry count: {summary.entry_count}
- First input timestamp UTC: {summary.first_input_timestamp_utc.isoformat() if summary.first_input_timestamp_utc else 'n/a'}
- Last input timestamp UTC: {summary.last_input_timestamp_utc.isoformat() if summary.last_input_timestamp_utc else 'n/a'}
- Latest transition classification: {summary.latest_transition_classification or 'n/a'}
- Latest global action: {summary.latest_global_action or 'n/a'}
- Latest epistemic status: {summary.latest_epistemic_status or 'n/a'}
- Severe/material drift count: {summary.severe_drift_count}
- Evidence gap count: {summary.evidence_gap_count}

## Summary

{summary.summary_line}

## Classification counts

{counts}

## Operator actions

{actions}
"""


def render_oracle_weekly_digest_markdown(digest: OracleWeeklyDigestReport) -> str:
    counts = "\n".join(f"- {key}: {value}" for key, value in sorted(digest.classification_counts.items())) or "- none"
    patterns = "\n".join(f"- {item}" for item in digest.recurring_patterns) or "- none"
    actions = "\n".join(f"- {item}" for item in digest.operator_actions) or "- none"
    return f"""# ORACLE WEEKLY DIGEST

- Generated at UTC: {digest.generated_at_utc.isoformat()}
- Lane id: {digest.lane_id}
- Window review count: {digest.window_review_count}
- Window start sequence: {digest.window_start_sequence_number if digest.window_start_sequence_number is not None else 'n/a'}
- Window end sequence: {digest.window_end_sequence_number if digest.window_end_sequence_number is not None else 'n/a'}
- Latest review classification: {digest.latest_review_classification or 'n/a'}
- Latest global action: {digest.latest_global_action or 'n/a'}
- Latest epistemic status: {digest.latest_epistemic_status or 'n/a'}
- Doctrine posture: {digest.doctrine_posture}
- Exact evidence support score: {digest.exact_evidence_support_score:.2f}
- Exact feedback confirmations: {digest.exact_feedback_confirmation_count}
- Exact feedback relief signals: {digest.exact_feedback_relief_count}

## Summary

{digest.summary_line}

## Classification counts

{counts}

## Recurring patterns

{patterns}

## Operator actions

{actions}
"""

