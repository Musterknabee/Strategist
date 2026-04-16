from datetime import datetime, timedelta, timezone

from strategy_validator.contracts.oracle import (
    MacroRegimeSensorSnapshot,
    MicrostructureSensorSnapshot,
    OracleAdvisoryInput,
    OracleSensorMatrix,
    SemanticSensorSnapshot,
)
from strategy_validator.validator.oracle_advisory import build_oracle_morning_attestation
from strategy_validator.validator.oracle_governance_plane import build_governance_review_sort_key


def test_governance_review_sort_key_orders_earlier_due_first():
    early = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    late = early + timedelta(hours=4)
    k1 = build_governance_review_sort_key(review_due_by_utc=early, priority_score=95, queue_key="A")
    k2 = build_governance_review_sort_key(review_due_by_utc=late, priority_score=10, queue_key="B")
    assert k1 < k2


def test_governance_review_sort_key_uses_priority_within_same_due_time():
    due = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    k1 = build_governance_review_sort_key(review_due_by_utc=due, priority_score=95, queue_key="A")
    k2 = build_governance_review_sort_key(review_due_by_utc=due, priority_score=40, queue_key="A")
    assert k1 < k2


def test_morning_attestation_carries_governance_review_sort_key():
    advisory_input = OracleAdvisoryInput(
        generated_for_utc=datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc),
        universe_label="test",
        sensors=OracleSensorMatrix(
            semantic=SemanticSensorSnapshot(),
            microstructure=MicrostructureSensorSnapshot(),
            macro=MacroRegimeSensorSnapshot(
                yield_curve_slope_bps=10,
                high_yield_credit_spread_bps=350,
                equity_bond_correlation=0.2,
            ),
        ),
        strategies=[],
    )
    attestation = build_oracle_morning_attestation(payload=advisory_input, now_utc=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc))
    assert attestation.governance_plane_review_sort_key
    assert attestation.governance_plane_queue_key in attestation.governance_plane_review_sort_key
    assert attestation.governance_plane_review_due_by_utc is not None
    assert attestation.governance_plane_review_due_by_utc.isoformat() in attestation.governance_plane_review_sort_key
