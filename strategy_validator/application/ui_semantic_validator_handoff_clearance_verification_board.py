"""Read-only clearance verification board for semantic validator handoff closure.

This module is intentionally kept as a compatibility facade. The clearance
verification-board implementation is decomposed into focused subphase modules
for shared helpers, row synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_clearance_resolution_plan import (
    build_ui_semantic_validator_handoff_clearance_resolution_plan_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_verification_board_common import (
    _LIMIT_MAX,
    _PRIORITY_RANK,
    _RESULT_RANK,
    _SCHEMA_VERSION,
    _SEVERITY_RANK,
    _STATUS_RANK,
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
from strategy_validator.application.ui_semantic_validator_handoff_clearance_verification_board_payload import (
    build_ui_semantic_validator_handoff_clearance_verification_board_latest_payload,
    build_ui_semantic_validator_handoff_clearance_verification_board_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_verification_board_rows import (
    _card,
    _degraded,
    _haystack,
    _matches,
    _sort_card,
    _verification_gate,
    _verification_note,
    _verification_result,
    _verification_status,
)

__all__ = [
    "build_ui_semantic_validator_handoff_clearance_verification_board_payload",
    "build_ui_semantic_validator_handoff_clearance_verification_board_latest_payload",
]
