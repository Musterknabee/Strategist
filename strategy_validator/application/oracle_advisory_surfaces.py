from __future__ import annotations

"""Bounded advisory / trust / diagnostic application surface."""

from strategy_validator.projections.oracle_event_checkpoints import emit_oracle_event_checkpoint_projection_registry
from strategy_validator.projections.oracle_event_views import emit_oracle_event_view_projection_registry
from strategy_validator.validator.oracle_advisory import (
    build_oracle_evidence_bundle,
    build_oracle_morning_attestation,
    load_oracle_input,
    render_oracle_morning_attestation_markdown,
    verify_oracle_evidence_bundle,
)
from strategy_validator.validator.oracle_diagnostics import (
    build_oracle_incident_pack,
    build_oracle_operator_diagnostic_from_checkpoint,
    build_oracle_operator_diagnostic_from_report,
    build_oracle_status_pack,
    materialize_oracle_incident_pack,
    materialize_oracle_status_pack,
    render_oracle_incident_pack_html,
    render_oracle_incident_pack_markdown,
    render_oracle_operator_diagnostic_markdown,
    render_oracle_status_pack_html,
    render_oracle_status_pack_markdown,
)
from strategy_validator.validator.oracle_explain import (
    explain_checkpoint_from_paths,
    explain_constitutional_gate,
    explain_derived_view_trust,
    explain_event_checkpoint_trust,
    explain_lineage_verification,
    explain_report_from_path,
    render_oracle_explanation_markdown,
)
from strategy_validator.validator.oracle_replay import (
    inspect_oracle_compacted_state,
    rebuild_oracle_compacted_state,
    render_oracle_compacted_state_inspection_markdown,
    render_oracle_compacted_state_rebuild_markdown,
)
from strategy_validator.validator.oracle_sealed_history import load_verified_strategic_stack_history_bundle
from strategy_validator.validator.oracle_strategic_artifact_evidence import (
    build_oracle_strategic_artifact_evidence_bundle,
    verify_oracle_strategic_artifact_evidence_bundle,
)
from strategy_validator.validator.oracle_strategic_stack_evidence import (
    build_oracle_strategic_stack_evidence_bundle,
    verify_oracle_strategic_stack_evidence_bundle,
)
from strategy_validator.validator.oracle_trust import (
    infer_repo_root_from_artifact_path as trust_infer_repo_root_from_artifact_path,
    maybe_verify_oracle_lineage as trust_maybe_verify_oracle_lineage,
    render_oracle_trust_banner,
    trust_banner_for_constitutional_gate,
    trust_banner_for_derived_view,
    trust_banner_for_event_checkpoint,
    trust_banner_for_legacy_surface,
    trust_banner_for_lineage_verification,
)

_TARGETS = {
    'build_incident_pack_payload': 'build_oracle_incident_pack',
    'build_morning_attestation_payload': 'build_oracle_morning_attestation',
    'build_operator_diagnostic_from_checkpoint_payload': 'build_oracle_operator_diagnostic_from_checkpoint',
    'build_operator_diagnostic_from_report_payload': 'build_oracle_operator_diagnostic_from_report',
    'build_oracle_evidence_bundle_payload': 'build_oracle_evidence_bundle',
    'build_status_pack_payload': 'build_oracle_status_pack',
    'build_strategic_artifact_evidence_bundle_payload': 'build_oracle_strategic_artifact_evidence_bundle',
    'build_strategic_stack_evidence_bundle_payload': 'build_oracle_strategic_stack_evidence_bundle',
    'emit_event_checkpoint_projection_registry_payload': 'emit_oracle_event_checkpoint_projection_registry',
    'emit_event_view_projection_registry_payload': 'emit_oracle_event_view_projection_registry',
    'explain_checkpoint_from_paths_payload': 'explain_checkpoint_from_paths',
    'explain_constitutional_gate_payload': 'explain_constitutional_gate',
    'explain_derived_view_trust_payload': 'explain_derived_view_trust',
    'explain_event_checkpoint_trust_payload': 'explain_event_checkpoint_trust',
    'explain_lineage_verification_payload': 'explain_lineage_verification',
    'explain_report_from_path_payload': 'explain_report_from_path',
    'inspect_compacted_state_payload': 'inspect_oracle_compacted_state',
    'load_oracle_input_payload': 'load_oracle_input',
    'load_verified_strategic_stack_history_bundle_payload': 'load_verified_strategic_stack_history_bundle',
    'materialize_incident_pack_payload': 'materialize_oracle_incident_pack',
    'materialize_status_pack_payload': 'materialize_oracle_status_pack',
    'rebuild_compacted_state_payload': 'rebuild_oracle_compacted_state',
    'render_compacted_state_inspection_markdown_payload': 'render_oracle_compacted_state_inspection_markdown',
    'render_compacted_state_rebuild_markdown_payload': 'render_oracle_compacted_state_rebuild_markdown',
    'render_incident_pack_html_payload': 'render_oracle_incident_pack_html',
    'render_incident_pack_markdown_payload': 'render_oracle_incident_pack_markdown',
    'render_morning_attestation_markdown_payload': 'render_oracle_morning_attestation_markdown',
    'render_operator_diagnostic_markdown_payload': 'render_oracle_operator_diagnostic_markdown',
    'render_oracle_explanation_markdown_payload': 'render_oracle_explanation_markdown',
    'render_oracle_trust_banner_payload': 'render_oracle_trust_banner',
    'render_status_pack_html_payload': 'render_oracle_status_pack_html',
    'render_status_pack_markdown_payload': 'render_oracle_status_pack_markdown',
    'trust_banner_for_constitutional_gate_payload': 'trust_banner_for_constitutional_gate',
    'trust_banner_for_derived_view_payload': 'trust_banner_for_derived_view',
    'trust_banner_for_event_checkpoint_payload': 'trust_banner_for_event_checkpoint',
    'trust_banner_for_legacy_surface_payload': 'trust_banner_for_legacy_surface',
    'trust_banner_for_lineage_verification_payload': 'trust_banner_for_lineage_verification',
    'trust_infer_repo_root_from_artifact_path_payload': 'trust_infer_repo_root_from_artifact_path',
    'trust_maybe_verify_oracle_lineage_payload': 'trust_maybe_verify_oracle_lineage',
    'verify_oracle_evidence_bundle_payload': 'verify_oracle_evidence_bundle',
    'verify_strategic_artifact_evidence_bundle_payload': 'verify_oracle_strategic_artifact_evidence_bundle',
    'verify_strategic_stack_evidence_bundle_payload': 'verify_oracle_strategic_stack_evidence_bundle',
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
