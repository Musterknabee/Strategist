"""Read-plane review gate for semantic validator-handoff chains.

This module is intentionally kept as a compatibility facade. The review
implementation is decomposed into focused subphase modules for shared helpers,
row synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_remediation import (
    build_ui_semantic_validator_handoff_remediation_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_review_common import (
    _BLOCKED_ACTION,
    _COMPONENT_LABELS,
    _LIMIT_MAX,
    _READY_ACTION,
    _SCHEMA_VERSION,
    _STACKED_CHECKS,
    _as_list,
    _authority,
    _contains,
    _counts,
    _digest,
    _norm_set,
    _s,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_review_payload import (
    build_ui_semantic_validator_handoff_review_latest_payload,
    build_ui_semantic_validator_handoff_review_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_review_rows import (
    _check_status,
    _component_paths,
    _haystack,
    _matches,
    _review_checklist,
    _review_row,
    _review_status,
    _trust_banner,
)

__all__ = [
    "build_ui_semantic_validator_handoff_review_payload",
    "build_ui_semantic_validator_handoff_review_latest_payload",
]
