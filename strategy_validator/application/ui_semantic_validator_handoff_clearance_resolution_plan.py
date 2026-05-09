"""Read-only clearance resolution plan for semantic validator handoff closure.

This module is intentionally kept as a compatibility facade. The clearance
resolution-plan implementation is decomposed into focused subphase modules for
shared helpers, resolution-step synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_clearance_action_register import (
    build_ui_semantic_validator_handoff_clearance_action_register_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_resolution_plan_common import (
    _LIMIT_MAX,
    _PHASE_RANK,
    _PRIORITY_RANK,
    _SCHEMA_VERSION,
    _SEVERITY_RANK,
    _STEP_STATE_RANK,
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
from strategy_validator.application.ui_semantic_validator_handoff_clearance_resolution_plan_payload import (
    build_ui_semantic_validator_handoff_clearance_resolution_plan_latest_payload,
    build_ui_semantic_validator_handoff_clearance_resolution_plan_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_clearance_resolution_plan_rows import (
    _completion_gate,
    _degraded,
    _haystack,
    _matches,
    _phase,
    _resolution_step,
    _safe_instruction,
    _sort_step,
    _step_state,
    _verification_hint,
)

__all__ = [
    "build_ui_semantic_validator_handoff_clearance_resolution_plan_payload",
    "build_ui_semantic_validator_handoff_clearance_resolution_plan_latest_payload",
]
