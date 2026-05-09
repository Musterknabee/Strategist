"""Read-only clearance release handoff board for semantic validator handoff closure.

This module is intentionally kept as a compatibility facade. The clearance
release-handoff implementation is decomposed into focused subphase modules for
shared helpers, handoff synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_packet import (
    build_ui_semantic_validator_handoff_clearance_release_packet_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_handoff_board_common import (
    _HANDOFF_READINESS_RANK,
    _HANDOFF_STATUS_RANK,
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
from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_handoff_board_payload import (
    build_ui_semantic_validator_handoff_clearance_release_handoff_board_latest_payload,
    build_ui_semantic_validator_handoff_clearance_release_handoff_board_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_handoff_board_rows import (
    _degraded,
    _handoff_from_packet,
    _handoff_gate,
    _handoff_instruction,
    _handoff_readiness,
    _handoff_status,
    _matches,
    _rank,
    _sort_handoff,
)

__all__ = [
    "build_ui_semantic_validator_handoff_clearance_release_handoff_board_payload",
    "build_ui_semantic_validator_handoff_clearance_release_handoff_board_latest_payload",
]
