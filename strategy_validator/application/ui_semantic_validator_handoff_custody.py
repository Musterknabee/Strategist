"""Read-plane custody seal verifier for semantic validator-handoff signoffs.

This module is intentionally kept as a compatibility facade. The custody
read-plane implementation is decomposed into focused subphase modules for
shared helpers, external seal discovery, packet synthesis, row
classification/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_custody_common import (
    _BLOCKED_STATUS,
    _CUSTODY_SEAL_SCHEMA_VERSION,
    _DIGEST_MISMATCH_STATUS,
    _INVALID_STATUS,
    _READY_STATUS,
    _RECORDED_SIGNOFF_STATUS,
    _RECORDED_STATUS,
    _SCHEMA_VERSION,
    _as_list,
    _authority_assertion_true,
    _contains,
    _counts,
    _digest,
    _norm,
    _norm_set,
    _placeholder,
    _read_json,
    _s,
    _seal_value,
    _sha256,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_custody_packet import (
    _custody_packet,
    _custody_packet_digest,
    _custody_template,
)
from strategy_validator.application.ui_semantic_validator_handoff_custody_payload import (
    build_ui_semantic_validator_handoff_custody_latest_payload,
    build_ui_semantic_validator_handoff_custody_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_custody_rows import (
    _custody_row,
    _custody_status,
    _haystack,
    _issue_codes,
    _match_seals,
    _matches,
)
from strategy_validator.application.ui_semantic_validator_handoff_custody_seals import (
    _custody_seal_artifacts,
    _is_custody_seal_candidate,
    _normalize_custody_seal,
)

__all__ = [
    "build_ui_semantic_validator_handoff_custody_payload",
    "build_ui_semantic_validator_handoff_custody_latest_payload",
]
