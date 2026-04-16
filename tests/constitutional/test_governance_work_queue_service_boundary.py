from datetime import UTC, datetime

from strategy_validator.control_plane import (
    OracleGovernanceWorkQueueState,
    assess_governance_plane,
    build_governance_work_queue_request,
    materialize_governance_work_queue_state,
)
from strategy_validator.control_plane.workflows import (
    materialize_governance_claim_envelope,
    materialize_governance_dispatch_envelope,
    materialize_governance_review_envelope,
    materialize_governance_routing_envelope,
)


def _sample_governance_plane():
    return assess_governance_plane(
        evidence_freshness_status='EVIDENCE_CURRENT',
        evidence_integrity_status='INTEGRITY_VERIFIED',
        evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='REMEDIATION_NONE',
        support_chain_remediation_actions=[],
        operator_readiness='READY_FOR_REVIEW',
        surface_label='test surface',
    )


def test_governance_work_queue_service_matches_direct_workflow_materialization():
    governance_plane = _sample_governance_plane()
    issued_at_utc = datetime(2026, 4, 14, 12, 0, tzinfo=UTC)

    state = materialize_governance_work_queue_state(
        governance_plane=governance_plane,
        issued_at_utc=issued_at_utc,
    )

    review = materialize_governance_review_envelope(
        issued_at_utc=issued_at_utc,
        review_sla_hours=governance_plane.governance_plane_review_sla_hours,
        priority_score=governance_plane.governance_plane_priority_score,
        queue_key=governance_plane.governance_plane_queue_key,
    )
    routing = materialize_governance_routing_envelope(
        review_target=governance_plane.governance_plane_review_target,
        review_sla_hours=governance_plane.governance_plane_review_sla_hours,
        queue_key=governance_plane.governance_plane_queue_key,
        route_vector=governance_plane.governance_plane_route_vector,
        review_envelope=review,
    )
    dispatch = materialize_governance_dispatch_envelope(
        queue_key=governance_plane.governance_plane_queue_key,
        route_sha256=governance_plane.governance_plane_route_sha256,
        review_envelope=review,
        routing_envelope=routing,
        dispatch_posture=governance_plane.governance_plane_dispatch_posture,
        dispatch_permitted=governance_plane.governance_plane_dispatch_permitted,
        dispatch_summary_line=governance_plane.governance_plane_dispatch_summary_line,
        dispatch_reasons=governance_plane.governance_plane_dispatch_reasons,
        priority_band=governance_plane.governance_plane_priority_band,
        now_utc=issued_at_utc,
    )
    claim = materialize_governance_claim_envelope(
        dispatch_envelope=dispatch,
        queue_key=governance_plane.governance_plane_queue_key,
        review_target=governance_plane.governance_plane_review_target,
        priority_band=governance_plane.governance_plane_priority_band,
        review_due_by_utc=review.governance_plane_review_due_by_utc,
        review_sort_key=review.governance_plane_review_sort_key,
        route_sha256=governance_plane.governance_plane_route_sha256,
        review_envelope_sha256=review.governance_plane_review_envelope_sha256,
        routing_envelope_sha256=routing.governance_plane_routing_sha256,
        now_utc=issued_at_utc,
    )

    assert state.governance_review_envelope == review
    assert state.governance_routing_envelope == routing
    assert state.governance_dispatch_envelope == dispatch
    assert state.governance_claim_envelope == claim


def test_governance_work_queue_service_supports_typed_request_builder():
    governance_plane = _sample_governance_plane()
    issued_at_utc = datetime(2026, 4, 14, 12, 0, tzinfo=UTC)
    request = build_governance_work_queue_request(
        governance_plane=governance_plane,
        issued_at_utc=issued_at_utc,
    )

    state = materialize_governance_work_queue_state(request)

    assert isinstance(state, OracleGovernanceWorkQueueState)
    assert state.governance_plane == governance_plane
    assert state.governance_claim_envelope.governance_plane_claim_queue_key == governance_plane.governance_plane_queue_key
