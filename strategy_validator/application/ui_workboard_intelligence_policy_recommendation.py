from __future__ import annotations

from typing import Any, Mapping

from strategy_validator.application.ui_workboard_intelligence_foundations import (
    _TRUST_ALERT_STATUSES,
    _normalize_tokens,
)

def _append_policy_signal(signals: list[dict[str, Any]], *, kind: str, severity: str, summary_line: str) -> None:
    for existing in signals:
        if str(existing.get('kind')) == kind:
            return
    signals.append({
        'kind': kind,
        'severity': severity,
        'summary_line': summary_line,
    })


def _build_policy_recommendation(
    *,
    entry: Mapping[str, Any],
    linked_pack: Mapping[str, Any] | None,
    projection_state: str,
    attention_state: str,
    blocking_reason: str | None,
    state_history: Mapping[str, Any],
    command_readiness: Mapping[str, Any],
    action_provenance: Mapping[str, Any],
    operator_brief: Mapping[str, Any],
) -> dict[str, Any]:
    readiness_items = list(command_readiness.get('items', []) or [])
    ready_actions = [str(item.get('action')) for item in readiness_items if str(item.get('state')) == 'READY']
    caution_actions = [str(item.get('action')) for item in readiness_items if str(item.get('state')) == 'CAUTION']
    blocked_actions = [str(item.get('action')) for item in readiness_items if str(item.get('state')) == 'BLOCKED']
    lawful_next_action = ready_actions[0] if ready_actions else (caution_actions[0] if caution_actions else None)
    lawful_next_action_state = (
        'READY' if ready_actions else ('CAUTION' if caution_actions else None)
    )

    contradictions: list[dict[str, Any]] = []
    drift_flags: list[str] = []
    anomaly_flags: list[str] = []
    drift_signals: list[dict[str, Any]] = []
    anomaly_details: list[dict[str, Any]] = []
    trust_status = str((linked_pack or {}).get('trust_status') or '').upper()
    current_state_label = str(state_history.get('current_state_label') or '').upper()
    prior_state_label = str(state_history.get('prior_state_label') or '').upper()
    review_target = str(entry.get('review_target') or 'this queue item')
    priority_band = str(entry.get('priority_band') or '').upper()
    urgency = str(entry.get('urgency') or '').upper()
    recommended_action_tokens = _normalize_tokens(*[str(item) for item in entry.get('recommended_actions', []) or []])
    evidence_anchor_count = int(action_provenance.get('evidence_anchor_count', 0) or 0)
    high_pressure_lane = attention_state in {'ACT_NOW', 'ESCALATE'} or 'CRITICAL' in priority_band or 'HIGH' in urgency

    if linked_pack is None:
        anomaly_flags.append('UNLINKED_LINEAGE')
        _append_policy_signal(
            anomaly_details,
            kind='UNLINKED_LINEAGE',
            severity='HIGH' if high_pressure_lane else 'MEDIUM',
            summary_line=f'{review_target} has no linked pack/publication lineage, so queue posture cannot be treated as durable evidence yet.',
        )
    elif evidence_anchor_count <= 0:
        anomaly_flags.append('EVIDENCE_ANCHOR_GAP')
        _append_policy_signal(
            anomaly_details,
            kind='EVIDENCE_ANCHOR_GAP',
            severity='HIGH',
            summary_line=f'{review_target} is linked to a pack, but no evidence anchor paths were recovered for operator commands.',
        )

    if projection_state == 'STALE':
        drift_flags.append('STALE_LINKAGE')
        _append_policy_signal(
            drift_signals,
            kind='STALE_LINKAGE',
            severity='HIGH' if high_pressure_lane else 'MEDIUM',
            summary_line=f'{review_target} is operating on stale lineage data; refresh or re-open evidence before relying on the queue posture.',
        )
    elif projection_state == 'AGING':
        drift_flags.append('AGING_LINKAGE')
        _append_policy_signal(
            drift_signals,
            kind='AGING_LINKAGE',
            severity='MEDIUM',
            summary_line=f'{review_target} is attached to aging lineage data; treat commands as cautionary until freshness is confirmed.',
        )

    if prior_state_label and current_state_label and prior_state_label != current_state_label:
        drift_flags.append('TRUST_SHIFT')
        _append_policy_signal(
            drift_signals,
            kind='TRUST_SHIFT',
            severity='HIGH' if current_state_label in _TRUST_ALERT_STATUSES else 'MEDIUM',
            summary_line=f'{review_target} moved from {prior_state_label or "UNKNOWN"} to {current_state_label or "UNKNOWN"} across recent indexed issuances.',
        )
        if prior_state_label not in _TRUST_ALERT_STATUSES and current_state_label in _TRUST_ALERT_STATUSES:
            drift_flags.append('DOWNWARD_TRUST_SHIFT')
            _append_policy_signal(
                drift_signals,
                kind='DOWNWARD_TRUST_SHIFT',
                severity='HIGH',
                summary_line=f'{review_target} regressed into an alert trust posture; operator handling should favor escalation and evidence review.',
            )
        elif prior_state_label in _TRUST_ALERT_STATUSES and current_state_label and current_state_label not in _TRUST_ALERT_STATUSES:
            drift_flags.append('TRUST_RECOVERY')
            _append_policy_signal(
                drift_signals,
                kind='TRUST_RECOVERY',
                severity='MEDIUM',
                summary_line=f'{review_target} recovered out of an alert trust posture, but recent history still warrants confirmation before routine throughput.',
            )

    if trust_status in _TRUST_ALERT_STATUSES:
        anomaly_flags.append('TRUST_ALERT')
        _append_policy_signal(
            anomaly_details,
            kind='TRUST_ALERT',
            severity='HIGH',
            summary_line=f'{review_target} is anchored to a {trust_status} lineage; operator commands should be treated as investigation-grade rather than routine.',
        )

    if lawful_next_action:
        lawful_tokens = _normalize_tokens(lawful_next_action)
        if recommended_action_tokens and lawful_tokens and not recommended_action_tokens.intersection(lawful_tokens):
            drift_flags.append('RECOMMENDED_ACTION_DRIFT')
            _append_policy_signal(
                drift_signals,
                kind='RECOMMENDED_ACTION_DRIFT',
                severity='MEDIUM',
                summary_line=f'Queue copy for {review_target} points operators away from the current lawful next action {lawful_next_action.replace("-", " ")}.',
            )

    if attention_state == 'BLOCKED' and (ready_actions or caution_actions):
        contradictions.append({
            'kind': 'GOVERNED_BLOCK_WITH_ACTIONABLE_COMMAND',
            'severity': 'HIGH',
            'summary_line': 'The queue is governed-blocked while at least one command still appears actionable; treat the lane as evidence review only.',
        })
    if trust_status in _TRUST_ALERT_STATUSES and attention_state not in {'ESCALATE', 'BLOCKED'}:
        contradictions.append({
            'kind': 'TRUST_ALERT_WITHOUT_ESCALATION',
            'severity': 'HIGH' if attention_state == 'ACT_NOW' else 'MEDIUM',
            'summary_line': f'Linked lineage trust posture is {trust_status}, but the queue attention state is only {attention_state}.',
        })
    if projection_state == 'STALE' and lawful_next_action_state == 'READY':
        contradictions.append({
            'kind': 'STALE_LINKAGE_WITH_READY_ACTION',
            'severity': 'HIGH' if high_pressure_lane else 'MEDIUM',
            'summary_line': 'A command is marked READY even though the linked lineage is stale; refresh evidence before relying on the queue posture.',
        })
    if linked_pack is None and lawful_next_action is not None:
        contradictions.append({
            'kind': 'ACTION_WITHOUT_LINKED_LINEAGE',
            'severity': 'HIGH',
            'summary_line': 'A command suggestion exists without a linked pack/publication lineage; do not treat it as durable until the lineage is resolved.',
        })
    if projection_state == 'STALE' and attention_state == 'ACT_NOW':
        contradictions.append({
            'kind': 'IMMEDIATE_POSTURE_WITH_STALE_LINKAGE',
            'severity': 'HIGH',
            'summary_line': 'The queue is asking for immediate operator handling while the linked lineage is stale.',
        })
    if lawful_next_action == 'acknowledge-reentry' and trust_status in _TRUST_ALERT_STATUSES:
        contradictions.append({
            'kind': 'REENTRY_ON_ALERT_LINEAGE',
            'severity': 'HIGH',
            'summary_line': 'Acknowledge re-entry is being suggested against an alert-trust lineage; hold the lane in review until the evidence posture improves.',
        })

    if lawful_next_action and lawful_next_action_state:
        summary_line = (
            f"Lawful next action is {lawful_next_action.replace('-', ' ')} ({lawful_next_action_state}) for {review_target}."
        )
        rationale_line = str(operator_brief.get('why_now_line') or command_readiness.get('summary_line') or '')
    else:
        summary_line = f'No direct command is currently lawful for {review_target}; keep the lane in evidence review.'
        rationale_line = blocking_reason or str(command_readiness.get('summary_line') or '') or 'The current queue posture does not support a governed command.'

    if blocked_actions:
        unsafe_actions = list(dict.fromkeys(blocked_actions + ([*caution_actions] if trust_status in _TRUST_ALERT_STATUSES or projection_state in {'AGING', 'STALE'} else [])))
    else:
        unsafe_actions = list(dict.fromkeys(caution_actions if trust_status in _TRUST_ALERT_STATUSES or projection_state in {'AGING', 'STALE'} else []))

    primary_anchor = str(action_provenance.get('primary_publication_path') or action_provenance.get('pack_manifest_path') or '') or 'the linked evidence anchor'
    action_label = lawful_next_action.replace('-', ' ') if lawful_next_action else "any queue action"
    evidence_check_line = f'Policy check: verify {primary_anchor} before relying on {action_label}.'
    operator_line = 'Unsafe alternatives: ' + ', '.join(action.replace('-', ' ') for action in unsafe_actions) + '.' if unsafe_actions else 'No unsafe alternatives are currently surfaced beyond the lawful path.'

    return {
        'summary_line': summary_line,
        'lawful_next_action': lawful_next_action,
        'lawful_next_action_state': lawful_next_action_state,
        'rationale_line': rationale_line,
        'evidence_check_line': evidence_check_line,
        'operator_line': operator_line,
        'blocked_actions': blocked_actions,
        'caution_actions': caution_actions,
        'unsafe_actions': unsafe_actions,
        'contradictions': contradictions,
        'drift_flags': drift_flags,
        'anomaly_flags': anomaly_flags,
        'drift_signals': drift_signals,
        'anomaly_details': anomaly_details,
    }


__all__ = [
    '_append_policy_signal',
    '_build_policy_recommendation',
]
