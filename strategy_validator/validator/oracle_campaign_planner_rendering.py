from __future__ import annotations

from strategy_validator.contracts.oracle_strategic_programs import OracleStrategicCampaignReport


def render_oracle_strategic_campaign_markdown(report: OracleStrategicCampaignReport) -> str:
    blocks = []
    for item in report.items:
        steps = "\n".join(
            f"- {step.step_kind}: {step.title} — {step.summary_line}"
            + (f" (depends_on={','.join(step.depends_on_step_ids)})" if step.depends_on_step_ids else "")
            for step in item.steps
        ) or "- none"
        evidence = "\n".join(f"- {entry}" for entry in item.evidence) or "- none"
        actions = "\n".join(f"- {entry}" for entry in [item.recommended_campaign]) or "- none"
        blocks.append(
            "\n".join(
                [
                    f"## {item.title}",
                    "",
                    f"- Objective kind: {item.objective_kind}",
                    f"- Priority score: {item.priority_score:.2f}",
                    f"- Exact cadence signal: {item.exact_cadence_signal_classification}",
                    f"- Exact feedback confirmation count: {item.exact_feedback_confirmation_count}",
                    f"- Exact feedback relief count: {item.exact_feedback_relief_count}",
                    f"- Exact evidence support: {item.exact_evidence_support_score:.2f}",
                    f"- Integrity penalty: {item.integrity_penalty_score:.2f}",
                    f"- Operator friction: {item.operator_friction_score:.2f}",
                    f"- Summary: {item.summary_line}",
                    "",
                    "### Evidence",
                    "",
                    evidence,
                    "",
                    "### Steps",
                    "",
                    steps,
                    "",
                    "### Recommended campaign",
                    "",
                    actions,
                ]
            )
        )
    operator_actions = "\n".join(f"- {entry}" for entry in report.operator_actions) or "- none"
    body = "\n\n".join(blocks)
    return f"""# ORACLE STRATEGIC CAMPAIGN REPORT

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Universe: {report.universe_label}
- Dominant regime: {report.dominant_regime}
- Strategic posture: {report.strategic_posture}
- Baseline conviction: {report.baseline_conviction_state} ({report.baseline_conviction_score:.2f})
- Baseline fragility: {report.baseline_fragility_score:.2f}
- History integrity: {report.history_integrity_status}
- Preferred strategic backing source: {report.preferred_strategic_backing_source or 'none'}
- Preferred strategic backing classification: {report.preferred_strategic_backing_classification or 'none'}
- Exact cadence signal: {report.exact_cadence_signal_classification}
- Exact feedback confirmation count: {report.exact_feedback_confirmation_count}
- Exact feedback relief count: {report.exact_feedback_relief_count}
- Exact evidence support: {report.exact_evidence_support_score:.2f}
- Integrity penalty: {report.integrity_penalty_score:.2f}
- Integrity friction: {report.integrity_operator_friction_score:.2f}

## Summary

{report.summary_line}

{body}

## Recommended operator actions

{operator_actions}
"""
