"""Read-plane lineage verifier for semantic validator-handoff artifacts.

This module is intentionally kept as a compatibility facade. The lineage
implementation is decomposed into focused subphase modules for shared helpers,
chain construction/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff import (
    build_ui_semantic_validator_handoff_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_lineage_common import (
    _CHAIN_KIND_ORDER,
    _LIMIT_MAX,
    _READY_ACTION,
    _REPAIR_ACTION,
    _SCHEMA_VERSION,
    _as_list,
    _authority,
    _component_id,
    _contains,
    _counts,
    _entry_ref,
    _find_first,
    _find_first_by_any,
    _link_digest,
    _norm_set,
    _s,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_lineage_payload import (
    build_ui_semantic_validator_handoff_lineage_latest_payload,
    build_ui_semantic_validator_handoff_lineage_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_lineage_rows import (
    _build_chains,
    _chain_entry,
    _chain_key,
    _issue_haystack,
    _link_check,
    _matches,
    _select_chain_from_anchor,
)

__all__ = [
    "build_ui_semantic_validator_handoff_lineage_payload",
    "build_ui_semantic_validator_handoff_lineage_latest_payload",
]
