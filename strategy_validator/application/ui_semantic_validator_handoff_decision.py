"""Read-plane decision dossiers for semantic validator-handoff review gates.

This module is intentionally kept as a compatibility facade. The decision
implementation is decomposed into focused subphase modules for shared helpers,
row synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_review import (
    build_ui_semantic_validator_handoff_review_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_decision_common import (
    _BLOCKED_EVIDENCE_STATUS,
    _BLOCKED_LINEAGE_STATUS,
    _BLOCKED_REMEDIATION_STATUS,
    _BLOCKED_UNTRUSTED_STATUS,
    _DECISION_PRECONDITIONS,
    _LIMIT_MAX,
    _READY_STATUS,
    _SCHEMA_VERSION,
    _as_list,
    _authority,
    _contains,
    _counts,
    _digest,
    _norm_set,
    _s,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_decision_payload import (
    build_ui_semantic_validator_handoff_decision_latest_payload,
    build_ui_semantic_validator_handoff_decision_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_decision_rows import (
    _decision_options,
    _decision_packet,
    _decision_row,
    _decision_status,
    _haystack,
    _matches,
    _preconditions,
)

__all__ = [
    "build_ui_semantic_validator_handoff_decision_payload",
    "build_ui_semantic_validator_handoff_decision_latest_payload",
]
