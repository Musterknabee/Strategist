from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from strategy_validator.contracts.oracle import (
    OracleStrategicDriverDriftItem,
    OracleStrategicMemoryHorizonReport,
    OracleStrategicMemoryPoint,
    OracleStrategicNarrativeReport,
)
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.oracle_run_identity import strategic_epoch_from_report

_DRIVER_KINDS = (
    "REGIME_DRIVER",
    "STRATEGY_DRIVER",
    "DOCTRINE_DRIVER",
    "SCENARIO_DRIVER",
    "CONTRADICTION_DRIVER",
    "INVESTIGATION_DRIVER",
)


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _unique(items: list[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if normalized and normalized not in output:
            output.append(normalized)
    return output


def _sorted_reports(reports: list[OracleStrategicNarrativeReport]) -> list[OracleStrategicNarrativeReport]:
    unique: dict[tuple[str, str, str | None], OracleStrategicNarrativeReport] = {}
    for report in reports:
        key = (
            report.oracle_run_id,
            report.generated_at_utc.isoformat(),
            report.highest_ranked_narrative_id,
        )
        unique[key] = report
    return sorted(unique.values(), key=lambda report: report.generated_at_utc)


def _point_id(report: OracleStrategicNarrativeReport) -> str:
    return f"memory:{report.generated_at_utc.isoformat()}:{report.highest_ranked_narrative_id or 'none'}"


def _point_from_report(report: OracleStrategicNarrativeReport) -> OracleStrategicMemoryPoint:
    top = report.items[0] if report.items else None
    return OracleStrategicMemoryPoint(
        oracle_run_id=report.oracle_run_id,
        input_timestamp_utc=report.input_timestamp_utc,
        point_id=_point_id(report),
        generated_at_utc=report.generated_at_utc,
        dominant_regime=report.dominant_regime,
        strategic_posture=report.strategic_posture,
        conviction_state=report.conviction_state,
        conviction_score=round(_clamp(report.conviction_score), 6),
        fragility_score=round(_clamp(report.fragility_score), 6),
        top_driver_kind=(top.driver_kind if top is not None else None),
        top_driver_title=(top.title if top is not None else None),
        top_driver_rank_score=round(_clamp(top.rank_score if top is not None else 0.0), 6),
        summary_line=report.summary_line,
    )


def _driver_rank(report: OracleStrategicNarrativeReport, driver_kind: str) -> float:
    values = [item.rank_score for item in report.items if item.driver_kind == driver_kind]
    return round(_clamp(max(values) if values else 0.0), 6)


def _drift_direction(delta: float) -> str:
    if delta >= 0.06:
        return "RISING"
    if delta <= -0.06:
        return "FALLING"
    return "STABLE"


def _conviction_level(state: str) -> int:
    order = {
        "BROKEN_CONVICTION": 0,
        "FRAGILE_CONVICTION": 1,
        "GUARDED_CONVICTION": 2,
        "HIGH_CONVICTION": 3,
    }
    return order.get(state, 0)


def _drift_state(points: list[OracleStrategicMemoryPoint], conviction_delta: float, fragility_delta: float) -> str:
    if len(points) <= 1:
        return "FIRST_OBSERVATION"
    latest = points[-1]
    prior = points[-2]
    state_delta = _conviction_level(latest.conviction_state) - _conviction_level(prior.conviction_state)
    if conviction_delta >= 0.12 and fragility_delta <= 0.02:
        return "STRENGTHENING"
    if conviction_delta <= -0.12 and fragility_delta >= -0.02:
        return "SOFTENING"
    if state_delta <= -2 or (conviction_delta <= -0.18 and fragility_delta >= 0.10):
        return "REVERSING"
    deltas = [points[i].conviction_score - points[i - 1].conviction_score for i in range(1, len(points))]
    signs = {1 if delta > 0.03 else -1 if delta < -0.03 else 0 for delta in deltas}
    if len([sign for sign in signs if sign != 0]) > 1 and max(abs(delta) for delta in deltas) >= 0.10:
        return "VOLATILE"
    return "STABLE"


def build_oracle_strategic_memory_horizon_report(
    current_report: OracleStrategicNarrativeReport,
    *,
    history_reports: list[OracleStrategicNarrativeReport] | None = None,
    sealed_history_reports: list[OracleStrategicNarrativeReport] | None = None,
    sealed_history_manifest_paths: list[str] | None = None,
    require_sealed_history: bool = False,
    now_utc: datetime | None = None,
) -> OracleStrategicMemoryHorizonReport:
    issued_at = now_utc or _utc_now()
    unsealed_reports = list(history_reports or [])
    sealed_reports = list(sealed_history_reports or [])
    source_stack_manifest_paths = _unique(list(sealed_history_manifest_paths or []))

    if require_sealed_history:
        reports = _sorted_reports([*sealed_reports, current_report])
        unsealed_history_excluded_count = len(unsealed_reports)
    else:
        reports = _sorted_reports([*unsealed_reports, *sealed_reports, current_report])
        unsealed_history_excluded_count = 0
    if not reports:
        raise ValueError("at least one strategic narrative report is required")
    points = [_point_from_report(report) for report in reports]
    baseline = points[0]
    current = points[-1]
    conviction_delta = round(current.conviction_score - baseline.conviction_score, 6)
    fragility_delta = round(current.fragility_score - baseline.fragility_score, 6)

    driver_drifts: list[OracleStrategicDriverDriftItem] = []
    for driver_kind in _DRIVER_KINDS:
        baseline_rank = _driver_rank(reports[0], driver_kind)
        current_rank = _driver_rank(reports[-1], driver_kind)
        delta = round(current_rank - baseline_rank, 6)
        direction = _drift_direction(delta)
        if direction == "RISING":
            summary = f"{driver_kind} has gained explanatory dominance across the memory horizon."
        elif direction == "FALLING":
            summary = f"{driver_kind} has lost explanatory dominance across the memory horizon."
        else:
            summary = f"{driver_kind} remained comparatively stable across the memory horizon."
        driver_drifts.append(
            OracleStrategicDriverDriftItem(
                driver_kind=driver_kind,
                baseline_rank_score=baseline_rank,
                current_rank_score=current_rank,
                drift_delta=delta,
                drift_direction=direction,
                summary_line=summary,
            )
        )
    driver_drifts = sorted(driver_drifts, key=lambda item: (-abs(item.drift_delta), item.driver_kind))
    rising = next((item for item in driver_drifts if item.drift_direction == "RISING"), None)
    falling = next((item for item in driver_drifts if item.drift_direction == "FALLING"), None)
    drift_state = _drift_state(points, conviction_delta, fragility_delta)
    if len(points) <= 1:
        history_integrity_status = "CURRENT_ONLY"
    elif require_sealed_history or (sealed_reports and not unsealed_reports):
        history_integrity_status = "SEALED_HISTORY"
    else:
        history_integrity_status = "MIXED_HISTORY"

    summary_line = (
        f"Strategic conviction is {current.conviction_state.lower().replace('_', ' ')} at {current.conviction_score:.2f} across {len(points)} observations, "
        f"with conviction delta {conviction_delta:+.2f} and fragility delta {fragility_delta:+.2f}; "
        f"the strongest rising driver is {(rising.driver_kind if rising is not None else 'none').lower().replace('_', ' ')}"
        f" and the strongest fading driver is {(falling.driver_kind if falling is not None else 'none').lower().replace('_', ' ')}. "
        f"History integrity is {history_integrity_status.lower().replace('_', ' ')} with {len(sealed_reports)} sealed prior observations"
        f" and {unsealed_history_excluded_count} excluded unsealed observations."
    )
    operator_actions = _unique([
        (
            f"Review why {rising.driver_kind.lower().replace('_', ' ')} gained dominance before leaning harder on the current strategic narrative."
            if rising is not None else "Persist another strategic narrative observation to identify which driver is gaining dominance over time."
        ),
        (
            f"Revisit the evidence behind {falling.driver_kind.lower().replace('_', ' ')} to confirm whether the loss of influence is durable."
            if falling is not None else "Keep tracking driver ranks so weakening conviction anchors remain visible over time."
        ),
        (
            "Treat the current map as fragile until the reversal in conviction is explained by fresh investigation evidence."
            if drift_state == "REVERSING" else
            "Increase monitoring cadence because the conviction path is volatile across recent cycles."
            if drift_state == "VOLATILE" else
            "Continue recording strategic narrative reports so belief drift remains replayable across the horizon."
        ),
        (
            "Use only sealed strategic stack bundles when comparing prior cycles, because mixed history can fabricate drift."
            if history_integrity_status == "MIXED_HISTORY" else
            "Preserve stack manifests alongside historical narratives so future contradiction and campaign logic remain replayable."
            if history_integrity_status == "SEALED_HISTORY" else
            "Seal at least one prior strategic stack before relying on drift across multiple cycles."
        ),
    ])
    return OracleStrategicMemoryHorizonReport(
        generated_at_utc=issued_at,
        universe_label=current_report.universe_label,
        oracle_run_id=current_report.oracle_run_id,
        input_timestamp_utc=current_report.input_timestamp_utc,
        horizon_observation_count=len(points),
        sealed_history_observation_count=len(sealed_reports),
        unsealed_history_excluded_count=unsealed_history_excluded_count,
        history_integrity_status=history_integrity_status,
        source_stack_manifest_paths=source_stack_manifest_paths,
        current_conviction_state=current.conviction_state,
        current_conviction_score=current.conviction_score,
        conviction_score_delta=conviction_delta,
        fragility_score_delta=fragility_delta,
        drift_state=drift_state,
        summary_line=summary_line,
        strongest_rising_driver_kind=(rising.driver_kind if rising is not None else None),
        strongest_falling_driver_kind=(falling.driver_kind if falling is not None else None),
        points=points,
        driver_drifts=driver_drifts,
        operator_actions=operator_actions,
    )


def render_oracle_strategic_memory_horizon_markdown(report: OracleStrategicMemoryHorizonReport) -> str:
    lines = [
        "# ORACLE STRATEGIC MEMORY HORIZON REPORT",
        "",
        f"- Generated at UTC: {report.generated_at_utc.isoformat()}",
        f"- Universe: {report.universe_label}",
        f"- Observation count: {report.horizon_observation_count}",
        f"- History integrity: {report.history_integrity_status}",
        f"- Sealed history observations: {report.sealed_history_observation_count}",
        f"- Excluded unsealed observations: {report.unsealed_history_excluded_count}",
        f"- Current conviction state: {report.current_conviction_state}",
        f"- Current conviction score: {report.current_conviction_score:.2f}",
        f"- Conviction delta: {report.conviction_score_delta:+.2f}",
        f"- Fragility delta: {report.fragility_score_delta:+.2f}",
        f"- Drift state: {report.drift_state}",
        f"- Strongest rising driver: {report.strongest_rising_driver_kind or 'none'}",
        f"- Strongest falling driver: {report.strongest_falling_driver_kind or 'none'}",
        "",
        "## Summary",
        "",
        report.summary_line,
        "",
        "## Belief Drift Timeline",
        "",
    ]
    for point in report.points:
        lines.extend([
            f"### {point.generated_at_utc.isoformat()}",
            "",
            f"- Conviction state: `{point.conviction_state}`",
            f"- Conviction score: `{point.conviction_score:.2f}`",
            f"- Fragility score: `{point.fragility_score:.2f}`",
            f"- Regime/posture: `{point.dominant_regime}` / `{point.strategic_posture}`",
            f"- Top driver: `{point.top_driver_kind or 'none'}` — {point.top_driver_title or 'none'}",
            f"- Summary: {point.summary_line}",
            "",
        ])
    lines.extend([
        "## Driver Drift",
        "",
    ])
    for item in report.driver_drifts:
        lines.extend([
            f"- `{item.driver_kind}` → {item.drift_direction} (baseline={item.baseline_rank_score:.2f}, current={item.current_rank_score:.2f}, delta={item.drift_delta:+.2f})",
            f"  - {item.summary_line}",
        ])
    if not report.driver_drifts:
        lines.append("- none")
    lines.extend([
        "",
        "## Recommended operator actions",
        "",
    ])
    lines.extend([f"- {action}" for action in report.operator_actions] or ["- none"])
    lines.append("")
    return "\n".join(lines)


def load_strategic_memory_horizon_report(path: Path) -> OracleStrategicMemoryHorizonReport:
    return OracleStrategicMemoryHorizonReport.model_validate(json.loads(path.read_text(encoding="utf-8")))
