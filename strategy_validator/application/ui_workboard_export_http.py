from __future__ import annotations

import base64
from datetime import datetime, timezone
from email.utils import format_datetime, parsedate_to_datetime
from pathlib import Path
from typing import Any, Mapping


def parse_export_generated_at(value: Any) -> datetime | None:
    raw = str(value or '').strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def build_ui_workboard_export_representation_headers(media_type: str = 'application/json') -> dict[str, str]:
    normalized_media_type = str(media_type or 'application/json').strip() or 'application/json'
    return {
        'Vary': 'Accept, If-None-Match, If-Modified-Since',
        'X-Board-Export-Accept': normalized_media_type,
        'X-Board-Export-Representation': normalized_media_type,
        'X-Board-Export-Negotiation-State': 'CANONICAL_JSON_ONLY' if normalized_media_type == 'application/json' else 'CUSTOM',
    }


def build_ui_workboard_export_profile_headers(payload: Mapping[str, Any]) -> dict[str, str]:
    schema_version = str(payload.get('schema_version') or '').strip()
    schema_family, _, schema_revision = schema_version.partition('/')
    profile_uri = f"urn:strategy-validator:schema:{schema_version.replace('/', ':')}" if schema_version else ''
    return {
        'X-Board-Export-Schema-Version': schema_version,
        'X-Board-Export-Schema-Family': schema_family,
        'X-Board-Export-Schema-Revision': schema_revision,
        'X-Board-Export-Profile': profile_uri,
        'X-Board-Export-Profile-Label': schema_version or 'unknown',
        'X-Board-Export-Profile-State': 'DECLARED' if profile_uri else 'MISSING',
    }


def build_ui_workboard_export_location_headers(payload: Mapping[str, Any]) -> dict[str, str]:
    canonical_relative_path = str(payload.get('relative_document_path') or '').strip()
    published_relative_path = str(payload.get('published_relative_document_path') or '').strip()
    headers = {
        'X-Board-Export-Canonical-Relative-Path': canonical_relative_path,
        'X-Board-Export-Published-Canonical-Relative-Path': published_relative_path,
        'X-Board-Export-Location-State': 'DECLARED' if canonical_relative_path else 'MISSING',
        'X-Board-Export-Published-Location-State': 'DECLARED' if published_relative_path else 'UNPUBLISHED',
    }
    if canonical_relative_path:
        headers['Content-Location'] = canonical_relative_path
    return headers


def default_export_filename(payload: Mapping[str, Any]) -> str:
    schema_version = str(payload.get('schema_version') or '').strip()
    schema_family, _, _ = schema_version.partition('/')
    canonical_relative_path = str(payload.get('relative_document_path') or '').strip()
    if schema_family.endswith('_index'):
        return 'board_export_index.json'
    if canonical_relative_path:
        return Path(canonical_relative_path).name
    if schema_family.endswith('_document'):
        return 'board_export_payload.json'
    return 'board_export_payload.json'


def build_ui_workboard_export_disposition_headers(payload: Mapping[str, Any]) -> dict[str, str]:
    filename = default_export_filename(payload)
    inline_disposition = f'inline; filename="{filename}"'
    attachment_disposition = f'attachment; filename="{filename}"'
    return {
        'Content-Disposition': inline_disposition,
        'X-Board-Export-Disposition': inline_disposition,
        'X-Board-Export-Disposition-State': 'INLINE_INSPECTION',
        'X-Board-Export-Attachment-Disposition': attachment_disposition,
        'X-Board-Export-Export-Intent': 'INSPECT_INLINE_OR_DOWNLOAD',
        'X-Board-Export-Filename': filename,
    }


