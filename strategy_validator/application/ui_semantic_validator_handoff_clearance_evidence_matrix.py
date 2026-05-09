"""Read-only clearance evidence matrix for semantic validator handoff evidence.

This module is intentionally kept as a compatibility facade. The clearance
matrix implementation is decomposed into focused subphase modules for shared
helpers, matrix-row synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_clearance_checklist import (
    build_ui_semantic_validator_handoff_clearance_checklist_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_evidence_matrix_common import (
    _LANE_RANK,
    _LIMIT_MAX,
    _PRIORITY_RANK,
    _SCHEMA_VERSION,
    _SEVERITY_RANK,
    _STATE_RANK,
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
from strategy_validator.application.ui_semantic_validator_handoff_clearance_evidence_matrix_payload import (
    build_ui_semantic_validator_handoff_clearance_evidence_matrix_latest_payload,
    build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_evidence_matrix_rows import (
    _coverage_state,
    _degraded,
    _evidence_lane,
    _evidence_state,
    _haystack,
    _instruction,
    _matches,
    _matrix_cells,
    _matrix_row,
    _sort_row,
)

__all__ = [
    "build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload",
    "build_ui_semantic_validator_handoff_clearance_evidence_matrix_latest_payload",
]
