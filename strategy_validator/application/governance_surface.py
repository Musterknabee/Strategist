from __future__ import annotations

from strategy_validator.application.operator_queue import (
    build_governance_queue_state as _build_governance_queue_state,
    build_workboard_action_contract_payload as _build_workboard_action_contract_payload,
)


def build_governance_queue_state(**kwargs):
    """Compatibility wrapper for the canonical operator queue governance surface."""
    return _build_governance_queue_state(**kwargs)



def build_workboard_action_contract_payload(*, board_label: str = 'default', **queue_kwargs) -> dict:
    """Compatibility wrapper for the canonical operator queue action-contract surface."""
    return _build_workboard_action_contract_payload(board_label=board_label, **queue_kwargs)


__all__ = [
    'build_governance_queue_state',
    'build_workboard_action_contract_payload',
]
