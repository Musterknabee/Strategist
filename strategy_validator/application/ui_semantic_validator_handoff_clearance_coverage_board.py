"""Read-only clearance coverage board for semantic validator handoff evidence.

This module is intentionally kept as a compatibility facade. The clearance
coverage implementation is decomposed into focused subphase modules for shared
helpers, coverage-card synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_clearance_evidence_matrix import (
    build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_coverage_board_common import (
    _LANE_RANK,
    _LIMIT_MAX,
    _PRIORITY_RANK,
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
from strategy_validator.application.ui_semantic_validator_handoff_clearance_coverage_board_payload import (
    build_ui_semantic_validator_handoff_clearance_coverage_board_latest_payload,
    build_ui_semantic_validator_handoff_clearance_coverage_board_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_coverage_board_rows import (
    _board_card,
    _cards_from_rows,
    _coverage_percent,
    _degraded,
    _haystack,
    _highest,
    _matches,
    _operator_instruction,
    _sort_card,
    _status,
)

__all__ = [
    "build_ui_semantic_validator_handoff_clearance_coverage_board_payload",
    "build_ui_semantic_validator_handoff_clearance_coverage_board_latest_payload",
]
