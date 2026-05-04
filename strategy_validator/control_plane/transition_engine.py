from __future__ import annotations

from strategy_validator.control_plane.primitives.transitions import (
    is_transition_allowed,
    normalize_transition_state,
)


def evaluate_transition(*, current_state: str | None, desired_state: str | None) -> dict[str, str | bool]:
    current = normalize_transition_state(current_state)
    desired = normalize_transition_state(desired_state, default=current)
    return {
        'current_state': current,
        'desired_state': desired,
        'allowed': is_transition_allowed(current, desired),
    }
