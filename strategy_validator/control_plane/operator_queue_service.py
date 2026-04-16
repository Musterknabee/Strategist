from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from strategy_validator.control_plane.governance_plane import OracleGovernancePlaneAssessment
from strategy_validator.control_plane.workflows import (
    OracleGovernanceClaimEnvelope,
    OracleGovernanceDispatchEnvelope,
    OracleGovernanceReviewEnvelope,
    OracleGovernanceRoutingEnvelope,
    materialize_governance_claim_envelope,
    materialize_governance_dispatch_envelope,
    materialize_governance_review_envelope,
    materialize_governance_routing_envelope,
)


@dataclass(frozen=True)
class OracleGovernanceWorkQueueState:
    governance_plane: OracleGovernancePlaneAssessment
    governance_review_envelope: OracleGovernanceReviewEnvelope
    governance_routing_envelope: OracleGovernanceRoutingEnvelope
    governance_dispatch_envelope: OracleGovernanceDispatchEnvelope
    governance_claim_envelope: OracleGovernanceClaimEnvelope


@dataclass(frozen=True)
class OracleGovernanceWorkQueueRequest:
    governance_plane: OracleGovernancePlaneAssessment
    issued_at_utc: datetime


def build_governance_work_queue_request(**kwargs) -> OracleGovernanceWorkQueueRequest:
    return OracleGovernanceWorkQueueRequest(**kwargs)


def materialize_governance_work_queue_state(
    request: OracleGovernanceWorkQueueRequest | None = None,
    **kwargs,
) -> OracleGovernanceWorkQueueState:
    request = request or OracleGovernanceWorkQueueRequest(**kwargs)
    governance_plane = request.governance_plane
    issued_at_utc = request.issued_at_utc

    governance_review_envelope = materialize_governance_review_envelope(
        issued_at_utc=issued_at_utc,
        review_sla_hours=governance_plane.governance_plane_review_sla_hours,
        priority_score=governance_plane.governance_plane_priority_score,
        queue_key=governance_plane.governance_plane_queue_key,
    )
    governance_routing_envelope = materialize_governance_routing_envelope(
        review_target=governance_plane.governance_plane_review_target,
        review_sla_hours=governance_plane.governance_plane_review_sla_hours,
        queue_key=governance_plane.governance_plane_queue_key,
        route_vector=governance_plane.governance_plane_route_vector,
        review_envelope=governance_review_envelope,
    )
    governance_dispatch_envelope = materialize_governance_dispatch_envelope(
        queue_key=governance_plane.governance_plane_queue_key,
        route_sha256=governance_plane.governance_plane_route_sha256,
        review_envelope=governance_review_envelope,
        routing_envelope=governance_routing_envelope,
        dispatch_posture=governance_plane.governance_plane_dispatch_posture,
        dispatch_permitted=governance_plane.governance_plane_dispatch_permitted,
        dispatch_summary_line=governance_plane.governance_plane_dispatch_summary_line,
        dispatch_reasons=governance_plane.governance_plane_dispatch_reasons,
        priority_band=governance_plane.governance_plane_priority_band,
        now_utc=issued_at_utc,
    )
    governance_claim_envelope = materialize_governance_claim_envelope(
        dispatch_envelope=governance_dispatch_envelope,
        queue_key=governance_plane.governance_plane_queue_key,
        review_target=governance_plane.governance_plane_review_target,
        priority_band=governance_plane.governance_plane_priority_band,
        review_due_by_utc=governance_review_envelope.governance_plane_review_due_by_utc,
        review_sort_key=governance_review_envelope.governance_plane_review_sort_key,
        route_sha256=governance_plane.governance_plane_route_sha256,
        review_envelope_sha256=governance_review_envelope.governance_plane_review_envelope_sha256,
        routing_envelope_sha256=governance_routing_envelope.governance_plane_routing_sha256,
        now_utc=issued_at_utc,
    )
    return OracleGovernanceWorkQueueState(
        governance_plane=governance_plane,
        governance_review_envelope=governance_review_envelope,
        governance_routing_envelope=governance_routing_envelope,
        governance_dispatch_envelope=governance_dispatch_envelope,
        governance_claim_envelope=governance_claim_envelope,
    )


__all__ = [
    'OracleGovernanceWorkQueueRequest',
    'OracleGovernanceWorkQueueState',
    'build_governance_work_queue_request',
    'materialize_governance_work_queue_state',
]
