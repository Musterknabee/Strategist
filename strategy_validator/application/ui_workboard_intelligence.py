from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from strategy_validator.application.ui_workboard_intelligence_board import (
    _build_board_evidence_briefing,
    _build_board_governance_clusters,
    _build_board_governance_digest,
    _build_board_governance_snapshot,
    _build_board_materialization_status,
    _build_board_operator_brief,
)
from strategy_validator.application.ui_workboard_intelligence_foundations import (
    _TRUST_ALERT_STATUSES,
    _attention_state,
    _build_state_history,
    _linked_pack_for_entry,
    _priority_bonus,
    _projection_age_state,
    _utc_now,
)
from strategy_validator.application.ui_workboard_intelligence_policy import (
    _build_action_provenance,
    _build_command_readiness,
    _build_evidence_backed_briefing,
    _build_operator_brief,
    _build_policy_recommendation,
)
from strategy_validator.application.ui_workboard_intelligence_publication import (
    _build_board_export_payload,
    _build_board_publication_bundle_manifest,
    _build_board_publication_surface,
)


def build_workboard_intelligence(*, workboard: Mapping[str, Any], workbench: Mapping[str, Any], now_utc: datetime | None = None) -> dict[str, Any]:
    now = now_utc or _utc_now()
    columns = workbench.get('columns', []) or []
    ranked_items: list[dict[str, Any]] = []
    for entry in workboard.get('entries', []) or []:
        linked_pack = _linked_pack_for_entry(entry, columns)
        projection_state, projection_age_hours = _projection_age_state(
            generated_at_utc=(linked_pack or {}).get('generated_at_utc') if linked_pack else None,
            now_utc=now,
        )
        attention_state, blocking_reason = _attention_state(entry, linked_pack)
        priority_score = int(entry.get('score', 0)) + _priority_bonus(entry)
        if linked_pack is None:
            priority_score += 5
        else:
            if str(linked_pack.get('trust_status') or '').upper() in _TRUST_ALERT_STATUSES:
                priority_score += 10
            if projection_state == 'STALE':
                priority_score += 8
            elif projection_state == 'AGING':
                priority_score += 4
        closure_state = str(entry.get('projection_downstream_closure_state') or '')
        if closure_state == 'DOWNSTREAM_CLOSURE_BLOCKED':
            priority_score += 9
        elif closure_state == 'DOWNSTREAM_CLOSURE_REVIEW_REQUIRED':
            priority_score += 5
        elif closure_state.endswith('READY'):
            priority_score += 2
        state_history = _build_state_history(entry=entry, linked_pack=linked_pack, columns=columns)
        command_readiness = _build_command_readiness(
            entry=entry,
            linked_pack=linked_pack,
            projection_state=projection_state,
            attention_state=attention_state,
            blocking_reason=blocking_reason,
        )
        action_provenance = _build_action_provenance(entry=entry, linked_pack=linked_pack)
        operator_brief = _build_operator_brief(
            entry=entry,
            projection_state=projection_state,
            attention_state=attention_state,
            blocking_reason=blocking_reason,
            state_history=state_history,
            command_readiness=command_readiness,
            action_provenance=action_provenance,
        )
        policy_recommendation = _build_policy_recommendation(
            entry=entry,
            linked_pack=linked_pack,
            projection_state=projection_state,
            attention_state=attention_state,
            blocking_reason=blocking_reason,
            state_history=state_history,
            command_readiness=command_readiness,
            action_provenance=action_provenance,
            operator_brief=operator_brief,
        )
        evidence_backed_briefing = _build_evidence_backed_briefing(
            entry=entry,
            action_provenance=action_provenance,
            operator_brief=operator_brief,
            policy_recommendation=policy_recommendation,
        )
        ranked_items.append({
            'work_item_key': entry.get('work_item_key'),
            'review_target': entry.get('review_target'),
            'priority_band': entry.get('priority_band'),
            'urgency': entry.get('urgency'),
            'score': int(entry.get('score', 0)),
            'priority_score': priority_score,
            'attention_state': attention_state,
            'blocking_reason': blocking_reason,
            'recommended_action': (entry.get('recommended_actions') or [None])[0],
            'linked_pack': linked_pack,
            'projection_recency': {
                'state': projection_state,
                'age_hours': projection_age_hours,
            },
            'projection_governed_merge_state': entry.get('projection_governed_merge_state'),
            'projection_governed_summary_line': entry.get('projection_governed_summary_line'),
            'projection_post_merge_lifecycle_state': entry.get('projection_post_merge_lifecycle_state'),
            'projection_post_merge_summary_line': entry.get('projection_post_merge_summary_line'),
            'projection_downstream_closure_state': entry.get('projection_downstream_closure_state'),
            'projection_downstream_closure_summary_line': entry.get('projection_downstream_closure_summary_line'),
            'state_history': state_history,
            'command_readiness': command_readiness,
            'action_provenance': action_provenance,
            'operator_brief': operator_brief,
            'policy_recommendation': policy_recommendation,
            'evidence_backed_briefing': evidence_backed_briefing,
        })
    ranked_items.sort(key=lambda item: (-int(item['priority_score']), str(item.get('work_item_key') or '')))
    for index, item in enumerate(ranked_items, start=1):
        item['rank'] = index

    blocked_count = sum(1 for item in ranked_items if item['attention_state'] == 'BLOCKED')
    escalation_count = sum(1 for item in ranked_items if item['attention_state'] == 'ESCALATE')
    missing_link_count = sum(1 for item in ranked_items if item['linked_pack'] is None)
    stale_link_count = sum(1 for item in ranked_items if item['projection_recency']['state'] == 'STALE')
    linked_count = len(ranked_items) - missing_link_count
    closure_ready_count = sum(1 for item in ranked_items if str(item.get('projection_downstream_closure_state') or '').endswith('READY'))
    closure_review_required_count = sum(1 for item in ranked_items if str(item.get('projection_downstream_closure_state') or '') == 'DOWNSTREAM_CLOSURE_REVIEW_REQUIRED')
    closure_blocked_count = sum(1 for item in ranked_items if str(item.get('projection_downstream_closure_state') or '') == 'DOWNSTREAM_CLOSURE_BLOCKED')

    top_summary = 'No active work items are currently ranked.'
    if ranked_items:
        head = ranked_items[0]
        top_summary = (
            f"Next operator focus is {head.get('work_item_key')} ({head.get('attention_state')}) "
            f"with priority score {head.get('priority_score')} targeting {head.get('review_target')}; "
            f"downstream closure state is {str(head.get('projection_downstream_closure_state') or 'none')}."
        )

    board_materialization_status = _build_board_materialization_status(workboard=workboard, workbench=workbench, now_utc=now)
    board_operator_brief = _build_board_operator_brief(ranked_items=ranked_items)
    board_governance_snapshot = _build_board_governance_snapshot(ranked_items=ranked_items)
    board_governance_clusters = _build_board_governance_clusters(ranked_items=ranked_items)
    board_evidence_briefing = _build_board_evidence_briefing(ranked_items=ranked_items)
    board_governance_digest = _build_board_governance_digest(
        ranked_items=ranked_items,
        board_operator_brief=board_operator_brief,
        board_governance_snapshot=board_governance_snapshot,
        board_governance_clusters=board_governance_clusters,
        board_evidence_briefing=board_evidence_briefing,
    )
    board_publication_surface = _build_board_publication_surface(
        workboard=workboard,
        ranked_items=ranked_items,
        board_operator_brief=board_operator_brief,
        board_governance_snapshot=board_governance_snapshot,
        board_governance_clusters=board_governance_clusters,
        board_evidence_briefing=board_evidence_briefing,
        board_governance_digest=board_governance_digest,
    )
    board_publication_bundle_manifest = _build_board_publication_bundle_manifest(
        board_publication_surface=board_publication_surface,
    )
    board_export_payload = _build_board_export_payload(
        board_publication_surface=board_publication_surface,
        board_publication_bundle_manifest=board_publication_bundle_manifest,
    )

    return {
        'schema_version': 'ui_workboard_intelligence/v1',
        'generated_at_utc': now.isoformat(),
        'summary': {
            'top_summary_line': top_summary,
            'ranked_count': len(ranked_items),
            'blocked_count': blocked_count,
            'escalation_count': escalation_count,
            'linked_count': linked_count,
            'missing_link_count': missing_link_count,
            'stale_link_count': stale_link_count,
            'closure_ready_count': closure_ready_count,
            'closure_review_required_count': closure_review_required_count,
            'closure_blocked_count': closure_blocked_count,
        },
        'board_materialization_status': board_materialization_status,
        'board_operator_brief': board_operator_brief,
        'board_governance_snapshot': board_governance_snapshot,
        'board_governance_clusters': board_governance_clusters,
        'board_evidence_briefing': board_evidence_briefing,
        'board_governance_digest': board_governance_digest,
        'board_publication_surface': board_publication_surface,
        'board_publication_bundle_manifest': board_publication_bundle_manifest,
        'board_export_payload': board_export_payload,
        'ranked_items': ranked_items,
    }


__all__ = [
    'build_workboard_intelligence',
]
