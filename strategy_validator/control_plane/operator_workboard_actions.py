from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from strategy_validator.control_plane.operator_queue_query import (
    OracleOperatorQueueQueryRequest,
    OracleOperatorQueueQueryResult,
    OracleOperatorQueueQueryWorkItem,
    run_operator_queue_query,
)
from strategy_validator.control_plane.operator_queue_snapshot import OracleOperatorQueueSnapshot, OracleOperatorQueueSnapshotRequest
from strategy_validator.control_plane.operator_queue_service import OracleGovernanceWorkQueueRequest, OracleGovernanceWorkQueueState


@dataclass(frozen=True)
class OracleOperatorWorkboardActionContractRequest:
    operator_queue_query_result: OracleOperatorQueueQueryResult
    board_label: str = 'default'


@dataclass(frozen=True)
class OracleOperatorWorkboardActionContractItem:
    work_item_key: str
    action_contract_key: str
    queue_key: str
    board_label: str
    review_target: str
    priority_band: str
    action_name: str
    action_state: str
    actor_lane: str
    dispatch_posture: str
    claim_operability: str
    permitted_now: bool
    rationale: str

    def to_payload(self) -> dict[str, Any]:
        return {
            'work_item_key': self.work_item_key,
            'action_contract_key': self.action_contract_key,
            'queue_key': self.queue_key,
            'board_label': self.board_label,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'action_name': self.action_name,
            'action_state': self.action_state,
            'actor_lane': self.actor_lane,
            'dispatch_posture': self.dispatch_posture,
            'claim_operability': self.claim_operability,
            'permitted_now': self.permitted_now,
            'rationale': self.rationale,
        }


@dataclass(frozen=True)
class OracleOperatorWorkboardActionContract:
    board_label: str
    queue_key: str
    review_target: str
    priority_band: str
    contract_count: int
    summary_line: str
    items: tuple[OracleOperatorWorkboardActionContractItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': 'oracle_operator_workboard_action_contract/v1',
            'board_label': self.board_label,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'contract_count': self.contract_count,
            'summary_line': self.summary_line,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_workboard_action_contract_request(**kwargs) -> OracleOperatorWorkboardActionContractRequest:
    return OracleOperatorWorkboardActionContractRequest(**kwargs)


def _to_contract_item(item: OracleOperatorQueueQueryWorkItem, board_label: str) -> OracleOperatorWorkboardActionContractItem:
    action_name = item.recommended_actions[0] if item.recommended_actions else item.claim_primary_action_text
    permitted_now = bool(item.dispatch_permitted and item.dispatch_claim_permitted_now)
    action_state = 'ACTION_EXECUTABLE' if permitted_now else 'ACTION_REVIEW_REQUIRED'
    return OracleOperatorWorkboardActionContractItem(
        work_item_key=item.work_item_key,
        action_contract_key=f"{item.work_item_key}:{board_label}",
        queue_key=item.queue_key,
        board_label=board_label,
        review_target=item.review_target,
        priority_band=item.priority_band,
        action_name=action_name,
        action_state=action_state,
        actor_lane=item.claim_worker_lane,
        dispatch_posture=item.dispatch_posture,
        claim_operability=item.claim_operability,
        permitted_now=permitted_now,
        rationale=item.claim_summary_line,
    )


def materialize_operator_workboard_action_contract(
    request: OracleOperatorWorkboardActionContractRequest | None = None,
    operator_queue_query_result: OracleOperatorQueueQueryResult | None = None,
    operator_queue_query_request: OracleOperatorQueueQueryRequest | None = None,
    operator_queue_snapshot: OracleOperatorQueueSnapshot | None = None,
    operator_queue_snapshot_request: OracleOperatorQueueSnapshotRequest | None = None,
    governance_work_queue: OracleGovernanceWorkQueueState | None = None,
    governance_work_queue_request: OracleGovernanceWorkQueueRequest | None = None,
    board_label: str = 'default',
    **kwargs,
) -> OracleOperatorWorkboardActionContract:
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
    items = tuple(_to_contract_item(item, board_label) for item in query.work_items)
    return OracleOperatorWorkboardActionContract(
        board_label=board_label,
        queue_key=query.queue_key,
        review_target=query.review_target,
        priority_band=query.priority_band,
        contract_count=len(items),
        summary_line=f"Operator action contract {board_label} exposes {len(items)} executable decision contract(s).",
        items=items,
    )


__all__ = [
    'OracleOperatorWorkboardActionContractRequest',
    'OracleOperatorWorkboardActionContractItem',
    'OracleOperatorWorkboardActionContract',
    'build_operator_workboard_action_contract_request',
    'materialize_operator_workboard_action_contract',
]
