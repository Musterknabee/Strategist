from __future__ import annotations

from typing import Any

from strategy_validator.control_plane.primitives.escalation import (
    classify_priority_band,
    is_escalated_status,
    summarize_escalation_posture,
)


def _get_attr(payload: Any, *names: str) -> Any:
    for name in names:
        if isinstance(payload, dict) and name in payload:
            return payload[name]
        if hasattr(payload, name):
            return getattr(payload, name)
    return None



def summarize_escalation_item(payload: Any) -> dict[str, Any]:
    priority_band = _get_attr(payload, 'priority_band', 'priority')
    status = _get_attr(payload, 'escalation_status', 'status')
    return {
        'priority_band': classify_priority_band(priority_band),
        'status': status,
        'is_escalated': is_escalated_status(status),
        'posture': summarize_escalation_posture(priority_band, status),
    }
