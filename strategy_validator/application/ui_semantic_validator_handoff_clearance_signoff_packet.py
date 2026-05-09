"""Read-only clearance signoff packet for semantic validator handoff closure.

This module is intentionally kept as a compatibility facade. The clearance
signoff-packet implementation is decomposed into focused subphase modules for
shared helpers, signoff-packet synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_clearance_review_docket import (
    build_ui_semantic_validator_handoff_clearance_review_docket_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_signoff_packet_common import (
    _LIMIT_MAX,
    _PRIORITY_RANK,
    _SCHEMA_VERSION,
    _SEVERITY_RANK,
    _SIGNOFF_READINESS_RANK,
    _SIGNOFF_STATUS_RANK,
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
from strategy_validator.application.ui_semantic_validator_handoff_clearance_signoff_packet_payload import (
    build_ui_semantic_validator_handoff_clearance_signoff_packet_latest_payload,
    build_ui_semantic_validator_handoff_clearance_signoff_packet_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_signoff_packet_rows import (
    _degraded,
    _haystack,
    _matches,
    _packet_from_docket,
    _signoff_gate,
    _signoff_instruction,
    _signoff_readiness,
    _signoff_status,
    _sort_packet,
)

__all__ = [
    "build_ui_semantic_validator_handoff_clearance_signoff_packet_payload",
    "build_ui_semantic_validator_handoff_clearance_signoff_packet_latest_payload",
]
