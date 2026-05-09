"""Read-plane closure attestation verifier for semantic validator-handoff archives.

This module is intentionally kept as a compatibility facade. The closure
read-plane implementation is decomposed into focused subphase modules for
shared helpers, external attestation discovery, closure packet synthesis, row
classification/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_closure_attestations import (
    _closure_attestation_artifacts,
    _is_closure_attestation_candidate,
    _normalize_closure_attestation,
)
from strategy_validator.application.ui_semantic_validator_handoff_closure_common import (
    _BLOCKED_STATUS,
    _CLOSURE_SCHEMA_VERSION,
    _DIGEST_MISMATCH_STATUS,
    _INVALID_STATUS,
    _READY_STATUS,
    _RECORDED_STATUS,
    _SCHEMA_VERSION,
    _VERIFIED_ARCHIVE_STATUS,
    _as_list,
    _authority_assertion_true,
    _closure_value,
    _contains,
    _counts,
    _digest,
    _norm,
    _norm_set,
    _placeholder,
    _read_json,
    _s,
    _sha256,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_closure_packet import (
    _closure_packet,
    _closure_template,
)
from strategy_validator.application.ui_semantic_validator_handoff_closure_payload import (
    build_ui_semantic_validator_handoff_closure_latest_payload,
    build_ui_semantic_validator_handoff_closure_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_closure_rows import (
    _closure_row,
    _closure_status,
    _haystack,
    _issue_codes,
    _match_attestations,
    _matches,
)

__all__ = [
    "build_ui_semantic_validator_handoff_closure_payload",
    "build_ui_semantic_validator_handoff_closure_latest_payload",
]
