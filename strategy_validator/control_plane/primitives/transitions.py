from __future__ import annotations

ALLOWED_TRANSITIONS = {
    'QUEUED': {'ASSIGNED', 'ESCALATED', 'CANCELLED'},
    'ASSIGNED': {'ACKNOWLEDGED', 'ESCALATED', 'COMPLETED', 'CANCELLED'},
    'ACKNOWLEDGED': {'EXECUTED', 'ESCALATED', 'COMPLETED'},
    'EXECUTED': {'COMPLETED', 'ESCALATED'},
    'ESCALATED': {'RETURNED', 'COMPLETED'},
    'RETURNED': {'QUEUED', 'ASSIGNED', 'COMPLETED'},
    'COMPLETED': set(),
    'CANCELLED': set(),
}



def normalize_transition_state(state: str | None, *, default: str = 'QUEUED') -> str:
    normalized = (state or default).strip().upper()
    return normalized or default



def is_transition_allowed(current_state: str | None, desired_state: str | None) -> bool:
    current = normalize_transition_state(current_state)
    desired = normalize_transition_state(desired_state, default=current)
    if current == desired:
        return True
    return desired in ALLOWED_TRANSITIONS.get(current, set())
