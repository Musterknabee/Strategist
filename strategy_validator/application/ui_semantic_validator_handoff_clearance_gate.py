"""Read-only clearance gate for semantic validator handoff closure.

This module is intentionally kept as a compatibility facade. The clearance gate
implementation is decomposed into focused subphase modules for shared helpers,
gate-row synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_clearance_gate_common import (
    _LIMIT_MAX,
    _PRIORITY_RANK,
    _SCHEMA_VERSION,
    _SEVERITY_RANK,
    _STATUS_RANK,
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
from strategy_validator.application.ui_semantic_validator_handoff_clearance_gate_payload import (
    build_ui_semantic_validator_handoff_clearance_gate_latest_payload,
    build_ui_semantic_validator_handoff_clearance_gate_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_gate_rows import (
    _completion_condition,
    _gate_from_steps,
    _gate_instruction,
    _group_steps,
    _haystack,
    _highest_priority,
    _highest_severity,
    _matches,
    _sort_gate,
    _status,
)
from strategy_validator.application.ui_semantic_validator_handoff_resolution_plan import (
    build_ui_semantic_validator_handoff_resolution_plan_payload,
)

__all__ = [
    "build_ui_semantic_validator_handoff_clearance_gate_payload",
    "build_ui_semantic_validator_handoff_clearance_gate_latest_payload",
]
