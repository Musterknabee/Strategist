from __future__ import annotations

from strategy_validator.validator.oracle_transition_common import (
    OracleAnnualReviewReport,
    OracleConstitutionalDigestReport,
    OracleDoctrineDriftReport,
    OracleMonthlyDigestReport,
    OracleQuarterlyReviewReport,
    OracleSemiannualAuditReport,
)


def render_oracle_doctrine_drift_markdown(report: OracleDoctrineDriftReport) -> str:
    actions = "\n".join(f"- {item}" for item in report.operator_actions) or "- none"
    return f"""# ORACLE DOCTRINE DRIFT REPORT

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Lane id: {report.lane_id}
- Previous digest id: {report.previous_digest_id}
- Current digest id: {report.current_digest_id}
- Comparison status: {report.comparison_status}
- Previous doctrine posture: {report.previous_doctrine_posture}
- Current doctrine posture: {report.current_doctrine_posture}
- Previous latest review classification: {report.previous_latest_review_classification or 'n/a'}
- Current latest review classification: {report.current_latest_review_classification or 'n/a'}
- Previous latest global action: {report.previous_latest_global_action or 'n/a'}
- Current latest global action: {report.current_latest_global_action or 'n/a'}
- Previous latest epistemic status: {report.previous_latest_epistemic_status or 'n/a'}
- Current latest epistemic status: {report.current_latest_epistemic_status or 'n/a'}
- Drift classification: {report.drift_classification}
- Drift level: {report.drift_level}
- Recurring pattern overlap count: {report.recurring_pattern_overlap_count}
- Recurring pattern shift count: {report.recurring_pattern_shift_count}

## Summary

{report.summary_line}

## Operator actions

{actions}
"""

_ORACLE_DOCTRINE_DRIFT_PAYLOAD_TYPE = "application/vnd.strategy-validator.oracle-doctrine-drift.v1+json"



def render_oracle_monthly_digest_markdown(digest: OracleMonthlyDigestReport) -> str:
    counts = "\n".join(f"- {key}: {value}" for key, value in sorted(digest.drift_classification_counts.items())) or "- none"
    patterns = "\n".join(f"- {item}" for item in digest.recurring_patterns) or "- none"
    actions = "\n".join(f"- {item}" for item in digest.operator_actions) or "- none"
    return f"""# ORACLE MONTHLY DIGEST

- Generated at UTC: {digest.generated_at_utc.isoformat()}
- Lane id: {digest.lane_id}
- Window entry count: {digest.window_entry_count}
- Window start sequence: {digest.window_start_sequence_number if digest.window_start_sequence_number is not None else 'n/a'}
- Window end sequence: {digest.window_end_sequence_number if digest.window_end_sequence_number is not None else 'n/a'}
- Latest drift classification: {digest.latest_drift_classification or 'n/a'}
- Latest current doctrine posture: {digest.latest_current_doctrine_posture or 'n/a'}
- Doctrine memory classification: {digest.doctrine_memory_classification}
- Exact evidence support score: {digest.exact_evidence_support_score:.2f}
- Exact feedback confirmations: {digest.exact_feedback_confirmation_count}
- Exact feedback relief signals: {digest.exact_feedback_relief_count}

## Summary

{digest.summary_line}

## Drift classification counts

{counts}

## Recurring patterns

{patterns}

## Operator actions

{actions}
"""


_ORACLE_MONTHLY_DIGEST_PAYLOAD_TYPE = "application/vnd.strategy-validator.oracle-monthly-digest.v1+json"



def render_oracle_quarterly_review_markdown(report: OracleQuarterlyReviewReport) -> str:
    counts = "\n".join(f"- {key}: {value}" for key, value in sorted(report.monthly_classification_counts.items())) or "- none"
    patterns = "\n".join(f"- {item}" for item in report.recurring_patterns) or "- none"
    actions = "\n".join(f"- {item}" for item in report.operator_actions) or "- none"
    return f"""# ORACLE QUARTERLY REVIEW

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Lane id: {report.lane_id}
- Window entry count: {report.window_entry_count}
- Window start sequence: {report.window_start_sequence_number if report.window_start_sequence_number is not None else 'n/a'}
- Window end sequence: {report.window_end_sequence_number if report.window_end_sequence_number is not None else 'n/a'}
- Latest monthly digest id: {report.latest_monthly_digest_id or 'n/a'}
- Latest doctrine memory classification: {report.latest_doctrine_memory_classification or 'n/a'}
- Latest drift classification: {report.latest_drift_classification or 'n/a'}
- Quarterly review classification: {report.quarterly_review_classification}
- Exact evidence support score: {report.exact_evidence_support_score:.2f}
- Exact feedback confirmations: {report.exact_feedback_confirmation_count}
- Exact feedback relief signals: {report.exact_feedback_relief_count}

## Summary

{report.summary_line}

## Monthly classification counts

{counts}

## Recurring patterns

{patterns}

## Operator actions

{actions}
"""


_ORACLE_QUARTERLY_REVIEW_PAYLOAD_TYPE = "application/vnd.strategy-validator.oracle-quarterly-review.v1+json"



