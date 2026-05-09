"""Read-only operator runbook for semantic validator handoff continuity rows.

This module is intentionally kept as a compatibility facade. The runbook
implementation is decomposed into focused subphase modules for shared helpers,
runbook card synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_continuity import (
    build_ui_semantic_validator_handoff_continuity_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_runbook_common import (
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
from strategy_validator.application.ui_semantic_validator_handoff_runbook_payload import (
    build_ui_semantic_validator_handoff_runbook_latest_payload,
    build_ui_semantic_validator_handoff_runbook_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_runbook_rows import (
    _checklist,
    _first_issue,
    _haystack,
    _matches,
    _runbook_card,
    _runbook_decision,
    _template_fields,
)

__all__ = [
    "build_ui_semantic_validator_handoff_runbook_payload",
    "build_ui_semantic_validator_handoff_runbook_latest_payload",
]
