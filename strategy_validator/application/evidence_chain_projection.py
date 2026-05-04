from __future__ import annotations

import hashlib
import json
import sqlite3
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


def _decision_issue_map(report: Any) -> dict[tuple[str, int | None], list[str]]:
    mapped: dict[tuple[str, int | None], list[str]] = {}
    for issue in getattr(report, 'issues', ()):
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
    return {
        'stream_family': _OPERATOR_STREAM_FAMILY,
        'record_id': event.action_event_id,
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
        'control_plane_event_id': payload.get('event_id') if event.action == 'control-plane-event' else None,
        'authorization_principal_id': authorization.get('principal_id'),
        'authorization_mode': authorization.get('authorization_mode'),
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


def build_ui_evidence_chain_payload(
    *,
    database_path: str | None = None,
    readonly: bool = True,
    limit: int = 200,
) -> dict[str, Any]:
    """Build a read-only forensic projection over decision and operator chains.

    This is a UI/read-plane surface only. It verifies and exposes existing
    append-only evidence streams without creating promotion, broker, or operator
    mutation authority.
    """

    safe_limit = max(1, min(int(limit), 1000))
    generated_at = datetime.now(timezone.utc).isoformat()
    decision, decision_degraded = _build_decision_ledger_payload(readonly=readonly)
    operator, operator_degraded = _build_operator_journal_payload(readonly=readonly)
    degraded = [*decision_degraded, *operator_degraded]

    timeline_entries = [*decision['entries'], *operator['entries']]
    timeline_entries.sort(key=lambda row: (str(row.get('created_at_utc') or ''), str(row.get('stream_family') or '')))
    limited_timeline = timeline_entries[-safe_limit:]

    decision_ok = bool(decision.get('chain_ok'))
    operator_ok = bool(operator.get('chain_ok'))
    total_events = int(decision.get('event_count') or 0) + int(operator.get('event_count') or 0)
    total_issues = int(decision.get('chain_issue_count') or 0) + int(operator.get('chain_issue_count') or 0)
    ok = decision_ok and operator_ok and not degraded

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
        'summary': {
            'event_count_total': total_events,
            'chain_issue_count_total': total_issues,
            'decision_ledger_event_count': int(decision.get('event_count') or 0),
            'decision_ledger_stream_count': int(decision.get('stream_count') or 0),
            'operator_action_event_count': int(operator.get('event_count') or 0),
            'decision_ledger_chain_ok': decision_ok,
            'operator_action_chain_ok': operator_ok,
        },
        'streams': {
            _DECISION_STREAM_FAMILY: decision,
            _OPERATOR_STREAM_FAMILY: operator,
        },
        'timeline': {
            'entry_count': len(timeline_entries),
            'returned_count': len(limited_timeline),
            'limit': safe_limit,
            'entries': limited_timeline,
        },
    }


__all__ = ['UI_EVIDENCE_CHAIN_SCHEMA_VERSION', 'build_ui_evidence_chain_payload']
