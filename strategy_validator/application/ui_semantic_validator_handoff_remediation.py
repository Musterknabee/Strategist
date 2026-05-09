"""Read-plane remediation queue for semantic validator-handoff lineage.

This module is intentionally kept as a compatibility facade. The remediation
implementation is decomposed into focused subphase modules for shared helpers,
row synthesis/filtering, and public payload assembly.
"""
from __future__ import annotations

from strategy_validator.application.ui_semantic_validator_handoff_lineage import (
    build_ui_semantic_validator_handoff_lineage_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_remediation_common import (
    _COMPONENT_FIELDS,
    _COMPONENT_LABELS,
    _LIMIT_MAX,
    _LINK_STEP_TEMPLATES,
    _READY_ACTION,
    _REMEDIATE_ACTION,
    _SCHEMA_VERSION,
    _SEVERITY_RANK,
    _STEP_LIBRARY,
    _as_list,
    _authority,
    _contains,
    _counts,
    _link_digest,
    _norm_set,
    _s,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_remediation_payload import (
    build_ui_semantic_validator_handoff_remediation_latest_payload,
    build_ui_semantic_validator_handoff_remediation_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_remediation_rows import (
    _broken_link_codes,
    _build_remediation_record,
    _chain_haystack,
    _component_labels_for_missing,
    _issue_step,
    _matches,
    _max_severity,
    _missing_components,
    _priority_score,
    _remediation_status,
    _step_template,
)

__all__ = [
    "build_ui_semantic_validator_handoff_remediation_payload",
    "build_ui_semantic_validator_handoff_remediation_latest_payload",
]
