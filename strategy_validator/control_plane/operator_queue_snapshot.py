from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from strategy_validator.control_plane.operator_queue_service import (
    OracleGovernanceWorkQueueRequest,
    OracleGovernanceWorkQueueState,
    materialize_governance_work_queue_state,
)


@dataclass(frozen=True)
class OracleOperatorWorkItem:
    work_item_key: str
    queue_key: str
    review_target: str
    priority_band: str
    review_due_by_utc: datetime
    review_sort_key: str
    claim_summary_line: str
    claim_primary_action_text: str
    claim_worker_lane: str
    claim_worker_summary_line: str
    claim_worker_sort_key: str
    claim_operability: str
    claim_operability_summary_line: str
    dispatch_posture: str
    dispatch_permitted: bool
    dispatch_claim_permitted_now: bool
    dispatch_claim_key: str
    dispatch_claim_urgency: str
    dispatch_claim_score: int
    dispatch_claim_summary_line: str
    lease_key: str
    lease_active_now: bool
    lease_summary_line: str
    lease_action: str
    lease_action_summary_line: str


@dataclass(frozen=True)
class OracleOperatorQueueSnapshot:
    queue_key: str
    review_target: str
    priority_band: str
    review_due_by_utc: datetime
    review_sort_key: str
    queue_summary_line: str
    queue_state: OracleGovernanceWorkQueueState
    primary_work_item: OracleOperatorWorkItem
    work_items: tuple[OracleOperatorWorkItem, ...]
    recommended_next_actions: tuple[str, ...]


@dataclass(frozen=True)
class OracleOperatorQueueSnapshotRequest:
    governance_work_queue: OracleGovernanceWorkQueueState


def build_operator_queue_snapshot_request(**kwargs) -> OracleOperatorQueueSnapshotRequest:
    return OracleOperatorQueueSnapshotRequest(**kwargs)


def _materialize_operator_work_item(queue_state: OracleGovernanceWorkQueueState) -> OracleOperatorWorkItem:
    claim = queue_state.governance_claim_envelope
    dispatch = queue_state.governance_dispatch_envelope
    return OracleOperatorWorkItem(
        work_item_key=claim.governance_plane_claim_sha256,
        queue_key=claim.governance_plane_claim_queue_key,
        review_target=claim.governance_plane_claim_review_target,
        priority_band=claim.governance_plane_claim_priority_band,
        review_due_by_utc=claim.governance_plane_claim_review_due_by_utc,
        review_sort_key=claim.governance_plane_claim_review_sort_key,
        claim_summary_line=claim.governance_plane_claim_summary_line,
        claim_primary_action_text=claim.governance_plane_claim_primary_action_text,
        claim_worker_lane=claim.governance_plane_claim_worker_lane,
        claim_worker_summary_line=claim.governance_plane_claim_worker_summary_line,
        claim_worker_sort_key=claim.governance_plane_claim_worker_sort_key,
        claim_operability=claim.governance_plane_claim_operability,
        claim_operability_summary_line=claim.governance_plane_claim_operability_summary_line,
        dispatch_posture=dispatch.governance_plane_dispatch_posture,
        dispatch_permitted=dispatch.governance_plane_dispatch_permitted,
        dispatch_claim_permitted_now=dispatch.governance_plane_dispatch_claim_permitted_now,
        dispatch_claim_key=dispatch.governance_plane_dispatch_claim_key,
        dispatch_claim_urgency=dispatch.governance_plane_dispatch_claim_urgency,
        dispatch_claim_score=dispatch.governance_plane_dispatch_claim_score,
        dispatch_claim_summary_line=dispatch.governance_plane_dispatch_claim_summary_line,
        lease_key=claim.governance_plane_claim_lease_key,
        lease_active_now=claim.governance_plane_claim_lease_active_now,
        lease_summary_line=claim.governance_plane_claim_lease_summary_line,
        lease_action=claim.governance_plane_claim_lease_action,
        lease_action_summary_line=claim.governance_plane_claim_lease_action_summary_line,
    )


def materialize_operator_queue_snapshot(
    request: OracleOperatorQueueSnapshotRequest | None = None,
    governance_work_queue: OracleGovernanceWorkQueueState | None = None,
    governance_work_queue_request: OracleGovernanceWorkQueueRequest | None = None,
    **kwargs,
) -> OracleOperatorQueueSnapshot:
    if request is not None:
        queue_state = request.governance_work_queue
    elif governance_work_queue is not None:
        queue_state = governance_work_queue
    else:
        queue_state = materialize_governance_work_queue_state(governance_work_queue_request, **kwargs)

    claim = queue_state.governance_claim_envelope
    item = _materialize_operator_work_item(queue_state)
    recommended_next_actions = tuple(
        action
        for action in (
            claim.governance_plane_claim_primary_action_text,
            queue_state.governance_plane.governance_plane_primary_action_text,
            *queue_state.governance_plane.governance_plane_actions,
        )
        if str(action).strip()
    )
    queue_summary_line = (
        f"Operator queue snapshot: queue_key={claim.governance_plane_claim_queue_key}; "
        f"review_target={claim.governance_plane_claim_review_target}; "
        f"priority_band={claim.governance_plane_claim_priority_band}; "
        f"dispatch_posture={queue_state.governance_dispatch_envelope.governance_plane_dispatch_posture}; "
        f"claim_operability={claim.governance_plane_claim_operability}."
    )
    return OracleOperatorQueueSnapshot(
        queue_key=claim.governance_plane_claim_queue_key,
        review_target=claim.governance_plane_claim_review_target,
        priority_band=claim.governance_plane_claim_priority_band,
        review_due_by_utc=claim.governance_plane_claim_review_due_by_utc,
        review_sort_key=claim.governance_plane_claim_review_sort_key,
        queue_summary_line=queue_summary_line,
        queue_state=queue_state,
        primary_work_item=item,
        work_items=(item,),
        recommended_next_actions=recommended_next_actions,
    )


__all__ = [
    'OracleOperatorQueueSnapshotRequest',
    'OracleOperatorQueueSnapshot',
    'OracleOperatorWorkItem',
    'build_operator_queue_snapshot_request',
    'materialize_operator_queue_snapshot',
]
