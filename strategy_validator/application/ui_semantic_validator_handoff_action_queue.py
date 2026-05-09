"""Read-only action queue for semantic validator handoff audit packets.

This module is intentionally kept as a compatibility facade. The action-queue
read-plane implementation is decomposed into focused subphase modules for
shared helpers, row classification/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_action_queue_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
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
from strategy_validator.application.ui_semantic_validator_handoff_action_queue_payload import (
    build_ui_semantic_validator_handoff_action_queue_latest_payload,
    build_ui_semantic_validator_handoff_action_queue_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_action_queue_rows import (
    _action_id,
    _hay,
    _matches,
    _queue_state,
    _row,
    _sort_key,
)
from strategy_validator.application.ui_semantic_validator_handoff_audit_packet import (
    build_ui_semantic_validator_handoff_audit_packet_payload,
)

__all__ = [
    "build_ui_semantic_validator_handoff_action_queue_payload",
    "build_ui_semantic_validator_handoff_action_queue_latest_payload",
]
