from __future__ import annotations

from typing import Any, Mapping

from strategy_validator.application.ui_workboard_intelligence_foundations import (
    _unique_nonempty_paths,
)
from strategy_validator.application.ui_workboard_intelligence_policy_commands import (
    _command_item,
)

def _build_operator_brief(
    *,
    entry: Mapping[str, Any],
    projection_state: str,
    attention_state: str,
    blocking_reason: str | None,
    state_history: Mapping[str, Any],
    command_readiness: Mapping[str, Any],
    action_provenance: Mapping[str, Any],
) -> dict[str, Any]:
    review_target = str(entry.get('review_target') or 'work item')
    safest_next_action = str(command_readiness.get('top_action') or '') or None
    safest_action_item = _command_item(command_readiness, safest_next_action)
    safest_next_action_state = str((safest_action_item or {}).get('state') or '') or None
    safest_action_label = safest_next_action.replace('-', ' ') if safest_next_action else 'review evidence only'
    if safest_next_action and safest_next_action_state:
        summary_line = f"Safest next move is {safest_action_label} ({safest_next_action_state}) for {review_target}."
    elif attention_state == 'BLOCKED':
        summary_line = f"No direct command is ready for {review_target}; treat this as a blocked governed lane."
    else:
        summary_line = f"No direct command is ready for {review_target}; inspect the linked evidence before moving it."

    why_parts: list[str] = []
    if blocking_reason:
        why_parts.append(blocking_reason)
    if attention_state == 'ACT_NOW':
        why_parts.append('Queue urgency and priority place this item at the head of the active operator lane.')
    elif attention_state == 'REVIEW_SOON':
        why_parts.append('Queue priority is elevated enough that it should be reviewed before routine items.')
    elif attention_state == 'ESCALATE':
        why_parts.append('Current trust posture or queue posture pushes this item into escalation handling.')
    elif attention_state == 'INVESTIGATE':
        why_parts.append('The queue item still lacks a linked pack lineage, so operator investigation comes first.')

    transition_summary = str(state_history.get('transition_summary_line') or '')
    if transition_summary:
        why_parts.append(transition_summary)
    if projection_state in {'AGING', 'STALE'}:
        why_parts.append(f'Projection recency is {projection_state}, so freshness should be checked before relying on the queue view.')
    why_now_line = ' '.join(dict.fromkeys(part for part in why_parts if part)) or 'This item remains on the queue because it still requires an operator decision.'

    primary_anchor = str(action_provenance.get('primary_publication_path') or action_provenance.get('pack_manifest_path') or '') or 'the linked evidence anchor'
    preflight_checks = [f'Confirm {primary_anchor} is still the right lineage target for {review_target}.']
    current_state_label = str(state_history.get('current_state_label') or '') or None
    prior_state_label = str(state_history.get('prior_state_label') or '') or None
    if current_state_label:
        if prior_state_label and prior_state_label != current_state_label:
            preflight_checks.append(f'Verify the latest trust shift from {prior_state_label} to {current_state_label} before acting.')
        else:
            preflight_checks.append(f'Confirm the latest trust posture remains {current_state_label}.')
    if projection_state in {'AGING', 'STALE'}:
        preflight_checks.append(f'Refresh the linked projection because recency is {projection_state}.')
    matched_terms = [str(term) for term in action_provenance.get('matched_terms', []) or []]
    if matched_terms:
        preflight_checks.append(f"Check that the linkage basis terms still match the queue target: {', '.join(matched_terms)}.")

    evidence_check_line = f"Before acting, verify {primary_anchor} and the current governed posture for {review_target}."
    follow_up_checks: list[str] = []
    if safest_next_action == 'claim-item':
        follow_up_checks.append('After claiming, open the linked pack detail and verify the evidence chain remains intact.')
        follow_up_checks.append('Confirm the command receipt stays anchored to the manifest/publication lineage.')
    elif safest_next_action == 'acknowledge-reentry':
        follow_up_checks.append('After acknowledgement, confirm the publication reflects the intended re-entry posture.')
        follow_up_checks.append('Re-check the queue item to ensure the governed lane state is now explicit.')
    elif safest_next_action == 'renew-lease':
        follow_up_checks.append('After renewal, verify the linked publication still carries the expected coverage/lease posture.')
        follow_up_checks.append('Confirm the lease evidence chain did not drift during renewal handling.')
    else:
        follow_up_checks.append('Use pack detail and lineage evidence to determine the next lawful action before submitting any command.')
    if projection_state in {'AGING', 'STALE'}:
        follow_up_checks.append('Schedule a projection refresh or verification pass after the immediate operator step.')

    return {
        'summary_line': summary_line,
        'why_now_line': why_now_line,
        'safest_next_action': safest_next_action,
        'safest_next_action_state': safest_next_action_state,
        'evidence_check_line': evidence_check_line,
        'follow_up_line': follow_up_checks[0],
        'preflight_checks': preflight_checks[:4],
        'follow_up_checks': follow_up_checks[:4],
    }


