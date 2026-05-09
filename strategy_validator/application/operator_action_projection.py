from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.projections.operator_action_event_index import build_operator_action_event_projection_index


def build_operator_action_event_index_payload(
    *,
    database_path: str | None = None,
    readonly: bool = True,
    operator_id: str | None = None,
    action: tuple[str, ...] | list[str] | None = None,
    status: tuple[str, ...] | list[str] | None = None,
    accepted: bool | None = None,
    control_plane_only: bool = False,
    issue_code: tuple[str, ...] | list[str] | None = None,
    authorization_role: str | None = None,
    review_target: str | None = None,
    work_item_key: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Build the operator-action projection payload for API/read-plane callers.

    API routes import this application wrapper instead of importing projections
    directly, preserving the route/application/projection boundary while giving
    the operator UI a stable append-only event journal read surface.
    """

    index = build_operator_action_event_projection_index(
        database_path=Path(database_path) if database_path else None,
        readonly=readonly,
        operator_id=operator_id,
        actions=tuple(action or ()),
        statuses=tuple(status or ()),
        accepted=accepted,
        control_plane_only=control_plane_only,
        issue_codes=tuple(issue_code or ()),
        authorization_role=authorization_role,
        review_target=review_target,
        work_item_key=work_item_key,
        limit=limit,
    )
    payload = index.to_payload()
    payload['read_model'] = 'operator_action_event_projection_index'
    payload['read_plane_only'] = True
    return payload


__all__ = ['build_operator_action_event_index_payload']
