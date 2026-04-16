from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from strategy_validator.contracts.oracle import OracleDoctrineAdaptationReport
from strategy_validator.validator.oracle_schema_registry import iter_registered_artifacts


@dataclass(frozen=True)
class OracleCadenceFeedbackSummary:
    exact_evidence_support_score: float = 0.0
    exact_feedback_confirmation_count: int = 0
    exact_feedback_relief_count: int = 0


def summarize_exact_cadence_feedback(
    *,
    repo_root: Optional[Path] = None,
    search_root: Optional[Path] = None,
    window_size: int = 1,
) -> OracleCadenceFeedbackSummary:
    roots: list[Path] = []
    for candidate in (search_root, repo_root):
        if candidate is None:
            continue
        resolved = candidate.resolve()
        if resolved not in roots and resolved.exists():
            roots.append(resolved)
    if not roots:
        return OracleCadenceFeedbackSummary()

    reports: list[OracleDoctrineAdaptationReport] = []
    for _, _, _, report in iter_registered_artifacts(
        roots=roots,
        expected_schemas={"oracle_doctrine_adaptation_report/v1"},
        expected_families={"oracle"},
    ):
        if isinstance(report, OracleDoctrineAdaptationReport):
            reports.append(report)
    if not reports:
        return OracleCadenceFeedbackSummary()
    reports.sort(key=lambda report: report.generated_at_utc)
    window_reports = reports[-max(window_size, 1):]
    support = max((float(report.exact_evidence_support_score or 0.0) for report in window_reports), default=0.0)
    confirmation_count = 0
    relief_count = 0
    for report in window_reports:
        for item in report.items:
            item_support = float(item.exact_evidence_support_score or 0.0)
            if item_support < 0.85:
                continue
            if item.stress_score >= 0.58 or item.review_priority_score >= 0.58:
                confirmation_count += 1
            elif item.stress_score <= 0.42 and item.review_priority_score <= 0.45:
                relief_count += 1
    return OracleCadenceFeedbackSummary(
        exact_evidence_support_score=round(min(1.0, support), 6),
        exact_feedback_confirmation_count=confirmation_count,
        exact_feedback_relief_count=relief_count,
    )


def classify_exact_cadence_signal(*, exact_feedback_confirmation_count: int, exact_feedback_relief_count: int) -> str:
    if exact_feedback_confirmation_count > exact_feedback_relief_count and exact_feedback_confirmation_count > 0:
        return "EXACT_CONFIRMED_PRESSURE"
    if exact_feedback_relief_count > exact_feedback_confirmation_count and exact_feedback_relief_count > 0:
        return "EXACT_RELIEF_PRESSURE"
    return "AMBIENT_DRIFT"


def cadence_operator_action(*, exact_cadence_signal_classification: str, exact_feedback_confirmation_count: int, exact_feedback_relief_count: int) -> str:
    if exact_cadence_signal_classification == "EXACT_CONFIRMED_PRESSURE":
        return (
            f"Treat repeated exact sealed confirmations ({exact_feedback_confirmation_count}) as active pressure: compress the decision loop and advance the best-supported move before widening posture."
        )
    if exact_cadence_signal_classification == "EXACT_RELIEF_PRESSURE":
        return (
            f"Treat repeated exact sealed relief ({exact_feedback_relief_count}) as a softening signal: keep progression guarded, monitor drift, and avoid forcing escalation."
        )
    return "Treat current pressure as ambient drift: advance cautiously and prefer incremental evidence collection over escalation."


def cadence_recommendation_suffix(*, exact_cadence_signal_classification: str, exact_evidence_support_score: float) -> str:
    if exact_cadence_signal_classification == "EXACT_CONFIRMED_PRESSURE":
        if exact_evidence_support_score >= 0.85:
            return " Repeated exact sealed confirmations justify a tighter execution loop on this already-supported path."
        return " Repeated exact sealed confirmations are tightening pressure here; resolve this path before widening posture."
    if exact_cadence_signal_classification == "EXACT_RELIEF_PRESSURE":
        if exact_evidence_support_score >= 0.85:
            return " Repeated exact sealed relief supports guarded progression and monitoring rather than forced escalation."
        return " Repeated exact sealed relief softens pressure, but keep progression guarded until direct support strengthens."
    return " Ambient drift remains the main driver here, so keep the next move incremental and evidence-seeking."
