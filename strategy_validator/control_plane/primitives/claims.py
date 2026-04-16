from __future__ import annotations


def _normalize(value: str | None, default: str = '') -> str:
    return (value or default).strip().upper()


CLAIMED_STATES = {'CLAIMED', 'CLAIM_ACTIVE', 'CLAIM_HELD', 'CLAIM_ASSIGNED'}
UNCLAIMED_STATES = {'UNCLAIMED', 'CLAIM_UNCLAIMED', 'UNASSIGNED', 'NONE', ''}
ACTIVE_LEASE_STATES = {'LEASE_ACTIVE', 'ACTIVE', 'ACKNOWLEDGED', 'LEASE_HELD'}


def is_claimed_state(state: str | None) -> bool:
    normalized = _normalize(state)
    if normalized in CLAIMED_STATES:
        return True
    if normalized in UNCLAIMED_STATES:
        return False
    return 'CLAIM' in normalized and 'UN' not in normalized



def is_active_lease_state(state: str | None) -> bool:
    normalized = _normalize(state)
    if normalized in ACTIVE_LEASE_STATES:
        return True
    return normalized.startswith('LEASE_') and 'EXPIRED' not in normalized and 'NO_' not in normalized



def summarize_claim_lease_posture(claim_state: str | None, lease_state: str | None) -> str:
    claimed = is_claimed_state(claim_state)
    leased = is_active_lease_state(lease_state)
    if claimed and leased:
        return 'CLAIMED_AND_LEASED'
    if claimed:
        return 'CLAIMED_AWAITING_LEASE'
    if leased:
        return 'LEASE_ONLY_ANOMALY'
    return 'UNCLAIMED'
