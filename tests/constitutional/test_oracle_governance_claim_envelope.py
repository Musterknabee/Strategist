from datetime import UTC, datetime, timedelta, timezone

from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_advisory import build_oracle_morning_attestation
from strategy_validator.validator.oracle_governance_plane import (
    assess_governance_plane,
    materialize_governance_claim_envelope,
    materialize_governance_dispatch_envelope,
    materialize_governance_review_envelope,
    materialize_governance_routing_envelope,
)


def test_materialize_governance_claim_envelope_has_stable_digest() -> None:
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
    claim = materialize_governance_claim_envelope(
        dispatch_envelope=dispatch,
        queue_key="HEIGHTENED_REVIEW_QUEUE::ELEVATED_PRIORITY::READINESS::RESTRICTING",
        review_target='HEIGHTENED_REVIEW_QUEUE',
        priority_band='ELEVATED_PRIORITY',
        review_due_by_utc=review.governance_plane_review_due_by_utc,
        review_sort_key=review.governance_plane_review_sort_key,
        route_sha256='abc123',
        review_envelope_sha256=review.governance_plane_review_envelope_sha256,
        routing_envelope_sha256=routing.governance_plane_routing_sha256,
    )
    assert claim.governance_plane_claim_vector.startswith('queue_key=HEIGHTENED_REVIEW_QUEUE')
    assert len(claim.governance_plane_claim_sha256) == 64
    assert 'CLAIM_SOON' in claim.governance_plane_claim_summary_line
    assert claim.governance_plane_claim_codes == ['CLAIM_DUE_SOON']
    assert claim.governance_plane_claim_primary_code == 'CLAIM_DUE_SOON'
    assert claim.governance_plane_claim_action_items
    assert claim.governance_plane_claim_primary_action_text
    assert claim.governance_plane_claim_action_items[0].severity == 'PROMPT'
    assert claim.governance_plane_claim_worker_lane == 'NEAR_DUE_CLAIM_WORKER'
    assert claim.governance_plane_claim_worker_sort_key.startswith('NEAR_DUE_CLAIM_WORKER::')
    assert claim.governance_plane_claim_lease_key.startswith('NEAR_DUE_CLAIM_WORKER::')
    assert claim.governance_plane_claim_lease_mode == 'SHORT_LEASE'
    assert claim.governance_plane_claim_lease_ttl_seconds == 1800
    assert claim.governance_plane_claim_lease_expires_at_utc is not None
    assert claim.governance_plane_claim_lease_expires_at_utc is not None
    assert claim.governance_plane_claim_lease_active_now is True
    assert claim.governance_plane_claim_lease_health == 'LEASE_HEALTHY'
    assert claim.governance_plane_claim_lease_health_summary_line
    assert claim.governance_plane_claim_lease_renewal_posture == 'NO_RENEWAL'
    assert claim.governance_plane_claim_lease_renewal_permitted_now is False
    assert claim.governance_plane_claim_lease_summary_line
    assert claim.governance_plane_claim_lease_renewal_summary_line
    assert claim.governance_plane_claim_lease_action == 'MAINTAIN_LEASE'
    assert claim.governance_plane_claim_lease_action_summary_line
    assert dispatch.governance_plane_dispatch_claim_key in claim.governance_plane_claim_lease_key
    assert claim.governance_plane_claim_disposition == 'CLAIM_QUEUE_PROMPT'
    assert 'CLAIM_QUEUE_PROMPT' in claim.governance_plane_claim_disposition_summary_line
    assert claim.governance_plane_claim_process_posture == 'PROCESS_READY_NOW'
    assert claim.governance_plane_claim_process_permitted_now is True
    assert claim.governance_plane_claim_process_summary_line
    assert claim.governance_plane_claim_operability == 'CLAIM_OPERABLE'
    assert claim.governance_plane_claim_operability_summary_line


