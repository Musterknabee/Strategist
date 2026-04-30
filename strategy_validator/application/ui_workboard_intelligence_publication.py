from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from strategy_validator.application.ui_workboard_intelligence_foundations import _slugify_for_path, _unique_nonempty_paths



def _build_publication_member_payload(
    *,
    export_key: str,
    board_operator_brief: Mapping[str, Any],
    board_governance_clusters: Mapping[str, Any],
    board_governance_digest: Mapping[str, Any],
    board_evidence_briefing: Mapping[str, Any],
) -> dict[str, Any] | None:
    if export_key == 'board_governance_digest':
        return {
            'schema_version': 'oracle_operator_board_governance_digest/v1',
            'publication_family': 'oracle_operator_board_governance_digest',
            'summary_line': str(board_governance_digest.get('summary_line') or ''),
            'action_line': str(board_governance_digest.get('action_line') or ''),
            'focus_line': str(board_governance_digest.get('focus_line') or ''),
            'cluster_line': str(board_governance_digest.get('cluster_line') or ''),
            'watch_line': str(board_governance_digest.get('watch_line') or ''),
            'closure_line': str(board_governance_digest.get('closure_line') or ''),
            'watch_items': list(board_governance_digest.get('watch_items', []) or []),
            'source_paths': list(board_governance_digest.get('source_paths', []) or []),
            'focus_work_item_key': board_governance_digest.get('focus_work_item_key'),
            'focus_action': board_governance_digest.get('focus_action'),
            'top_cluster_signal_kind': board_governance_digest.get('top_cluster_signal_kind'),
            'high_severity_count': int(board_governance_digest.get('high_severity_count') or 0),
            'cluster_count': int(board_governance_digest.get('cluster_count') or 0),
            'focus_projection_post_merge_lifecycle_state': board_governance_digest.get('focus_projection_post_merge_lifecycle_state'),
            'focus_projection_downstream_closure_state': board_governance_digest.get('focus_projection_downstream_closure_state'),
            'journal_downstream_closure_ready_count': int(board_governance_digest.get('journal_downstream_closure_ready_count') or 0),
            'journal_downstream_closure_review_required_count': int(board_governance_digest.get('journal_downstream_closure_review_required_count') or 0),
            'journal_downstream_closure_blocked_count': int(board_governance_digest.get('journal_downstream_closure_blocked_count') or 0),
        }
    if export_key == 'board_evidence_briefing':
        return {
            'schema_version': 'oracle_operator_board_evidence_briefing/v1',
            'publication_family': 'oracle_operator_board_evidence_briefing',
            'summary_line': str(board_evidence_briefing.get('summary_line') or ''),
            'focus_line': str(board_evidence_briefing.get('focus_line') or ''),
            'pressure_line': str(board_evidence_briefing.get('pressure_line') or ''),
            'action_line': str(board_evidence_briefing.get('action_line') or ''),
            'evidence_line': str(board_evidence_briefing.get('evidence_line') or ''),
            'watch_items': list(board_evidence_briefing.get('watch_items', []) or []),
            'focus_work_item_key': board_evidence_briefing.get('focus_work_item_key'),
            'source_paths': list(board_evidence_briefing.get('source_paths', []) or []),
        }
    if export_key == 'board_cluster_summary':
        top_cluster = ((board_governance_clusters.get('clusters') or [])[:1] or [None])[0] or {}
        return {
            'schema_version': 'oracle_operator_board_cluster_summary/v1',
            'publication_family': 'oracle_operator_board_cluster_summary',
            'summary_line': str(top_cluster.get('summary_line') or board_governance_clusters.get('summary_line') or ''),
            'pressure_line': str(board_governance_clusters.get('pressure_line') or ''),
            'operator_line': str(top_cluster.get('operator_line') or ''),
            'sample_summary_line': top_cluster.get('sample_summary_line'),
            'cluster_count': int(board_governance_clusters.get('cluster_count') or 0),
            'top_cluster_signal_kind': str(top_cluster.get('signal_kind') or '') or None,
            'top_cluster_category': str(top_cluster.get('category') or '') or None,
            'top_cluster_severity': str(top_cluster.get('dominant_severity') or '') or None,
            'affected_item_count': int(top_cluster.get('affected_item_count') or 0),
            'affected_work_item_keys': list(top_cluster.get('affected_work_item_keys', []) or []),
            'affected_review_targets': list(top_cluster.get('affected_review_targets', []) or []),
            'source_paths': list(top_cluster.get('source_paths', []) or []),
        }
    if export_key == 'board_focus_action_posture':
        return {
            'schema_version': 'oracle_operator_board_focus_action_posture/v1',
            'publication_family': 'oracle_operator_board_focus_action_posture',
            'summary_line': str(board_operator_brief.get('throughput_line') or board_governance_digest.get('action_line') or ''),
            'focus_line': str(board_operator_brief.get('summary_line') or ''),
            'throughput_line': str(board_operator_brief.get('throughput_line') or ''),
            'evidence_check_line': str(board_operator_brief.get('evidence_check_line') or ''),
            'blocked_follow_up_line': str(board_operator_brief.get('blocked_follow_up_line') or ''),
            'closure_follow_up_line': str(board_operator_brief.get('closure_follow_up_line') or board_governance_digest.get('closure_line') or ''),
            'focus_work_item_key': board_operator_brief.get('focus_work_item_key'),
            'focus_action': board_operator_brief.get('focus_action'),
            'source_paths': _unique_nonempty_paths(
                *[str(path) for path in board_evidence_briefing.get('source_paths', []) or []],
                extra_paths=[str(path) for path in board_governance_digest.get('source_paths', []) or []],
            ),
        }
    return None


