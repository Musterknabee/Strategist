from __future__ import annotations

import pytest

from strategy_validator.core.enums import PromotionState
from strategy_validator.core.exceptions import IllegalPromotionStateTransition
from strategy_validator.ledger.writer import _validate_state_transition


def test_quarantined_state_allows_forward_and_degrade_paths() -> None:
    allowed = {
        PromotionState.QUARANTINED,
        PromotionState.REJECTED,
        PromotionState.INVALID,
        PromotionState.CONDITIONAL,
        PromotionState.CANARY_ONLY,
        PromotionState.PROMOTABLE,
    }
    for next_state in allowed:
        _validate_state_transition(PromotionState.QUARANTINED.name, next_state.name)


def test_rejected_state_cannot_return_to_promotable_flow() -> None:
    with pytest.raises(IllegalPromotionStateTransition):
        _validate_state_transition(PromotionState.REJECTED.name, PromotionState.PROMOTABLE.name)
