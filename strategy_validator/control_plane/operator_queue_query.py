from __future__ import annotations

from strategy_validator.contracts.operator_queue import (
    OracleOperatorQueueQueryRequest,
    OracleOperatorQueueQueryResult,
    OracleOperatorQueueQueryWorkItem,
    OracleOperatorQueueSnapshot,
    OracleOperatorQueueSnapshotRequest,
)
from strategy_validator.control_plane.operator_queue_snapshot import materialize_operator_queue_snapshot
from strategy_validator.control_plane.operator_queue_service import (
    OracleGovernanceWorkQueueRequest,
    OracleGovernanceWorkQueueState,
)


def build_operator_queue_query_request(**kwargs) -> OracleOperatorQueueQueryRequest:
    return OracleOperatorQueueQueryRequest(**kwargs)


def _materialize_query_work_item(
    item,
    *,
    recommended_actions: tuple[str, ...],
) -> OracleOperatorQueueQueryWorkItem:
    return OracleOperatorQueueQueryWorkItem(
        work_item_key=item.work_item_key,
        queue_key=item.queue_key,
        review_target=item.review_target,
        priority_band=item.priority_band,
        review_due_by_utc=item.review_due_by_utc,
        review_sort_key=item.review_sort_key,
        source_kind=item.source_kind,
        source_event_id=item.source_event_id,
        source_created_at_utc=item.source_created_at_utc,
        claim_summary_line=item.claim_summary_line,
        claim_primary_action_text=item.claim_primary_action_text,
        claim_worker_lane=item.claim_worker_lane,
        claim_operability=item.claim_operability,
        dispatch_posture=item.dispatch_posture,
        dispatch_permitted=item.dispatch_permitted,
        dispatch_claim_permitted_now=item.dispatch_claim_permitted_now,
        dispatch_claim_key=item.dispatch_claim_key,
        dispatch_claim_urgency=item.dispatch_claim_urgency,
        dispatch_claim_score=item.dispatch_claim_score,
        lease_key=item.lease_key,
        lease_active_now=item.lease_active_now,
        projected_operator_id=item.projected_operator_id,
        projected_action_name=item.projected_action_name,
        projection_generated_at_utc=item.projection_generated_at_utc,
        projection_age_seconds=item.projection_age_seconds,
        projection_freshness_state=item.projection_freshness_state,
        projection_summary_line=item.projection_summary_line,
        projection_governed_merge_state=item.projection_governed_merge_state,
        projection_governed_queue_key=item.projection_governed_queue_key,
        projection_governed_priority_band=item.projection_governed_priority_band,
        projection_governed_dispatch_posture=item.projection_governed_dispatch_posture,
        projection_governed_summary_line=item.projection_governed_summary_line,
        projection_post_merge_lifecycle_state=item.projection_post_merge_lifecycle_state,
        projection_post_merge_summary_line=item.projection_post_merge_summary_line,
        projection_downstream_closure_state=item.projection_downstream_closure_state,
        projection_downstream_closure_summary_line=item.projection_downstream_closure_summary_line,
        recommended_actions=recommended_actions,
    )


