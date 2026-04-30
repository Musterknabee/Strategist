from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from strategy_validator.contracts.control_plane_event_envelope import ControlPlaneEventEnvelope
from strategy_validator.contracts.operator_action_journal import (
    AppendOperatorActionEventRequest,
    OperatorActionChainVerificationReport,
    OperatorActionEvent,
    ReadOperatorActionEventsRequest,
)
from strategy_validator.ledger._append_only import _connect, _connect_readonly

_TABLE_NAME = 'operator_action_events'
_ALLOWED_ACTIONS = frozenset({'claim-item', 'acknowledge-reentry', 'renew-lease', 'control-plane-event'})
_CHAIN_COLUMN_DEFINITIONS = {
    'sequence_number': 'INTEGER',
    'previous_event_hash': 'TEXT',
}
_WRITE_LOCK_RETRY_ATTEMPTS = 5
_WRITE_LOCK_RETRY_DELAY_SECONDS = 0.05


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(',', ':'), default=str)


def _compute_event_hash(
    *,
    action_event_id: str,
    action: str,
    operator_id: str,
    target_payload_json: str,
    accepted: bool,
    status: str,
    summary_line: str,
    created_at_utc: datetime,
    sequence_number: int | None,
    previous_event_hash: str | None,
) -> str:
    return hashlib.sha256(
        _canonical_json(
            {
                'action_event_id': action_event_id,
                'action': action,
                'operator_id': operator_id,
                'target_payload_json': target_payload_json,
                'accepted': accepted,
                'status': status,
                'summary_line': summary_line,
                'created_at_utc': created_at_utc.isoformat(),
                'sequence_number': sequence_number,
                'previous_event_hash': previous_event_hash,
            }
        ).encode('utf-8')
    ).hexdigest()


def _compute_legacy_event_hash(
    *,
    action_event_id: str,
    action: str,
    operator_id: str,
    target_payload_json: str,
    accepted: bool,
    status: str,
    summary_line: str,
    created_at_utc: datetime,
) -> str:
    """Hash shape used before operator action events were chained."""
    return hashlib.sha256(
        _canonical_json(
            {
                'action_event_id': action_event_id,
                'action': action,
                'operator_id': operator_id,
                'target_payload_json': target_payload_json,
                'accepted': accepted,
                'status': status,
                'summary_line': summary_line,
                'created_at_utc': created_at_utc.isoformat(),
            }
        ).encode('utf-8')
    ).hexdigest()



def _operator_action_table_exists(connection: Any) -> bool:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (_TABLE_NAME,),
    ).fetchone()
    return row is not None

def _ensure_operator_action_chain_schema() -> None:
    with _connect() as connection:
        rows = connection.execute(f'PRAGMA table_info({_TABLE_NAME})').fetchall()
        existing = {row['name'] for row in rows}
        for column_name, column_definition in _CHAIN_COLUMN_DEFINITIONS.items():
            if column_name not in existing:
                connection.execute(f'ALTER TABLE {_TABLE_NAME} ADD COLUMN {column_name} {column_definition}')
        connection.execute(
            f'''
            CREATE INDEX IF NOT EXISTS idx_operator_action_events_sequence
            ON {_TABLE_NAME} (sequence_number, created_at_utc, action_event_id)
            '''
        )
        connection.execute(
            f'''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_operator_action_events_sequence_unique
            ON {_TABLE_NAME} (sequence_number)
            WHERE sequence_number IS NOT NULL
            '''
        )
        connection.execute(
            f'''
            CREATE INDEX IF NOT EXISTS idx_operator_action_events_idempotency_key
            ON {_TABLE_NAME} (json_extract(target_payload_json, '$.idempotency_key'))
            '''
        )
        connection.execute(
            f'''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_operator_action_events_idempotency_key_unique
            ON {_TABLE_NAME} (json_extract(target_payload_json, '$.idempotency_key'))
            WHERE json_extract(target_payload_json, '$.idempotency_key') IS NOT NULL
              AND json_extract(target_payload_json, '$.idempotency_key') != ''
            '''
        )
        connection.commit()


def _idempotency_key_from_target(target: dict[str, Any]) -> str | None:
    value = target.get('idempotency_key')
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _lookup_existing_idempotency_event(connection: Any, *, idempotency_key: str) -> OperatorActionEvent | None:
    row = connection.execute(
        f'''
        SELECT *
        FROM {_TABLE_NAME}
        WHERE json_extract(target_payload_json, '$.idempotency_key') = ?
        ORDER BY sequence_number ASC, created_at_utc ASC, action_event_id ASC
        LIMIT 1
        ''',
        (idempotency_key,),
    ).fetchone()
    if row is None:
        return None
    return _row_to_operator_action_event(row)


