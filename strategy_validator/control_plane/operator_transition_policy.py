from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from strategy_validator.control_plane.operator_workboard_actions import (
    OracleOperatorWorkboardActionContract,
    OracleOperatorWorkboardActionContractItem,
    materialize_operator_workboard_action_contract,
)


@dataclass(frozen=True)
class OracleOperatorTransitionPolicyRequest:
    board_label: str = 'default'


@dataclass(frozen=True)
class OracleOperatorTransitionPolicyItem:
    action_contract_key: str
    work_item_key: str
    policy_key: str
    current_action_state: str
    policy_decision: str
    default_transition: str
    allowed_transitions: tuple[str, ...]
    rationale: str

    def to_payload(self) -> dict[str, Any]:
        return {
            'action_contract_key': self.action_contract_key,
            'work_item_key': self.work_item_key,
            'policy_key': self.policy_key,
            'current_action_state': self.current_action_state,
            'policy_decision': self.policy_decision,
            'default_transition': self.default_transition,
            'allowed_transitions': list(self.allowed_transitions),
            'rationale': self.rationale,
        }


@dataclass(frozen=True)
class OracleOperatorTransitionPolicy:
    schema_version: str
    board_label: str
    queue_key: str
    review_target: str
    priority_band: str
    policy_count: int
    summary_line: str
    items: tuple[OracleOperatorTransitionPolicyItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'policy_count': self.policy_count,
            'summary_line': self.summary_line,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_transition_policy_request(**kwargs: Any) -> OracleOperatorTransitionPolicyRequest:
    return OracleOperatorTransitionPolicyRequest(**kwargs)


def _policy_for_item(item: OracleOperatorWorkboardActionContractItem) -> OracleOperatorTransitionPolicyItem:
    if item.claim_operability != 'CLAIM_INOPERABLE':
        decision = 'ALLOW_EXECUTION'
        default_transition = 'EXECUTED'
        allowed = ('ACKNOWLEDGED', 'EXECUTED')
        rationale = f'{item.work_item_key} remains operator-executable under the current governance posture.'
    elif item.dispatch_posture in {'DISPATCH_BLOCKED', 'ESCALATE'} or item.claim_operability == 'CLAIM_INOPERABLE':
        decision = 'ESCALATION_ONLY'
        default_transition = 'ESCALATED'
        allowed = ('ACKNOWLEDGED', 'ESCALATED')
        rationale = f'{item.work_item_key} requires escalation because direct execution is not currently permitted.'
    else:
        decision = 'RECORD_ONLY'
        default_transition = 'ACKNOWLEDGED'
        allowed = ('ACKNOWLEDGED',)
        rationale = f'{item.work_item_key} may be recorded but not executed yet.'
    return OracleOperatorTransitionPolicyItem(
        action_contract_key=item.action_contract_key,
        work_item_key=item.work_item_key,
        policy_key=f'policy:{item.action_contract_key}',
        current_action_state=item.action_state,
        policy_decision=decision,
        default_transition=default_transition,
        allowed_transitions=allowed,
        rationale=rationale,
    )


def materialize_operator_transition_policy(
    request: OracleOperatorTransitionPolicyRequest | None = None,
    action_contract: OracleOperatorWorkboardActionContract | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorTransitionPolicy:
    if request is not None:
        board_label = request.board_label
    if action_contract is None:
        action_contract = materialize_operator_workboard_action_contract(
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    items = tuple(_policy_for_item(item) for item in action_contract.items)
    return OracleOperatorTransitionPolicy(
        schema_version='oracle_operator_transition_policy/v1',
        board_label=action_contract.board_label,
        queue_key=action_contract.queue_key,
        review_target=action_contract.review_target,
        priority_band=action_contract.priority_band,
        policy_count=len(items),
        summary_line=f'Operator transition policy {action_contract.board_label} exposes {len(items)} governed transition policy item(s).',
        items=items,
    )


__all__ = [
    'OracleOperatorTransitionPolicy',
    'OracleOperatorTransitionPolicyItem',
    'OracleOperatorTransitionPolicyRequest',
    'build_operator_transition_policy_request',
    'materialize_operator_transition_policy',
]
