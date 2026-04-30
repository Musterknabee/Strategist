from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from strategy_validator.projections.control_plane_event_sidecars import (
    ControlPlaneEventReconciliationReport,
    build_control_plane_event_reconciliation_report,
)


@dataclass(frozen=True)
class ControlPlaneEventIndexEntry:
    """Projection index entry for one control-plane event across sidecar and journal sources."""

    event_id: str
    status: str
    sidecar_event_path: str | None
    journal_action_event_id: str | None
    payload_digest: str | None
    source_count: int
    issue_codes: tuple[str, ...]

    @property
    def fully_indexed(self) -> bool:
        return self.status == "MATCHED" and self.source_count == 2 and not self.issue_codes

    def to_payload(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "status": self.status,
            "sidecar_event_path": self.sidecar_event_path,
            "journal_action_event_id": self.journal_action_event_id,
            "payload_digest": self.payload_digest,
            "source_count": self.source_count,
            "fully_indexed": self.fully_indexed,
            "issue_codes": list(self.issue_codes),
        }


@dataclass(frozen=True)
class ControlPlaneEventProjectionIndex:
    """Replayable projection index over control-plane event sidecars and journal entries."""

    schema_version: str
    event_root: str
    event_count: int
    fully_indexed_count: int
    drift_count: int
    sidecar_only_count: int
    journal_only_count: int
    operator_journal_chain_ok: bool
    operator_journal_chain_issue_count: int
    entries: tuple[ControlPlaneEventIndexEntry, ...]

    @property
    def ok(self) -> bool:
        return (
            self.event_count == self.fully_indexed_count
            and self.drift_count == 0
            and self.sidecar_only_count == 0
            and self.journal_only_count == 0
            and self.operator_journal_chain_ok
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "event_root": self.event_root,
            "event_count": self.event_count,
            "fully_indexed_count": self.fully_indexed_count,
            "drift_count": self.drift_count,
            "sidecar_only_count": self.sidecar_only_count,
            "journal_only_count": self.journal_only_count,
            "operator_journal_chain_ok": self.operator_journal_chain_ok,
            "operator_journal_chain_issue_count": self.operator_journal_chain_issue_count,
            "ok": self.ok,
            "entries": [entry.to_payload() for entry in self.entries],
        }


def build_control_plane_event_projection_index(
    event_root: Path | str,
    *,
    reconciliation_report: ControlPlaneEventReconciliationReport | None = None,
) -> ControlPlaneEventProjectionIndex:
    """Build a compact replay index from sidecar/journal reconciliation output."""

    report = reconciliation_report or build_control_plane_event_reconciliation_report(event_root)
    entries: list[ControlPlaneEventIndexEntry] = []
    for record in report.records:
        sidecar_present = record.sidecar_event_path is not None
        journal_present = record.journal_action_event_id is not None
        payload_digest = record.sidecar_payload_digest or record.journal_payload_digest
        entries.append(
            ControlPlaneEventIndexEntry(
                event_id=record.event_id,
                status=record.status,
                sidecar_event_path=record.sidecar_event_path,
                journal_action_event_id=record.journal_action_event_id,
                payload_digest=payload_digest,
                source_count=int(sidecar_present) + int(journal_present),
                issue_codes=record.issue_codes,
            )
        )

    return ControlPlaneEventProjectionIndex(
        schema_version="control_plane_event_projection_index/v1",
        event_root=report.event_root,
        event_count=len(entries),
        fully_indexed_count=sum(1 for entry in entries if entry.fully_indexed),
        drift_count=report.drift_count,
        sidecar_only_count=report.sidecar_only_count,
        journal_only_count=report.journal_only_count,
        operator_journal_chain_ok=report.operator_journal_chain_ok,
        operator_journal_chain_issue_count=report.operator_journal_chain_issue_count,
        entries=tuple(entries),
    )


def write_control_plane_event_projection_index(
    *,
    event_root: Path | str,
    output_path: Path | str,
) -> ControlPlaneEventProjectionIndex:
    """Materialize the control-plane event projection index as JSON."""

    index = build_control_plane_event_projection_index(event_root)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(index.to_payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


__all__ = [
    "ControlPlaneEventIndexEntry",
    "ControlPlaneEventProjectionIndex",
    "build_control_plane_event_projection_index",
    "write_control_plane_event_projection_index",
]