def test_morning_attestation_carries_governance_claim_fields() -> None:
    payload = OracleAdvisoryInput.model_validate({
        'generated_for_utc': '2026-04-14T09:00:00Z',
        'universe_label': 'GLOBAL_MACRO',
        'sensors': {
            'semantic': {
                'inflation_hawkishness_score': 0.2,
                'geopolitical_risk_index': 0.7,
                'narrative_contradiction_count': 4,
                'tribunal_belief_conflict': 0.9,
            },
            'microstructure': {
                'vpin': 0.63,
                'order_flow_imbalance': 0.04,
                'spread_variance_zscore': 1.1,
                'liquidity_thinning_score': 0.72,
            },
            'macro': {
                'yield_curve_slope_bps': 8.0,
                'high_yield_credit_spread_bps': 340.0,
                'equity_bond_correlation': 0.88,
                'cross_asset_correlation_stress': 0.9,
                'realized_volatility_zscore': 1.4,
            },
        },
        'strategies': [],
    })
    report = build_oracle_morning_attestation(payload=payload)
    assert report.governance_plane_claim_summary_line
    assert report.governance_plane_claim_review_target
    assert report.governance_plane_claim_priority_band
    assert report.governance_plane_claim_route_sha256
    assert report.governance_plane_claim_review_envelope_sha256
    assert report.governance_plane_claim_routing_envelope_sha256
    assert report.governance_plane_claim_dispatch_claim_key
    assert report.governance_plane_claim_dispatch_sha256
    assert report.governance_plane_claim_codes
    assert report.governance_plane_claim_primary_code
    assert report.governance_plane_claim_action_items
    assert report.governance_plane_claim_primary_action_text
    assert report.governance_plane_claim_operability
    assert report.governance_plane_claim_operability_summary_line
    assert report.governance_plane_claim_worker_sort_key
    assert report.governance_plane_claim_lease_key
    assert report.governance_plane_claim_lease_mode
    assert report.governance_plane_claim_lease_ttl_seconds >= 0
    assert report.governance_plane_claim_lease_active_now in {True, False}
    assert report.governance_plane_claim_lease_health
    assert report.governance_plane_claim_lease_health_summary_line
    assert report.governance_plane_claim_lease_renewal_posture
    assert report.governance_plane_claim_lease_renewal_permitted_now in {True, False}
    assert report.governance_plane_claim_lease_summary_line
    assert report.governance_plane_claim_lease_renewal_summary_line
    assert report.governance_plane_claim_lease_action
    assert report.governance_plane_claim_lease_action_summary_line
    assert report.governance_plane_claim_disposition
    assert report.governance_plane_claim_disposition_summary_line
    assert report.governance_plane_claim_process_posture
    assert report.governance_plane_claim_process_permitted_now in {True, False}
    assert report.governance_plane_claim_process_summary_line
    assert report.governance_plane_claim_vector
    assert len(report.governance_plane_claim_sha256) == 64



def test_materialize_governance_claim_envelope_exposes_routing_metadata() -> None:
    assessment = assess_governance_plane(
        support_chain_trust_status='TRUST_RESTRICTED',
        support_chain_remediation_status='REMEDIATION_RECOMMENDED',
        evidence_freshness_status='AGING',
        evidence_integrity_status='MIXED',
        evidence_coverage_status='PARTIAL',
        support_verification_status='INCOMPLETE',
        operator_readiness='REVIEW_WITH_CAUTION',
    )
    review = materialize_governance_review_envelope(
        issued_at_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
        review_sla_hours=assessment.governance_plane_review_sla_hours,
        priority_score=assessment.governance_plane_priority_score,
        queue_key=assessment.governance_plane_queue_key,
    )
    routing = materialize_governance_routing_envelope(
        review_target=assessment.governance_plane_review_target,
        review_sla_hours=assessment.governance_plane_review_sla_hours,
        queue_key=assessment.governance_plane_queue_key,
        route_vector=assessment.governance_plane_route_vector,
        review_envelope=review,
    )
    dispatch = materialize_governance_dispatch_envelope(
        queue_key=assessment.governance_plane_queue_key,
        route_sha256=assessment.governance_plane_route_sha256,
        review_envelope=review,
        routing_envelope=routing,
        dispatch_posture=assessment.governance_plane_dispatch_posture,
        dispatch_permitted=assessment.governance_plane_dispatch_permitted,
        dispatch_summary_line=assessment.governance_plane_dispatch_summary_line,
        dispatch_reasons=assessment.governance_plane_dispatch_reasons,
        priority_band=assessment.governance_plane_priority_band,
        now_utc=datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
    )
    claim = materialize_governance_claim_envelope(
        dispatch_envelope=dispatch,
        queue_key=assessment.governance_plane_queue_key,
        review_target=assessment.governance_plane_review_target,
        priority_band=assessment.governance_plane_priority_band,
        review_due_by_utc=review.governance_plane_review_due_by_utc,
        review_sort_key=review.governance_plane_review_sort_key,
        route_sha256=assessment.governance_plane_route_sha256,
        review_envelope_sha256=review.governance_plane_review_envelope_sha256,
        routing_envelope_sha256=routing.governance_plane_routing_sha256,
    )
    assert claim.governance_plane_claim_queue_key == assessment.governance_plane_queue_key
    assert claim.governance_plane_claim_review_due_by_utc == review.governance_plane_review_due_by_utc
    assert claim.governance_plane_claim_review_sort_key == review.governance_plane_review_sort_key
    assert claim.governance_plane_claim_dispatch_claim_key == dispatch.governance_plane_dispatch_claim_key
    assert claim.governance_plane_claim_dispatch_sha256 == dispatch.governance_plane_dispatch_sha256
    assert claim.governance_plane_claim_lease_key.endswith(dispatch.governance_plane_dispatch_claim_key)
    assert claim.governance_plane_claim_lease_mode == 'SHORT_LEASE'
    assert claim.governance_plane_claim_lease_ttl_seconds == 1800
    assert claim.governance_plane_claim_lease_expires_at_utc is not None
    assert f'queue_key={assessment.governance_plane_queue_key}' in claim.governance_plane_claim_vector
    assert f'review_sort_key={review.governance_plane_review_sort_key}' in claim.governance_plane_claim_vector
    assert claim.governance_plane_claim_codes
    assert claim.governance_plane_claim_primary_code in claim.governance_plane_claim_codes


