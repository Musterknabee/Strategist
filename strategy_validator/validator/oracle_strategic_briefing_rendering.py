from __future__ import annotations

from strategy_validator.contracts.oracle import OracleStrategicBriefingReport


def render_oracle_strategic_briefing_markdown(report: OracleStrategicBriefingReport) -> str:
    blocks = []
    for section in report.sections:
        facts = "\n".join(f"- {item}" for item in section.facts) or "- none"
        actions = "\n".join(f"- {item}" for item in section.operator_actions) or "- none"
        provenance = "\n".join(f"- {item}" for item in section.provenance_refs) or "- none"
        blocks.append(
            f"## {section.title}\n\n"
            f"- Status: {section.status}\n"
            f"- Summary: {section.summary_line}\n"
            f"- Preferred strategic backing source: {section.preferred_strategic_backing_source or 'none'}\n"
            f"- Preferred strategic backing classification: {section.preferred_strategic_backing_classification or 'none'}\n"
            f"- Preferred strategic artifact evidence manifest: {section.preferred_strategic_artifact_evidence_manifest or 'none'}\n"
            f"- Preferred strategic artifact evidence kind: {section.preferred_strategic_artifact_evidence_kind or 'none'}\n"
            f"- Preferred strategic artifact evidence status: {section.preferred_strategic_artifact_evidence_status or 'none'}\n\n"
            f"### Facts\n\n{facts}\n\n"
            f"### Operator actions\n\n{actions}\n\n"
            f"### Provenance\n\n{provenance}"
        )
    action_lines = "\n".join(f"- {item}" for item in report.operator_actions) or "- none"
    return f"""# ORACLE STRATEGIC BRIEFING

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Universe: {report.universe_label}
- Dominant regime: {report.dominant_regime}
- Strategic posture: {report.strategic_posture}
- Transition classification: {report.transition_classification or 'N/A'}
- Preferred strategic backing source: {report.preferred_strategic_backing_source or 'none'}
- Preferred strategic backing classification: {report.preferred_strategic_backing_classification or 'none'}
- Exact cadence signal: {report.exact_cadence_signal_classification}
- Exact feedback confirmation count: {report.exact_feedback_confirmation_count}
- Exact feedback relief count: {report.exact_feedback_relief_count}
- Exact cadence signal: {report.exact_cadence_signal_classification}
- Exact feedback confirmation count: {report.exact_feedback_confirmation_count}
- Exact feedback relief count: {report.exact_feedback_relief_count}

## Summary

{report.summary_line}

{"\n\n".join(blocks)}

## Recommended operator actions

{action_lines}
"""
