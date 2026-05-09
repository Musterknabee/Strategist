from __future__ import annotations

from typing import Any, Mapping

from strategy_validator.application.ui_workboard_intelligence_foundations import (
    _BLOCKING_CLAIM_OPERABILITY,
    _BLOCKING_DISPATCH_POSTURES,
    _TRUST_ALERT_STATUSES,
    _normalize_tokens,
)

def _action_precondition_state(*, intrinsic_ready: bool, caution: bool) -> str:
    if not intrinsic_ready:
        return 'BLOCKED'
    if caution:
        return 'CAUTION'
    return 'READY'


def _build_command_readiness(
    *,
    entry: Mapping[str, Any],
    linked_pack: Mapping[str, Any] | None,
    projection_state: str,
    attention_state: str,
    blocking_reason: str | None,
) -> dict[str, Any]:
    review_target = str(entry.get('review_target') or '')
    summary_line = str(entry.get('summary_line') or '')
    recommended_actions = [str(item) for item in entry.get('recommended_actions', []) or []]
    signal_tokens = _normalize_tokens(review_target, summary_line, *recommended_actions)
    claim_operability = str(entry.get('claim_operability') or '').upper()
    dispatch_posture = str(entry.get('dispatch_posture') or '').upper()
    trust_status = str((linked_pack or {}).get('trust_status') or '').upper()
    blocked_transition = claim_operability in _BLOCKING_CLAIM_OPERABILITY or dispatch_posture in _BLOCKING_DISPATCH_POSTURES
    missing_link = linked_pack is None
    trust_alert = trust_status in _TRUST_ALERT_STATUSES
    lease_signal = bool(signal_tokens.intersection({'lease', 'renew', 'renewal', 'coverage'})) or trust_status == 'TRUST_RESTRICTED'
    projection_caution = projection_state in {'STALE', 'AGING'}

    items: list[dict[str, Any]] = []

    claim_reason = None
    claim_hint = 'Claiming the item keeps operator handling attached to the governed queue surface.'
    claim_intrinsic_ready = not blocked_transition
    claim_caution = False
    if blocked_transition:
        claim_reason = blocking_reason or 'Current governed posture does not permit direct claim execution.'
        claim_hint = 'Escalate or review evidence first; direct claim is not lawful under the present posture.'
    elif missing_link:
        claim_caution = True
        claim_reason = 'No linked pack/publication is indexed yet; claim can proceed only with evidence follow-up.'
        claim_hint = 'Open detail and confirm the target before relying on the claim as a durable handoff.'
    elif trust_alert:
        claim_caution = True
        claim_reason = f'Linked pack trust posture is {trust_status}; claim is allowed but should be handled as an investigation lane.'
        claim_hint = 'Claiming is still useful here, but operators should inspect the linked pack before acting downstream.'
    elif projection_caution:
        claim_caution = True
        claim_reason = f'Linked projection recency is {projection_state}; confirm freshness after claiming.'
        claim_hint = 'Projection freshness is degraded enough that the claim should be followed by a refresh check.'
    items.append({
        'action': 'claim-item',
        'state': _action_precondition_state(intrinsic_ready=claim_intrinsic_ready, caution=claim_caution),
        'reason': claim_reason,
        'operator_hint': claim_hint,
    })

    reentry_reason = None
    reentry_hint = 'Acknowledge re-entry when the item is ready to return to the active governed lane.'
    reentry_intrinsic_ready = not blocked_transition and not missing_link
    reentry_caution = False
    if blocked_transition:
        reentry_reason = blocking_reason or 'Current governed posture blocks re-entry acknowledgement.'
        reentry_hint = 'Resolve the blocked posture or escalate before acknowledging re-entry.'
    elif missing_link:
        reentry_reason = 'No linked pack/publication is available to anchor re-entry acknowledgement.'
        reentry_hint = 'Wait for indexed evidence or open the linked pack detail before acknowledging re-entry.'
    elif trust_alert:
        reentry_caution = True
        reentry_reason = f'Linked pack trust posture is {trust_status}; acknowledge re-entry only after evidence review.'
        reentry_hint = 'Treat this as a governed handoff marker, not as proof the target is healthy.'
    items.append({
        'action': 'acknowledge-reentry',
        'state': _action_precondition_state(intrinsic_ready=reentry_intrinsic_ready, caution=reentry_caution),
        'reason': reentry_reason,
        'operator_hint': reentry_hint,
    })

    renew_reason = None
    renew_hint = 'Renew lease only when the work item or linked pack shows lease / coverage pressure.'
    renew_intrinsic_ready = not blocked_transition and not missing_link and lease_signal
    renew_caution = False
    if blocked_transition:
        renew_reason = blocking_reason or 'Current governed posture blocks lease renewal.'
        renew_hint = 'Escalate or restore operability before attempting lease renewal.'
    elif missing_link:
        renew_reason = 'No linked pack/publication is available to justify a lease renewal.'
        renew_hint = 'Lease renewal should remain evidence-backed; wait for the indexed pack or detail target.'
    elif not lease_signal:
        renew_reason = 'This item does not currently advertise lease or coverage pressure.'
        renew_hint = 'Prefer claim or acknowledgement actions unless lease pressure appears in the queue or pack evidence.'
    elif projection_caution or trust_alert or attention_state in {'ESCALATE', 'BLOCKED'}:
        renew_caution = True
        renew_reason = (
            f'Lease renewal is available, but current posture is {attention_state} '
            f'with trust status {trust_status or "UNKNOWN"} and recency {projection_state}.'
        )
        renew_hint = 'Renewal is possible, but the operator should verify the evidence chain before relying on it.'
    items.append({
        'action': 'renew-lease',
        'state': _action_precondition_state(intrinsic_ready=renew_intrinsic_ready, caution=renew_caution),
        'reason': renew_reason,
        'operator_hint': renew_hint,
    })

    ready_count = sum(1 for item in items if item['state'] == 'READY')
    caution_count = sum(1 for item in items if item['state'] == 'CAUTION')
    blocked_count = sum(1 for item in items if item['state'] == 'BLOCKED')
    top_action = next((item['action'] for item in items if item['state'] == 'READY'), None)
    if top_action is None:
        top_action = next((item['action'] for item in items if item['state'] == 'CAUTION'), None)
    if blocked_count == len(items):
        summary_line = 'No governed queue commands are currently ready for direct execution on this item.'
    else:
        summary_line = (
            f'{ready_count} command(s) are ready and {caution_count} require extra operator review '
            f'before submission.'
        )
    return {
        'summary_line': summary_line,
        'ready_count': ready_count,
        'caution_count': caution_count,
        'blocked_count': blocked_count,
        'top_action': top_action,
        'items': items,
    }


def _command_item(readiness: Mapping[str, Any], action: str | None) -> Mapping[str, Any] | None:
    if not action:
        return None
    for item in readiness.get('items', []) or []:
        if item.get('action') == action:
            return item
    return None


__all__ = [
    '_action_precondition_state',
    '_build_command_readiness',
    '_command_item',
]
