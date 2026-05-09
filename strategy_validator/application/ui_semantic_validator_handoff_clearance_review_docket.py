"""Read-only clearance review docket for semantic validator handoff closure.

This module is intentionally kept as a compatibility facade. The clearance
review-docket implementation is decomposed into focused subphase modules for
shared helpers, row synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_clearance_closeout_board import (
    build_ui_semantic_validator_handoff_clearance_closeout_board_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_review_docket_common import (
    _DOCKET_READINESS_RANK,
    _DOCKET_STATUS_RANK,
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
    _uniq,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_review_docket_payload import (
    build_ui_semantic_validator_handoff_clearance_review_docket_latest_payload,
    build_ui_semantic_validator_handoff_clearance_review_docket_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_review_docket_rows import (
    _degraded,
    _docket_from_card,
    _docket_readiness,
    _docket_status,
    _haystack,
    _matches,
    _review_gate,
    _review_instruction,
    _sort_docket,
)

__all__ = [
    "build_ui_semantic_validator_handoff_clearance_review_docket_payload",
    "build_ui_semantic_validator_handoff_clearance_review_docket_latest_payload",
]
