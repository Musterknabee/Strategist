from __future__ import annotations

from strategy_validator.contracts.operator_queue import (
    OracleOperatorQueueSnapshot,
    OracleOperatorQueueSnapshotRequest,
    OracleOperatorWorkItem,
)
from strategy_validator.control_plane.operator_queue_service import (
    OracleGovernanceWorkQueueRequest,
    OracleGovernanceWorkQueueState,
    materialize_governance_work_queue_state,
)
from strategy_validator.projections.operator_action_workboard import materialize_operator_action_workboard_projection


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
        source_kind='GOVERNED_PRIMARY',
        source_event_id=None,
        source_created_at_utc=None,
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
    journal_projection = materialize_operator_action_workboard_projection(queue_state)
    journal_items = journal_projection.work_items
    work_items = (item, *journal_items)
    recommended_next_actions = tuple(dict.fromkeys(
        action
        for action in (
            claim.governance_plane_claim_primary_action_text,
            queue_state.governance_plane.governance_plane_primary_action_text,
            *queue_state.governance_plane.governance_plane_actions,
            *journal_projection.recommended_next_actions,
            *(journal_item.claim_primary_action_text for journal_item in journal_items),
        )
        if str(action).strip()
    ))
    latest_journal_text = (
        journal_projection.latest_action_created_at_utc.isoformat()
        if journal_projection.latest_action_created_at_utc is not None
        else 'none'
    )
    queue_summary_line = (
        f"Operator queue snapshot: queue_key={claim.governance_plane_claim_queue_key}; "
        f"review_target={claim.governance_plane_claim_review_target}; "
        f"priority_band={claim.governance_plane_claim_priority_band}; "
        f"dispatch_posture={queue_state.governance_dispatch_envelope.governance_plane_dispatch_posture}; "
        f"claim_operability={claim.governance_plane_claim_operability}; "
        f"journal_projection_count={journal_projection.projected_work_item_count}; "
        f"journal_operator_count={journal_projection.operator_count}; "
        f"journal_action_count={journal_projection.action_count}; "
        f"journal_primary_merge_pending_count={journal_projection.primary_merge_pending_count}; "
        f"journal_auxiliary_merge_pending_count={journal_projection.auxiliary_merge_pending_count}; "
        f"journal_post_merge_ready_count={journal_projection.post_merge_ready_count}; "
        f"journal_post_merge_review_required_count={journal_projection.post_merge_review_required_count}; "
        f"journal_post_merge_stale_count={journal_projection.post_merge_stale_count}; "
        f"journal_downstream_closure_ready_count={journal_projection.downstream_closure_ready_count}; "
        f"journal_downstream_closure_review_required_count={journal_projection.downstream_closure_review_required_count}; "
        f"journal_downstream_closure_blocked_count={journal_projection.downstream_closure_blocked_count}; "
        f"latest_journaled_action_at_utc={latest_journal_text}; "
        f"work_item_count={len(work_items)}."
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
        work_items=work_items,
        recommended_next_actions=recommended_next_actions,
        latest_journaled_action_at_utc=journal_projection.latest_action_created_at_utc,
        journal_operator_count=journal_projection.operator_count,
        journal_action_count=journal_projection.action_count,
        journal_projection_summary_line=journal_projection.summary_line,
        journal_primary_merge_pending_count=journal_projection.primary_merge_pending_count,
        journal_auxiliary_merge_pending_count=journal_projection.auxiliary_merge_pending_count,
        journal_post_merge_ready_count=journal_projection.post_merge_ready_count,
        journal_post_merge_review_required_count=journal_projection.post_merge_review_required_count,
        journal_post_merge_stale_count=journal_projection.post_merge_stale_count,
        journal_downstream_closure_ready_count=journal_projection.downstream_closure_ready_count,
        journal_downstream_closure_review_required_count=journal_projection.downstream_closure_review_required_count,
        journal_downstream_closure_blocked_count=journal_projection.downstream_closure_blocked_count,
        journal_projection_enabled=journal_projection.projection_enabled,
        journal_projection_status_state=journal_projection.projection_status_state,
        journal_projection_status_reason=journal_projection.projection_status_reason,
        journal_projection_trust_status=journal_projection.projection_trust_status,
        journal_projection_source_label=journal_projection.projection_source_label,
        journal_projection_ledger_db_path_configured=journal_projection.projection_ledger_db_path_configured,
    )


__all__ = [
    'OracleOperatorQueueSnapshotRequest',
    'OracleOperatorQueueSnapshot',
    'OracleOperatorWorkItem',
    'build_operator_queue_snapshot_request',
    'materialize_operator_queue_snapshot',
]
