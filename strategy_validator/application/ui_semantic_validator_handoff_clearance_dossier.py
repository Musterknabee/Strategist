"""Read-only clearance dossier for semantic validator handoff closure.

This module is intentionally kept as a compatibility facade. The clearance
 dossier implementation is decomposed into focused subphase modules for shared
helpers, dossier-row synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_clearance_dossier_common import (
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
from strategy_validator.application.ui_semantic_validator_handoff_clearance_dossier_payload import (
    build_ui_semantic_validator_handoff_clearance_dossier_latest_payload,
    build_ui_semantic_validator_handoff_clearance_dossier_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_dossier_rows import (
    _degraded,
    _dossier_from_gate,
    _haystack,
    _matches,
    _operator_brief,
    _review_checks,
    _review_posture,
    _sort_dossier,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_gate import (
    build_ui_semantic_validator_handoff_clearance_gate_payload,
)

__all__ = [
    "build_ui_semantic_validator_handoff_clearance_dossier_payload",
    "build_ui_semantic_validator_handoff_clearance_dossier_latest_payload",
]
