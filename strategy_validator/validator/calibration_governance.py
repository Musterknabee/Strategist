"""
Calibration artifact acceptance beyond JSON schema (governance).

Used by readiness (fail-closed) and the calibration CLI. Does not replace
Pydantic validation on ``CalibrationArtifactV1`` — it adds policy gates.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, List

from strategy_validator.contracts.calibration import CalibrationArtifactV1, empirical_curve_spread_bps

if TYPE_CHECKING:
    from strategy_validator.core.config import RuntimePolicy


def calibration_governance_violations(art: CalibrationArtifactV1, policy: "RuntimePolicy") -> List[str]:
    """
    Return human-readable violation codes (empty list == accepted for governance).

    Policy fields default to permissive values so existing artifacts keep working
    until operators tighten gates via env / YAML.
    """
    violations: list[str] = []
    now = datetime.now(timezone.utc)
    fitted = art.fitted_at_utc
    if fitted.tzinfo is None:
        fitted = fitted.replace(tzinfo=timezone.utc)
    if fitted > now + timedelta(minutes=5):
        violations.append("CALIBRATION_FITTED_AT_IN_FUTURE")

    if policy.calibration_require_training_run_id:
        if not (art.training_run_id and art.training_run_id.strip()):
            violations.append("CALIBRATION_TRAINING_RUN_ID_REQUIRED")

    thr = float(policy.calibration_minimum_validation_score)
    if thr > 0.0:
        if art.validation_quality_score is None:
            violations.append("CALIBRATION_VALIDATION_SCORE_MISSING")
        elif float(art.validation_quality_score) < thr:
            violations.append(
                f"CALIBRATION_VALIDATION_SCORE_BELOW_THRESHOLD:{float(art.validation_quality_score):.4f}<{thr:.4f}"
            )

    if policy.calibration_require_empirical_curve_in_production:
        if art.empirical_participation_curve is None:
            violations.append("CALIBRATION_EMPIRICAL_CURVE_REQUIRED")

    spread_floor = float(policy.calibration_reject_flat_curve_spread_bps_below)
    if spread_floor > 0.0 and art.empirical_participation_curve:
        sp = empirical_curve_spread_bps(art.empirical_participation_curve)
        if sp < spread_floor:
            violations.append(f"CALIBRATION_CURVE_TOO_FLAT:{sp:.4f}bps<{spread_floor:.4f}bps")

    return violations
