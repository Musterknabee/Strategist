from __future__ import annotations

from strategy_validator.contracts.operator_queue import (
    OracleOperatorQueueQueryRequest,
    OracleOperatorQueueQueryResult,
    OracleOperatorQueueQueryWorkItem,
    OracleOperatorQueueSnapshot,
    OracleOperatorQueueSnapshotRequest,
    OracleOperatorWorkboard,
    OracleOperatorWorkboardEntry,
    OracleOperatorWorkboardRequest,
)
from strategy_validator.control_plane.operator_queue_query import run_operator_queue_query
from strategy_validator.control_plane.operator_queue_service import (
    OracleGovernanceWorkQueueRequest,
    OracleGovernanceWorkQueueState,
)




def build_operator_workboard_request(**kwargs) -> OracleOperatorWorkboardRequest:
    return OracleOperatorWorkboardRequest(**kwargs)


def _materialize_workboard_entry(item: OracleOperatorQueueQueryWorkItem) -> OracleOperatorWorkboardEntry:
    return OracleOperatorWorkboardEntry(
        work_item_key=item.work_item_key,
        queue_key=item.queue_key,
        review_target=item.review_target,
        priority_band=item.priority_band,
        review_due_by_utc=item.review_due_by_utc,
        review_sort_key=item.review_sort_key,
        source_kind=item.source_kind,
        source_event_id=item.source_event_id,
        source_created_at_utc=item.source_created_at_utc,
        action_owner_lane=item.claim_worker_lane,
        claim_operability=item.claim_operability,
        dispatch_posture=item.dispatch_posture,
        urgency=item.dispatch_claim_urgency,
        score=item.dispatch_claim_score,
        summary_line=item.claim_summary_line,
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
        recommended_actions=item.recommended_actions,
    )


def materialize_operator_workboard(
    request: OracleOperatorWorkboardRequest | None = None,
    operator_queue_query_result: OracleOperatorQueueQueryResult | None = None,
    operator_queue_query_request: OracleOperatorQueueQueryRequest | None = None,
    operator_queue_snapshot: OracleOperatorQueueSnapshot | None = None,
    operator_queue_snapshot_request: OracleOperatorQueueSnapshotRequest | None = None,
    governance_work_queue: OracleGovernanceWorkQueueState | None = None,
    governance_work_queue_request: OracleGovernanceWorkQueueRequest | None = None,
    board_label: str = 'default',
    **kwargs,
) -> OracleOperatorWorkboard:
    if request is not None:
        query = request.operator_queue_query_result
        board_label = request.board_label
    elif operator_queue_query_result is not None:
        query = operator_queue_query_result
    else:
        query = run_operator_queue_query(
            request=operator_queue_query_request,
            operator_queue_snapshot=operator_queue_snapshot,
            operator_queue_snapshot_request=operator_queue_snapshot_request,
            governance_work_queue=governance_work_queue,
            governance_work_queue_request=governance_work_queue_request,
            **kwargs,
        )

    entries = tuple(_materialize_workboard_entry(item) for item in query.work_items)
    summary_line = (
        f"Operator workboard {board_label} tracks {query.work_item_count} active work item(s) "
        f"for {query.review_target} in priority band {query.priority_band}; "
        f"journal_primary_merge_pending_count={query.journal_primary_merge_pending_count}; "
        f"journal_auxiliary_merge_pending_count={query.journal_auxiliary_merge_pending_count}; "
        f"journal_post_merge_ready_count={query.journal_post_merge_ready_count}; "
        f"journal_post_merge_review_required_count={query.journal_post_merge_review_required_count}; "
        f"journal_post_merge_stale_count={query.journal_post_merge_stale_count}; "
        f"journal_downstream_closure_ready_count={query.journal_downstream_closure_ready_count}; "
        f"journal_downstream_closure_review_required_count={query.journal_downstream_closure_review_required_count}; "
        f"journal_downstream_closure_blocked_count={query.journal_downstream_closure_blocked_count}."
    )
    return OracleOperatorWorkboard(
        board_label=board_label,
        queue_key=query.queue_key,
        review_target=query.review_target,
        priority_band=query.priority_band,
        review_due_by_utc=query.review_due_by_utc,
        review_sort_key=query.review_sort_key,
        work_item_count=query.work_item_count,
        governed_work_item_count=query.governed_work_item_count,
        journaled_work_item_count=query.journaled_work_item_count,
        summary_line=summary_line,
        queue_summary_line=query.queue_summary_line,
        recommended_next_actions=query.recommended_next_actions,
        entries=entries,
        latest_journaled_action_at_utc=query.latest_journaled_action_at_utc,
        journal_operator_count=query.journal_operator_count,
        journal_action_count=query.journal_action_count,
        journal_projection_summary_line=query.journal_projection_summary_line,
        journal_primary_merge_pending_count=query.journal_primary_merge_pending_count,
        journal_auxiliary_merge_pending_count=query.journal_auxiliary_merge_pending_count,
        journal_post_merge_ready_count=query.journal_post_merge_ready_count,
        journal_post_merge_review_required_count=query.journal_post_merge_review_required_count,
        journal_post_merge_stale_count=query.journal_post_merge_stale_count,
        journal_downstream_closure_ready_count=query.journal_downstream_closure_ready_count,
        journal_downstream_closure_review_required_count=query.journal_downstream_closure_review_required_count,
        journal_downstream_closure_blocked_count=query.journal_downstream_closure_blocked_count,
        journal_projection_enabled=query.journal_projection_enabled,
        journal_projection_status_state=query.journal_projection_status_state,
        journal_projection_status_reason=query.journal_projection_status_reason,
        journal_projection_trust_status=query.journal_projection_trust_status,
        journal_projection_source_label=query.journal_projection_source_label,
        journal_projection_ledger_db_path_configured=query.journal_projection_ledger_db_path_configured,
    )


__all__ = [
    'OracleOperatorWorkboard',
    'OracleOperatorWorkboardEntry',
    'OracleOperatorWorkboardRequest',
    'build_operator_workboard_request',
    'materialize_operator_workboard',
]
