"""Read-plane archive manifest verifier for semantic validator-handoff custody seals.

This module is intentionally kept as a compatibility facade. The archive
read-plane implementation is decomposed into focused subphase modules for
shared helpers, external manifest discovery, packet synthesis, row
classification/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_archive_common import (
    _ARCHIVE_SCHEMA_VERSION,
    _BLOCKED_STATUS,
    _DIGEST_MISMATCH_STATUS,
    _INVALID_STATUS,
    _READY_STATUS,
    _RECORDED_CUSTODY_STATUS,
    _SCHEMA_VERSION,
    _VERIFIED_STATUS,
    _as_list,
    _authority_assertion_true,
    _contains,
    _counts,
    _digest,
    _manifest_value,
    _norm,
    _norm_set,
    _placeholder,
    _read_json,
    _s,
    _sha256,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_archive_manifests import (
    _archive_manifest_artifacts,
    _is_archive_manifest_candidate,
    _normalize_archive_manifest,
)
from strategy_validator.application.ui_semantic_validator_handoff_archive_packet import _archive_packet, _archive_template
from strategy_validator.application.ui_semantic_validator_handoff_archive_payload import (
    build_ui_semantic_validator_handoff_archive_latest_payload,
    build_ui_semantic_validator_handoff_archive_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_archive_rows import (
    _archive_row,
    _archive_status,
    _haystack,
    _issue_codes,
    _match_manifests,
    _matches,
)

__all__ = [
    "build_ui_semantic_validator_handoff_archive_payload",
    "build_ui_semantic_validator_handoff_archive_latest_payload",
]
