"""Read-plane cockpit for semantic validator-handoff artifacts.

This module is intentionally kept as a compatibility facade. The implementation
is decomposed into focused subphase modules for shared helpers, artifact entry
builders, discovery, filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_common import (
    _DEFAULT_RELATIVE_ROOTS,
    _KNOWN_SCHEMAS,
    _SCHEMA_VERSION,
    _as_list,
    _authority,
    _bool_counts,
    _coerce_root,
    _contains,
    _counts,
    _issue_haystack,
    _norm_set,
    _read_json,
    _sha256,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_discovery import _discover
from strategy_validator.application.ui_semantic_validator_handoff_entries import (
    _artifact_entry,
    _base_entry,
    _decision_ledger_entry,
    _handoff_certificate_entry,
    _ingress_certificate_entry,
    _validator_packet_entry,
)
from strategy_validator.application.ui_semantic_validator_handoff_payload import (
    build_ui_semantic_validator_handoff_latest_payload,
    build_ui_semantic_validator_handoff_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_rows import _matches

__all__ = ["build_ui_semantic_validator_handoff_payload", "build_ui_semantic_validator_handoff_latest_payload"]
