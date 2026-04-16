import pytest

from strategy_validator.contracts.calibration import ParticipationImpactPoint
from strategy_validator.validator.calibration_curve import interpolate_impact_bps


@pytest.mark.parametrize(
    "x,expected",
    [
        (0.0, 10.0),
        (0.005, 15.0),
        (0.01, 20.0),
        (0.02, 30.0),
        (0.10, 100.0),
    ],
)
def test_interpolate_piecewise_linear(x: float, expected: float) -> None:
    curve = [
        ParticipationImpactPoint(participation_rate=0.0, impact_bps=10.0),
        ParticipationImpactPoint(participation_rate=0.01, impact_bps=20.0),
        ParticipationImpactPoint(participation_rate=0.02, impact_bps=30.0),
        ParticipationImpactPoint(participation_rate=0.10, impact_bps=100.0),
    ]
    got = interpolate_impact_bps(x, curve)
    assert abs(got - expected) < 1e-6
