from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class UiOperatorQueueQueryPayload:
    payload: Mapping[str, Any]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> 'UiOperatorQueueQueryPayload':
        normalized = dict(payload)
        normalized.setdefault('schema_version', 'oracle_operator_queue_query_report/v1')
        return cls(payload=normalized)

    def to_payload(self) -> dict[str, Any]:
        return dict(self.payload)


@dataclass(frozen=True)
class UiOperatorWorkboardPayload:
    payload: Mapping[str, Any]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> 'UiOperatorWorkboardPayload':
        normalized = dict(payload)
        normalized.setdefault('schema_version', 'oracle_operator_workboard/v1')
        return cls(payload=normalized)

    def to_payload(self) -> dict[str, Any]:
        return dict(self.payload)


@dataclass(frozen=True)
class UiWorkboardDashboardStats:
    active_count: int = 0
    governed_count: int = 0
    journaled_count: int = 0
    escalated_count: int = 0
    blocked_count: int = 0
    linked_count: int = 0
    stale_link_count: int = 0
    pack_item_count: int = 0
    pack_column_count: int = 0
    freshness_state: str = 'UNKNOWN'

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> 'UiWorkboardDashboardStats':
        return cls(
            active_count=int(payload.get('active_count', 0)),
            governed_count=int(payload.get('governed_count', 0)),
            journaled_count=int(payload.get('journaled_count', 0)),
            escalated_count=int(payload.get('escalated_count', 0)),
            blocked_count=int(payload.get('blocked_count', 0)),
            linked_count=int(payload.get('linked_count', 0)),
            stale_link_count=int(payload.get('stale_link_count', 0)),
            pack_item_count=int(payload.get('pack_item_count', 0)),
            pack_column_count=int(payload.get('pack_column_count', 0)),
            freshness_state=str(payload.get('freshness_state') or 'UNKNOWN'),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            'active_count': self.active_count,
            'governed_count': self.governed_count,
            'journaled_count': self.journaled_count,
            'escalated_count': self.escalated_count,
            'blocked_count': self.blocked_count,
            'linked_count': self.linked_count,
            'stale_link_count': self.stale_link_count,
            'pack_item_count': self.pack_item_count,
            'pack_column_count': self.pack_column_count,
            'freshness_state': self.freshness_state,
        }


@dataclass(frozen=True)
class UiWorkboardDashboardPayload:
    board_label: str
    generated_at_utc: str
    queue: Mapping[str, Any]
    pack_workbench: Mapping[str, Any]
    transition_policy: Mapping[str, Any]
    intelligence: Mapping[str, Any]
    materialization: Mapping[str, Any]
    stats: UiWorkboardDashboardStats
    schema_version: str = 'ui_workboard_dashboard/v1'

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> 'UiWorkboardDashboardPayload':
        return cls(
            schema_version=str(payload.get('schema_version') or 'ui_workboard_dashboard/v1'),
            board_label=str(payload.get('board_label') or 'operator'),
            generated_at_utc=str(payload.get('generated_at_utc') or ''),
            queue=dict(payload.get('queue', {}) or {}),
            pack_workbench=dict(payload.get('pack_workbench', {}) or {}),
            transition_policy=dict(payload.get('transition_policy', {}) or {}),
            intelligence=dict(payload.get('intelligence', {}) or {}),
            materialization=dict(payload.get('materialization', {}) or {}),
            stats=UiWorkboardDashboardStats.from_mapping(payload.get('stats', {}) or {}),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'generated_at_utc': self.generated_at_utc,
            'board_label': self.board_label,
            'queue': dict(self.queue),
            'pack_workbench': dict(self.pack_workbench),
            'transition_policy': dict(self.transition_policy),
            'intelligence': dict(self.intelligence),
            'materialization': dict(self.materialization),
            'stats': self.stats.to_payload(),
        }


__all__ = [
    'UiOperatorQueueQueryPayload',
    'UiOperatorWorkboardPayload',
    'UiWorkboardDashboardPayload',
    'UiWorkboardDashboardStats',
]
