from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from strategy_validator.application.ui_projection_surfaces import build_ui_projection_read_model
from strategy_validator.application.operator_queue_commands import build_transition_policy_payload, build_workboard_payload
from strategy_validator.application.ui_workboard_intelligence import build_workboard_intelligence


def build_ui_workboard_context(
    *,
    board_label: str = "operator",
    search_root: str | Path | None = None,
    pack_kinds: Iterable[str] = (),
    trust_statuses: Iterable[str] = (),
) -> dict[str, Any]:
    workboard = build_workboard_payload(board_label=board_label)
    root = Path(search_root) if search_root is not None else Path.cwd()
    workbench = build_ui_projection_read_model(
        search_root=root,
        pack_kinds=list(pack_kinds),
        trust_statuses=list(trust_statuses),
    )
    intelligence = build_workboard_intelligence(workboard=workboard, workbench=workbench)
    return {
        "workboard": workboard,
        "workbench": workbench,
        "intelligence": intelligence,
    }


def build_ui_workboard_dashboard_context(
    *,
    board_label: str,
    context: dict[str, Any],
    transition_policy: dict[str, Any],
) -> dict[str, Any]:
    return {
        "board_label": board_label,
        "workboard": dict(context["workboard"]),
        "workbench": dict(context["workbench"]),
        "intelligence": dict(context["intelligence"]),
        "transition_policy": dict(transition_policy),
    }


def build_ui_workboard_export_context(*, board_label: str, context: dict[str, Any]) -> dict[str, Any]:
    return {
        "board_label": board_label,
        "workboard": dict(context["workboard"]),
        "workbench": dict(context["workbench"]),
        "intelligence": dict(context["intelligence"]),
    }


__all__ = [
    "build_ui_workboard_context",
    "build_ui_workboard_dashboard_context",
    "build_ui_workboard_export_context",
]
