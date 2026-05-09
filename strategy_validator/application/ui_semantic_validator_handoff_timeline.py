"""Read-only timeline cockpit for semantic validator handoff continuity chains.

This module is intentionally kept as a compatibility facade. Timeline
implementation is decomposed into focused subphase modules for shared helpers,
event-row synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_continuity import (
    build_ui_semantic_validator_handoff_continuity_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_timeline_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _STAGE_ORDER,
    _as_list,
    _authority,
    _contains,
    _counts,
    _norm,
    _norm_set,
    _s,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_timeline_payload import (
    build_ui_semantic_validator_handoff_timeline_latest_payload,
    build_ui_semantic_validator_handoff_timeline_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_timeline_rows import (
    _event_severity,
    _event_state,
    _haystack,
    _matches,
    _operator_focus,
    _timeline_event,
    _timeline_events,
)

__all__ = [
    "build_ui_semantic_validator_handoff_timeline_payload",
    "build_ui_semantic_validator_handoff_timeline_latest_payload",
]