def _ensure_idempotent_replay_matches(
    *,
    existing: OperatorActionEvent,
    action: str,
    operator_id: str,
    target_payload_json: str,
) -> None:
    if existing.action != action or existing.operator_id != operator_id or existing.target_payload_json != target_payload_json:
        raise ValueError('idempotency_key already used for a different operator action payload')


def _row_to_operator_action_event(row: Any) -> OperatorActionEvent:
    keys = set(row.keys()) if hasattr(row, 'keys') else set()
    return OperatorActionEvent(
        action_event_id=row['action_event_id'],
        action=row['action'],
        operator_id=row['operator_id'],
        target_payload_json=row['target_payload_json'],
        accepted=bool(row['accepted']),
        status=row['status'],
        summary_line=row['summary_line'],
        created_at_utc=datetime.fromisoformat(row['created_at_utc']),
        event_hash=row['event_hash'],
        sequence_number=row['sequence_number'] if 'sequence_number' in keys else None,
        previous_event_hash=row['previous_event_hash'] if 'previous_event_hash' in keys else None,
    )



def _begin_immediate_operator_action_transaction(connection: Any) -> None:
    # A BEGIN IMMEDIATE transaction serializes journal sequence assignment.
    # Without this write lock, two writers can both observe the same latest
    # sequence number before either INSERT commits. The unique sequence index is
    # the database backstop; the immediate transaction prevents normal races.
    connection.execute('PRAGMA busy_timeout = 5000')
    connection.execute('BEGIN IMMEDIATE')


def _rollback_quietly(connection: Any) -> None:
    try:
        connection.rollback()
    except Exception:
        pass


