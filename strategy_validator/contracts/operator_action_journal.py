from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AppendOperatorActionEventRequest:
    action: str
    operator_id: str
    target: dict[str, Any]
    accepted: bool = True
    status: str = 'accepted'
    summary_line: str = ''
    created_at_utc: datetime | None = None


@dataclass(frozen=True)
class ReadOperatorActionEventsRequest:
    operator_id: str | None = None
    review_target: str | None = None
    work_item_key: str | None = None
    idempotency_key: str | None = None


@dataclass(frozen=True)
class OperatorActionEvent:
    action_event_id: str
    action: str
    operator_id: str
    target_payload_json: str
    accepted: bool
    status: str
    summary_line: str
    created_at_utc: datetime
    event_hash: str
    sequence_number: int | None = None
    previous_event_hash: str | None = None

    @property
    def target_payload(self) -> dict[str, Any]:
        return json.loads(self.target_payload_json)


@dataclass(frozen=True)
class OperatorActionChainVerificationReport:
    ok: bool
    event_count: int
    issue_count: int
    issues: tuple[str, ...]


__all__ = [
    'AppendOperatorActionEventRequest',
    'OperatorActionEvent',
    'OperatorActionChainVerificationReport',
    'ReadOperatorActionEventsRequest',
]
