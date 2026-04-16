from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from strategy_validator.control_plane.operator_queue_query import (
    OracleOperatorQueueQueryRequest,
    OracleOperatorQueueQueryResult,
    OracleOperatorQueueQueryWorkItem,
    run_operator_queue_query,
)
from strategy_validator.control_plane.operator_queue_snapshot import (
    OracleOperatorQueueSnapshot,
    OracleOperatorQueueSnapshotRequest,
)
from strategy_validator.control_plane.operator_queue_service import (
    OracleGovernanceWorkQueueRequest,
    OracleGovernanceWorkQueueState,
)


@dataclass(frozen=True)
class OracleOperatorWorkboardRequest:
    operator_queue_query_result: OracleOperatorQueueQueryResult
    board_label: str = 'default'


@dataclass(frozen=True)
class OracleOperatorWorkboardEntry:
    work_item_key: str
    queue_key: str
    review_target: str
    priority_band: str
    review_due_by_utc: datetime
    review_sort_key: str
    action_owner_lane: str
    claim_operability: str
    dispatch_posture: str
    urgency: str
    score: int
    summary_line: str
    recommended_actions: tuple[str, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'work_item_key': self.work_item_key,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'review_due_by_utc': self.review_due_by_utc.isoformat(),
            'review_sort_key': self.review_sort_key,
            'action_owner_lane': self.action_owner_lane,
            'claim_operability': self.claim_operability,
            'dispatch_posture': self.dispatch_posture,
            'urgency': self.urgency,
            'score': self.score,
            'summary_line': self.summary_line,
            'recommended_actions': list(self.recommended_actions),
        }


@dataclass(frozen=True)
class OracleOperatorWorkboard:
    board_label: str
    queue_key: str
    review_target: str
    priority_band: str
    review_due_by_utc: datetime
    review_sort_key: str
    work_item_count: int
    summary_line: str
    queue_summary_line: str
    recommended_next_actions: tuple[str, ...]
    entries: tuple[OracleOperatorWorkboardEntry, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': 'oracle_operator_workboard/v1',
            'board_label': self.board_label,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'review_due_by_utc': self.review_due_by_utc.isoformat(),
            'review_sort_key': self.review_sort_key,
            'work_item_count': self.work_item_count,
            'summary_line': self.summary_line,
            'queue_summary_line': self.queue_summary_line,
            'recommended_next_actions': list(self.recommended_next_actions),
            'entries': [entry.to_payload() for entry in self.entries],
        }


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
        action_owner_lane=item.claim_worker_lane,
        claim_operability=item.claim_operability,
        dispatch_posture=item.dispatch_posture,
        urgency=item.dispatch_claim_urgency,
        score=item.dispatch_claim_score,
        summary_line=item.claim_summary_line,
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
        f"for {query.review_target} in priority band {query.priority_band}."
    )
    return OracleOperatorWorkboard(
        board_label=board_label,
        queue_key=query.queue_key,
        review_target=query.review_target,
        priority_band=query.priority_band,
        review_due_by_utc=query.review_due_by_utc,
        review_sort_key=query.review_sort_key,
        work_item_count=query.work_item_count,
        summary_line=summary_line,
        queue_summary_line=query.queue_summary_line,
        recommended_next_actions=query.recommended_next_actions,
        entries=entries,
    )


__all__ = [
    'OracleOperatorWorkboard',
    'OracleOperatorWorkboardEntry',
    'OracleOperatorWorkboardRequest',
    'build_operator_workboard_request',
    'materialize_operator_workboard',
]
