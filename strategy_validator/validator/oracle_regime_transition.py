from __future__ import annotations

from datetime import datetime
from pathlib import Path

from strategy_validator.contracts.oracle import OracleRegimeTransitionSignalReport, OracleStrategicFusionReport
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.oracle_strategic_artifact_evidence import discover_preferred_strategic_artifact_evidence, preferred_artifact_evidence_fact, strategic_artifact_evidence_support_score


def _resolve_preferred_artifact_evidence(*artifact_evidences: dict[str, str] | None) -> dict[str, str] | None:
    candidates = [item for item in artifact_evidences if item is not None]
    if not candidates:
        return None
    return max(candidates, key=strategic_artifact_evidence_support_score)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def compare_strategic_fusion_reports(
    previous: OracleStrategicFusionReport,
    current: OracleStrategicFusionReport,
    now_utc: datetime | None = None,
    doctrine_adaptation_report_path: Path | None = None,
    research_priority_report_path: Path | None = None,
    repo_root: Path | None = None,
    search_root: Path | None = None,
) -> OracleRegimeTransitionSignalReport:
    issued_at = now_utc or _utc_now()
    if previous.universe_label != current.universe_label:
        raise ValueError("strategic fusion transition requires matching universe_label values")
    oracle_run_id = current.oracle_run_id
    input_timestamp_utc = current.input_timestamp_utc
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
    exact_evidence_support_score = round(max(strategic_artifact_evidence_support_score(doctrine_artifact_evidence), strategic_artifact_evidence_support_score(research_artifact_evidence)), 6)
    preferred_artifact_evidence = _resolve_preferred_artifact_evidence(doctrine_artifact_evidence, research_artifact_evidence)
    confidence_delta = round(current.regime_confidence - previous.regime_confidence, 6)
    caution_delta = current.caution_score - previous.caution_score
    doctrine_delta = current.doctrine_stress_score - previous.doctrine_stress_score
    posture_changed = previous.strategic_posture != current.strategic_posture
    regime_changed = previous.dominant_regime != current.dominant_regime
    drivers: list[str] = []
    if regime_changed:
        drivers.append(f"dominant regime rotated from {previous.dominant_regime} to {current.dominant_regime}")
    if abs(confidence_delta) >= 0.15:
        drivers.append(f"regime confidence moved by {confidence_delta:+.1%}")
    if caution_delta >= 0.15:
        drivers.append("caution pressure stepped higher")
    if doctrine_delta >= 0.15:
        drivers.append("doctrine stress stepped higher")
    if posture_changed:
        drivers.append(f"strategic posture shifted from {previous.strategic_posture} to {current.strategic_posture}")
    drivers.extend(preferred_artifact_evidence_fact("transition_support", preferred_artifact_evidence))

    classification = "STABLE_REGIME"
    if current.epistemic_status == "UNKNOWN_UNKNOWNS" and current.caution_score >= 0.80 and (posture_changed or caution_delta >= 0.18 or doctrine_delta >= 0.18):
        classification = "STRUCTURAL_BREAK_CANDIDATE"
    elif regime_changed and posture_changed:
        classification = "TRANSITIONING"
    elif current.epistemic_status != "NOMINAL" or abs(confidence_delta) >= 0.10 or caution_delta >= 0.12:
        classification = "HIGH_UNCERTAINTY"
    elif regime_changed or posture_changed or abs(confidence_delta) >= 0.06:
        classification = "DRIFTING"

    operator_actions = [
        "Preserve both fusion reports and associated sensor evidence before revising strategic doctrine.",
    ]
    if classification == "STRUCTURAL_BREAK_CANDIDATE":
        operator_actions.append("Escalate for structural-break review and suspend broadening research confidence until contradictory signals are resolved.")
    elif classification in {"TRANSITIONING", "HIGH_UNCERTAINTY"}:
        operator_actions.append("Refresh the fusion stack soon and focus on whether the posture change is persistent or transient.")
    else:
        operator_actions.append("Continue monitoring for persistence before reclassifying strategy cohorts.")
    if exact_evidence_support_score >= 0.99:
        operator_actions.append("Exact sealed doctrine or research subjects are stabilizing the interpretation of this transition, even though the signal remains advisory-only.")

    return OracleRegimeTransitionSignalReport(
        generated_at_utc=issued_at,
        universe_label=current.universe_label,
        oracle_run_id=oracle_run_id,
        input_timestamp_utc=input_timestamp_utc,
        preferred_strategic_backing_source=(preferred_artifact_evidence.get("manifest_path") if preferred_artifact_evidence is not None else None) and "strategic_artifact_evidence_manifest" or None,
        preferred_strategic_backing_classification=(preferred_artifact_evidence.get("preferred_strategic_backing_classification") if preferred_artifact_evidence is not None else None) or None,
        exact_evidence_support_score=exact_evidence_support_score,
        previous_generated_at_utc=previous.generated_at_utc,
        current_generated_at_utc=current.generated_at_utc,
        previous_dominant_regime=previous.dominant_regime,
        current_dominant_regime=current.dominant_regime,
        previous_regime_confidence=previous.regime_confidence,
        current_regime_confidence=current.regime_confidence,
        confidence_delta=confidence_delta,
        previous_strategic_posture=previous.strategic_posture,
        current_strategic_posture=current.strategic_posture,
        transition_classification=classification,
        drivers=drivers,
        operator_actions=operator_actions,
        summary_line=(
            f"Strategic transition classified as {classification} with dominant regime {previous.dominant_regime} -> {current.dominant_regime} "
            f"and posture {previous.strategic_posture} -> {current.strategic_posture}."
        ),
    )


def render_oracle_regime_transition_markdown(report: OracleRegimeTransitionSignalReport) -> str:
    drivers = "\n".join(f"- {item}" for item in report.drivers) or "- none"
    actions = "\n".join(f"- {item}" for item in report.operator_actions) or "- none"
    return f"""# ORACLE REGIME TRANSITION SIGNAL REPORT

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Previous regime: {report.previous_dominant_regime}
- Current regime: {report.current_dominant_regime}
- Previous posture: {report.previous_strategic_posture}
- Current posture: {report.current_strategic_posture}
- Classification: {report.transition_classification}
- Preferred strategic backing source: {report.preferred_strategic_backing_source or "none"}
- Preferred strategic backing classification: {report.preferred_strategic_backing_classification or "none"}
- Exact evidence support score: {report.exact_evidence_support_score:.2f}

## Summary

{report.summary_line}

## Drivers

{drivers}

## Operator actions

{actions}
"""
