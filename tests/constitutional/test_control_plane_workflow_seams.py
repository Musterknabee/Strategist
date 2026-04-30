from datetime import datetime, timezone

from strategy_validator.control_plane import (
    OracleGovernanceClaimEnvelope,
    OracleGovernanceDispatchEnvelope,
    OracleGovernanceReviewEnvelope,
    OracleGovernanceRoutingEnvelope,
    build_governance_review_sort_key,
    materialize_governance_claim_envelope,
    materialize_governance_dispatch_envelope,
    materialize_governance_review_envelope,
    materialize_governance_routing_envelope,
)
from strategy_validator.validator.oracle_governance_plane import (
    build_governance_review_sort_key as legacy_build_governance_review_sort_key,
    materialize_governance_claim_envelope as legacy_materialize_governance_claim_envelope,
    materialize_governance_dispatch_envelope as legacy_materialize_governance_dispatch_envelope,
    materialize_governance_review_envelope as legacy_materialize_governance_review_envelope,
    materialize_governance_routing_envelope as legacy_materialize_governance_routing_envelope,
)


def test_control_plane_workflow_exports_are_typed_primitives() -> None:
    assert OracleGovernanceReviewEnvelope.__name__ == 'OracleGovernanceReviewEnvelope'
    assert OracleGovernanceRoutingEnvelope.__name__ == 'OracleGovernanceRoutingEnvelope'
    assert OracleGovernanceDispatchEnvelope.__name__ == 'OracleGovernanceDispatchEnvelope'
    assert OracleGovernanceClaimEnvelope.__name__ == 'OracleGovernanceClaimEnvelope'


def test_control_plane_review_sort_key_matches_legacy_behavior() -> None:
    due = datetime(2026, 4, 14, 10, 0, tzinfo=timezone.utc)
    assert build_governance_review_sort_key(
        review_due_by_utc=due,
        priority_score=73,
        queue_key='ROUTINE_REVIEW_QUEUE::ROUTINE_PRIORITY::READY::READY',
    ) == legacy_build_governance_review_sort_key(
        review_due_by_utc=due,
        priority_score=73,
        queue_key='ROUTINE_REVIEW_QUEUE::ROUTINE_PRIORITY::READY::READY',
    )


def test_control_plane_workflow_materialization_matches_legacy_outputs() -> None:
    issued_at = datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)
    queue_key = 'HEIGHTENED_REVIEW_QUEUE::ELEVATED_PRIORITY::VERIFICATION::WARNING'
    route_sha256 = 'abc123route'

    review = materialize_governance_review_envelope(
        issued_at_utc=issued_at,
        review_sla_hours=24,
        priority_score=84,
        queue_key=queue_key,
    )
    legacy_review = legacy_materialize_governance_review_envelope(
        issued_at_utc=issued_at,
        review_sla_hours=24,
        priority_score=84,
        queue_key=queue_key,
    )
    assert review.__dict__ == legacy_review.__dict__

    routing = materialize_governance_routing_envelope(
        review_target='HEIGHTENED_REVIEW_QUEUE',
        review_sla_hours=24,
        queue_key=queue_key,
        route_vector='priority=ELEVATED_PRIORITY|priority_score=84|review_target=HEIGHTENED_REVIEW_QUEUE',
        review_envelope=review,
    )
    legacy_routing = legacy_materialize_governance_routing_envelope(
        review_target='HEIGHTENED_REVIEW_QUEUE',
        review_sla_hours=24,
        queue_key=queue_key,
        route_vector='priority=ELEVATED_PRIORITY|priority_score=84|review_target=HEIGHTENED_REVIEW_QUEUE',
        review_envelope=legacy_review,
    )
    assert routing.__dict__ == legacy_routing.__dict__

    dispatch = materialize_governance_dispatch_envelope(
        queue_key=queue_key,
        route_sha256=route_sha256,
        review_envelope=review,
        routing_envelope=routing,
        dispatch_posture='DISPATCH_REVIEW_ONLY',
        dispatch_permitted=True,
        dispatch_summary_line='Dispatch posture: DISPATCH_REVIEW_ONLY; handoff is permitted only into governed review queues.',
        dispatch_reasons=['Dispatch is restricted to review-controlled handoff rather than routine downstream flow.'],
        priority_band='ELEVATED_PRIORITY',
        now_utc=issued_at,
    )
    legacy_dispatch = legacy_materialize_governance_dispatch_envelope(
        queue_key=queue_key,
        route_sha256=route_sha256,
        review_envelope=legacy_review,
        routing_envelope=legacy_routing,
        dispatch_posture='DISPATCH_REVIEW_ONLY',
        dispatch_permitted=True,
        dispatch_summary_line='Dispatch posture: DISPATCH_REVIEW_ONLY; handoff is permitted only into governed review queues.',
        dispatch_reasons=['Dispatch is restricted to review-controlled handoff rather than routine downstream flow.'],
        priority_band='ELEVATED_PRIORITY',
        now_utc=issued_at,
    )
    assert dispatch.__dict__ == legacy_dispatch.__dict__

    claim = materialize_governance_claim_envelope(
        dispatch_envelope=dispatch,
        queue_key=queue_key,
        review_target='HEIGHTENED_REVIEW_QUEUE',
        priority_band='ELEVATED_PRIORITY',
        review_due_by_utc=review.governance_plane_review_due_by_utc,
        review_sort_key=review.governance_plane_review_sort_key,
        route_sha256=route_sha256,
        review_envelope_sha256=review.governance_plane_review_envelope_sha256,
        routing_envelope_sha256=routing.governance_plane_routing_sha256,
        now_utc=issued_at,
    )
    legacy_claim = legacy_materialize_governance_claim_envelope(
        dispatch_envelope=legacy_dispatch,
        queue_key=queue_key,
        review_target='HEIGHTENED_REVIEW_QUEUE',
        priority_band='ELEVATED_PRIORITY',
        review_due_by_utc=legacy_review.governance_plane_review_due_by_utc,
        review_sort_key=legacy_review.governance_plane_review_sort_key,
        route_sha256=route_sha256,
        review_envelope_sha256=legacy_review.governance_plane_review_envelope_sha256,
        routing_envelope_sha256=legacy_routing.governance_plane_routing_sha256,
        now_utc=issued_at,
    )
    assert claim.__dict__ == legacy_claim.__dict__