def run_operator_queue_query(
    request: OracleOperatorQueueQueryRequest | None = None,
    operator_queue_snapshot: OracleOperatorQueueSnapshot | None = None,
    operator_queue_snapshot_request: OracleOperatorQueueSnapshotRequest | None = None,
    governance_work_queue: OracleGovernanceWorkQueueState | None = None,
    governance_work_queue_request: OracleGovernanceWorkQueueRequest | None = None,
    **kwargs,
) -> OracleOperatorQueueQueryResult:
    if request is not None:
        snapshot = request.operator_queue_snapshot
    elif operator_queue_snapshot is not None:
        snapshot = operator_queue_snapshot
    else:
        snapshot = materialize_operator_queue_snapshot(
            request=operator_queue_snapshot_request,
            governance_work_queue=governance_work_queue,
            governance_work_queue_request=governance_work_queue_request,
            **kwargs,
        )

    work_items = []
    for item in snapshot.work_items:
        base_actions = item.projection_recommended_actions if item.source_kind == 'JOURNALED_PENDING' else (item.claim_primary_action_text,)
        work_item_actions = tuple(dict.fromkeys(
            action
            for action in (
                *base_actions,
                *snapshot.recommended_next_actions,
            )
            if str(action).strip()
        ))
        work_items.append(_materialize_query_work_item(item, recommended_actions=work_item_actions))
    governed_count = sum(1 for item in snapshot.work_items if item.source_kind == 'GOVERNED_PRIMARY')
    journaled_count = sum(1 for item in snapshot.work_items if item.source_kind == 'JOURNALED_PENDING')
    summary_line = (
        f"Operator queue {snapshot.queue_key} targets {snapshot.review_target} in priority band "
        f"{snapshot.priority_band} with {len(snapshot.work_items)} active work item(s): "
        f"{governed_count} governed and {journaled_count} journal-backed; "
        f"journal_operator_count={snapshot.journal_operator_count}; journal_action_count={snapshot.journal_action_count}; "
        f"journal_primary_merge_pending_count={snapshot.journal_primary_merge_pending_count}; journal_auxiliary_merge_pending_count={snapshot.journal_auxiliary_merge_pending_count}; "
        f"journal_post_merge_ready_count={snapshot.journal_post_merge_ready_count}; journal_post_merge_review_required_count={snapshot.journal_post_merge_review_required_count}; journal_post_merge_stale_count={snapshot.journal_post_merge_stale_count}; "
        f"journal_downstream_closure_ready_count={snapshot.journal_downstream_closure_ready_count}; journal_downstream_closure_review_required_count={snapshot.journal_downstream_closure_review_required_count}; journal_downstream_closure_blocked_count={snapshot.journal_downstream_closure_blocked_count}; "
        f"journal_projection_status={snapshot.journal_projection_status_state}; "
        f"projection_summary={snapshot.journal_projection_summary_line or 'none'}."
    )
    return OracleOperatorQueueQueryResult(
        queue_key=snapshot.queue_key,
        review_target=snapshot.review_target,
        priority_band=snapshot.priority_band,
        review_due_by_utc=snapshot.review_due_by_utc,
        review_sort_key=snapshot.review_sort_key,
        work_item_count=len(snapshot.work_items),
        governed_work_item_count=governed_count,
        journaled_work_item_count=journaled_count,
        summary_line=summary_line,
        queue_summary_line=snapshot.queue_summary_line,
        recommended_next_actions=snapshot.recommended_next_actions,
        work_items=tuple(work_items),
        latest_journaled_action_at_utc=snapshot.latest_journaled_action_at_utc,
        journal_operator_count=snapshot.journal_operator_count,
        journal_action_count=snapshot.journal_action_count,
        journal_projection_summary_line=snapshot.journal_projection_summary_line,
        journal_primary_merge_pending_count=snapshot.journal_primary_merge_pending_count,
        journal_auxiliary_merge_pending_count=snapshot.journal_auxiliary_merge_pending_count,
        journal_post_merge_ready_count=snapshot.journal_post_merge_ready_count,
        journal_post_merge_review_required_count=snapshot.journal_post_merge_review_required_count,
        journal_post_merge_stale_count=snapshot.journal_post_merge_stale_count,
        journal_downstream_closure_ready_count=snapshot.journal_downstream_closure_ready_count,
        journal_downstream_closure_review_required_count=snapshot.journal_downstream_closure_review_required_count,
        journal_downstream_closure_blocked_count=snapshot.journal_downstream_closure_blocked_count,
        journal_projection_enabled=snapshot.journal_projection_enabled,
        journal_projection_status_state=snapshot.journal_projection_status_state,
        journal_projection_status_reason=snapshot.journal_projection_status_reason,
        journal_projection_trust_status=snapshot.journal_projection_trust_status,
        journal_projection_source_label=snapshot.journal_projection_source_label,
        journal_projection_ledger_db_path_configured=snapshot.journal_projection_ledger_db_path_configured,
    )


__all__ = [
    'OracleOperatorQueueQueryRequest',
    'OracleOperatorQueueQueryResult',
    'OracleOperatorQueueQueryWorkItem',
    'build_operator_queue_query_request',
    'run_operator_queue_query',
]
