"""Read-only clearance checklist for semantic validator handoff closure.

This module is intentionally kept as a compatibility facade. The clearance
checklist implementation is decomposed into focused subphase modules for shared
helpers, checklist-item synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_clearance_checklist_common import (
    _CHECK_STATE_RANK,
    _LIMIT_MAX,
    _POSTURE_RANK,
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
from strategy_validator.application.ui_semantic_validator_handoff_clearance_checklist_payload import (
    build_ui_semantic_validator_handoff_clearance_checklist_latest_payload,
    build_ui_semantic_validator_handoff_clearance_checklist_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_checklist_rows import (
    _checklist_item,
    _degraded,
    _haystack,
    _instruction,
    _items_from_dossiers,
    _matches,
    _sort_item,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_dossier import (
    build_ui_semantic_validator_handoff_clearance_dossier_payload,
)

__all__ = [
    "build_ui_semantic_validator_handoff_clearance_checklist_payload",
    "build_ui_semantic_validator_handoff_clearance_checklist_latest_payload",
]
