"""Read-only clearance release disposition board for semantic validator handoff closure.

This module is intentionally kept as a compatibility facade. The clearance release disposition board
implementation is decomposed into focused subphase modules for shared helpers,
row synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_retention_board import (
    build_ui_semantic_validator_handoff_clearance_release_retention_board_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_disposition_board_common import (
    _LIMIT_MAX,
    _PRIORITY_RANK,
    _READINESS_RANK,
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
from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_disposition_board_payload import (
    build_ui_semantic_validator_handoff_clearance_release_disposition_board_latest_payload,
    build_ui_semantic_validator_handoff_clearance_release_disposition_board_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_disposition_board_rows import (
    _degraded,
    _gate,
    _instruction,
    _matches,
    _readiness,
    _row,
    _sort,
    _status,
)

__all__ = [
    "build_ui_semantic_validator_handoff_clearance_release_disposition_board_payload",
    "build_ui_semantic_validator_handoff_clearance_release_disposition_board_latest_payload",
]
