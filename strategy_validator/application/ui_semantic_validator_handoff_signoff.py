"""Read-plane signoff receipt verifier for semantic validator-handoff decisions.

This module is intentionally kept as a compatibility facade. The signoff
implementation is decomposed into focused subphase modules for shared helpers,
external signoff artifact discovery, row synthesis/filtering, and public payload
assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_decision import (
    build_ui_semantic_validator_handoff_decision_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_signoff_artifacts import (
    _is_signoff_candidate,
    _normalize_signoff,
    _signoff_artifacts,
)
from strategy_validator.application.ui_semantic_validator_handoff_signoff_common import (
    _AWAITING_STATUS,
    _BLOCKED_STATUS,
    _DIGEST_MISMATCH_STATUS,
    _INVALID_STATUS,
    _LIMIT_MAX,
    _PLACEHOLDER_MARKERS,
    _READY_DECISION_STATUS,
    _RECORDED_STATUS,
    _SCHEMA_VERSION,
    _SIGNOFF_SCHEMA_VERSION,
    _as_list,
    _authority,
    _authority_assertion_true,
    _contains,
    _counts,
    _digest,
    _norm,
    _norm_set,
    _packet_digest,
    _placeholder,
    _read_json,
    _s,
    _sha256,
    _signoff_value,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_signoff_payload import (
    build_ui_semantic_validator_handoff_signoff_latest_payload,
    build_ui_semantic_validator_handoff_signoff_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_signoff_rows import (
    _haystack,
    _issue_codes,
    _match_signoffs,
    _matches,
    _signoff_row,
    _signoff_status,
    _signoff_template,
)

__all__ = [
    "build_ui_semantic_validator_handoff_signoff_payload",
    "build_ui_semantic_validator_handoff_signoff_latest_payload",
]
