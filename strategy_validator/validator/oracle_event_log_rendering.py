from __future__ import annotations

from strategy_validator.contracts.oracle_evidence_events import OracleDerivedViewReport, OracleEventCheckpointManifest


def render_oracle_rolling_review_markdown(report: OracleDerivedViewReport) -> str:
    lines = [
        "# ORACLE ROLLING REVIEW",
        "",
        "> Preferred converged review surface: derived directly from the canonical Oracle Event Log.",
        "",
        f"- Horizon: `{report.view_label}`",
        f"- Classification: `{report.derived_classification}`",
        f"- Event log: `{report.lane_id}`",
        f"- Window entries: `{report.window_entry_count}`",
        f"- Latest regime: `{report.latest_dominant_regime}`",
        f"- Latest global action: `{report.latest_global_action}`",
        f"- Latest epistemic status: `{report.latest_epistemic_status}`",
        f"- Average posterior confidence: `{report.average_posterior_edge_confidence:.3f}`",
        "",
        "## Operator actions",
    ]
    lines.extend(f"- {item}" for item in report.operator_actions)
    lines.extend([
        "",
        "## Summary",
        report.summary_line,
        "",
    ])
    return "\n".join(lines)


def render_oracle_derived_view_markdown(report: OracleDerivedViewReport) -> str:
    lines = [
        "# ORACLE DERIVED VIEW",
        "",
        "> Derived directly from the canonical Oracle Event Log.",
        "",
        f"- View label: `{report.view_label}`",
        f"- Classification: `{report.derived_classification}`",
        f"- Lane: `{report.lane_id}`",
        f"- Window entries: `{report.window_entry_count}`",
        f"- Latest regime: `{report.latest_dominant_regime}`",
        f"- Latest global action: `{report.latest_global_action}`",
        f"- Latest epistemic status: `{report.latest_epistemic_status}`",
        f"- Average posterior confidence: `{report.average_posterior_edge_confidence:.3f}`",
        f"- Evidence gaps: `{report.evidence_gap_count}`",
        f"- Defensive posture count: `{report.defensive_posture_count}`",
        f"- Retrain pressure count: `{report.retrain_pressure_count}`",
        "",
        "## Operator actions",
    ]
    lines.extend(f"- {item}" for item in report.operator_actions)
    lines.extend([
        "",
        "## Summary",
        report.summary_line,
        "",
    ])
    return "\n".join(lines)


def render_oracle_event_checkpoint_markdown(report: OracleEventCheckpointManifest) -> str:
    lines = [
        "# ORACLE EVENT CHECKPOINT",
        "",
        f"- Lane: `{report.lane_id}`",
        f"- View label: `{report.view_label}`",
        f"- Classification: `{report.derived_classification}`",
        f"- Window entries: `{report.window_entry_count}`",
        f"- Integrity status: `{report.integrity_status}`",
        f"- Last entry hash: `{report.last_entry_hash}`",
        "",
        "## Summary",
        report.summary_line,
        "",
    ]
    if report.missing_artifact_paths:
        lines.extend(["## Missing artifacts", *[f"- {item}" for item in report.missing_artifact_paths], ""])
    return "\n".join(lines)
