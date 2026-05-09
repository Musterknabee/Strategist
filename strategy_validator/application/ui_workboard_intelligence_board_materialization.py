from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from strategy_validator.application.ui_workboard_intelligence_foundations import _coerce_datetime


def _build_board_materialization_status(*, workboard: Mapping[str, Any], workbench: Mapping[str, Any], now_utc: datetime) -> dict[str, Any]:
    entries = list(workboard.get('entries', []) or [])
    governed_count = int(workboard.get('governed_work_item_count', 0)) or sum(
        1 for entry in entries if str(entry.get('source_kind') or '') == 'GOVERNED_PRIMARY'
    )
    journaled_count = int(workboard.get('journaled_work_item_count', 0)) or sum(
        1 for entry in entries if str(entry.get('source_kind') or '') == 'JOURNALED_PENDING'
    )

    journal_times = [
        _coerce_datetime(str(entry.get('source_created_at_utc') or ''))
        for entry in entries
        if str(entry.get('source_kind') or '') == 'JOURNALED_PENDING'
    ]
    journal_times = [value for value in journal_times if value is not None]

    projection_times = [
        _coerce_datetime(str(item.get('generated_at_utc') or ''))
        for column in (workbench.get('columns', []) or [])
        for item in (column.get('items', []) or [])
    ]
    projection_times = [value for value in projection_times if value is not None]

    latest_journal_at = _coerce_datetime(str(workboard.get('latest_journaled_action_at_utc') or ''))
    if latest_journal_at is None:
        latest_journal_at = max(journal_times) if journal_times else None
    latest_projection_at = max(projection_times) if projection_times else None

    if journaled_count == 0:
        freshness_state = 'CURRENT'
        materialization_state = 'GOVERNED_ONLY'
        summary_line = 'Board is currently governed-only; no journal-backed pending items require projection catch-up.'
    elif latest_projection_at is None:
        freshness_state = 'UNKNOWN'
        materialization_state = 'JOURNALED_PENDING_UNREFRESHED'
        summary_line = 'Journal-backed pending items exist, but no projection issuance is available to confirm refresh state.'
    elif latest_journal_at is not None and latest_journal_at > latest_projection_at:
        freshness_state = 'STALE'
        materialization_state = 'JOURNALED_PENDING_UNREFRESHED'
        summary_line = 'Journal-backed pending items are newer than the latest projection issuance; refresh is required before treating the board as fully materialized.'
    else:
        freshness_state = 'CURRENT'
        materialization_state = 'JOURNALED_CURRENT'
        summary_line = 'Journal-backed pending items are visible and the latest projection issuance is at least as recent as the action journal.'

    post_merge_ready_count = int(workboard.get('journal_post_merge_ready_count', 0) or 0)
    post_merge_review_required_count = int(workboard.get('journal_post_merge_review_required_count', 0) or 0)
    post_merge_stale_count = int(workboard.get('journal_post_merge_stale_count', 0) or 0)
    downstream_closure_ready_count = int(workboard.get('journal_downstream_closure_ready_count', 0) or 0)
    downstream_closure_review_required_count = int(workboard.get('journal_downstream_closure_review_required_count', 0) or 0)
    downstream_closure_blocked_count = int(workboard.get('journal_downstream_closure_blocked_count', 0) or 0)
    projection_summary_line = str(workboard.get('journal_projection_summary_line') or '').strip() or None
    projection_enabled = bool(workboard.get('journal_projection_enabled', False))
    projection_status_state = str(workboard.get('journal_projection_status_state') or 'DISABLED')
    projection_status_reason = str(workboard.get('journal_projection_status_reason') or '')
    projection_trust_status = str(workboard.get('journal_projection_trust_status') or 'TRUST_RESTRICTED')
    projection_source_label = str(workboard.get('journal_projection_source_label') or 'operator_action_journal')
    projection_ledger_db_path_configured = bool(workboard.get('journal_projection_ledger_db_path_configured', False))
    if not projection_enabled:
        materialization_state = 'PROJECTION_DISABLED'
        freshness_state = 'TRUST_RESTRICTED'
    summary_line = (
        f"{summary_line} Downstream closure posture: ready={downstream_closure_ready_count}, "
        f"review_required={downstream_closure_review_required_count}, blocked={downstream_closure_blocked_count}."
    )
    return {
        'materialization_state': materialization_state,
        'freshness_state': freshness_state,
        'governed_work_item_count': governed_count,
        'journaled_work_item_count': journaled_count,
        'latest_journaled_action_at_utc': latest_journal_at.isoformat() if latest_journal_at else None,
        'latest_projection_generated_at_utc': latest_projection_at.isoformat() if latest_projection_at else None,
        'journal_operator_count': int(workboard.get('journal_operator_count', 0) or 0),
        'journal_action_count': int(workboard.get('journal_action_count', 0) or 0),
        'journal_primary_merge_pending_count': int(workboard.get('journal_primary_merge_pending_count', 0) or 0),
        'journal_auxiliary_merge_pending_count': int(workboard.get('journal_auxiliary_merge_pending_count', 0) or 0),
        'journal_post_merge_ready_count': post_merge_ready_count,
        'journal_post_merge_review_required_count': post_merge_review_required_count,
        'journal_post_merge_stale_count': post_merge_stale_count,
        'journal_downstream_closure_ready_count': downstream_closure_ready_count,
        'journal_downstream_closure_review_required_count': downstream_closure_review_required_count,
        'journal_downstream_closure_blocked_count': downstream_closure_blocked_count,
        'projection_summary_line': projection_summary_line,
        'projection_enabled': projection_enabled,
        'projection_status_state': projection_status_state,
        'projection_status_reason': projection_status_reason,
        'projection_trust_status': projection_trust_status,
        'projection_source_label': projection_source_label,
        'projection_ledger_db_path_configured': projection_ledger_db_path_configured,
        'summary_line': summary_line,
    }


__all__ = [
    '_build_board_materialization_status',
]
