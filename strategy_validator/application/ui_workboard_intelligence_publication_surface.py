from __future__ import annotations

from typing import Any, Mapping

from strategy_validator.application.ui_workboard_intelligence_foundations import _slugify_for_path, _unique_nonempty_paths
from strategy_validator.application.ui_workboard_intelligence_publication_members import _build_publication_member_payload


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


__all__ = ['_build_board_publication_surface']
