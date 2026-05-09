"""Read-only clearance action register for semantic validator handoff operations.

This module is intentionally kept as a compatibility facade. The clearance
register implementation is decomposed into focused subphase modules for shared
helpers, action row synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_clearance_action_register_common import (
    _ACTION_STATE_RANK,
    _ACTION_TYPE_RANK,
    _LIMIT_MAX,
    _PRIORITY_RANK,
    _SCHEMA_VERSION,
    _SEVERITY_RANK,
    _as_list,
    _authority,
    _contains,
    _counts,
    _digest,
    _norm,
    _norm_set,
    _s,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_action_register_payload import (
    build_ui_semantic_validator_handoff_clearance_action_register_latest_payload,
    build_ui_semantic_validator_handoff_clearance_action_register_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_action_register_rows import (
    _action_state,
    _action_type,
    _completion_gate,
    _degraded,
    _haystack,
    _matches,
    _operator_action,
    _register_action,
    _sort_action,
    _verification_hint,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_operations_board import (
    build_ui_semantic_validator_handoff_clearance_operations_board_payload,
)

__all__ = [
    "build_ui_semantic_validator_handoff_clearance_action_register_payload",
    "build_ui_semantic_validator_handoff_clearance_action_register_latest_payload",
]
