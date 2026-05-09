"""Read-only clearance release readiness board for semantic validator handoff closure.

This module is intentionally kept as a compatibility facade. The clearance
release-readiness-board implementation is decomposed into focused subphase modules
for shared helpers, release-readiness-card synthesis/filtering, and public payload
assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_clearance_acceptance_board import (
    build_ui_semantic_validator_handoff_clearance_acceptance_board_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_readiness_board_common import (
    _LIMIT_MAX,
    _PRIORITY_RANK,
    _RELEASE_READINESS_RANK,
    _RELEASE_STATUS_RANK,
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
from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_readiness_board_payload import (
    build_ui_semantic_validator_handoff_clearance_release_readiness_board_latest_payload,
    build_ui_semantic_validator_handoff_clearance_release_readiness_board_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_readiness_board_rows import (
    _card_from_acceptance,
    _degraded,
    _haystack,
    _matches,
    _release_gate,
    _release_instruction,
    _release_readiness,
    _release_status,
    _sort_card,
)

__all__ = [
    "build_ui_semantic_validator_handoff_clearance_release_readiness_board_payload",
    "build_ui_semantic_validator_handoff_clearance_release_readiness_board_latest_payload",
]
