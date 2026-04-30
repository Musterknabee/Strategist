"""Bounded query-normalization helpers for UI route workboard/export surfaces."""
from __future__ import annotations

from strategy_validator.contracts.ui_workboard_query import UiWorkboardQuery


def build_ui_workboard_query(
    *,
    board_label: str = 'operator',
    search_root: str | None = None,
    pack_kind: list[str] | None = None,
    trust_status: list[str] | None = None,
) -> UiWorkboardQuery:
    return UiWorkboardQuery(
        board_label=board_label,
        search_root=search_root,
        pack_kinds=list(pack_kind or ()),
        trust_statuses=list(trust_status or ()),
    )


__all__ = ['build_ui_workboard_query']
