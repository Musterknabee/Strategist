from datetime import UTC, datetime, timedelta

from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_advisory import build_oracle_morning_attestation
from strategy_validator.validator.oracle_governance_plane import (
    materialize_governance_dispatch_envelope,
    materialize_governance_review_envelope,
    materialize_governance_routing_envelope,
)


def test_dispatch_envelope_marks_due_soon_claimable() -> None:
    issued_at = datetime(2026, 4, 14, 8, 0, tzinfo=UTC)
    review = materialize_governance_review_envelope(
        issued_at_utc=issued_at,
        review_sla_hours=2,
        priority_score=80,
        queue_key='HEIGHTENED_REVIEW_QUEUE::ELEVATED_PRIORITY::READINESS::RESTRICTING',
    )
    routing = materialize_governance_routing_envelope(
        review_target='HEIGHTENED_REVIEW_QUEUE',
        review_sla_hours=2,
        queue_key='HEIGHTENED_REVIEW_QUEUE::ELEVATED_PRIORITY::READINESS::RESTRICTING',
        route_vector='priority=ELEVATED_PRIORITY|priority_score=80|review_target=HEIGHTENED_REVIEW_QUEUE',
        review_envelope=review,
    )
    dispatch = materialize_governance_dispatch_envelope(
        queue_key='HEIGHTENED_REVIEW_QUEUE::ELEVATED_PRIORITY::READINESS::RESTRICTING',
        route_sha256='b' * 64,
        review_envelope=review,
        routing_envelope=routing,
        dispatch_posture='DISPATCH_REVIEW_ONLY',
        dispatch_permitted=True,
        dispatch_summary_line='Dispatch posture: DISPATCH_REVIEW_ONLY; handoff is permitted only into governed review queues.',
        dispatch_reasons=['Dispatch is restricted to review-controlled handoff rather than routine downstream flow.'],
        priority_band='ELEVATED_PRIORITY',
        now_utc=issued_at + timedelta(minutes=30),
    )
    assert dispatch.governance_plane_dispatch_timeliness == 'DISPATCH_DUE_SOON'
    assert dispatch.governance_plane_dispatch_claim_permitted_now is True
    assert dispatch.governance_plane_dispatch_claim_urgency == 'CLAIM_NOW'
    assert dispatch.governance_plane_dispatch_claim_score >= 95
    assert 'claim now' in dispatch.governance_plane_dispatch_timeliness_summary_line.lower()


def test_dispatch_envelope_marks_overdue_not_claimable() -> None:
    issued_at = datetime(2026, 4, 14, 8, 0, tzinfo=UTC)
    review = materialize_governance_review_envelope(
        issued_at_utc=issued_at,
        review_sla_hours=1,
        priority_score=95,
        queue_key='CONSTITUTIONAL_REPAIR_QUEUE::CRITICAL_PRIORITY::REMEDIATION::BLOCKING',
    )
    routing = materialize_governance_routing_envelope(
        review_target='CONSTITUTIONAL_REPAIR_QUEUE',
        review_sla_hours=1,
        queue_key='CONSTITUTIONAL_REPAIR_QUEUE::CRITICAL_PRIORITY::REMEDIATION::BLOCKING',
        route_vector='priority=CRITICAL_PRIORITY|priority_score=95|review_target=CONSTITUTIONAL_REPAIR_QUEUE',
        review_envelope=review,
    )
    dispatch = materialize_governance_dispatch_envelope(
        queue_key='CONSTITUTIONAL_REPAIR_QUEUE::CRITICAL_PRIORITY::REMEDIATION::BLOCKING',
        route_sha256='c' * 64,
        review_envelope=review,
        routing_envelope=routing,
        dispatch_posture='DISPATCH_ALLOWED',
        dispatch_permitted=True,
        dispatch_summary_line='Dispatch posture: DISPATCH_ALLOWED; routine governed queue handoff is acceptable.',
        dispatch_reasons=['Dispatch is permitted for routine governed queue handoff.'],
        priority_band='CRITICAL_PRIORITY',
        now_utc=issued_at + timedelta(hours=2),
    )
    assert dispatch.governance_plane_dispatch_timeliness == 'DISPATCH_OVERDUE'
    assert dispatch.governance_plane_dispatch_claim_permitted_now is False
    assert dispatch.governance_plane_dispatch_claim_urgency == 'DO_NOT_CLAIM'
    assert dispatch.governance_plane_dispatch_claim_score == 0


def test_morning_attestation_carries_dispatch_timeliness_fields() -> None:
    payload = OracleAdvisoryInput.model_validate({
        'generated_for_utc': '2026-04-14T09:00:00Z',
        'universe_label': 'GLOBAL_MACRO',
        'sensors': {
            'semantic': {
                'inflation_hawkishness_score': 0.2,
                'geopolitical_risk_index': 0.7,
                'narrative_contradiction_count': 4,
                'tribunal_belief_conflict': 0.9
            },
            'microstructure': {
                'vpin': 0.63,
                'order_flow_imbalance': 0.04,
                'spread_variance_zscore': 1.1,
                'liquidity_thinning_score': 0.72
            },
            'macro': {
                'yield_curve_slope_bps': 8.0,
                'high_yield_credit_spread_bps': 340.0,
                'equity_bond_correlation': 0.88,
                'cross_asset_correlation_stress': 0.9,
                'realized_volatility_zscore': 1.4
            }
        },
        'strategies': []
    })
    report = build_oracle_morning_attestation(payload=payload)
    assert report.governance_plane_dispatch_timeliness in {'DISPATCH_ACTIVE', 'DISPATCH_DUE_SOON', 'DISPATCH_OVERDUE'}
    assert isinstance(report.governance_plane_dispatch_claim_permitted_now, bool)
    assert report.governance_plane_dispatch_timeliness_summary_line
    assert report.governance_plane_dispatch_claim_urgency in {'CLAIM_NOW', 'CLAIM_SOON', 'DO_NOT_CLAIM'}
    assert 0 <= report.governance_plane_dispatch_claim_score <= 100
    assert report.governance_plane_dispatch_claim_summary_line
