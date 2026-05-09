"""Read-only exception queue for semantic validator handoff runbook cards.

This module is intentionally kept as a compatibility facade. The exception
queue implementation is decomposed into focused subphase modules for shared
helpers, exception row synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_runbook import (
    build_ui_semantic_validator_handoff_runbook_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_exceptions_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _as_list,
    _authority,
    _contains,
    _counts,
    _norm,
    _norm_set,
    _s,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_exceptions_payload import (
    build_ui_semantic_validator_handoff_exceptions_latest_payload,
    build_ui_semantic_validator_handoff_exceptions_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_exceptions_rows import (
    _escalation_lane,
    _exception_kind,
    _exception_row,
    _exception_state,
    _haystack,
    _matches,
)

__all__ = [
    "build_ui_semantic_validator_handoff_exceptions_payload",
    "build_ui_semantic_validator_handoff_exceptions_latest_payload",
]
