"""Bounded application entrypoints for UI-facing API routes.

This module provides a narrower import surface for API route handlers so they do
not need to depend on the giant ``strategy_validator.application`` compatibility
barrel.
"""

from __future__ import annotations

from strategy_validator.application.api_ui_detail_queries import (
    build_ui_evidence_query,
    build_ui_pack_detail_query,
)
from strategy_validator.application.api_ui_export_responses import (
    build_ui_export_entity_headers,
    build_ui_export_options_response,
    build_ui_export_response,
)
from strategy_validator.application.api_ui_query_params import build_ui_workboard_query
from strategy_validator.application.api_ui_runtime_queries import (
    build_ui_burnin_query,
    build_ui_runtime_query,
    build_ui_tribunal_query,
)
from strategy_validator.application.ui_command_actions import execute_ui_operator_command
from strategy_validator.application.ui_public_facade import (
    build_ui_public_facade_inventory,
    build_ui_provider_health_payload,
)
from strategy_validator.application.ui_research_compute import build_ui_research_compute_payload
from strategy_validator.application.operator_action_projection import build_operator_action_event_index_payload
from strategy_validator.application.evidence_chain_projection import build_ui_evidence_chain_payload
from strategy_validator.application.ui_views import (
    build_ui_burnin_payload,
    build_ui_evidence_payload,
    build_ui_operator_command_receipt_payload,
    build_ui_pack_detail_payload,
    build_ui_runtime_status_payload,
    build_ui_tribunal_payload,
    build_ui_workboard_export_allow_headers,
    build_ui_workboard_export_disposition_headers,
    build_ui_workboard_export_document,
    build_ui_workboard_export_document_headers,
    build_ui_workboard_export_index,
    build_ui_workboard_export_index_headers,
    build_ui_workboard_export_location_headers,
    build_ui_workboard_export_payload,
    build_ui_workboard_export_profile_headers,
    build_ui_workboard_export_representation_headers,
    build_ui_workboard_export_response_class_headers,
    build_ui_workboard_payload,
    export_etag_matches,
    export_last_modified_matches,
)

__all__ = [
    'build_ui_burnin_payload',
    'build_ui_evidence_query',
    'build_ui_pack_detail_query',
    'build_ui_public_facade_inventory',
    'build_ui_provider_health_payload',
    'build_ui_research_compute_payload',
    'build_ui_export_entity_headers',
    'build_ui_export_options_response',
    'build_ui_export_response',
    'build_ui_workboard_query',
    'build_ui_burnin_query',
    'build_ui_runtime_query',
    'build_ui_tribunal_query',
    'execute_ui_operator_command',
    'build_operator_action_event_index_payload',
    'build_ui_evidence_chain_payload',
    'build_ui_evidence_payload',
    'build_ui_operator_command_receipt_payload',
    'build_ui_pack_detail_payload',
    'build_ui_runtime_status_payload',
    'build_ui_tribunal_payload',
    'build_ui_workboard_export_allow_headers',
    'build_ui_workboard_export_disposition_headers',
    'build_ui_workboard_export_document',
    'build_ui_workboard_export_document_headers',
    'build_ui_workboard_export_index',
    'build_ui_workboard_export_index_headers',
    'build_ui_workboard_export_location_headers',
    'build_ui_workboard_export_payload',
    'build_ui_workboard_export_profile_headers',
    'build_ui_workboard_export_representation_headers',
    'build_ui_workboard_export_response_class_headers',
    'build_ui_workboard_payload',
    'export_etag_matches',
    'export_last_modified_matches',
]
