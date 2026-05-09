"""Read-only clearance operations board for semantic validator handoff coverage.

This module is intentionally kept as a compatibility facade. The clearance
operations implementation is decomposed into focused subphase modules for shared
helpers, operation-card synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_clearance_coverage_board import (
    build_ui_semantic_validator_handoff_clearance_coverage_board_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_operations_board_common import (
    _ACTION_GROUP_RANK,
    _LIMIT_MAX,
    _OPERATION_STATE_RANK,
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
from strategy_validator.application.ui_semantic_validator_handoff_clearance_operations_board_payload import (
    build_ui_semantic_validator_handoff_clearance_operations_board_latest_payload,
    build_ui_semantic_validator_handoff_clearance_operations_board_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_operations_board_rows import (
    _action_group,
    _degraded,
    _haystack,
    _matches,
    _next_safe_action,
    _operation_card,
    _operation_state,
    _sort_card,
    _source_row_values,
)

__all__ = [
    "build_ui_semantic_validator_handoff_clearance_operations_board_payload",
    "build_ui_semantic_validator_handoff_clearance_operations_board_latest_payload",
]
