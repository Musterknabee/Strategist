from __future__ import annotations

from typing import Any, Mapping

from strategy_validator.application.ui_workboard_intelligence_foundations import _unique_nonempty_paths


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


__all__ = ['_build_publication_member_payload']
