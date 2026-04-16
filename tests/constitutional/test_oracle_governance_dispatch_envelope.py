from datetime import datetime, UTC

from strategy_validator.validator.oracle_governance_plane import (
    materialize_governance_dispatch_envelope,
    materialize_governance_review_envelope,
    materialize_governance_routing_envelope,
)
from strategy_validator.validator.oracle_advisory import build_oracle_morning_attestation
from strategy_validator.contracts.oracle import OracleAdvisoryInput


def test_materialize_governance_dispatch_envelope_has_stable_digest():
    review = materialize_governance_review_envelope(
        issued_at_utc=datetime(2026, 4, 14, 9, 0, tzinfo=UTC),
        review_sla_hours=24,
        priority_score=61,
        queue_key='HEIGHTENED_REVIEW_QUEUE::ELEVATED_PRIORITY::READINESS::RESTRICTING',
    )
    routing = materialize_governance_routing_envelope(
        review_target='HEIGHTENED_REVIEW_QUEUE',
        review_sla_hours=24,
        queue_key='HEIGHTENED_REVIEW_QUEUE::ELEVATED_PRIORITY::READINESS::RESTRICTING',
        route_vector='priority=ELEVATED_PRIORITY|priority_score=61|review_target=HEIGHTENED_REVIEW_QUEUE|review_sla_hours=24|queue_key=HEIGHTENED_REVIEW_QUEUE::ELEVATED_PRIORITY::READINESS::RESTRICTING|primary_dimension=READINESS|primary_severity=RESTRICTING',
        review_envelope=review,
    )
    dispatch = materialize_governance_dispatch_envelope(
        queue_key='HEIGHTENED_REVIEW_QUEUE::ELEVATED_PRIORITY::READINESS::RESTRICTING',
        route_sha256='abc123',
        review_envelope=review,
        routing_envelope=routing,
        dispatch_posture='DISPATCH_REVIEW_ONLY',
        dispatch_permitted=True,
        dispatch_summary_line='Dispatch posture: DISPATCH_REVIEW_ONLY; handoff is permitted only into governed review queues.',
        dispatch_reasons=['Dispatch is restricted to review-controlled handoff rather than routine downstream flow.'],
        priority_band='ELEVATED_PRIORITY',
        now_utc=datetime(2026, 4, 14, 10, 0, tzinfo=UTC),
    )
    assert dispatch.governance_plane_dispatch_vector.startswith('queue_key=HEIGHTENED_REVIEW_QUEUE')
    assert len(dispatch.governance_plane_dispatch_sha256) == 64
    assert dispatch.governance_plane_dispatch_claim_urgency == 'CLAIM_SOON'
    assert dispatch.governance_plane_dispatch_claim_score > 0


def test_morning_attestation_carries_governance_dispatch_fields():
    payload = OracleAdvisoryInput.model_validate({
        "generated_for_utc": "2026-04-14T09:00:00Z",
        "universe_label": "GLOBAL_MACRO",
        "sensors": {
            "semantic": {
                "inflation_hawkishness_score": 0.2,
                "geopolitical_risk_index": 0.7,
                "narrative_contradiction_count": 4,
                "tribunal_belief_conflict": 0.9
            },
            "microstructure": {
                "vpin": 0.63,
                "order_flow_imbalance": 0.04,
                "spread_variance_zscore": 1.1,
                "liquidity_thinning_score": 0.72
            },
            "macro": {
                "yield_curve_slope_bps": 8.0,
                "high_yield_credit_spread_bps": 340.0,
                "equity_bond_correlation": 0.88,
                "cross_asset_correlation_stress": 0.9,
                "realized_volatility_zscore": 1.4
            }
        },
        "strategies": []
    })
    report = build_oracle_morning_attestation(payload=payload)
    assert report.governance_plane_dispatch_summary_line
    assert report.governance_plane_dispatch_vector
    assert len(report.governance_plane_dispatch_sha256) == 64