def test_materialize_governance_claim_envelope_carries_route_and_review_digests() -> None:
    assessment = assess_governance_plane(
        support_chain_trust_status='TRUST_RESTRICTED',
        support_chain_remediation_status='REMEDIATION_RECOMMENDED',
        evidence_freshness_status='AGING',
        evidence_integrity_status='MIXED',
        evidence_coverage_status='PARTIAL',
        support_verification_status='INCOMPLETE',
        operator_readiness='REVIEW_WITH_CAUTION',
    )
    review = materialize_governance_review_envelope(
        issued_at_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
        review_sla_hours=assessment.governance_plane_review_sla_hours,
        priority_score=assessment.governance_plane_priority_score,
        queue_key=assessment.governance_plane_queue_key,
    )
    routing = materialize_governance_routing_envelope(
        review_target=assessment.governance_plane_review_target,
        review_sla_hours=assessment.governance_plane_review_sla_hours,
        queue_key=assessment.governance_plane_queue_key,
        route_vector=assessment.governance_plane_route_vector,
        review_envelope=review,
    )
    dispatch = materialize_governance_dispatch_envelope(
        queue_key=assessment.governance_plane_queue_key,
        route_sha256=assessment.governance_plane_route_sha256,
        review_envelope=review,
        routing_envelope=routing,
        dispatch_posture=assessment.governance_plane_dispatch_posture,
        dispatch_permitted=assessment.governance_plane_dispatch_permitted,
        dispatch_summary_line=assessment.governance_plane_dispatch_summary_line,
        dispatch_reasons=assessment.governance_plane_dispatch_reasons,
        priority_band=assessment.governance_plane_priority_band,
        now_utc=datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
    )
    claim = materialize_governance_claim_envelope(
        dispatch_envelope=dispatch,
        queue_key=assessment.governance_plane_queue_key,
        review_target=assessment.governance_plane_review_target,
        priority_band=assessment.governance_plane_priority_band,
        review_due_by_utc=review.governance_plane_review_due_by_utc,
        review_sort_key=review.governance_plane_review_sort_key,
        route_sha256=assessment.governance_plane_route_sha256,
        review_envelope_sha256=review.governance_plane_review_envelope_sha256,
        routing_envelope_sha256=routing.governance_plane_routing_sha256,
    )
    assert claim.governance_plane_claim_review_target == assessment.governance_plane_review_target
    assert claim.governance_plane_claim_priority_band == assessment.governance_plane_priority_band
    assert claim.governance_plane_claim_route_sha256 == assessment.governance_plane_route_sha256
    assert claim.governance_plane_claim_review_envelope_sha256 == review.governance_plane_review_envelope_sha256
    assert claim.governance_plane_claim_routing_envelope_sha256 == routing.governance_plane_routing_sha256
    assert f'review_target={assessment.governance_plane_review_target}' in claim.governance_plane_claim_vector
    assert f'route_sha256={assessment.governance_plane_route_sha256}' in claim.governance_plane_claim_vector


