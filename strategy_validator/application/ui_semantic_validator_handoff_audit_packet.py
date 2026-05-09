"""Read-only consolidated audit packets for semantic validator handoff chains.

This module is intentionally kept as a compatibility facade. The audit-packet
read-plane implementation is decomposed into focused subphase modules for
shared helpers, input indexing, row classification/filtering, and public payload
assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_audit_packet_common import (
    _DETAIL_ROUTES,
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
from strategy_validator.application.ui_semantic_validator_handoff_audit_packet_indexing import (
    _index_rows,
    _related,
    _row_key,
)
from strategy_validator.application.ui_semantic_validator_handoff_audit_packet_payload import (
    build_ui_semantic_validator_handoff_audit_packet_latest_payload,
    build_ui_semantic_validator_handoff_audit_packet_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_audit_packet_rows import (
    _audit_packet_row,
    _haystack,
    _matches,
    _packet_lane,
    _packet_status,
    _required_actions,
    _timeline_tail,
    _trust_banner,
)
from strategy_validator.application.ui_semantic_validator_handoff_continuity import (
    build_ui_semantic_validator_handoff_continuity_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_evidence_gaps import (
    build_ui_semantic_validator_handoff_evidence_gaps_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_exceptions import (
    build_ui_semantic_validator_handoff_exceptions_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_timeline import (
    build_ui_semantic_validator_handoff_timeline_payload,
)

__all__ = [
    "build_ui_semantic_validator_handoff_audit_packet_payload",
    "build_ui_semantic_validator_handoff_audit_packet_latest_payload",
]
