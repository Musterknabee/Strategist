from __future__ import annotations

from datetime import datetime, timezone

from strategy_validator.application.operator_queue import build_governance_queue, query_operator_queue
from strategy_validator.control_plane.operator_queue_snapshot import materialize_operator_queue_snapshot
from strategy_validator.control_plane.operator_transition_policy import (
    build_operator_transition_policy_request,
    materialize_operator_transition_policy,
)
from strategy_validator.control_plane.operator_workboard import materialize_operator_workboard


def build_queue_snapshot(*args, **kwargs):
    kwargs.setdefault("issued_at_utc", datetime.now(timezone.utc))
    kwargs.setdefault("surface_label", "operator_queue_materialization")
    queue_state = build_governance_queue(*args, **kwargs)
    return materialize_operator_queue_snapshot(governance_work_queue=queue_state)



def build_queue_query_result(*args, **kwargs):
    snapshot = build_queue_snapshot(*args, **kwargs)
    return query_operator_queue(operator_queue_snapshot=snapshot)



def build_workboard_state(*args, board_label: str = 'default', **kwargs):
    snapshot = build_queue_snapshot(*args, **kwargs)
    return materialize_operator_workboard(operator_queue_snapshot=snapshot, board_label=board_label)



def build_transition_policy_state(*args, board_label: str = 'default', **kwargs):
    query_result = build_queue_query_result(*args, **kwargs)
    return materialize_operator_transition_policy(
        build_operator_transition_policy_request(board_label=board_label),
        operator_queue_query_result=query_result,
        board_label=board_label,
    )


__all__ = [
    'build_queue_snapshot',
    'build_queue_query_result',
    'build_workboard_state',
    'build_transition_policy_state',
]
