from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def _stable_json_sha256(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    ).hexdigest()


def _build_board_publication_verification_envelope(
    *,
    board_publication_surface: Mapping[str, Any],
    export_completeness_state: str,
    bundle_members: list[dict[str, Any]],
    schema_versions: list[str],
    canonical_source_paths: list[str],
) -> dict[str, Any]:
    normalized_members = list(board_publication_surface.get('normalized_members', []) or [])
    bundle_root = str(board_publication_surface.get('bundle_root') or '')
    export_state = str(board_publication_surface.get('export_state') or 'IDLE')

    content_inventory: list[dict[str, Any]] = []
    fingerprint_inputs: list[str] = [
        f'bundle_root={bundle_root}',
        f'export_state={export_state}',
        f'export_completeness_state={export_completeness_state}',
    ]
    for member, bundle_member in zip(normalized_members, bundle_members):
        export_key = str(member.get('export_key') or '')
        payload_state = str(member.get('payload_state') or 'METADATA_ONLY')
        payload_object = member.get('payload_object')
        payload_sha256 = _stable_json_sha256(payload_object) if payload_object is not None else None
        content_entry = {
            'export_key': export_key,
            'schema_version': str(member.get('schema_version') or ''),
            'relative_publication_path': str(member.get('relative_publication_path') or ''),
            'generated_relative_path': str(member.get('generated_relative_path') or ''),
            'published_relative_path': member.get('published_relative_path'),
            'artifact_class': str(member.get('artifact_class') or ''),
            'publication_stage': str(member.get('publication_stage') or ''),
            'source_backing_state': str(member.get('source_backing_state') or ''),
            'payload_state': payload_state,
            'payload_sha256': payload_sha256,
            'source_path_count': int(bundle_member.get('source_path_count') or 0),
        }
        content_inventory.append(content_entry)
        fingerprint_inputs.append(
            'member=' + '|'.join([
                export_key,
                content_entry['schema_version'],
                content_entry['relative_publication_path'],
                content_entry['artifact_class'],
                content_entry['publication_stage'],
                content_entry['source_backing_state'],
                payload_state,
                payload_sha256 or 'none',
                str(content_entry['source_path_count']),
            ])
        )

    for path in canonical_source_paths:
        fingerprint_inputs.append(f'source={path}')

    bundle_fingerprint_sha256 = _stable_json_sha256(fingerprint_inputs)

    if export_state == 'IDLE' or not content_inventory:
        verification_state = 'IDLE'
    elif export_completeness_state == 'FULLY_EMBEDDED':
        verification_state = 'VERIFIABLE'
    else:
        verification_state = 'PARTIAL'

    summary_line = (
        f"Verification envelope: {verification_state} with fingerprint {bundle_fingerprint_sha256[:12]} covering "
        f"{len(content_inventory)} publication member(s)."
    ) if content_inventory else 'Verification envelope: no publication members are available yet.'
    source_coverage_line = (
        f"Source coverage: {len(canonical_source_paths)} canonical source path(s) contribute to the current board bundle."
    )
    schema_inventory_line = (
        f"Schema inventory: {len(schema_versions)} schema version(s) are represented in the publication bundle."
    )

    return {
        'schema_version': 'oracle_operator_board_publication_bundle_verification/v1',
        'verification_state': verification_state,
        'summary_line': summary_line,
        'bundle_fingerprint_sha256': bundle_fingerprint_sha256 if content_inventory else None,
        'fingerprint_input_count': len(fingerprint_inputs) if content_inventory else 0,
        'content_member_count': len(content_inventory),
        'schema_inventory_count': len(schema_versions),
        'source_path_count': len(canonical_source_paths),
        'source_coverage_line': source_coverage_line,
        'schema_inventory_line': schema_inventory_line,
        'content_inventory': content_inventory,
        'schema_inventory': schema_versions,
        'fingerprint_inputs': fingerprint_inputs if content_inventory else [],
    }


