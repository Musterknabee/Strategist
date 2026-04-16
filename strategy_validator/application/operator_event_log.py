from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

_ENV_OPERATOR_EVENT_LOG_PATH = 'STRATEGY_VALIDATOR_OPERATOR_EVENT_LOG_PATH'


def resolve_operator_command_event_log_path() -> Path:
    configured = os.environ.get(_ENV_OPERATOR_EVENT_LOG_PATH, '').strip()
    if configured:
        return Path(configured).resolve()
    return (Path.cwd() / 'docs' / 'artifacts' / 'operator' / 'ORACLE_OPERATOR_COMMAND_EVENT_LOG.jsonl').resolve()


def append_operator_command_event(*, receipt: dict[str, Any]) -> dict[str, Any]:
    log_path = resolve_operator_command_event_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    event_id = f'operator-event-{uuid4().hex}'
    event = {
        'schema_version': 'operator_command_event/v1',
        'event_id': event_id,
        'command_id': receipt.get('command_id'),
        'generated_at_utc': receipt.get('generated_at_utc'),
        'action': receipt.get('action'),
        'accepted': receipt.get('accepted'),
        'operator_id': receipt.get('operator_id'),
        'target': receipt.get('target'),
        'governance': receipt.get('governance'),
        'summary_line': receipt.get('summary_line'),
    }
    with log_path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(event, default=str) + '\n')
    return {
        'event_id': event_id,
        'log_path': str(log_path),
        'schema_version': event['schema_version'],
    }


__all__ = ['append_operator_command_event', 'resolve_operator_command_event_log_path']
