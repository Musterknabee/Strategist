from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from strategy_validator.contracts.events import EventEnvelope
from strategy_validator.ledger.reader import iter_event_envelopes


class EventStore(Protocol):
    """Abstract event-store surface used by application services."""

    def list_events(self, aggregate_id: str | None = None) -> tuple[EventEnvelope, ...]: ...


@dataclass(slots=True)
class AppendOnlyLedgerEventStore:
    """Adapter over the current append-only ledger implementation."""

    authority: str = 'ledger.append_only'

    def list_events(self, aggregate_id: str | None = None) -> tuple[EventEnvelope, ...]:
        return iter_event_envelopes(aggregate_id)
