from __future__ import annotations

from pathlib import Path

from strategy_validator.application.operator_queue import build_governance_queue, query_operator_queue
from strategy_validator.control_plane.operator_queue_snapshot import materialize_operator_queue_snapshot
from strategy_validator.control_plane.operator_transition_policy import (
    build_operator_transition_policy_request,
    materialize_operator_transition_policy,
)
from strategy_validator.control_plane.operator_workboard import materialize_operator_workboard


def build_queue_snapshot(*args, **kwargs):
    queue_state = build_governance_queue(*args, **kwargs)
    return materialize_operator_queue_snapshot(governance_work_queue=queue_state)



def build_queue_query_payload(*args, **kwargs) -> dict:
    snapshot = build_queue_snapshot(*args, **kwargs)
    return query_operator_queue(operator_queue_snapshot=snapshot).to_payload()



def build_workboard_payload(*args, board_label: str = 'default', **kwargs) -> dict:
    snapshot = build_queue_snapshot(*args, **kwargs)
    return materialize_operator_workboard(operator_queue_snapshot=snapshot, board_label=board_label).to_payload()



def build_transition_policy_payload(*args, board_label: str = 'default', **kwargs) -> dict:
    snapshot = build_queue_snapshot(*args, **kwargs)
    query_result = query_operator_queue(operator_queue_snapshot=snapshot)
    return materialize_operator_transition_policy(
        build_operator_transition_policy_request(board_label=board_label),
        operator_queue_query_result=query_result,
        board_label=board_label,
    ).to_payload()
