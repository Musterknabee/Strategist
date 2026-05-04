from __future__ import annotations

from strategy_validator.application.ui_view_helpers import utc_now_iso
from strategy_validator.application.ui_workboard_contexts import (
    build_ui_workboard_dashboard_context,
    build_ui_workboard_export_context,
)
from strategy_validator.application.ui_workboard_export_documents import (
    canonicalize_ui_workboard_export_payload as _canonicalize_ui_workboard_export_payload,
    serialize_ui_workboard_export_document as _serialize_ui_workboard_export_document,
)
from strategy_validator.application.ui_workboard_export_http import (
    build_ui_workboard_export_allow_headers as _build_ui_workboard_export_allow_headers,
    build_ui_workboard_export_disposition_headers as _build_ui_workboard_export_disposition_headers,
    build_ui_workboard_export_document_headers as _build_ui_workboard_export_document_headers,
    build_ui_workboard_export_freshness_headers as _build_ui_workboard_export_freshness_headers,
    build_ui_workboard_export_index_headers as _build_ui_workboard_export_index_headers,
    build_ui_workboard_export_location_headers as _build_ui_workboard_export_location_headers,
    build_ui_workboard_export_profile_headers as _build_ui_workboard_export_profile_headers,
    build_ui_workboard_export_representation_headers as _build_ui_workboard_export_representation_headers,
    build_ui_workboard_export_response_class_headers as _build_ui_workboard_export_response_class_headers,
    default_export_filename as _default_export_filename,
    export_etag_matches as _export_etag_matches,
    export_last_modified_matches as _export_last_modified_matches,
)
from strategy_validator.application.ui_workboard_export_indexes import (
    build_ui_workboard_export_index_from_payload as _build_ui_workboard_export_index_from_payload,
)
from strategy_validator.application.ui_workboard_payload_models import (
    build_ui_workboard_dashboard_payload_model,
    build_ui_workboard_export_payload_model,
)

_utc_now = utc_now_iso


def build_ui_workboard_payload_from_context(*, board_label: str, context: Mapping[str, Any], transition_policy: Mapping[str, Any]) -> dict[str, Any]:
    dashboard_context = build_ui_workboard_dashboard_context(
        board_label=board_label,
        context=dict(context),
        transition_policy=dict(transition_policy),
    )
    return build_ui_workboard_dashboard_payload_model(dashboard_context=dashboard_context).to_payload()


def build_ui_workboard_export_payload_from_context(*, board_label: str, context: Mapping[str, Any]) -> dict[str, Any]:
    export_context = build_ui_workboard_export_context(board_label=board_label, context=dict(context))
    payload = build_ui_workboard_export_payload_model(export_context=export_context).to_payload()
    payload['source_surface'] = 'ui/workboard/export'
    return payload


def canonicalize_ui_workboard_export_payload(export_payload: Mapping[str, Any]) -> dict[str, Any]:
    return _canonicalize_ui_workboard_export_payload(export_payload)


def serialize_ui_workboard_export_document(export_payload: Mapping[str, Any]) -> dict[str, Any]:
    return _serialize_ui_workboard_export_document(export_payload)


def parse_export_generated_at(value: Any):
    from strategy_validator.application.ui_workboard_export_http import parse_export_generated_at as _parse_export_generated_at
    return _parse_export_generated_at(value)


def build_ui_workboard_export_representation_headers(media_type: str = 'application/json') -> dict[str, str]:
    return _build_ui_workboard_export_representation_headers(media_type)

def build_ui_workboard_export_profile_headers(payload: Mapping[str, Any]) -> dict[str, str]:
    return _build_ui_workboard_export_profile_headers(payload)

def build_ui_workboard_export_location_headers(payload: Mapping[str, Any]) -> dict[str, str]:
    return _build_ui_workboard_export_location_headers(payload)

def default_export_filename(payload: Mapping[str, Any]) -> str:
    return _default_export_filename(payload)

def build_ui_workboard_export_disposition_headers(payload: Mapping[str, Any]) -> dict[str, str]:
    return _build_ui_workboard_export_disposition_headers(payload)

def build_ui_workboard_export_response_class_headers(payload: Mapping[str, Any]) -> dict[str, str]:
    return _build_ui_workboard_export_response_class_headers(payload)

def build_ui_workboard_export_freshness_headers(payload: Mapping[str, Any]) -> dict[str, str]:
    return _build_ui_workboard_export_freshness_headers(payload)

def build_ui_workboard_export_allow_headers(headers: Mapping[str, Any] | None = None) -> dict[str, str]:
    return _build_ui_workboard_export_allow_headers(headers)

def build_ui_workboard_export_document_headers(export_document: Mapping[str, Any]) -> dict[str, str]:
    return _build_ui_workboard_export_document_headers(export_document)


def export_etag_matches(if_none_match: str | None, etag: str | None) -> bool:
    return _export_etag_matches(if_none_match, etag)


def export_last_modified_matches(if_modified_since: str | None, last_modified: str | None) -> bool:
    return _export_last_modified_matches(if_modified_since, last_modified)


def build_ui_workboard_export_index_headers(index_payload: Mapping[str, Any]) -> dict[str, str]:
    return _build_ui_workboard_export_index_headers(index_payload)


def build_ui_workboard_export_index_from_payload(
    *,
    board_label: str,
    export_payload: Mapping[str, Any],
) -> dict[str, Any]:
    return _build_ui_workboard_export_index_from_payload(board_label=board_label, export_payload=export_payload)


__all__ = [
    'build_ui_workboard_payload_from_context',
    'build_ui_workboard_export_payload_from_context',
    'canonicalize_ui_workboard_export_payload',
    'serialize_ui_workboard_export_document',
    'build_ui_workboard_export_representation_headers',
    'build_ui_workboard_export_profile_headers',
    'build_ui_workboard_export_location_headers',
    'default_export_filename',
    'build_ui_workboard_export_disposition_headers',
    'build_ui_workboard_export_response_class_headers',
    'build_ui_workboard_export_freshness_headers',
    'build_ui_workboard_export_allow_headers',
    'build_ui_workboard_export_document_headers',
    'export_etag_matches',
    'export_last_modified_matches',
    'build_ui_workboard_export_index_headers',
    'build_ui_workboard_export_index_from_payload',
]
