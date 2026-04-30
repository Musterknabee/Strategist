from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable, Mapping


_BLOCKING_DISPATCH_POSTURES = {
    'DISPATCH_BLOCKED',
    'ESCALATE',
    'ESCALATED',
}
_BLOCKING_CLAIM_OPERABILITY = {
    'CLAIM_INOPERABLE',
}
_TRUST_ALERT_STATUSES = {
    'UNTRUSTED',
    'TRUST_RESTRICTED',
    'FAILED',
    'DEGRADED',
    'INVALID',
}


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _normalize_tokens(*values: str | None) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        if not value:
            continue
        normalized = value.lower().replace('-', '_').replace('/', '_').replace(':', '_')
        parts = [part for part in normalized.replace('.', '_').split('_') if part]
        tokens.update(parts)
        compact = ''.join(ch for ch in normalized if ch.isalnum())
        if compact:
            tokens.add(compact)
    return tokens


def _coerce_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _linked_pack_for_entry(entry: Mapping[str, Any], columns: Iterable[Mapping[str, Any]]) -> dict[str, Any] | None:
    haystack_text = ' '.join([
        str(entry.get('review_target') or ''),
        str(entry.get('summary_line') or ''),
        ' '.join(str(item) for item in entry.get('recommended_actions', []) or []),
    ]).lower()
    haystack_tokens = _normalize_tokens(haystack_text)
    best_match: dict[str, Any] | None = None
    best_score = -1
    best_linkage_basis: dict[str, Any] | None = None
    generic_tokens = {'pack', 'review', 'operator', 'queue', 'item'}
    for column in columns:
        for item in column.get('items', []) or []:
            pack_kind = str(item.get('pack_kind') or '')
            pack_root = pack_kind.replace('_pack', '')
            pack_tokens = _normalize_tokens(pack_kind, pack_root)
            meaningful_tokens = {token for token in pack_tokens if token not in generic_tokens and len(token) > 2}
            overlap = haystack_tokens.intersection(meaningful_tokens)
            direct_phrase = pack_kind.lower() in haystack_text or pack_root.lower() in haystack_text
            if not overlap and not direct_phrase:
                continue
            score = len(overlap) * 3
            if direct_phrase:
                score += 5
            if item.get('trust_status') in _TRUST_ALERT_STATUSES:
                score += 1
            if best_match is None or score > best_score:
                best_match = item
                best_score = score
                best_linkage_basis = {
                    'matched_terms': sorted(overlap),
                    'direct_phrase': direct_phrase,
                    'match_score': score,
                    'source': 'token_overlap' if overlap else 'direct_phrase',
                }
    if best_match is None:
        return None
    return {
        'pack_kind': best_match.get('pack_kind'),
        'trust_status': best_match.get('trust_status'),
        'manifest_path': best_match.get('manifest_path'),
        'primary_output_artifact_path': best_match.get('primary_output_artifact_path'),
        'generated_at_utc': best_match.get('generated_at_utc'),
        'summary_line': best_match.get('summary_line'),
        'pack_root': best_match.get('pack_root'),
        'output_artifact_labels': list(best_match.get('output_artifact_labels', []) or []),
        'output_artifact_paths': list(best_match.get('output_artifact_paths', []) or []),
        'linkage_basis': best_linkage_basis or {
            'matched_terms': [],
            'direct_phrase': False,
            'match_score': 0,
            'source': 'unlinked',
        },
    }


def _column_for_pack_kind(columns: Iterable[Mapping[str, Any]], pack_kind: str | None) -> Mapping[str, Any] | None:
    if not pack_kind:
        return None
    for column in columns:
        if column.get('pack_kind') == pack_kind:
            return column
    return None


def _priority_bonus(entry: Mapping[str, Any]) -> int:
    bonus = 0
    priority_band = str(entry.get('priority_band') or '').upper()
    urgency = str(entry.get('urgency') or '').upper()
    if 'CRITICAL' in priority_band:
        bonus += 40
    elif 'ELEVATED' in priority_band or 'HIGH' in priority_band:
        bonus += 25
    elif 'NORMAL' in priority_band:
        bonus += 8
    if 'HIGH' in urgency:
        bonus += 15
    elif 'MEDIUM' in urgency:
        bonus += 7
    return bonus


def _projection_age_state(*, generated_at_utc: str | None, now_utc: datetime) -> tuple[str, float | None]:
    generated_at = _coerce_datetime(generated_at_utc)
    if generated_at is None:
        return 'UNKNOWN', None
    age_hours = max(0.0, round((now_utc - generated_at).total_seconds() / 3600.0, 2))
    if age_hours >= 72:
        return 'STALE', age_hours
    if age_hours >= 24:
        return 'AGING', age_hours
    return 'CURRENT', age_hours


