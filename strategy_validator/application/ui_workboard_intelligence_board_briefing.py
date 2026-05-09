from __future__ import annotations

from typing import Any, Mapping

def _build_board_evidence_briefing(*, ranked_items: list[Mapping[str, Any]]) -> dict[str, Any]:
    if not ranked_items:
        return {
            'summary_line': 'No evidence-backed briefing is available because the ranked queue is empty.',
            'focus_line': 'No focus item is currently generating governance pressure.',
            'pressure_line': 'Board pressure is idle: no contradictions, drift, or anomalies are currently active.',
            'action_line': 'No lawful next action is currently queued.',
            'evidence_line': 'No evidence anchors are currently required.',
            'watch_items': [],
            'focus_work_item_key': None,
            'source_paths': [],
        }

    focus = ranked_items[0]
    focus_policy = focus.get('policy_recommendation') or {}
    focus_brief = focus.get('evidence_backed_briefing') or {}
    focus_action = str(focus_policy.get('lawful_next_action') or '') or None
    focus_action_state = str(focus_policy.get('lawful_next_action_state') or '') or None
    focus_action_label = focus_action.replace('-', ' ') if focus_action else 'evidence review'
    contradiction_count = sum(len(list((item.get('policy_recommendation') or {}).get('contradictions', []) or [])) for item in ranked_items)
    drift_count = sum(len(list((item.get('policy_recommendation') or {}).get('drift_signals', []) or [])) for item in ranked_items)
    anomaly_count = sum(len(list((item.get('policy_recommendation') or {}).get('anomaly_details', []) or [])) for item in ranked_items)

    summary_line = (
        f"Board evidence-backed briefing: {focus.get('work_item_key')} is the current focus because it combines the highest queue pressure with the most actionable lineage-backed next step."
    )
    focus_line = (
        f"Focus lane: {focus.get('review_target')} is currently {focus.get('attention_state')} with lawful action "
        f"{focus_action_label}{f' ({focus_action_state})' if focus_action_state else ''}."
    )
    pressure_line = (
        f"Board pressure combines {contradiction_count} contradiction(s), {drift_count} drift detail(s), and {anomaly_count} anomaly detail(s) across {len(ranked_items)} ranked item(s)."
    )
    action_line = (
        f"Action focus: start with {focus_action_label}{f' ({focus_action_state})' if focus_action_state else ''} on {focus.get('work_item_key')} before lower-ranked queue work."
    )
    evidence_line = str(focus_brief.get('evidence_line') or 'Evidence line is not available for the current focus item.')

    watch_items: list[str] = []
    for item in [
        str(focus_brief.get('contradiction_line') or ''),
        str(focus_brief.get('drift_line') or ''),
        str(focus_brief.get('anomaly_line') or ''),
        *[str(item) for item in focus_brief.get('watch_items', []) or []],
    ]:
        if item and item not in watch_items:
            watch_items.append(item)

    return {
        'summary_line': summary_line,
        'focus_line': focus_line,
        'pressure_line': pressure_line,
        'action_line': action_line,
        'evidence_line': evidence_line,
        'watch_items': watch_items[:6],
        'focus_work_item_key': focus.get('work_item_key'),
        'source_paths': list(focus_brief.get('source_paths', []) or []),
    }
def _build_board_operator_brief(*, ranked_items: list[Mapping[str, Any]]) -> dict[str, Any]:
    if not ranked_items:
        return {
            'summary_line': 'No ranked work items are available yet.',
            'throughput_line': 'The board has no current operator pressure.',
            'evidence_check_line': 'No evidence checks are required until queue items appear.',
            'focus_work_item_key': None,
            'focus_action': None,
            'blocked_follow_up_line': 'Blocked, stale, and unlinked counts are all zero.',
            'closure_follow_up_line': 'No downstream closure pressure is currently active.',
        }

    focus = ranked_items[0]
    focus_brief = focus.get('operator_brief') or {}
    focus_action = str(focus_brief.get('safest_next_action') or '') or None
    focus_action_state = str(focus_brief.get('safest_next_action_state') or '') or None
    focus_action_label = focus_action.replace('-', ' ') if focus_action else 'review evidence'
    summary_line = (
        f"Focus first on {focus.get('work_item_key')} because it is the highest-ranked {focus.get('attention_state')} item targeting {focus.get('review_target')}."
    )
    if focus_action and focus_action_state:
        throughput_line = (
            f"Fastest safe lane is {focus_action_label} on {focus.get('work_item_key')} ({focus_action_state}); use the item brief before submitting it."
        )
    else:
        throughput_line = f"No direct command is ready on {focus.get('work_item_key')}; use evidence review before any mutation."
    blocked_count = sum(1 for item in ranked_items if item.get('attention_state') == 'BLOCKED')
    stale_count = sum(1 for item in ranked_items if (item.get('projection_recency') or {}).get('state') == 'STALE')
    missing_link_count = sum(1 for item in ranked_items if item.get('linked_pack') is None)
    closure_ready_count = sum(1 for item in ranked_items if str(item.get('projection_downstream_closure_state') or '').endswith('READY'))
    closure_review_required_count = sum(1 for item in ranked_items if str(item.get('projection_downstream_closure_state') or '') == 'DOWNSTREAM_CLOSURE_REVIEW_REQUIRED')
    closure_blocked_count = sum(1 for item in ranked_items if str(item.get('projection_downstream_closure_state') or '') == 'DOWNSTREAM_CLOSURE_BLOCKED')
    evidence_check_line = (
        f"Board-wide evidence check: {stale_count} stale linkage(s), {missing_link_count} unlinked item(s), and {blocked_count} blocked governed lane(s) need explicit review."
    )
    blocked_follow_up_line = 'After the top item, clear blocked or stale queue rows before routine throughput work to keep the board truthful under operator load.'
    closure_follow_up_line = (
        f"Downstream closure follow-up: ready={closure_ready_count}, review_required={closure_review_required_count}, blocked={closure_blocked_count}; "
        f"focus closure state is {str(focus.get('projection_downstream_closure_state') or 'none')}."
    )
    return {
        'summary_line': summary_line,
        'throughput_line': throughput_line,
        'evidence_check_line': evidence_check_line,
        'focus_work_item_key': focus.get('work_item_key'),
        'focus_action': focus_action,
        'blocked_follow_up_line': blocked_follow_up_line,
        'closure_follow_up_line': closure_follow_up_line,
    }


__all__ = [
    '_build_board_evidence_briefing',
    '_build_board_operator_brief',
]
