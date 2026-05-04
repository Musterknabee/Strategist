"""Lazy public export surface for projection services and artifact queries.

This package intentionally avoids eager importing of the full projection tree.
The root package remains a compatibility surface with lazy attribute resolution
so submodule imports do not trigger unrelated operator/publication flows.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORT_MAP = {
    'ControlPlaneEventSidecarRecord': 'strategy_validator.projections.control_plane_event_sidecars',
    'ControlPlaneEventSidecarReplayReport': 'strategy_validator.projections.control_plane_event_sidecars',
    'build_control_plane_event_sidecar_replay_report': 'strategy_validator.projections.control_plane_event_sidecars',
    'write_control_plane_event_sidecar_replay_report': 'strategy_validator.projections.control_plane_event_sidecars',
    'ControlPlaneEventIndexEntry': 'strategy_validator.projections.control_plane_event_index',
    'ControlPlaneEventProjectionIndex': 'strategy_validator.projections.control_plane_event_index',
    'build_control_plane_event_projection_index': 'strategy_validator.projections.control_plane_event_index',
    'write_control_plane_event_projection_index': 'strategy_validator.projections.control_plane_event_index',
    'build_projection_artifact_registry': 'strategy_validator.projections.artifact_registry',
    'build_projection_source_descriptor': 'strategy_validator.projections.artifact_registry',
    'write_projection_artifact_registry': 'strategy_validator.projections.artifact_registry',
    'write_projection_artifact_registry_with_index': 'strategy_validator.projections.artifact_registry',
    'build_briefing_pack_projection_registry': 'strategy_validator.projections.briefing_pack',
    'ProjectionArtifactDiscoveryMatch': 'strategy_validator.projections.discovery',
    'ProjectionArtifactQueryReport': 'strategy_validator.projections.discovery',
    'build_projection_artifact_query_report': 'strategy_validator.projections.discovery',
    'discover_latest_projection_output': 'strategy_validator.projections.discovery',
    'discover_projection_artifact_matches': 'strategy_validator.projections.discovery',
    'find_projection_artifact_match': 'strategy_validator.projections.discovery',
    'build_oracle_event_view_projection_registry': 'strategy_validator.projections.oracle_event_views',
    'emit_oracle_event_view_projection_registry': 'strategy_validator.projections.oracle_event_views',
    'build_single_source_projection_registry': 'strategy_validator.projections.query_build',
    'build_projection_artifact_index': 'strategy_validator.projections.artifact_index',
    'build_projection_artifact_index_entry': 'strategy_validator.projections.artifact_index',
    'load_projection_artifact_index': 'strategy_validator.projections.artifact_index',
    'upsert_projection_artifact_index': 'strategy_validator.projections.artifact_index',
    'write_projection_artifact_index': 'strategy_validator.projections.artifact_index',
    'build_oracle_event_checkpoint_projection_registry': 'strategy_validator.projections.oracle_event_checkpoints',
    'emit_oracle_event_checkpoint_projection_registry': 'strategy_validator.projections.oracle_event_checkpoints',
    'CANONICAL_EVENT_PROJECTION_FAMILY': 'strategy_validator.projections.service',
    'CANONICAL_EVENT_PROJECTION_LABELS': 'strategy_validator.projections.service',
    'ProjectionArtifactOperatorQueryResult': 'strategy_validator.projections.service',
    'ProjectionArtifactQuery': 'strategy_validator.projections.service',
    'ProjectionArtifactSelection': 'strategy_validator.projections.service',
    'build_projection_artifact_query': 'strategy_validator.projections.service',
    'run_projection_artifact_operator_query': 'strategy_validator.projections.service',
    'select_latest_canonical_event_projection': 'strategy_validator.projections.service',
    'select_latest_projection_artifact': 'strategy_validator.projections.service',
    'OperatorBundleArtifactCopy': 'strategy_validator.projections.operator_materialization',
    'OperatorBundleMaterializationRequest': 'strategy_validator.projections.operator_materialization',
    'OperatorBundleMaterializationResult': 'strategy_validator.projections.operator_materialization',
    'build_operator_bundle_output_paths': 'strategy_validator.projections.operator_materialization',
    'compute_report_provenance_digest': 'strategy_validator.projections.operator_materialization',
    'materialize_operator_bundle': 'strategy_validator.projections.operator_materialization',
    'with_report_provenance_digest': 'strategy_validator.projections.operator_materialization',
    'OperatorActionProjectionStatus': 'strategy_validator.projections.operator_action_workboard',
    'OperatorActionWorkboardProjection': 'strategy_validator.projections.operator_action_workboard',
    'materialize_journaled_operator_work_items': 'strategy_validator.projections.operator_action_workboard',
    'materialize_operator_action_workboard_projection': 'strategy_validator.projections.operator_action_workboard',
    'get_operator_action_projection_status': 'strategy_validator.projections.operator_action_workboard',
    'operator_action_projection_enabled': 'strategy_validator.projections.operator_action_workboard',
    'build_operator_pack_manifest': 'strategy_validator.projections.operator_pack_registry',
    'build_operator_pack_index': 'strategy_validator.projections.operator_pack_registry',
    'build_operator_pack_index_entry': 'strategy_validator.projections.operator_pack_registry',
    'discover_latest_operator_pack': 'strategy_validator.projections.operator_pack_registry',
    'load_operator_pack_index': 'strategy_validator.projections.operator_pack_registry',
    'upsert_operator_pack_index': 'strategy_validator.projections.operator_pack_registry',
    'write_operator_pack_index': 'strategy_validator.projections.operator_pack_registry',
    'write_operator_pack_manifest': 'strategy_validator.projections.operator_pack_registry',
    'write_operator_pack_manifest_with_index': 'strategy_validator.projections.operator_pack_registry',
    'OperatorPackDiscoveryMatch': 'strategy_validator.projections.operator_pack_discovery',
    'OperatorPackOperatorQueryResult': 'strategy_validator.projections.operator_pack_discovery',
    'OperatorPackQuery': 'strategy_validator.projections.operator_pack_discovery',
    'OperatorPackQueryReport': 'strategy_validator.projections.operator_pack_discovery',
    'build_operator_pack_query': 'strategy_validator.projections.operator_pack_discovery',
    'build_operator_pack_query_report': 'strategy_validator.projections.operator_pack_discovery',
    'discover_latest_operator_pack_match': 'strategy_validator.projections.operator_pack_discovery',
    'discover_operator_pack_matches': 'strategy_validator.projections.operator_pack_discovery',
    'run_operator_pack_query': 'strategy_validator.projections.operator_pack_discovery',
    'materialize_briefing_pack_bundle': 'strategy_validator.projections.operator_pack_service',
    'materialize_incident_pack_bundle': 'strategy_validator.projections.operator_pack_service',
    'materialize_status_pack_bundle': 'strategy_validator.projections.operator_pack_service',
    'OperatorTerminalRecordMaterializationResult': 'strategy_validator.projections.operator_terminal_record_service',
    'OperatorTerminalRecordPublication': 'strategy_validator.projections.operator_terminal_record_service',
    'build_operator_terminal_record_manifest': 'strategy_validator.projections.operator_terminal_record_service',
    'write_operator_terminal_record_manifest': 'strategy_validator.projections.operator_terminal_record_service',
    'build_operator_terminal_record_index_entry': 'strategy_validator.projections.operator_terminal_record_service',
    'load_operator_terminal_record_index': 'strategy_validator.projections.operator_terminal_record_service',
    'build_operator_terminal_record_index': 'strategy_validator.projections.operator_terminal_record_service',
    'materialize_operator_terminal_record_publication': 'strategy_validator.projections.operator_terminal_record_service',
    'write_operator_terminal_record_index': 'strategy_validator.projections.operator_terminal_record_service',
    'upsert_operator_terminal_record_index': 'strategy_validator.projections.operator_terminal_record_service',
    'OracleBriefingPackAssemblyRequest': 'strategy_validator.projections.operator_pack_assembly',
    'OracleIncidentPackAssemblyRequest': 'strategy_validator.projections.operator_pack_assembly',
    'OracleStatusPackAssemblyRequest': 'strategy_validator.projections.operator_pack_assembly',
    'assemble_oracle_briefing_pack': 'strategy_validator.projections.operator_pack_assembly',
    'assemble_oracle_incident_pack': 'strategy_validator.projections.operator_pack_assembly',
    'assemble_oracle_status_pack': 'strategy_validator.projections.operator_pack_assembly',
    'build_briefing_pack_assembly_request': 'strategy_validator.projections.operator_pack_assembly',
    'build_incident_pack_assembly_request': 'strategy_validator.projections.operator_pack_assembly',
    'build_status_pack_assembly_request': 'strategy_validator.projections.operator_pack_assembly',
}

__all__ = list(_EXPORT_MAP)


def __getattr__(name: str) -> Any:
    module_name = _EXPORT_MAP.get(name)
    if module_name is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    module = import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))


from strategy_validator.projections.operator_action_event_index import (
    OperatorActionEventIndexEntry,
    OperatorActionEventProjectionIndex,
    build_operator_action_event_projection_index,
    write_operator_action_event_projection_index,
)