def _build_board_publication_surface(
    *,
    workboard: Mapping[str, Any],
    ranked_items: list[Mapping[str, Any]],
    board_operator_brief: Mapping[str, Any],
    board_governance_snapshot: Mapping[str, Any],
    board_governance_clusters: Mapping[str, Any],
    board_evidence_briefing: Mapping[str, Any],
    board_governance_digest: Mapping[str, Any],
) -> dict[str, Any]:
    board_label = _slugify_for_path(str(workboard.get('board_label') or 'operator'))
    queue_key = _slugify_for_path(str(workboard.get('queue_key') or 'workboard'))
    bundle_root = f"generated/publications/{board_label}/{queue_key}"
    published_bundle_root = f"published/publications/{board_label}/{queue_key}"

    top_cluster = ((board_governance_clusters.get('clusters') or [])[:1] or [None])[0]
    focus_item = ranked_items[0] if ranked_items else None
    focus_key = str((focus_item or {}).get('work_item_key') or board_governance_digest.get('focus_work_item_key') or '') or None
    focus_action = str(board_governance_digest.get('focus_action') or board_operator_brief.get('focus_action') or '') or None
    top_cluster_signal_kind = str((top_cluster or {}).get('signal_kind') or board_governance_digest.get('top_cluster_signal_kind') or '') or None
    closure_ready_count = int(board_governance_digest.get('journal_downstream_closure_ready_count') or 0)
    closure_review_required_count = int(board_governance_digest.get('journal_downstream_closure_review_required_count') or 0)
    closure_blocked_count = int(board_governance_digest.get('journal_downstream_closure_blocked_count') or 0)
    focus_closure_state = str(board_governance_digest.get('focus_projection_downstream_closure_state') or '') or None
    export_state = 'EXPORT_READY' if ranked_items else 'IDLE'

    normalized_members = [
        {
            'export_key': 'board_governance_digest',
            'schema_version': 'oracle_operator_board_governance_digest/v1',
            'title': 'Board governance digest',
            'relative_publication_path': f"{bundle_root}/board_governance_digest.json",
            'generated_relative_path': f"{bundle_root}/board_governance_digest.json",
            'published_relative_path': f"{published_bundle_root}/board_governance_digest.json",
            'media_type': 'application/json',
            'summary_line': str(board_governance_digest.get('summary_line') or 'No board governance digest is available.'),
            'source_paths': list(board_governance_digest.get('source_paths', []) or []),
        },
        {
            'export_key': 'board_evidence_briefing',
            'schema_version': 'oracle_operator_board_evidence_briefing/v1',
            'title': 'Board evidence briefing',
            'relative_publication_path': f"{bundle_root}/board_evidence_briefing.json",
            'generated_relative_path': f"{bundle_root}/board_evidence_briefing.json",
            'published_relative_path': f"{published_bundle_root}/board_evidence_briefing.json",
            'media_type': 'application/json',
            'summary_line': str(board_evidence_briefing.get('summary_line') or 'No board evidence briefing is available.'),
            'source_paths': list(board_evidence_briefing.get('source_paths', []) or []),
        },
        {
            'export_key': 'board_cluster_summary',
            'schema_version': 'oracle_operator_board_cluster_summary/v1',
            'title': 'Board governance cluster summary',
            'relative_publication_path': f"{bundle_root}/board_cluster_summary.json",
            'generated_relative_path': f"{bundle_root}/board_cluster_summary.json",
            'published_relative_path': f"{published_bundle_root}/board_cluster_summary.json",
            'media_type': 'application/json',
            'summary_line': str((top_cluster or {}).get('summary_line') or board_governance_clusters.get('summary_line') or 'No board governance cluster summary is available.'),
            'source_paths': list((top_cluster or {}).get('source_paths', []) or []),
        },
        {
            'export_key': 'board_focus_action_posture',
            'schema_version': 'oracle_operator_board_focus_action_posture/v1',
            'title': 'Board focus action posture',
            'relative_publication_path': f"{bundle_root}/board_focus_action_posture.json",
            'generated_relative_path': f"{bundle_root}/board_focus_action_posture.json",
            'published_relative_path': f"{published_bundle_root}/board_focus_action_posture.json",
            'media_type': 'application/json',
            'summary_line': str(board_operator_brief.get('throughput_line') or board_governance_digest.get('action_line') or 'No board focus action posture is available.'),
            'source_paths': _unique_nonempty_paths(
                *[str(path) for path in board_evidence_briefing.get('source_paths', []) or []],
                extra_paths=[str(path) for path in board_governance_digest.get('source_paths', []) or []],
            ),
        },
    ]
    for member in normalized_members:
        payload_object = _build_publication_member_payload(
            export_key=str(member.get('export_key') or ''),
            board_operator_brief=board_operator_brief,
            board_governance_clusters=board_governance_clusters,
            board_governance_digest=board_governance_digest,
            board_evidence_briefing=board_evidence_briefing,
        )
        member['payload_state'] = 'EMBEDDED' if payload_object is not None else 'METADATA_ONLY'
        member['payload_object'] = payload_object
        member['artifact_class'] = 'GENERATED'
        member['publication_stage'] = 'GENERATED_READY'
        member['source_backing_state'] = 'SOURCE_BACKED' if (member.get('source_paths') or []) else 'DERIVED_ONLY'

    canonical_source_paths = _unique_nonempty_paths(
        *[str(path) for member in normalized_members for path in member.get('source_paths', []) or []]
    )

    generated_member_count = sum(1 for member in normalized_members if str(member.get('artifact_class') or '') == 'GENERATED')
    published_member_count = sum(1 for member in normalized_members if str(member.get('publication_stage') or '') == 'PUBLISHED')
    source_backed_member_count = sum(1 for member in normalized_members if str(member.get('source_backing_state') or '') == 'SOURCE_BACKED')
    artifact_class_summary_line = (
        f"Artifact-class posture: {generated_member_count} generated member(s), {published_member_count} published member(s), and "
        f"{source_backed_member_count} source-backed member(s) are currently tracked."
    )

    if ranked_items:
        summary_line = (
            f"Board publication surface: {len(normalized_members)} machine-readable export member(s) are normalized for "
            f"{focus_key or 'the current focus lane'} under {bundle_root}; downstream closure counts are "
            f"ready={closure_ready_count}, review_required={closure_review_required_count}, blocked={closure_blocked_count}."
        )
        export_line = (
            f"Export posture: {focus_key or 'the board'} remains {export_state} with focus action "
            f"{focus_action.replace('-', ' ') if focus_action else 'evidence review'}, top cluster "
            f"{top_cluster_signal_kind or 'none'}, and focus closure state {focus_closure_state or 'none'}."
        )
    else:
        summary_line = 'Board publication surface: no ranked items are available, so no export members are currently normalized.'
        export_line = 'Export posture: board publication remains idle until ranked items appear.'

    return {
        'schema_version': 'oracle_operator_board_publication_surface/v1',
        'publication_family': 'oracle_operator_board_publication_surface',
        'export_state': export_state,
        'summary_line': summary_line,
        'export_line': export_line,
        'bundle_root': bundle_root,
        'published_bundle_root': published_bundle_root,
        'focus_work_item_key': focus_key,
        'focus_action': focus_action,
        'top_cluster_signal_kind': top_cluster_signal_kind,
        'focus_projection_downstream_closure_state': focus_closure_state,
        'journal_downstream_closure_ready_count': closure_ready_count,
        'journal_downstream_closure_review_required_count': closure_review_required_count,
        'journal_downstream_closure_blocked_count': closure_blocked_count,
        'canonical_source_paths': canonical_source_paths,
        'embedded_payload_count': sum(1 for member in normalized_members if member.get('payload_state') == 'EMBEDDED'),
        'generated_member_count': generated_member_count,
        'published_member_count': published_member_count,
        'source_backed_member_count': source_backed_member_count,
        'artifact_class_summary_line': artifact_class_summary_line,
        'normalized_members': normalized_members,
    }


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


__all__ = [
    '_build_publication_member_payload',
    '_build_board_publication_surface',
    '_stable_json_sha256',
    '_build_board_publication_verification_envelope',
    '_build_board_publication_bundle_manifest',
    '_build_board_export_payload',
]