def _append_operator_action_event_once(
    *,
    request: AppendOperatorActionEventRequest,
    target_payload_json: str,
    idempotency_key: str | None,
    action_event_id: str,
    created_at_utc: datetime,
) -> OperatorActionEvent:
    with _connect() as connection:
        _begin_immediate_operator_action_transaction(connection)
        try:
            if idempotency_key is not None:
                existing = _lookup_existing_idempotency_event(connection, idempotency_key=idempotency_key)
                if existing is not None:
                    _ensure_idempotent_replay_matches(
                        existing=existing,
                        action=request.action,
                        operator_id=request.operator_id,
                        target_payload_json=target_payload_json,
                    )
                    connection.commit()
                    return existing
            latest = connection.execute(
                f'''
                SELECT sequence_number, event_hash
                FROM {_TABLE_NAME}
                WHERE sequence_number IS NOT NULL
                ORDER BY sequence_number DESC
                LIMIT 1
                '''
            ).fetchone()
            sequence_number = 1 if latest is None else int(latest['sequence_number']) + 1
            previous_event_hash = None if latest is None else str(latest['event_hash'])
            event_hash = _compute_event_hash(
                action_event_id=action_event_id,
                action=request.action,
                operator_id=request.operator_id,
                target_payload_json=target_payload_json,
                accepted=request.accepted,
                status=request.status,
                summary_line=request.summary_line,
                created_at_utc=created_at_utc,
                sequence_number=sequence_number,
                previous_event_hash=previous_event_hash,
            )
            event = OperatorActionEvent(
                action_event_id=action_event_id,
                action=request.action,
                operator_id=request.operator_id,
                target_payload_json=target_payload_json,
                accepted=request.accepted,
                status=request.status,
                summary_line=request.summary_line,
                created_at_utc=created_at_utc,
                event_hash=event_hash,
                sequence_number=sequence_number,
                previous_event_hash=previous_event_hash,
            )
            connection.execute(
                f'''
                INSERT INTO {_TABLE_NAME} (
                    action_event_id,
                    action,
                    operator_id,
                    target_payload_json,
                    accepted,
                    status,
                    summary_line,
                    created_at_utc,
                    event_hash,
                    sequence_number,
                    previous_event_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    event.action_event_id,
                    event.action,
                    event.operator_id,
                    event.target_payload_json,
                    int(event.accepted),
                    event.status,
                    event.summary_line,
                    event.created_at_utc.isoformat(),
                    event.event_hash,
                    event.sequence_number,
                    event.previous_event_hash,
                ),
            )
            connection.commit()
            return event
        except Exception:
            _rollback_quietly(connection)
            raise


def append_operator_action_event(
    *,
    action: str,
    operator_id: str,
    target: dict[str, Any],
    accepted: bool = True,
    status: str = 'accepted',
    summary_line: str,
    created_at_utc: datetime | None = None,
) -> OperatorActionEvent:
    request = AppendOperatorActionEventRequest(
        action=action,
        operator_id=operator_id,
        target=target,
        accepted=accepted,
        status=status,
        summary_line=summary_line,
        created_at_utc=created_at_utc,
    )
    if request.action not in _ALLOWED_ACTIONS:
        raise ValueError(f'unsupported operator action: {request.action}')
    created_at_utc = request.created_at_utc or datetime.now(timezone.utc)
    target_payload_json = _canonical_json(request.target)
    idempotency_key = _idempotency_key_from_target(request.target)

    _ensure_operator_action_chain_schema()
    last_locked_error: sqlite3.OperationalError | None = None
    for attempt in range(_WRITE_LOCK_RETRY_ATTEMPTS):
        action_event_id = f'ui-cmd-{uuid4().hex}'
        try:
            return _append_operator_action_event_once(
                request=request,
                target_payload_json=target_payload_json,
                idempotency_key=idempotency_key,
                action_event_id=action_event_id,
                created_at_utc=created_at_utc,
            )
        except sqlite3.OperationalError as exc:
            message = str(exc).lower()
            if 'locked' not in message and 'busy' not in message:
                raise
            last_locked_error = exc
            time.sleep(_WRITE_LOCK_RETRY_DELAY_SECONDS * (attempt + 1))
        except sqlite3.IntegrityError as exc:
            # Unique sequence/idempotency indexes are the final line of defense.
            # Retrying lets the next attempt observe the committed event and either
            # allocate the following sequence number or return the idempotent event.
            message = str(exc).lower()
            if 'sequence' not in message and 'unique' not in message and 'idempotency' not in message:
                raise
            time.sleep(_WRITE_LOCK_RETRY_DELAY_SECONDS * (attempt + 1))
    if last_locked_error is not None:
        raise last_locked_error
    raise RuntimeError('operator action journal append could not acquire a stable sequence slot')

def append_control_plane_event_envelope(
    envelope: ControlPlaneEventEnvelope,
    *,
    operator_id: str | None = None,
    summary_line: str | None = None,
    created_at_utc: datetime | None = None,
) -> OperatorActionEvent:
    """Append a verified control-plane event envelope to the operator action journal.

    The operator action journal is still the durable transport here; this helper
    gives event-first control-plane workflows an explicit bridge into the
    existing append-only operator event stream. When an idempotency key is
    present, repeated writes of the same event envelope return the original
    journal event instead of appending a duplicate.
    """

    target = envelope.to_payload()
    idempotency_key = envelope.idempotency_key
    if idempotency_key:
        existing = tuple(
            event for event in read_operator_action_events(idempotency_key=idempotency_key)
            if event.action == 'control-plane-event'
        )
        if existing:
            existing_target = json.loads(existing[0].target_payload_json)
            if existing_target.get('event_id') != envelope.event_id:
                raise ValueError('idempotency_key already used for a different control-plane event')
            return existing[0]

    return append_operator_action_event(
        action='control-plane-event',
        operator_id=operator_id or envelope.actor_id or 'control-plane',
        target=target,
        accepted=True,
        status='recorded',
        summary_line=summary_line or f'control-plane event recorded: {envelope.event_type}',
        created_at_utc=created_at_utc,
    )


def read_operator_action_events(
    *,
    operator_id: str | None = None,
    review_target: str | None = None,
    work_item_key: str | None = None,
    idempotency_key: str | None = None,
    readonly: bool = False,
) -> tuple[OperatorActionEvent, ...]:
    request = ReadOperatorActionEventsRequest(
        operator_id=operator_id,
        review_target=review_target,
        work_item_key=work_item_key,
        idempotency_key=idempotency_key,
    )
    if not readonly:
        _ensure_operator_action_chain_schema()
    conditions: list[str] = []
    params: list[Any] = []
    if request.operator_id:
        conditions.append('operator_id = ?')
        params.append(request.operator_id)
    if request.review_target:
        conditions.append("json_extract(target_payload_json, '$.review_target') = ?")
        params.append(request.review_target)
    if request.work_item_key:
        conditions.append("json_extract(target_payload_json, '$.work_item_key') = ?")
        params.append(request.work_item_key)
    if request.idempotency_key:
        conditions.append("json_extract(target_payload_json, '$.idempotency_key') = ?")
        params.append(request.idempotency_key)

    where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ''
    statement = (
        f'SELECT * FROM {_TABLE_NAME}{where_clause} '
        'ORDER BY sequence_number ASC, created_at_utc ASC, action_event_id ASC'
    )
    connector = _connect_readonly if readonly else _connect
    try:
        with connector() as connection:
            if readonly and not _operator_action_table_exists(connection):
                return ()
            rows = connection.execute(statement, tuple(params)).fetchall()
    except sqlite3.OperationalError:
        if readonly:
            return ()
        raise
    return tuple(_row_to_operator_action_event(row) for row in rows)


def read_operator_action_events_readonly(
    *,
    operator_id: str | None = None,
    review_target: str | None = None,
    work_item_key: str | None = None,
    idempotency_key: str | None = None,
) -> tuple[OperatorActionEvent, ...]:
    return read_operator_action_events(
        operator_id=operator_id,
        review_target=review_target,
        work_item_key=work_item_key,
        idempotency_key=idempotency_key,
        readonly=True,
    )


def verify_operator_action_event_chain(*, readonly: bool = False) -> OperatorActionChainVerificationReport:
    if not readonly:
        _ensure_operator_action_chain_schema()
    connector = _connect_readonly if readonly else _connect
    try:
        with connector() as connection:
            if readonly and not _operator_action_table_exists(connection):
                return OperatorActionChainVerificationReport(
                    ok=False,
                    event_count=0,
                    issue_count=1,
                    issues=(f'{_TABLE_NAME}: table missing',),
                )
            rows = connection.execute(
                f"""
                SELECT * FROM {_TABLE_NAME}
                ORDER BY sequence_number ASC, created_at_utc ASC, action_event_id ASC
                """
            ).fetchall()
    except sqlite3.OperationalError:
        if readonly:
            return OperatorActionChainVerificationReport(
                ok=False,
                event_count=0,
                issue_count=1,
                issues=(f'{_TABLE_NAME}: table unreadable',),
            )
        raise

    issues: list[str] = []
    previous_hash: str | None = None
    expected_sequence = 1
    for row in rows:
        event = _row_to_operator_action_event(row)
        if event.sequence_number is None:
            legacy_hash = _compute_legacy_event_hash(
                action_event_id=event.action_event_id,
                action=event.action,
                operator_id=event.operator_id,
                target_payload_json=event.target_payload_json,
                accepted=event.accepted,
                status=event.status,
                summary_line=event.summary_line,
                created_at_utc=event.created_at_utc,
            )
            if event.event_hash != legacy_hash:
                issues.append(f'{event.action_event_id}: event_hash mismatch on legacy unchained event')
            issues.append(f'{event.action_event_id}: legacy unchained operator action event has no sequence_number')
            continue
        if event.sequence_number != expected_sequence:
            issues.append(
                f'{event.action_event_id}: sequence_number {event.sequence_number} != expected {expected_sequence}'
            )
            expected_sequence = int(event.sequence_number)
        if event.previous_event_hash != previous_hash:
            issues.append(
                f'{event.action_event_id}: previous_event_hash {event.previous_event_hash!r} != expected {previous_hash!r}'
            )
        expected_hash = _compute_event_hash(
            action_event_id=event.action_event_id,
            action=event.action,
            operator_id=event.operator_id,
            target_payload_json=event.target_payload_json,
            accepted=event.accepted,
            status=event.status,
            summary_line=event.summary_line,
            created_at_utc=event.created_at_utc,
            sequence_number=event.sequence_number,
            previous_event_hash=event.previous_event_hash,
        )
        if event.event_hash != expected_hash:
            issues.append(f'{event.action_event_id}: event_hash mismatch')
        previous_hash = event.event_hash
        expected_sequence += 1

    return OperatorActionChainVerificationReport(
        ok=not issues,
        event_count=len(rows),
        issue_count=len(issues),
        issues=tuple(issues),
    )

def verify_operator_action_event_chain_readonly() -> OperatorActionChainVerificationReport:
    return verify_operator_action_event_chain(readonly=True)


__all__ = [
    'OperatorActionEvent',
    'OperatorActionChainVerificationReport',
    'append_operator_action_event',
    'append_control_plane_event_envelope',
    'read_operator_action_events',
    'read_operator_action_events_readonly',
    'verify_operator_action_event_chain',
    'verify_operator_action_event_chain_readonly',
]
