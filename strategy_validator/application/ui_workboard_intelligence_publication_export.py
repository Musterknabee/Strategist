from __future__ import annotations

from typing import Any, Mapping


def _build_board_export_payload(
    *,
    board_publication_surface: Mapping[str, Any],
    board_publication_bundle_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    normalized_members = list(board_publication_surface.get('normalized_members', []) or [])
    payload_members = {
        str(member.get('export_key') or ''): {
            'schema_version': str(member.get('schema_version') or ''),
            'summary_line': str(member.get('summary_line') or ''),
            'generated_relative_path': str(member.get('generated_relative_path') or ''),
            'published_relative_path': member.get('published_relative_path'),
            'artifact_class': str(member.get('artifact_class') or ''),
            'publication_stage': str(member.get('publication_stage') or ''),
            'source_backing_state': str(member.get('source_backing_state') or ''),
            'payload_state': str(member.get('payload_state') or 'METADATA_ONLY'),
            'payload_object': member.get('payload_object'),
            'source_paths': list(member.get('source_paths', []) or []),
        }
        for member in normalized_members
        if str(member.get('export_key') or '')
    }

    export_state = str(board_publication_surface.get('export_state') or 'IDLE')
    export_completeness_state = str(board_publication_bundle_manifest.get('export_completeness_state') or 'IDLE')
    verification_envelope = dict(board_publication_bundle_manifest.get('verification_envelope') or {})
    verification_state = str(verification_envelope.get('verification_state') or 'IDLE')
    focus_key = board_publication_surface.get('focus_work_item_key')
    focus_action = board_publication_surface.get('focus_action')
    top_cluster_signal_kind = board_publication_surface.get('top_cluster_signal_kind')
    bundle_root = str(board_publication_surface.get('bundle_root') or '')
    published_bundle_root = str(board_publication_surface.get('published_bundle_root') or '')
    embedded_payload_count = int(board_publication_surface.get('embedded_payload_count') or 0)
    member_count = int(board_publication_bundle_manifest.get('member_count') or len(normalized_members))
    schema_versions = list(board_publication_bundle_manifest.get('schema_versions', []) or [])
    canonical_source_paths = list(board_publication_surface.get('canonical_source_paths', []) or [])
    closure_ready_count = int(board_publication_surface.get('journal_downstream_closure_ready_count') or 0)
    closure_review_required_count = int(board_publication_surface.get('journal_downstream_closure_review_required_count') or 0)
    closure_blocked_count = int(board_publication_surface.get('journal_downstream_closure_blocked_count') or 0)
    focus_closure_state = str(board_publication_surface.get('focus_projection_downstream_closure_state') or '') or None

    if member_count:
        summary_line = (
            f"Standalone board export payload: {embedded_payload_count} embedded publication payload(s) are consolidated "
            f"for {focus_key or 'the current board'} under {bundle_root or 'the current bundle root'}; downstream closure counts are "
            f"ready={closure_ready_count}, review_required={closure_review_required_count}, blocked={closure_blocked_count}."
        )
        export_line = (
            f"Export payload posture: {export_state} / {export_completeness_state} / {verification_state} with focus action "
            f"{focus_action.replace('-', ' ') if isinstance(focus_action, str) and focus_action else 'evidence review'}, "
            f"top cluster {top_cluster_signal_kind or 'none'}, and focus closure state {focus_closure_state or 'none'}."
        )
    else:
        summary_line = 'Standalone board export payload: no publication members are available for export yet.'
        export_line = 'Export payload posture: board export remains idle until publication members appear.'

    payload_keys = [key for key, member in payload_members.items() if member.get('payload_object') is not None]
    return {
        'schema_version': 'oracle_operator_board_export_payload/v1',
        'export_family': 'oracle_operator_board_export_payload',
        'summary_line': summary_line,
        'export_line': export_line,
        'export_state': export_state,
        'export_completeness_state': export_completeness_state,
        'verification_state': verification_state,
        'bundle_root': bundle_root or None,
        'published_bundle_root': published_bundle_root or None,
        'focus_work_item_key': focus_key,
        'focus_action': focus_action,
        'top_cluster_signal_kind': top_cluster_signal_kind,
        'focus_projection_downstream_closure_state': focus_closure_state,
        'journal_downstream_closure_ready_count': closure_ready_count,
        'journal_downstream_closure_review_required_count': closure_review_required_count,
        'journal_downstream_closure_blocked_count': closure_blocked_count,
        'embedded_payload_count': embedded_payload_count,
        'member_count': member_count,
        'schema_versions': schema_versions,
        'canonical_source_paths': canonical_source_paths,
        'bundle_fingerprint_sha256': verification_envelope.get('bundle_fingerprint_sha256'),
        'payload_keys': payload_keys,
        'publication_payloads': payload_members,
        'bundle_manifest': {
            'schema_version': str(board_publication_bundle_manifest.get('schema_version') or ''),
            'publication_family': str(board_publication_bundle_manifest.get('publication_family') or ''),
            'summary_line': str(board_publication_bundle_manifest.get('summary_line') or ''),
            'completeness_line': str(board_publication_bundle_manifest.get('completeness_line') or ''),
            'embedded_export_keys': list(board_publication_bundle_manifest.get('embedded_export_keys', []) or []),
            'canonical_source_paths': list(board_publication_bundle_manifest.get('canonical_source_paths', []) or []),
            'artifact_class_summary_line': str(board_publication_bundle_manifest.get('artifact_class_summary_line') or ''),
        },
        'verification_envelope': verification_envelope,
    }


__all__ = ['_build_board_export_payload']