def _attention_state(entry: Mapping[str, Any], linked_pack: Mapping[str, Any] | None) -> tuple[str, str | None]:
    claim_operability = str(entry.get('claim_operability') or '').upper()
    dispatch_posture = str(entry.get('dispatch_posture') or '').upper()
    if claim_operability in _BLOCKING_CLAIM_OPERABILITY or dispatch_posture in _BLOCKING_DISPATCH_POSTURES:
        return 'BLOCKED', f"Governed transition is blocked by {claim_operability or dispatch_posture}."
    if linked_pack is None:
        return 'INVESTIGATE', 'No linked operator pack was found for this work item.'
    trust_status = str(linked_pack.get('trust_status') or '').upper()
    if trust_status in _TRUST_ALERT_STATUSES:
        return 'ESCALATE', f"Linked pack trust posture is {trust_status}."
    if 'CRITICAL' in str(entry.get('priority_band') or '').upper() or 'HIGH' in str(entry.get('urgency') or '').upper():
        return 'ACT_NOW', None
    if 'ELEVATED' in str(entry.get('priority_band') or '').upper() or 'MEDIUM' in str(entry.get('urgency') or '').upper():
        return 'REVIEW_SOON', None
    return 'MONITOR', None


def _build_state_history(
    *,
    entry: Mapping[str, Any],
    linked_pack: Mapping[str, Any] | None,
    columns: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    governance_posture = ' / '.join(
        part for part in [
            str(entry.get('claim_operability') or '').upper() or None,
            str(entry.get('dispatch_posture') or '').upper() or None,
        ]
        if part
    )
    if linked_pack is None:
        return {
            'transition_summary_line': 'No linked pack history is available yet; use the current governed posture until an indexed pack appears.',
            'governance_posture': governance_posture or None,
            'current_state_label': None,
            'prior_state_label': None,
            'item_count': 0,
            'entries': [],
        }

    column = _column_for_pack_kind(columns, str(linked_pack.get('pack_kind') or ''))
    ordered_items = list((column or {}).get('items', []) or [])
    ordered_items = sorted(
        ordered_items,
        key=lambda item: ((str(item.get('generated_at_utc') or '')), str(item.get('manifest_path') or '')),
        reverse=True,
    )
    latest = ordered_items[0] if ordered_items else linked_pack
    previous = ordered_items[1] if len(ordered_items) > 1 else None
    current_state_label = str(latest.get('trust_status') or '').upper() or None
    prior_state_label = str(previous.get('trust_status') or '').upper() or None if previous else None
    if previous is None:
        transition_summary_line = (
            f"Latest linked pack posture is {current_state_label or 'UNKNOWN'}; no prior indexed issuance was found for comparison."
        )
    elif current_state_label != prior_state_label:
        transition_summary_line = (
            f"Trust shift detected: {prior_state_label or 'UNKNOWN'} → {current_state_label or 'UNKNOWN'} across recent pack issuances."
        )
    else:
        transition_summary_line = (
            f"Latest linked pack remains {current_state_label or 'UNKNOWN'} across the two most recent indexed issuances."
        )
    if governance_posture:
        transition_summary_line = f"{transition_summary_line} Current governed posture: {governance_posture}."

    history_entries = []
    for item in ordered_items[:3]:
        history_entries.append({
            'generated_at_utc': item.get('generated_at_utc'),
            'trust_status': item.get('trust_status'),
            'summary_line': item.get('summary_line'),
            'manifest_path': item.get('manifest_path'),
            'primary_output_artifact_path': item.get('primary_output_artifact_path'),
            'is_latest': item.get('manifest_path') == latest.get('manifest_path'),
        })

    return {
        'transition_summary_line': transition_summary_line,
        'governance_posture': governance_posture or None,
        'current_state_label': current_state_label,
        'prior_state_label': prior_state_label,
        'item_count': len(ordered_items),
        'entries': history_entries,
    }


def _unique_nonempty_paths(*paths: str | None, extra_paths: Iterable[str] | None = None) -> list[str]:
    ordered: list[str] = []
    for value in [*paths, *((extra_paths or []))]:
        if not value or value in ordered:
            continue
        ordered.append(value)
    return ordered


def _slugify_for_path(value: str | None) -> str:
    text = str(value or '').strip().lower()
    slug = ''.join(ch if ch.isalnum() else '-' for ch in text)
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug.strip('-') or 'workboard'


__all__ = [
    '_BLOCKING_DISPATCH_POSTURES',
    '_BLOCKING_CLAIM_OPERABILITY',
    '_TRUST_ALERT_STATUSES',
    '_utc_now',
    '_normalize_tokens',
    '_coerce_datetime',
    '_linked_pack_for_entry',
    '_column_for_pack_kind',
    '_priority_bonus',
    '_projection_age_state',
    '_attention_state',
    '_build_state_history',
    '_unique_nonempty_paths',
    '_slugify_for_path',
]
