"""Read-only continuity cockpit for semantic validator handoff closure chains.

This module is intentionally kept as a compatibility facade. Continuity
implementation is decomposed into focused subphase modules for shared helpers,
row synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_closure import (
    build_ui_semantic_validator_handoff_closure_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_continuity_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _STAGES,
    _as_list,
    _authority,
    _contains,
    _counts,
    _norm,
    _norm_set,
    _s,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_continuity_payload import (
    build_ui_semantic_validator_handoff_continuity_latest_payload,
    build_ui_semantic_validator_handoff_continuity_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_continuity_rows import (
    _continuity_row,
    _current_stage,
    _haystack,
    _matches,
    _stage_record,
    _terminal_status,
)

__all__ = [
    "build_ui_semantic_validator_handoff_continuity_payload",
    "build_ui_semantic_validator_handoff_continuity_latest_payload",
]