def _build_evidence_backed_briefing(
    *,
    entry: Mapping[str, Any],
    action_provenance: Mapping[str, Any],
    operator_brief: Mapping[str, Any],
    policy_recommendation: Mapping[str, Any],
) -> dict[str, Any]:
    review_target = str(entry.get('review_target') or 'this work item')
    lawful_next_action = str(policy_recommendation.get('lawful_next_action') or '') or None
    lawful_next_action_state = str(policy_recommendation.get('lawful_next_action_state') or '') or None
    if lawful_next_action and lawful_next_action_state:
        summary_line = (
            f"Evidence-backed briefing: {review_target} should stay on {lawful_next_action.replace('-', ' ')} "
            f"({lawful_next_action_state}) while lineage checks remain in scope."
        )
    else:
        summary_line = f"Evidence-backed briefing: {review_target} should remain in evidence review until a lawful command path clears."

    contradictions = list(policy_recommendation.get('contradictions', []) or [])
    drift_signals = list(policy_recommendation.get('drift_signals', []) or [])
    anomaly_details = list(policy_recommendation.get('anomaly_details', []) or [])
    primary_anchor = str(action_provenance.get('primary_publication_path') or action_provenance.get('pack_manifest_path') or '') or 'the linked evidence anchor'

    if lawful_next_action and lawful_next_action_state:
        action_line = (
            f"Action lane: {lawful_next_action.replace('-', ' ')} is the current lawful next move at {lawful_next_action_state} state."
        )
    else:
        action_line = 'Action lane: no direct governed command is currently lawful; use evidence review and queue clarification first.'

    evidence_line = (
        f"Evidence anchor: use {primary_anchor} plus the current governed posture before relying on queue copy or command readiness."
    )

    if contradictions:
        contradiction_line = f"Contradiction watch: {contradictions[0].get('summary_line')}"
    else:
        contradiction_line = 'Contradiction watch: no direct queue-vs-lineage contradiction is currently surfaced.'

    if drift_signals:
        drift_line = f"Drift watch: {drift_signals[0].get('summary_line')}"
    else:
        drift_line = 'Drift watch: no material lineage drift is currently surfaced.'

    if anomaly_details:
        anomaly_line = f"Anomaly watch: {anomaly_details[0].get('summary_line')}"
    else:
        anomaly_line = 'Anomaly watch: no anomaly flags are currently surfaced beyond the normal queue posture.'

    watch_items: list[str] = []
    for item in [
        *[str(signal.get('summary_line') or '') for signal in contradictions[:1]],
        *[str(signal.get('summary_line') or '') for signal in drift_signals[:2]],
        *[str(signal.get('summary_line') or '') for signal in anomaly_details[:1]],
        str(operator_brief.get('follow_up_line') or ''),
    ]:
        if item and item not in watch_items:
            watch_items.append(item)

    return {
        'summary_line': summary_line,
        'action_line': action_line,
        'evidence_line': evidence_line,
        'contradiction_line': contradiction_line,
        'drift_line': drift_line,
        'anomaly_line': anomaly_line,
        'watch_items': watch_items[:5],
        'source_paths': _unique_nonempty_paths(
            str(action_provenance.get('pack_manifest_path') or None),
            str(action_provenance.get('primary_publication_path') or None),
            extra_paths=[str(path) for path in action_provenance.get('anchor_paths', []) or []],
        ),
    }


__all__ = [
    '_build_operator_brief',
    '_build_evidence_backed_briefing',
]
