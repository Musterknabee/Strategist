from __future__ import annotations

"""Bounded event / replay / constitutional application surface."""

from strategy_validator.projections.oracle_event_checkpoints import emit_oracle_event_checkpoint_projection_registry
from strategy_validator.projections.oracle_event_views import emit_oracle_event_view_projection_registry
from strategy_validator.validator.oracle_constitutional import (
    append_oracle_constitutional_digest_to_lane,
    build_oracle_constitutional_digest_evidence_bundle,
    generate_oracle_constitutional_gate,
    generate_oracle_doctrine_lineage_index,
    render_oracle_constitutional_gate_markdown,
    render_oracle_doctrine_lineage_index_markdown,
    render_oracle_doctrine_lineage_verification_markdown,
    verify_oracle_constitutional_digest_evidence_bundle,
    verify_oracle_doctrine_lineage,
)
from strategy_validator.validator.oracle_event_log import (
    build_oracle_event_checkpoint_bundle,
    generate_oracle_derived_view,
    generate_oracle_horizon_view,
    generate_oracle_rolling_review,
    legacy_compatibility_banner,
    render_oracle_derived_view_markdown,
    render_oracle_event_checkpoint_markdown,
    render_oracle_rolling_review_markdown,
    resolve_oracle_horizon_window,
    verify_oracle_event_checkpoint_bundle,
)
from strategy_validator.validator.oracle_replay import (
    inspect_oracle_compacted_state,
    rebuild_oracle_compacted_state,
    render_oracle_compacted_state_inspection_markdown,
    render_oracle_compacted_state_rebuild_markdown,
)
from strategy_validator.validator.oracle_transition import (
    append_oracle_annual_review_to_lane,
    append_oracle_doctrine_drift_to_lane,
    append_oracle_memory_review_to_lane,
    append_oracle_monthly_digest_to_lane,
    append_oracle_quarterly_review_to_lane,
    append_oracle_semiannual_audit_to_lane,
    append_oracle_transition_to_lane,
    build_oracle_annual_review_evidence_bundle,
    build_oracle_doctrine_drift_evidence_bundle,
    build_oracle_memory_review_evidence_bundle,
    build_oracle_monthly_digest_evidence_bundle,
    build_oracle_quarterly_review_evidence_bundle,
    build_oracle_semiannual_audit_evidence_bundle,
    build_oracle_transition_evidence_bundle,
    build_oracle_weekly_digest_evidence_bundle,
    compare_oracle_evidence,
    compare_oracle_weekly_digests,
    generate_oracle_annual_review,
    generate_oracle_constitutional_digest,
    generate_oracle_monthly_digest,
    generate_oracle_quarterly_review,
    generate_oracle_semiannual_audit,
    generate_oracle_weekly_digest,
    render_oracle_annual_review_markdown,
    render_oracle_constitutional_digest_markdown,
    render_oracle_doctrine_drift_markdown,
    render_oracle_memory_lane_summary_markdown,
    render_oracle_memory_review_markdown,
    render_oracle_monthly_digest_markdown,
    render_oracle_quarterly_review_markdown,
    render_oracle_semiannual_audit_markdown,
    render_oracle_state_transition_markdown,
    render_oracle_weekly_digest_markdown,
    review_oracle_memory_lane,
    summarize_oracle_memory_lane,
    verify_oracle_annual_review_evidence_bundle,
    verify_oracle_doctrine_drift_evidence_bundle,
    verify_oracle_memory_review_evidence_bundle,
    verify_oracle_monthly_digest_evidence_bundle,
    verify_oracle_quarterly_review_evidence_bundle,
    verify_oracle_semiannual_audit_evidence_bundle,
    verify_oracle_transition_evidence_bundle,
    verify_oracle_weekly_digest_evidence_bundle,
)

