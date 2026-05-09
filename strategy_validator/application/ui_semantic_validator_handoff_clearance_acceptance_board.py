"""Read-only clearance acceptance board for semantic validator handoff closure.

This module is intentionally kept as a compatibility facade. The clearance
acceptance-board implementation is decomposed into focused subphase modules for
shared helpers, acceptance-card synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_clearance_signoff_packet import (
    build_ui_semantic_validator_handoff_clearance_signoff_packet_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_acceptance_board_common import (
    _ACCEPTANCE_READINESS_RANK,
    _ACCEPTANCE_STATUS_RANK,
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
from strategy_validator.application.ui_semantic_validator_handoff_clearance_acceptance_board_payload import (
    build_ui_semantic_validator_handoff_clearance_acceptance_board_latest_payload,
    build_ui_semantic_validator_handoff_clearance_acceptance_board_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_acceptance_board_rows import (
    _acceptance_gate,
    _acceptance_instruction,
    _acceptance_readiness,
    _acceptance_status,
    _card_from_packet,
    _degraded,
    _haystack,
    _matches,
    _sort_card,
)

__all__ = [
    "build_ui_semantic_validator_handoff_clearance_acceptance_board_payload",
    "build_ui_semantic_validator_handoff_clearance_acceptance_board_latest_payload",
]
