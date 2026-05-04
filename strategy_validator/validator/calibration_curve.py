"""Deterministic interpolation for empirical participation → impact curves."""
from __future__ import annotations

from strategy_validator.contracts.calibration import ParticipationImpactPoint


def interpolate_impact_bps(participation_rate: float, curve: list[ParticipationImpactPoint]) -> float:
    """
    Piecewise-linear interpolation on a strictly increasing participation curve.

    Clamps below the first point to the first impact; above the last to the last impact.
    """
    if not curve:
        return 0.0
    x = max(0.0, min(1.0, float(participation_rate)))
    if x <= curve[0].participation_rate:
        return float(curve[0].impact_bps)
    if x >= curve[-1].participation_rate:
        return float(curve[-1].impact_bps)
    for i in range(len(curve) - 1):
        x0, x1 = curve[i].participation_rate, curve[i + 1].participation_rate
        if x0 <= x <= x1:
            y0, y1 = curve[i].impact_bps, curve[i + 1].impact_bps
            if x1 == x0:
                return float(y0)
            t = (x - x0) / (x1 - x0)
            return float(y0 + t * (y1 - y0))
    return float(curve[-1].impact_bps)
