from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from strategy_validator.control_plane.operator_queue_snapshot import (
    OracleOperatorQueueSnapshot,
    OracleOperatorQueueSnapshotRequest,
    materialize_operator_queue_snapshot,
)
from strategy_validator.control_plane.operator_queue_service import (
    OracleGovernanceWorkQueueRequest,
    OracleGovernanceWorkQueueState,
)


@dataclass(frozen=True)
class OracleOperatorQueueQueryRequest:
    operator_queue_snapshot: OracleOperatorQueueSnapshot


@dataclass(frozen=True)
class OracleOperatorQueueQueryWorkItem:
    work_item_key: str
    queue_key: str
    review_target: str
    priority_band: str
    review_due_by_utc: datetime
    review_sort_key: str
    claim_summary_line: str
    claim_primary_action_text: str
    claim_worker_lane: str
    claim_operability: str
    dispatch_posture: str
    dispatch_permitted: bool
    dispatch_claim_permitted_now: bool
    dispatch_claim_key: str
    dispatch_claim_urgency: str
    dispatch_claim_score: int
    lease_key: str
    lease_active_now: bool
    recommended_actions: tuple[str, ...]


@dataclass(frozen=True)
class OracleOperatorQueueQueryResult:
    queue_key: str
    review_target: str
    priority_band: str
    review_due_by_utc: datetime
    review_sort_key: str
    work_item_count: int
    summary_line: str
    queue_summary_line: str
    recommended_next_actions: tuple[str, ...]
    work_items: tuple[OracleOperatorQueueQueryWorkItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': 'oracle_operator_queue_query_report/v1',
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'review_due_by_utc': self.review_due_by_utc.isoformat(),
            'review_sort_key': self.review_sort_key,
            'work_item_count': self.work_item_count,
            'summary_line': self.summary_line,
            'queue_summary_line': self.queue_summary_line,
            'recommended_next_actions': list(self.recommended_next_actions),
            'work_items': [
                {
                    **asdict(item),
                    'review_due_by_utc': item.review_due_by_utc.isoformat(),
                    'recommended_actions': list(item.recommended_actions),
                }
                for item in self.work_items
            ],
        }


def build_operator_queue_query_request(**kwargs) -> OracleOperatorQueueQueryRequest:
    return OracleOperatorQueueQueryRequest(**kwargs)


def _materialize_query_work_item(
    snapshot: OracleOperatorQueueSnapshot,
    *,
    recommended_actions: tuple[str, ...],
) -> OracleOperatorQueueQueryWorkItem:
    item = snapshot.primary_work_item
    return OracleOperatorQueueQueryWorkItem(
        work_item_key=item.work_item_key,
        queue_key=item.queue_key,
        review_target=item.review_target,
        priority_band=item.priority_band,
        review_due_by_utc=item.review_due_by_utc,
        review_sort_key=item.review_sort_key,
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

    work_item_actions = tuple(
        action
        for action in (
            snapshot.primary_work_item.claim_primary_action_text,
            snapshot.primary_work_item.lease_action_summary_line,
            *snapshot.recommended_next_actions,
        )
        if str(action).strip()
    )
    work_item = _materialize_query_work_item(snapshot, recommended_actions=work_item_actions)
    summary_line = (
        f"Operator queue {snapshot.queue_key} targets {snapshot.review_target} in priority band "
        f"{snapshot.priority_band} with {len(snapshot.work_items)} active work item(s)."
    )
    return OracleOperatorQueueQueryResult(
        queue_key=snapshot.queue_key,
        review_target=snapshot.review_target,
        priority_band=snapshot.priority_band,
        review_due_by_utc=snapshot.review_due_by_utc,
        review_sort_key=snapshot.review_sort_key,
        work_item_count=len(snapshot.work_items),
        summary_line=summary_line,
        queue_summary_line=snapshot.queue_summary_line,
        recommended_next_actions=snapshot.recommended_next_actions,
        work_items=(work_item,),
    )


__all__ = [
    'OracleOperatorQueueQueryRequest',
    'OracleOperatorQueueQueryResult',
    'OracleOperatorQueueQueryWorkItem',
    'build_operator_queue_query_request',
    'run_operator_queue_query',
]