def render_oracle_semiannual_audit_markdown(report: OracleSemiannualAuditReport) -> str:
    counts = "\n".join(f"- {key}: {value}" for key, value in sorted(report.quarterly_classification_counts.items())) or "- none"
    patterns = "\n".join(f"- {item}" for item in report.recurring_patterns) or "- none"
    actions = "\n".join(f"- {item}" for item in report.operator_actions) or "- none"
    return f"""# ORACLE SEMIANNUAL AUDIT

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Lane id: {report.lane_id}
- Window entry count: {report.window_entry_count}
- Window start sequence: {report.window_start_sequence_number if report.window_start_sequence_number is not None else 'n/a'}
- Window end sequence: {report.window_end_sequence_number if report.window_end_sequence_number is not None else 'n/a'}
- Latest quarterly review id: {report.latest_quarterly_review_id or 'n/a'}
- Latest quarterly review classification: {report.latest_quarterly_review_classification or 'n/a'}
- Semiannual audit classification: {report.semiannual_audit_classification}
- Exact evidence support score: {report.exact_evidence_support_score:.2f}
- Exact feedback confirmations: {report.exact_feedback_confirmation_count}
- Exact feedback relief signals: {report.exact_feedback_relief_count}
- Strategic backing classification: {report.strategic_backing_classification}
- Strategic stack evidence count: {report.strategic_stack_evidence_count}
- Strategic stack requirement met: {'yes' if report.strategic_stack_requirement_met else 'no'}

## Summary

{report.summary_line}

## Quarterly classification counts

{counts}

## Recurring patterns

{patterns}

## Operator actions

{actions}
"""


_ORACLE_SEMIANNUAL_AUDIT_PAYLOAD_TYPE = "application/vnd.strategy-validator.oracle-semiannual-audit.v1+json"



def render_oracle_annual_review_markdown(report: OracleAnnualReviewReport) -> str:
    counts = "\n".join(f"- {key}: {value}" for key, value in sorted(report.semiannual_classification_counts.items())) or "- none"
    patterns = "\n".join(f"- {item}" for item in report.recurring_patterns) or "- none"
    actions = "\n".join(f"- {item}" for item in report.operator_actions) or "- none"
    return f"""# ORACLE ANNUAL REVIEW

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Lane id: {report.lane_id}
- Window entry count: {report.window_entry_count}
- Window start sequence: {report.window_start_sequence_number if report.window_start_sequence_number is not None else 'n/a'}
- Window end sequence: {report.window_end_sequence_number if report.window_end_sequence_number is not None else 'n/a'}
- Latest semiannual audit id: {report.latest_semiannual_audit_id or 'n/a'}
- Latest semiannual audit classification: {report.latest_semiannual_audit_classification or 'n/a'}
- Annual review classification: {report.annual_review_classification}
- Exact evidence support score: {report.exact_evidence_support_score:.2f}
- Exact feedback confirmations: {report.exact_feedback_confirmation_count}
- Exact feedback relief signals: {report.exact_feedback_relief_count}
- Strategic backing classification: {report.strategic_backing_classification}
- Strategic stack evidence count: {report.strategic_stack_evidence_count}
- Strategic stack requirement met: {'yes' if report.strategic_stack_requirement_met else 'no'}

## Summary

{report.summary_line}

## Semiannual classification counts

{counts}

## Recurring patterns

{patterns}

## Operator actions

{actions}
"""



_ORACLE_ANNUAL_REVIEW_PAYLOAD_TYPE = "application/vnd.strategy-validator.oracle-annual-review.v1+json"



def render_oracle_constitutional_digest_markdown(report: OracleConstitutionalDigestReport) -> str:
    counts = "\n".join(f"- {key}: {value}" for key, value in sorted(report.annual_classification_counts.items())) or "- none"
    patterns = "\n".join(f"- {item}" for item in report.recurring_patterns) or "- none"
    actions = "\n".join(f"- {item}" for item in report.operator_actions) or "- none"
    return f"""# ORACLE CONSTITUTIONAL DIGEST

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Lane id: {report.lane_id}
- Window entry count: {report.window_entry_count}
- Window start sequence: {report.window_start_sequence_number if report.window_start_sequence_number is not None else 'n/a'}
- Window end sequence: {report.window_end_sequence_number if report.window_end_sequence_number is not None else 'n/a'}
- Latest annual review id: {report.latest_annual_review_id or 'n/a'}
- Latest annual review classification: {report.latest_annual_review_classification or 'n/a'}
- Constitutional digest classification: {report.constitutional_digest_classification}
- Strategic backing classification: {report.strategic_backing_classification}
- Exact evidence support score: {report.exact_evidence_support_score:.2f}
- Exact feedback confirmations: {report.exact_feedback_confirmation_count}
- Exact feedback relief signals: {report.exact_feedback_relief_count}
- Strategic stack evidence count: {report.strategic_stack_evidence_count}
- Strategic stack requirement met: {'yes' if report.strategic_stack_requirement_met else 'no'}

## Summary

{report.summary_line}

## Annual classification counts

{counts}

## Recurring patterns

{patterns}

## Operator actions

{actions}
"""