def build_ui_workboard_export_response_class_headers(payload: Mapping[str, Any]) -> dict[str, str]:
    schema_version = str(payload.get('schema_version') or '').strip()
    schema_family, _, _ = schema_version.partition('/')
    response_class = 'UNKNOWN'
    body_role = 'UNKNOWN'
    if schema_family.endswith('_index'):
        response_class = 'INDEX_DOCUMENT'
        body_role = 'EXPORT_CATALOG'
    elif schema_family.endswith('_document'):
        response_class = 'CANONICAL_EXPORT_DOCUMENT'
        body_role = 'EXPORT_PAYLOAD'
    return {
        'X-Board-Export-Response-Class': response_class,
        'X-Board-Export-Body-Role': body_role,
        'X-Board-Export-Response-Class-State': 'DECLARED' if response_class != 'UNKNOWN' else 'MISSING',
    }


def build_ui_workboard_export_freshness_headers(payload: Mapping[str, Any]) -> dict[str, str]:
    generated_at = str(payload.get('generated_at_utc') or '').strip()
    generated_dt = parse_export_generated_at(generated_at)
    headers = {
        'Cache-Control': 'no-cache',
        'X-Board-Export-Generated-At': generated_at,
        'X-Board-Export-Freshness-State': 'CURRENT' if generated_dt else 'UNKNOWN',
        'X-Board-Export-Freshness-Basis': 'generated_at_utc' if generated_dt else 'missing_generated_at_utc',
    }
    if generated_dt is not None:
        headers['Last-Modified'] = format_datetime(generated_dt, usegmt=True)
    return headers


def build_ui_workboard_export_allow_headers(headers: Mapping[str, Any] | None = None) -> dict[str, str]:
    merged = dict(headers or {})
    merged['Allow'] = 'GET, HEAD, OPTIONS'
    merged['X-Board-Export-Allow'] = 'GET, HEAD, OPTIONS'
    return merged


def build_ui_workboard_export_document_headers(export_document: Mapping[str, Any]) -> dict[str, str]:
    canonical_payload = dict(export_document.get('canonical_payload', {}) or {})
    document_sha256 = str(export_document.get('document_sha256') or '').strip()
    digest_value = ''
    if document_sha256:
        try:
            digest_value = base64.b64encode(bytes.fromhex(document_sha256)).decode('ascii')
        except ValueError:
            digest_value = ''
    headers = build_ui_workboard_export_representation_headers()
    headers.update(build_ui_workboard_export_profile_headers(export_document))
    headers.update(build_ui_workboard_export_location_headers(export_document))
    headers.update(build_ui_workboard_export_disposition_headers(export_document))
    headers.update(build_ui_workboard_export_response_class_headers(export_document))
    headers.update(build_ui_workboard_export_freshness_headers(export_document))
    headers.update({
        'ETag': f'"sha256:{document_sha256}"' if document_sha256 else '""',
        'X-Board-Export-Document-SHA256': document_sha256,
        'X-Board-Export-Bundle-Fingerprint-SHA256': str(canonical_payload.get('bundle_fingerprint_sha256') or ''),
        'X-Board-Export-Relative-Path': str(export_document.get('relative_document_path') or ''),
        'X-Board-Export-Published-Relative-Path': str(export_document.get('published_relative_document_path') or ''),
        'X-Board-Export-Index-Route': '/ui/workboard/export/index',
        'X-Board-Export-Document-Route': '/ui/workboard/export/document',
        'X-Board-Export-State': str(export_document.get('export_state') or 'IDLE'),
        'X-Board-Export-Completeness': str(export_document.get('export_completeness_state') or 'IDLE'),
        'X-Board-Export-Verification': str(export_document.get('verification_state') or 'IDLE'),
        'X-Board-Export-Byte-Count': str(int(export_document.get('byte_count') or 0)),
        'X-Board-Export-Line-Count': str(int(export_document.get('line_count') or 0)),
        'Link': '</ui/workboard/export/index>; rel="index", </ui/workboard/export/document>; rel="self"',
    })
    if digest_value:
        headers['Digest'] = f'sha-256={digest_value}'
    if headers.get('X-Board-Export-Profile'):
        headers['Link'] = f"{headers['Link']}, <{headers['X-Board-Export-Profile']}>; rel=\"profile\""
    if headers.get('Content-Location'):
        headers['Link'] = f"{headers['Link']}, <{headers['Content-Location']}>; rel=\"canonical\""
    return build_ui_workboard_export_allow_headers(headers)


