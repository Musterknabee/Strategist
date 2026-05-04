from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.projections.operator_action_event_index import build_operator_action_event_projection_index


def build_operator_action_event_index_payload(
    *,
    database_path: str | None = None,
    readonly: bool = True,
) -> dict[str, Any]:
    """Build the operator-action projection payload for API/read-plane callers.

    API routes import this application wrapper instead of importing projections
    directly, preserving the route/application/projection boundary while giving
    the future operator UI a stable append-only event read surface.
    """

    index = build_operator_action_event_projection_index(
        database_path=Path(database_path) if database_path else None,
        readonly=readonly,
    )
    payload = index.to_payload()
    payload['read_model'] = 'operator_action_event_projection_index'
    payload['readonly'] = readonly
    return payload


__all__ = ['build_operator_action_event_index_payload']
