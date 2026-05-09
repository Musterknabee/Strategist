"""Read-only clearance release packet for semantic validator handoff closure.

This module is intentionally kept as a compatibility facade. The clearance
release-packet implementation is decomposed into focused subphase modules for
shared helpers, release-packet synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_readiness_board import (
    build_ui_semantic_validator_handoff_clearance_release_readiness_board_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_packet_common import (
    _LIMIT_MAX,
    _PACKET_READINESS_RANK,
    _PACKET_STATUS_RANK,
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
from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_packet_payload import (
    build_ui_semantic_validator_handoff_clearance_release_packet_latest_payload,
    build_ui_semantic_validator_handoff_clearance_release_packet_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_packet_rows import (
    _degraded,
    _matches,
    _packet_from_release,
    _packet_gate,
    _packet_instruction,
    _packet_readiness,
    _packet_status,
    _rank,
    _sort_packet,
)

__all__ = [
    "build_ui_semantic_validator_handoff_clearance_release_packet_payload",
    "build_ui_semantic_validator_handoff_clearance_release_packet_latest_payload",
]