def export_etag_matches(if_none_match: str | None, etag: str | None) -> bool:
    candidate = str(etag or '').strip()
    if not candidate:
        return False
    header_value = str(if_none_match or '').strip()
    if not header_value:
        return False
    if header_value == '*':
        return True
    for token in header_value.split(','):
        if token.strip() == candidate:
            return True
    return False


def export_last_modified_matches(if_modified_since: str | None, last_modified: str | None) -> bool:
    candidate = str(last_modified or '').strip()
    if not candidate:
        return False
    header_value = str(if_modified_since or '').strip()
    if not header_value:
        return False
    try:
        candidate_dt = parsedate_to_datetime(candidate)
        header_dt = parsedate_to_datetime(header_value)
    except (TypeError, ValueError, IndexError, OverflowError):
        return False
    if candidate_dt is None or header_dt is None:
        return False
    if candidate_dt.tzinfo is None:
        candidate_dt = candidate_dt.replace(tzinfo=timezone.utc)
    else:
        candidate_dt = candidate_dt.astimezone(timezone.utc)
    if header_dt.tzinfo is None:
        header_dt = header_dt.replace(tzinfo=timezone.utc)
    else:
        header_dt = header_dt.astimezone(timezone.utc)
    return header_dt >= candidate_dt


def build_ui_workboard_export_index_headers(index_payload: Mapping[str, Any]) -> dict[str, str]:
    document_sha256 = str(index_payload.get('document_sha256') or '').strip()
    digest_value = ''
    if document_sha256:
        try:
            digest_value = base64.b64encode(bytes.fromhex(document_sha256)).decode('ascii')
        except ValueError:
            digest_value = ''
    headers = build_ui_workboard_export_representation_headers()
    headers.update(build_ui_workboard_export_profile_headers(index_payload))
    headers.update(build_ui_workboard_export_location_headers(index_payload))
    headers.update(build_ui_workboard_export_disposition_headers(index_payload))
    headers.update(build_ui_workboard_export_response_class_headers(index_payload))
    headers.update(build_ui_workboard_export_freshness_headers(index_payload))
    headers.update({
        'ETag': f'"sha256:{document_sha256}"' if document_sha256 else '""',
        'X-Board-Export-Index-Route': '/ui/workboard/export/index',
        'X-Board-Export-Document-Route': '/ui/workboard/export/document',
        'X-Board-Export-Document-SHA256': document_sha256,
        'X-Board-Export-Bundle-Fingerprint-SHA256': str(index_payload.get('bundle_fingerprint_sha256') or ''),
        'X-Board-Export-Relative-Path': str(index_payload.get('relative_document_path') or ''),
        'X-Board-Export-Published-Relative-Path': str(index_payload.get('published_relative_document_path') or ''),
        'X-Board-Export-State': str(index_payload.get('export_state') or 'IDLE'),
        'X-Board-Export-Completeness': str(index_payload.get('export_completeness_state') or 'IDLE'),
        'X-Board-Export-Verification': str(index_payload.get('verification_state') or 'IDLE'),
        'X-Board-Export-Byte-Count': str(int(index_payload.get('document_byte_count') or 0)),
        'X-Board-Export-Line-Count': str(int(index_payload.get('document_line_count') or 0)),
        'Link': '</ui/workboard/export/document>; rel="describedby", </ui/workboard/export/index>; rel="self"',
    })
    if digest_value:
        headers['Digest'] = f'sha-256={digest_value}'
    if headers.get('X-Board-Export-Profile'):
        headers['Link'] = f"{headers['Link']}, <{headers['X-Board-Export-Profile']}>; rel=\"profile\""
    if headers.get('Content-Location'):
        headers['Link'] = f"{headers['Link']}, <{headers['Content-Location']}>; rel=\"canonical\""
    return build_ui_workboard_export_allow_headers(headers)


__all__ = [
    'parse_export_generated_at',
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
]