def test_claim_envelope_assigns_blocked_worker_lane():
    from strategy_validator.validator.oracle_governance_plane import OracleGovernanceDispatchEnvelope, materialize_governance_claim_envelope

    dispatch = OracleGovernanceDispatchEnvelope(
        governance_plane_dispatch_posture="DISPATCH_BLOCKED",
        governance_plane_dispatch_permitted=False,
        governance_plane_dispatch_summary_line="blocked",
        governance_plane_dispatch_reasons=["blocked"],
        governance_plane_dispatch_timeliness="DISPATCH_OVERDUE",
        governance_plane_dispatch_claim_permitted_now=False,
        governance_plane_dispatch_timeliness_summary_line="overdue",
        governance_plane_dispatch_claim_urgency="DO_NOT_CLAIM",
        governance_plane_dispatch_claim_score=0,
        governance_plane_dispatch_claim_summary_line="blocked",
        governance_plane_dispatch_vector="dispatch",
        governance_plane_dispatch_sha256="deadbeef",
        governance_plane_dispatch_claim_key="claim-key",
    )
    due = datetime(2026, 1, 1, tzinfo=timezone.utc)
    claim = materialize_governance_claim_envelope(
        dispatch_envelope=dispatch,
        queue_key="Q",
        review_target="CONSTITUTIONAL_REPAIR_QUEUE",
        priority_band="CRITICAL_PRIORITY",
        review_due_by_utc=due,
        review_sort_key="sort",
        route_sha256="route",
        review_envelope_sha256="review",
        routing_envelope_sha256="routing",
    )
    assert claim.governance_plane_claim_worker_lane == "BLOCKED_CLAIM_HOLDING"
    assert claim.governance_plane_claim_primary_code == "CLAIM_PERMISSION_BLOCKED"
    assert claim.governance_plane_claim_action_items[0].severity == "BLOCKED"
    assert "Do not claim" in claim.governance_plane_claim_primary_action_text
    assert claim.governance_plane_claim_worker_sort_key.startswith("BLOCKED_CLAIM_HOLDING::")
    assert claim.governance_plane_claim_lease_key.startswith("BLOCKED_CLAIM_HOLDING::")
    assert claim.governance_plane_claim_lease_mode == 'NO_LEASE'
    assert claim.governance_plane_claim_lease_ttl_seconds == 0
    assert claim.governance_plane_claim_lease_expires_at_utc is None
    assert claim.governance_plane_claim_lease_active_now is False
    assert claim.governance_plane_claim_lease_health == 'LEASE_BLOCKED'
    assert claim.governance_plane_claim_lease_health_summary_line
    assert claim.governance_plane_claim_lease_renewal_posture == 'NO_RENEWAL'
    assert claim.governance_plane_claim_lease_renewal_permitted_now is False


def test_claim_worker_sort_key_orders_by_lane_due_score() -> None:
    from datetime import datetime, timedelta, timezone
    from strategy_validator.validator.oracle_governance_plane import _governance_claim_worker_sort_key

    due = datetime(2026, 4, 14, 12, 0, tzinfo=timezone.utc)
    key = _governance_claim_worker_sort_key(
        claim_worker_lane="IMMEDIATE_CLAIM_WORKER",
        review_due_by_utc=due,
        dispatch_claim_score=97,
        claim_primary_code="CLAIM_IMMEDIATE",
        dispatch_claim_key="dispatch-abc",
    )
    assert key == "IMMEDIATE_CLAIM_WORKER::2026-04-14T12:00:00+00:00::003::CLAIM_IMMEDIATE::dispatch-abc"