def _build_board_publication_bundle_manifest(*, board_publication_surface: Mapping[str, Any]) -> dict[str, Any]:
    normalized_members = list(board_publication_surface.get('normalized_members', []) or [])
    embedded_members = [member for member in normalized_members if str(member.get('payload_state') or '') == 'EMBEDDED']
    metadata_only_members = [member for member in normalized_members if str(member.get('payload_state') or '') != 'EMBEDDED']
    export_state = str(board_publication_surface.get('export_state') or 'IDLE')
    member_count = len(normalized_members)
    embedded_count = len(embedded_members)
    metadata_only_count = len(metadata_only_members)

    if export_state == 'IDLE' or member_count == 0:
        export_completeness_state = 'IDLE'
    elif metadata_only_count == 0:
        export_completeness_state = 'FULLY_EMBEDDED'
    elif embedded_count == 0:
        export_completeness_state = 'METADATA_ONLY'
    else:
        export_completeness_state = 'PARTIALLY_EMBEDDED'

    schema_versions = sorted({str(member.get('schema_version') or '') for member in normalized_members if str(member.get('schema_version') or '')})
    embedded_export_keys = [str(member.get('export_key') or '') for member in embedded_members if str(member.get('export_key') or '')]
    metadata_only_export_keys = [str(member.get('export_key') or '') for member in metadata_only_members if str(member.get('export_key') or '')]

    bundle_members = [
        {
            'export_key': str(member.get('export_key') or ''),
            'schema_version': str(member.get('schema_version') or ''),
            'relative_publication_path': str(member.get('relative_publication_path') or ''),
            'generated_relative_path': str(member.get('generated_relative_path') or ''),
            'published_relative_path': member.get('published_relative_path'),
            'artifact_class': str(member.get('artifact_class') or ''),
            'publication_stage': str(member.get('publication_stage') or ''),
            'source_backing_state': str(member.get('source_backing_state') or ''),
            'payload_state': str(member.get('payload_state') or 'METADATA_ONLY'),
            'source_path_count': len(member.get('source_paths', []) or []),
        }
        for member in normalized_members
    ]

    focus_key = board_publication_surface.get('focus_work_item_key')
    focus_action = board_publication_surface.get('focus_action')
    top_cluster_signal_kind = board_publication_surface.get('top_cluster_signal_kind')
    bundle_root = str(board_publication_surface.get('bundle_root') or '')
    published_bundle_root = str(board_publication_surface.get('published_bundle_root') or '')
    canonical_source_paths = list(board_publication_surface.get('canonical_source_paths', []) or [])
    generated_member_count = int(board_publication_surface.get('generated_member_count') or 0)
    published_member_count = int(board_publication_surface.get('published_member_count') or 0)
    source_backed_member_count = int(board_publication_surface.get('source_backed_member_count') or 0)
    artifact_class_summary_line = str(board_publication_surface.get('artifact_class_summary_line') or '')

    if member_count == 0:
        summary_line = 'Board publication bundle manifest: no normalized publication members are available yet.'
        completeness_line = 'Bundle completeness remains idle until export-ready publication members are generated.'
    else:
        summary_line = (
            f"Board publication bundle manifest: {member_count} normalized publication member(s) are staged under "
            f"{bundle_root or 'the current bundle root'}."
        )
        completeness_line = (
            f"Bundle completeness: {export_completeness_state} with {embedded_count} embedded payload member(s) and "
            f"{metadata_only_count} metadata-only member(s)."
        )

    verification_envelope = _build_board_publication_verification_envelope(
        board_publication_surface=board_publication_surface,
        export_completeness_state=export_completeness_state,
        bundle_members=bundle_members,
        schema_versions=schema_versions,
        canonical_source_paths=canonical_source_paths,
    )

    return {
        'schema_version': 'oracle_operator_board_publication_bundle_manifest/v1',
        'publication_family': 'oracle_operator_board_publication_bundle_manifest',
        'bundle_root': bundle_root or None,
        'published_bundle_root': published_bundle_root or None,
        'export_state': export_state,
        'export_completeness_state': export_completeness_state,
        'summary_line': summary_line,
        'completeness_line': completeness_line,
        'focus_work_item_key': focus_key,
        'focus_action': focus_action,
        'top_cluster_signal_kind': top_cluster_signal_kind,
        'member_count': member_count,
        'embedded_member_count': embedded_count,
        'metadata_only_member_count': metadata_only_count,
        'schema_versions': schema_versions,
        'embedded_export_keys': embedded_export_keys,
        'metadata_only_export_keys': metadata_only_export_keys,
        'canonical_source_paths': canonical_source_paths,
        'generated_member_count': generated_member_count,
        'published_member_count': published_member_count,
        'source_backed_member_count': source_backed_member_count,
        'artifact_class_summary_line': artifact_class_summary_line,
        'bundle_members': bundle_members,
        'verification_envelope': verification_envelope,
    }


__all__ = [
    '_stable_json_sha256',
    '_build_board_publication_verification_envelope',
    '_build_board_publication_bundle_manifest',
]
