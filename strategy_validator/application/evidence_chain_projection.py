from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.ledger._append_only import LedgerEvent, read_events, read_events_readonly, resolve_database_path
from strategy_validator.ledger.operator_actions import (
    read_operator_action_events,
    read_operator_action_events_readonly,
    verify_operator_action_event_chain,
    verify_operator_action_event_chain_readonly,
)
from strategy_validator.ledger.reader import verify_hash_chain, verify_hash_chain_readonly

UI_EVIDENCE_CHAIN_SCHEMA_VERSION = 'ui_evidence_chain/v1'
_DECISION_STREAM_FAMILY = 'decision_ledger'
_OPERATOR_STREAM_FAMILY = 'operator_action_journal'


def _payload_digest_from_json(payload_json: str) -> str:
    return hashlib.sha256(payload_json.encode('utf-8')).hexdigest()


def _target_payload_digest(target_payload_json: str) -> str:
    return hashlib.sha256(target_payload_json.encode('utf-8')).hexdigest()


def _json_object_from_text(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _database_path_text(database_path: str | None) -> str:
    if database_path:
        return str(Path(database_path))
    try:
        return str(resolve_database_path())
    except Exception:
        return ''


def _normalize_tuple(values: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    return tuple(str(value).strip() for value in (values or ()) if str(value).strip())


def _normalize_contains(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped.casefold() if stripped else None


def _contains(haystack: object, needle: str | None) -> bool:
    if not needle:
        return True
    if haystack is None:
        return False
    return needle in str(haystack).casefold()


def _decision_issue_map(report: Any) -> dict[tuple[str, int | None], list[str]]:
    mapped: dict[tuple[str, int | None], list[str]] = {}
    for issue in getattr(report, 'issues', ()):  # pragma: no branch - report contract is tuple-like in production.
        key = (str(getattr(issue, 'experiment_id', '')), getattr(issue, 'sequence_number', None))
        mapped.setdefault(key, []).append(str(getattr(issue, 'code', 'UNKNOWN_LEDGER_ISSUE')))
    return mapped


def _decision_event_entry(event: LedgerEvent, issue_codes: list[str]) -> dict[str, Any]:
    return {
        'stream_family': _DECISION_STREAM_FAMILY,
        'record_id': event.event_hash,
        'aggregate_id': event.experiment_id,
        'experiment_id': event.experiment_id,
        'sequence_number': event.sequence_number,
        'event_type': event.event_type,
        'status': event.promotion_state,
        'promotion_state': event.promotion_state,
        'actor_id': event.writer_identity,
        'writer_identity': event.writer_identity,
        'created_at_utc': event.created_at_utc.isoformat(),
        'event_hash': event.event_hash,
        'previous_event_hash': event.previous_event_hash,
        'manifest_hash': event.manifest_hash,
        'payload_digest_sha256': _payload_digest_from_json(event.event_payload_json),
        'summary_line': f"{event.event_type} · {event.experiment_id} · {event.promotion_state}",
        'chained': not issue_codes,
        'issue_codes': issue_codes,
    }


def _operator_event_entry(event: Any, chain_issues: tuple[str, ...]) -> dict[str, Any]:
    payload = _json_object_from_text(event.target_payload_json)
    issue_codes: list[str] = []
    if event.sequence_number is None:
        issue_codes.append('LEGACY_UNCHAINED_EVENT')
    if event.action == 'control-plane-event':
        if not payload.get('event_id'):
            issue_codes.append('CONTROL_PLANE_EVENT_ID_MISSING')
        if not payload.get('payload_digest'):
            issue_codes.append('CONTROL_PLANE_PAYLOAD_DIGEST_MISSING')
    event_id = str(event.action_event_id)
    for issue in chain_issues:
        if event_id in str(issue):
            issue_codes.append('CHAIN_VERIFICATION_ISSUE')
            break
    authorization = payload.get('authorization')
    if not isinstance(authorization, dict):
        authorization = {}
    work_item_key = payload.get('work_item_key')
    review_target = payload.get('review_target')
    return {
        'stream_family': _OPERATOR_STREAM_FAMILY,
        'record_id': event.action_event_id,
        'aggregate_id': work_item_key or review_target or event.action_event_id,
        'action_event_id': event.action_event_id,
        'sequence_number': event.sequence_number,
        'event_type': event.action,
        'action': event.action,
        'status': event.status,
        'accepted': event.accepted,
        'actor_id': event.operator_id,
        'operator_id': event.operator_id,
        'created_at_utc': event.created_at_utc.isoformat(),
        'event_hash': event.event_hash,
        'previous_event_hash': event.previous_event_hash,
        'target_payload_digest': _target_payload_digest(event.target_payload_json),
        'idempotency_key': payload.get('idempotency_key'),
        'review_target': review_target,
        'work_item_key': work_item_key,
        'control_plane_event_id': payload.get('event_id') if event.action == 'control-plane-event' else None,
        'authorization_principal_id': authorization.get('principal_id'),
        'authorization_mode': authorization.get('authorization_mode'),
        'summary_line': event.summary_line or f"{event.action} · {event.operator_id} · {event.status}",
        'chained': event.sequence_number is not None and not issue_codes,
        'issue_codes': issue_codes,
    }


def _build_decision_ledger_payload(*, readonly: bool) -> tuple[dict[str, Any], list[str]]:
    degraded: list[str] = []
    try:
        events = tuple((read_events_readonly if readonly else read_events)())
        report = (verify_hash_chain_readonly if readonly else verify_hash_chain)()
    except (OSError, RuntimeError, sqlite3.Error) as exc:
        return {
            'schema_version': 'decision_ledger_chain/v1',
            'stream_family': _DECISION_STREAM_FAMILY,
            'event_count': 0,
            'stream_count': 0,
            'chain_ok': False,
            'chain_issue_count': 1,
            'chain_issues': [f'DECISION_LEDGER_UNREADABLE: {exc}'],
            'entries': [],
        }, [f'DECISION_LEDGER_UNREADABLE: {exc}']

    issues_by_event = _decision_issue_map(report)
    entries = [
        _decision_event_entry(
            event,
            issues_by_event.get((event.experiment_id, event.sequence_number), []),
        )
        for event in events
    ]
    stream_ids = {event.experiment_id for event in events}
    return {
        'schema_version': 'decision_ledger_chain/v1',
        'stream_family': _DECISION_STREAM_FAMILY,
        'event_count': len(entries),
        'stream_count': len(stream_ids),
        'chain_ok': bool(report.ok),
        'chain_issue_count': int(report.issue_count),
        'chain_issues': [issue.to_payload() for issue in report.issues],
        'entries': entries,
    }, degraded


def _build_operator_journal_payload(*, readonly: bool) -> tuple[dict[str, Any], list[str]]:
    degraded: list[str] = []
    try:
        events = tuple((read_operator_action_events_readonly if readonly else read_operator_action_events)())
        report = (verify_operator_action_event_chain_readonly if readonly else verify_operator_action_event_chain)()
    except (OSError, RuntimeError, sqlite3.Error) as exc:
        return {
            'schema_version': 'operator_action_journal_chain/v1',
            'stream_family': _OPERATOR_STREAM_FAMILY,
            'event_count': 0,
            'chain_ok': False,
            'chain_issue_count': 1,
            'chain_issues': [f'OPERATOR_ACTION_JOURNAL_UNREADABLE: {exc}'],
            'entries': [],
        }, [f'OPERATOR_ACTION_JOURNAL_UNREADABLE: {exc}']

    chain_issues = tuple(str(issue) for issue in report.issues)
    entries = [_operator_event_entry(event, chain_issues) for event in events]
    return {
        'schema_version': 'operator_action_journal_chain/v1',
        'stream_family': _OPERATOR_STREAM_FAMILY,
        'event_count': len(entries),
        'chain_ok': bool(report.ok),
        'chain_issue_count': int(report.issue_count),
        'chain_issues': list(chain_issues),
        'entries': entries,
    }, degraded


def _entry_matches(
    entry: dict[str, Any],
    *,
    stream_families: tuple[str, ...],
    issue_codes: tuple[str, ...],
    statuses: tuple[str, ...],
    actor_contains: str | None,
    aggregate_contains: str | None,
    event_type_contains: str | None,
    chained: bool | None,
) -> bool:
    if stream_families and str(entry.get('stream_family')) not in stream_families:
        return False
    if statuses and str(entry.get('status')) not in statuses:
        return False
    entry_issues = tuple(str(code) for code in (entry.get('issue_codes') or ()))
    if issue_codes and not any(code in entry_issues for code in issue_codes):
        return False
    if chained is not None and bool(entry.get('chained')) is not chained:
        return False
    if not _contains(entry.get('actor_id') or entry.get('writer_identity') or entry.get('operator_id'), actor_contains):
        return False
    if not _contains(entry.get('aggregate_id') or entry.get('experiment_id') or entry.get('action_event_id'), aggregate_contains):
        return False
    if not _contains(entry.get('event_type') or entry.get('action'), event_type_contains):
        return False
    return True


def _count_values(entries: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(entry.get(key) or 'UNKNOWN') for entry in entries).items()))


def _count_issue_codes(entries: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for entry in entries:
        counts.update(str(code) for code in (entry.get('issue_codes') or ()))
    return dict(sorted(counts.items()))


def build_ui_evidence_chain_payload(
    *,
    database_path: str | None = None,
    readonly: bool = True,
    stream_family: tuple[str, ...] | list[str] | None = None,
    issue_code: tuple[str, ...] | list[str] | None = None,
    status: tuple[str, ...] | list[str] | None = None,
    actor_contains: str | None = None,
    aggregate_contains: str | None = None,
    event_type_contains: str | None = None,
    chained: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    """Build a read-only forensic projection over decision and operator chains.

    This UI/read-plane surface verifies and exposes existing append-only evidence
    streams. It deliberately grants no promotion, broker, adjudication, or
    operator mutation authority.
    """

    safe_limit = max(1, min(int(limit), 1000))
    stream_families = _normalize_tuple(stream_family)
    issue_codes = _normalize_tuple(issue_code)
    statuses = _normalize_tuple(status)
    actor_needle = _normalize_contains(actor_contains)
    aggregate_needle = _normalize_contains(aggregate_contains)
    event_type_needle = _normalize_contains(event_type_contains)

    generated_at = datetime.now(timezone.utc).isoformat()
    decision, decision_degraded = _build_decision_ledger_payload(readonly=readonly)
    operator, operator_degraded = _build_operator_journal_payload(readonly=readonly)
    degraded = [*decision_degraded, *operator_degraded]

    timeline_entries = [*decision['entries'], *operator['entries']]
    timeline_entries.sort(key=lambda row: (str(row.get('created_at_utc') or ''), str(row.get('stream_family') or '')))
    filtered_entries = [
        entry for entry in timeline_entries
        if _entry_matches(
            entry,
            stream_families=stream_families,
            issue_codes=issue_codes,
            statuses=statuses,
            actor_contains=actor_needle,
            aggregate_contains=aggregate_needle,
            event_type_contains=event_type_needle,
            chained=chained,
        )
    ]
    limited_timeline = filtered_entries[-safe_limit:]

    decision_ok = bool(decision.get('chain_ok'))
    operator_ok = bool(operator.get('chain_ok'))
    total_events = int(decision.get('event_count') or 0) + int(operator.get('event_count') or 0)
    total_issues = int(decision.get('chain_issue_count') or 0) + int(operator.get('chain_issue_count') or 0)
    ok = decision_ok and operator_ok and not degraded and not _count_issue_codes(timeline_entries)

    return {
        'schema_version': UI_EVIDENCE_CHAIN_SCHEMA_VERSION,
        'generated_at_utc': generated_at,
        'read_plane_only': True,
        'mutation_authority': 'NONE',
        'promotion_authority': 'NONE',
        'execution_authority': 'NONE',
        'readonly': readonly,
        'database_path': _database_path_text(database_path),
        'ok': ok,
        'degraded': degraded,
        'filters': {
            'stream_family': list(stream_families),
            'issue_code': list(issue_codes),
            'status': list(statuses),
            'actor_contains': actor_contains,
            'aggregate_contains': aggregate_contains,
            'event_type_contains': event_type_contains,
            'chained': chained,
            'limit': safe_limit,
        },
        'summary': {
            'event_count_total': total_events,
            'filtered_event_count': len(filtered_entries),
            'returned_event_count': len(limited_timeline),
            'unchained_filtered_event_count': sum(1 for entry in filtered_entries if not bool(entry.get('chained'))),
            'chain_issue_count_total': total_issues,
            'decision_ledger_event_count': int(decision.get('event_count') or 0),
            'decision_ledger_stream_count': int(decision.get('stream_count') or 0),
            'operator_action_event_count': int(operator.get('event_count') or 0),
            'decision_ledger_chain_ok': decision_ok,
            'operator_action_chain_ok': operator_ok,
            'stream_family_counts': _count_values(filtered_entries, 'stream_family'),
            'status_counts': _count_values(filtered_entries, 'status'),
            'issue_code_counts': _count_issue_codes(filtered_entries),
        },
        'guardrails': [
            'read_plane_only_no_ledger_mutation',
            'no_promotion_or_adjudication_authority',
            'no_broker_or_live_execution_authority',
            'append_only_streams_are_observed_not_rewritten',
        ],
        'streams': {
            _DECISION_STREAM_FAMILY: decision,
            _OPERATOR_STREAM_FAMILY: operator,
        },
        'timeline': {
            'entry_count': len(timeline_entries),
            'filtered_count': len(filtered_entries),
            'returned_count': len(limited_timeline),
            'limit': safe_limit,
            'entries': limited_timeline,
        },
    }


__all__ = ['UI_EVIDENCE_CHAIN_SCHEMA_VERSION', 'build_ui_evidence_chain_payload']
