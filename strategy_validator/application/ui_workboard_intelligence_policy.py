from __future__ import annotations

from typing import Any, Mapping

from strategy_validator.application.ui_workboard_intelligence_foundations import (
    _BLOCKING_CLAIM_OPERABILITY,
    _BLOCKING_DISPATCH_POSTURES,
    _TRUST_ALERT_STATUSES,
    _normalize_tokens,
    _unique_nonempty_paths,
)

def _build_action_provenance(
    *,
    entry: Mapping[str, Any],
    linked_pack: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if linked_pack is None:
        empty_targets = [
            {
                'action': action,
                'anchor_kind': 'UNLINKED',
                'target_label': 'lineage unavailable',
                'target_path': None,
                'supporting_paths': [],
                'rationale': 'No linked pack/publication is indexed yet, so this command has no evidence anchor path.',
            }
            for action in ('claim-item', 'acknowledge-reentry', 'renew-lease')
        ]
        return {
            'summary_line': 'No linked pack/publication is available, so command provenance remains unresolved.',
            'linkage_basis_line': 'The current queue item has not yet been matched to an indexed pack lineage.',
            'matched_terms': [],
            'evidence_anchor_count': 0,
            'anchor_paths': [],
            'anchor_labels': [],
            'pack_root': None,
            'pack_manifest_path': None,
            'primary_publication_path': None,
            'command_targets': empty_targets,
        }

    manifest_path = str(linked_pack.get('manifest_path') or '') or None
    primary_publication_path = str(linked_pack.get('primary_output_artifact_path') or '') or None
    pack_root = str(linked_pack.get('pack_root') or '') or None
    matched_terms = [str(token) for token in (linked_pack.get('linkage_basis', {}) or {}).get('matched_terms', []) or []]
    direct_phrase = bool((linked_pack.get('linkage_basis', {}) or {}).get('direct_phrase'))
    pack_kind = str(linked_pack.get('pack_kind') or 'operator_pack')
    review_target = str(entry.get('review_target') or 'work item')
    anchor_paths = _unique_nonempty_paths(
        manifest_path,
        primary_publication_path,
        extra_paths=[str(path) for path in linked_pack.get('output_artifact_paths', []) or []],
    )
    anchor_labels = ['manifest', 'primary_publication']
    for label in [str(label) for label in linked_pack.get('output_artifact_labels', []) or []]:
        if label and label not in anchor_labels:
            anchor_labels.append(label)

    if matched_terms:
        linkage_basis_line = (
            f"Queue target '{review_target}' maps to {pack_kind} via token overlap on: {', '.join(matched_terms)}."
        )
    elif direct_phrase:
        linkage_basis_line = f"Queue target '{review_target}' directly names the {pack_kind} lineage."
    else:
        linkage_basis_line = f"Queue target '{review_target}' is attached to the best available {pack_kind} lineage."

    summary_line = (
        f"Commands on this item will anchor to {pack_kind} evidence rooted at "
        f"{primary_publication_path or manifest_path or 'the indexed pack lineage'}."
    )

    command_targets = [
        {
            'action': 'claim-item',
            'anchor_kind': 'PACK_MANIFEST',
            'target_label': 'pack manifest',
            'target_path': manifest_path,
            'supporting_paths': anchor_paths,
            'rationale': 'Claiming should attach operator ownership to the current pack manifest and its supporting evidence chain.',
        },
        {
            'action': 'acknowledge-reentry',
            'anchor_kind': 'PUBLICATION_ARTIFACT' if primary_publication_path else 'PACK_MANIFEST',
            'target_label': 'primary publication' if primary_publication_path else 'pack manifest',
            'target_path': primary_publication_path or manifest_path,
            'supporting_paths': anchor_paths,
            'rationale': 'Re-entry acknowledgement should point at the operator-visible publication that reflects the current posture.',
        },
        {
            'action': 'renew-lease',
            'anchor_kind': 'EVIDENCE_CHAIN',
            'target_label': 'lease evidence chain',
            'target_path': primary_publication_path or manifest_path,
            'supporting_paths': anchor_paths,
            'rationale': 'Lease renewal should stay anchored to the current publication and supporting evidence artifacts.',
        },
    ]

    return {
        'summary_line': summary_line,
        'linkage_basis_line': linkage_basis_line,
        'matched_terms': matched_terms,
        'evidence_anchor_count': len(anchor_paths),
        'anchor_paths': anchor_paths,
        'anchor_labels': anchor_labels,
        'pack_root': pack_root,
        'pack_manifest_path': manifest_path,
        'primary_publication_path': primary_publication_path,
        'command_targets': command_targets,
    }


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
    '_build_action_provenance',
    '_action_precondition_state',
    '_build_command_readiness',
    '_command_item',
    '_build_operator_brief',
    '_append_policy_signal',
    '_build_policy_recommendation',
    '_build_evidence_backed_briefing',
]
