from __future__ import annotations

from strategy_validator.application.operator_queue_materialization import (
    build_queue_query_result,
    build_transition_policy_state,
    build_workboard_state,
)
from strategy_validator.contracts.ui_workboard_dashboard import UiOperatorQueueQueryPayload, UiOperatorWorkboardPayload


def build_queue_query_payload(*args, **kwargs) -> dict:
    query_result = build_queue_query_result(*args, **kwargs)
    return UiOperatorQueueQueryPayload.from_mapping(query_result.to_payload()).to_payload()



def build_workboard_payload(*args, board_label: str = 'default', **kwargs) -> dict:
    workboard = build_workboard_state(*args, board_label=board_label, **kwargs)
    return UiOperatorWorkboardPayload.from_mapping(workboard.to_payload()).to_payload()



def build_transition_policy_payload(*args, board_label: str = 'default', **kwargs) -> dict:
    return build_transition_policy_state(*args, board_label=board_label, **kwargs).to_payload()


__all__ = [
    'build_queue_query_payload',
    'build_workboard_payload',
    'build_transition_policy_payload',
]