def test_claim_envelope_flags_lease_renew_now_when_expiry_is_near() -> None:
    from strategy_validator.validator.oracle_governance_plane import (
        materialize_governance_claim_envelope,
        materialize_governance_dispatch_envelope,
        materialize_governance_review_envelope,
        materialize_governance_routing_envelope,
    )

    now_utc = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    review = materialize_governance_review_envelope(
        issued_at_utc=now_utc,
        review_sla_hours=1,
        priority_score=70,
        queue_key='HEIGHTENED_REVIEW_QUEUE::ELEVATED_PRIORITY::ESCALATION::RESTRICTING',
    )
    routing = materialize_governance_routing_envelope(
        review_target='HEIGHTENED_REVIEW_QUEUE',
        review_sla_hours=1,
        queue_key='HEIGHTENED_REVIEW_QUEUE::ELEVATED_PRIORITY::ESCALATION::RESTRICTING',
        route_vector='route',
        review_envelope=review,
    )
    dispatch = materialize_governance_dispatch_envelope(
        queue_key='HEIGHTENED_REVIEW_QUEUE::ELEVATED_PRIORITY::ESCALATION::RESTRICTING',
        route_sha256='route',
        review_envelope=review,
        routing_envelope=routing,
        dispatch_posture='DISPATCH_REVIEW_ONLY',
        dispatch_permitted=True,
        dispatch_summary_line='demo',
        dispatch_reasons=['demo'],
        priority_band='ELEVATED_PRIORITY',
        now_utc=now_utc,
    )
    claim = materialize_governance_claim_envelope(
        dispatch_envelope=dispatch,
        queue_key='HEIGHTENED_REVIEW_QUEUE::ELEVATED_PRIORITY::ESCALATION::RESTRICTING',
        review_target='HEIGHTENED_REVIEW_QUEUE',
        priority_band='ELEVATED_PRIORITY',
        review_due_by_utc=review.governance_plane_review_due_by_utc,
        review_sort_key=review.governance_plane_review_sort_key,
        route_sha256='route',
        review_envelope_sha256=review.governance_plane_review_envelope_sha256,
        routing_envelope_sha256=routing.governance_plane_routing_sha256,
        now_utc=now_utc,
    )
    assert claim.governance_plane_claim_lease_mode == 'SHORT_LEASE'
    assert claim.governance_plane_claim_lease_health == 'LEASE_DEGRADED'
    assert claim.governance_plane_claim_lease_health_summary_line
    assert claim.governance_plane_claim_lease_renewal_posture == 'RENEW_SOON'
    assert claim.governance_plane_claim_lease_renewal_permitted_now is True
    assert claim.governance_plane_claim_lease_action == 'MAINTAIN_LEASE'
    assert claim.governance_plane_claim_lease_renewal_summary_line


def test_materialize_governance_claim_envelope_exposes_process_gate_for_allowed_claims() -> None:
    review = materialize_governance_review_envelope(
        issued_at_utc=datetime(2026, 4, 14, 9, 0, tzinfo=UTC),
        review_sla_hours=24,
        priority_score=95,
        queue_key='CONSTITUTIONAL_REPAIR_QUEUE::CRITICAL_PRIORITY::ESCALATION::BLOCKING',
    )
    routing = materialize_governance_routing_envelope(
        review_target='CONSTITUTIONAL_REPAIR_QUEUE',
        review_sla_hours=24,
        queue_key='CONSTITUTIONAL_REPAIR_QUEUE::CRITICAL_PRIORITY::ESCALATION::BLOCKING',
        route_vector='priority=CRITICAL_PRIORITY|priority_score=95|review_target=CONSTITUTIONAL_REPAIR_QUEUE|review_sla_hours=24|queue_key=CONSTITUTIONAL_REPAIR_QUEUE::CRITICAL_PRIORITY::ESCALATION::BLOCKING|primary_dimension=ESCALATION|primary_severity=BLOCKING',
        review_envelope=review,
    )
    dispatch = materialize_governance_dispatch_envelope(
        queue_key='CONSTITUTIONAL_REPAIR_QUEUE::CRITICAL_PRIORITY::ESCALATION::BLOCKING',
        route_sha256='def456',
        review_envelope=review,
        routing_envelope=routing,
        dispatch_posture='DISPATCH_ALLOWED',
        dispatch_permitted=True,
        dispatch_summary_line='Dispatch posture: DISPATCH_ALLOWED; governed handoff is permitted.',
        dispatch_reasons=['Dispatch is permitted into governed claim flow.'],
        priority_band='CRITICAL_PRIORITY',
        now_utc=datetime(2026, 4, 14, 9, 0, tzinfo=UTC),
    )
    claim = materialize_governance_claim_envelope(
        dispatch_envelope=dispatch,
        queue_key='CONSTITUTIONAL_REPAIR_QUEUE::CRITICAL_PRIORITY::ESCALATION::BLOCKING',
        review_target='CONSTITUTIONAL_REPAIR_QUEUE',
        priority_band='CRITICAL_PRIORITY',
        review_due_by_utc=review.governance_plane_review_due_by_utc,
        review_sort_key=review.governance_plane_review_sort_key,
        route_sha256='def456',
        review_envelope_sha256=review.governance_plane_review_envelope_sha256,
        routing_envelope_sha256=routing.governance_plane_routing_sha256,
        now_utc=review.governance_plane_review_due_by_utc - timedelta(seconds=120),
    )
    assert claim.governance_plane_claim_lease_health == 'LEASE_HEALTHY'
    assert claim.governance_plane_claim_lease_action == 'MAINTAIN_LEASE'
    assert claim.governance_plane_claim_process_posture == 'PROCESS_READY_NOW'
    assert claim.governance_plane_claim_process_permitted_now is True
