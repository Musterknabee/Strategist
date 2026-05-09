"""Read-only evidence gap cockpit for semantic validator handoff timelines.

This module is intentionally kept as a compatibility facade. Evidence-gap
implementation is decomposed into focused subphase modules for shared helpers,
gap-row synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_evidence_gaps_common import (
    _LIMIT_MAX,
    _PRIORITY_RANK,
    _SCHEMA_VERSION,
    _STAGE_RANK,
    _as_list,
    _authority,
    _contains,
    _counts,
    _norm,
    _norm_set,
    _s,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_evidence_gaps_payload import (
    build_ui_semantic_validator_handoff_evidence_gaps_latest_payload,
    build_ui_semantic_validator_handoff_evidence_gaps_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_evidence_gaps_rows import (
    _checklist,
    _classify,
    _gap_row,
    _haystack,
    _matches,
    _repair_route,
)
from strategy_validator.application.ui_semantic_validator_handoff_timeline import (
    build_ui_semantic_validator_handoff_timeline_payload,
)

__all__ = [
    "build_ui_semantic_validator_handoff_evidence_gaps_payload",
    "build_ui_semantic_validator_handoff_evidence_gaps_latest_payload",
]
