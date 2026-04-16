from __future__ import annotations

from strategy_validator.contracts.source_registry import SourceRegistryRecord


class SourceRegistry:
    """In-memory source registry used as the application seam for lawful source references."""

    def __init__(self) -> None:
        self._records: dict[str, SourceRegistryRecord] = {}

    def register(self, record: SourceRegistryRecord) -> SourceRegistryRecord:
        self._records[record.source_id] = record
        return record

    def get(self, source_id: str) -> SourceRegistryRecord | None:
        return self._records.get(source_id)

    def list_records(self) -> tuple[SourceRegistryRecord, ...]:
        return tuple(self._records.values())