_TARGETS = {
    'append_annual_review_to_lane_payload': 'append_oracle_annual_review_to_lane',
    'append_constitutional_digest_to_lane_payload': 'append_oracle_constitutional_digest_to_lane',
    'append_doctrine_drift_to_lane_payload': 'append_oracle_doctrine_drift_to_lane',
    'append_memory_review_to_lane_payload': 'append_oracle_memory_review_to_lane',
    'append_monthly_digest_to_lane_payload': 'append_oracle_monthly_digest_to_lane',
    'append_quarterly_review_to_lane_payload': 'append_oracle_quarterly_review_to_lane',
    'append_semiannual_audit_to_lane_payload': 'append_oracle_semiannual_audit_to_lane',
    'append_state_transition_to_lane_payload': 'append_oracle_transition_to_lane',
    'build_annual_review_evidence_bundle_payload': 'build_oracle_annual_review_evidence_bundle',
    'build_annual_review_payload': 'generate_oracle_annual_review',
    'build_constitutional_digest_evidence_bundle_payload': 'build_oracle_constitutional_digest_evidence_bundle',
    'build_constitutional_digest_payload': 'generate_oracle_constitutional_digest',
    'build_constitutional_gate_payload': 'generate_oracle_constitutional_gate',
    'build_derived_view_payload': 'generate_oracle_derived_view',
    'build_doctrine_drift_evidence_bundle_payload': 'build_oracle_doctrine_drift_evidence_bundle',
    'build_doctrine_drift_payload': 'compare_oracle_evidence',
    'build_doctrine_lineage_index_payload': 'generate_oracle_doctrine_lineage_index',
    'build_event_checkpoint_payload': 'build_oracle_event_checkpoint_bundle',
    'build_horizon_view_payload': 'generate_oracle_horizon_view',
    'build_memory_lane_summary_payload': 'summarize_oracle_memory_lane',
    'build_memory_review_evidence_bundle_payload': 'build_oracle_memory_review_evidence_bundle',
    'build_memory_review_payload': 'review_oracle_memory_lane',
    'build_monthly_digest_evidence_bundle_payload': 'build_oracle_monthly_digest_evidence_bundle',
    'build_monthly_digest_payload': 'generate_oracle_monthly_digest',
    'build_quarterly_review_evidence_bundle_payload': 'build_oracle_quarterly_review_evidence_bundle',
    'build_quarterly_review_payload': 'generate_oracle_quarterly_review',
    'build_rolling_review_payload': 'generate_oracle_rolling_review',
    'build_semiannual_audit_evidence_bundle_payload': 'build_oracle_semiannual_audit_evidence_bundle',
    'build_semiannual_audit_payload': 'generate_oracle_semiannual_audit',
    'build_state_transition_evidence_bundle_payload': 'build_oracle_transition_evidence_bundle',
    'build_state_transition_payload': 'compare_oracle_evidence',
    'build_weekly_digest_evidence_bundle_payload': 'build_oracle_weekly_digest_evidence_bundle',
    'build_weekly_digest_payload': 'generate_oracle_weekly_digest',
    'compare_weekly_digest_payloads': 'compare_oracle_weekly_digests',
    'emit_event_checkpoint_projection_registry_payload': 'emit_oracle_event_checkpoint_projection_registry',
    'emit_event_view_projection_registry_payload': 'emit_oracle_event_view_projection_registry',
    'inspect_compacted_state_payload': 'inspect_oracle_compacted_state',
    'legacy_compatibility_banner_payload': 'legacy_compatibility_banner',
    'rebuild_compacted_state_payload': 'rebuild_oracle_compacted_state',
    'render_annual_review_markdown_payload': 'render_oracle_annual_review_markdown',
    'render_compacted_state_inspection_markdown_payload': 'render_oracle_compacted_state_inspection_markdown',
    'render_compacted_state_rebuild_markdown_payload': 'render_oracle_compacted_state_rebuild_markdown',
    'render_constitutional_digest_markdown_payload': 'render_oracle_constitutional_digest_markdown',
    'render_constitutional_gate_markdown_payload': 'render_oracle_constitutional_gate_markdown',
    'render_derived_view_markdown_payload': 'render_oracle_derived_view_markdown',
    'render_doctrine_drift_markdown_payload': 'render_oracle_doctrine_drift_markdown',
    'render_doctrine_lineage_index_markdown_payload': 'render_oracle_doctrine_lineage_index_markdown',
    'render_doctrine_lineage_verification_markdown_payload': 'render_oracle_doctrine_lineage_verification_markdown',
    'render_event_checkpoint_markdown_payload': 'render_oracle_event_checkpoint_markdown',
    'render_memory_lane_summary_markdown_payload': 'render_oracle_memory_lane_summary_markdown',
    'render_memory_review_markdown_payload': 'render_oracle_memory_review_markdown',
    'render_monthly_digest_markdown_payload': 'render_oracle_monthly_digest_markdown',
    'render_quarterly_review_markdown_payload': 'render_oracle_quarterly_review_markdown',
    'render_rolling_review_markdown_payload': 'render_oracle_rolling_review_markdown',
    'render_semiannual_audit_markdown_payload': 'render_oracle_semiannual_audit_markdown',
    'render_state_transition_markdown_payload': 'render_oracle_state_transition_markdown',
    'render_weekly_digest_markdown_payload': 'render_oracle_weekly_digest_markdown',
    'resolve_horizon_window_payload': 'resolve_oracle_horizon_window',
    'verify_annual_review_evidence_bundle_payload': 'verify_oracle_annual_review_evidence_bundle',
    'verify_constitutional_digest_evidence_bundle_payload': 'verify_oracle_constitutional_digest_evidence_bundle',
    'verify_doctrine_drift_evidence_bundle_payload': 'verify_oracle_doctrine_drift_evidence_bundle',
    'verify_doctrine_lineage_payload': 'verify_oracle_doctrine_lineage',
    'verify_event_checkpoint_payload': 'verify_oracle_event_checkpoint_bundle',
    'verify_memory_review_evidence_bundle_payload': 'verify_oracle_memory_review_evidence_bundle',
    'verify_monthly_digest_evidence_bundle_payload': 'verify_oracle_monthly_digest_evidence_bundle',
    'verify_quarterly_review_evidence_bundle_payload': 'verify_oracle_quarterly_review_evidence_bundle',
    'verify_semiannual_audit_evidence_bundle_payload': 'verify_oracle_semiannual_audit_evidence_bundle',
    'verify_state_transition_evidence_bundle_payload': 'verify_oracle_transition_evidence_bundle',
    'verify_weekly_digest_evidence_bundle_payload': 'verify_oracle_weekly_digest_evidence_bundle',
}


def _make_payload(target_name: str):
    def _payload(*args, **kwargs):
        return globals()[target_name](*args, **kwargs)

    return _payload


for _payload_name, _target_name in _TARGETS.items():
    globals()[_payload_name] = _make_payload(_target_name)
    globals()[_payload_name].__name__ = _payload_name
    globals()[_payload_name].__qualname__ = _payload_name
    globals()[_payload_name].__doc__ = f"Compatibility payload wrapper for ``{_target_name}``."


__all__ = sorted(_TARGETS)
