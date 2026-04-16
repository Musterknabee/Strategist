from __future__ import annotations

from typing import Any

from strategy_validator.control_plane.primitives.claims import (
    is_active_lease_state,
    is_claimed_state,
    summarize_claim_lease_posture,
)


def _get_attr(payload: Any, *names: str) -> Any:
    for name in names:
        if isinstance(payload, dict) and name in payload:
            return payload[name]
        if hasattr(payload, name):
            return getattr(payload, name)
    return None



def summarize_claim_item(payload: Any) -> dict[str, Any]:
    claim_state = _get_attr(payload, 'claim_state')
    lease_state = _get_attr(payload, 'lease_state')
    pack_kind = _get_attr(payload, 'pack_kind')
    manifest_path = _get_attr(payload, 'latest_manifest_path', 'manifest_path')
    return {
        'pack_kind': pack_kind,
        'manifest_path': manifest_path,
        'claim_state': claim_state,
        'lease_state': lease_state,
        'is_claimed': is_claimed_state(claim_state),
        'has_active_lease': is_active_lease_state(lease_state),
        'posture': summarize_claim_lease_posture(claim_state, lease_state),
    }



def summarize_claim_items(items: list[Any] | tuple[Any, ...]) -> list[dict[str, Any]]:
    return [summarize_claim_item(item) for item in items]
