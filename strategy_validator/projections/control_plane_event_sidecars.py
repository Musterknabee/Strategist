from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from strategy_validator.contracts.control_plane_event_envelope import (
    ControlPlaneEventEnvelope,
    control_plane_event_envelope_from_payload,
    verify_control_plane_event_envelope,
)


@dataclass(frozen=True)
class ControlPlaneEventSidecarRecord:
    """Verified or rejected control-plane event sidecar discovered on disk."""

    event_path: str
    event_id: str | None
    event_type: str | None
    producer: str | None
    occurred_at_utc: str | None
    payload_digest: str | None
    verified: bool
    issue_codes: tuple[str, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "event_path": self.event_path,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "producer": self.producer,
            "occurred_at_utc": self.occurred_at_utc,
            "payload_digest": self.payload_digest,
            "verified": self.verified,
            "issue_codes": list(self.issue_codes),
        }


@dataclass(frozen=True)
class ControlPlaneEventSidecarReplayReport:
    """Replay/projection report for event-shaped control-plane sidecars."""

    schema_version: str
    event_root: str
    event_count: int
    verified_count: int
    rejected_count: int
    records: tuple[ControlPlaneEventSidecarRecord, ...]

    @property
    def ok(self) -> bool:
        return self.rejected_count == 0

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "event_root": self.event_root,
            "event_count": self.event_count,
            "verified_count": self.verified_count,
            "rejected_count": self.rejected_count,
            "ok": self.ok,
            "records": [record.to_payload() for record in self.records],
        }


def _record_from_envelope(path: Path, envelope: ControlPlaneEventEnvelope) -> ControlPlaneEventSidecarRecord:
    verified, issues = verify_control_plane_event_envelope(envelope)
    return ControlPlaneEventSidecarRecord(
        event_path=str(path),
        event_id=envelope.event_id,
        event_type=envelope.event_type,
        producer=envelope.producer,
        occurred_at_utc=envelope.occurred_at_utc,
        payload_digest=envelope.payload_digest,
        verified=verified,
        issue_codes=issues,
    )


def build_control_plane_event_sidecar_replay_report(event_root: Path | str) -> ControlPlaneEventSidecarReplayReport:
    """Discover and verify ``*.event.json`` control-plane event sidecars."""

    root = Path(event_root).resolve()
    records: list[ControlPlaneEventSidecarRecord] = []
    for path in sorted(root.rglob("*.event.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            envelope = control_plane_event_envelope_from_payload(payload)
        except Exception as exc:  # deliberate: replay must report, not crash, on malformed sidecars
            records.append(
                ControlPlaneEventSidecarRecord(
                    event_path=str(path),
                    event_id=None,
                    event_type=None,
                    producer=None,
                    occurred_at_utc=None,
                    payload_digest=None,
                    verified=False,
                    issue_codes=(f"CONTROL_PLANE_EVENT_SIDECAR_UNREADABLE:{type(exc).__name__}",),
                )
            )
            continue
        records.append(_record_from_envelope(path, envelope))

    records.sort(key=lambda record: (record.occurred_at_utc or "", record.event_id or "", record.event_path))
    verified_count = sum(1 for record in records if record.verified)
    return ControlPlaneEventSidecarReplayReport(
        schema_version="control_plane_event_sidecar_replay/v1",
        event_root=str(root),
        event_count=len(records),
        verified_count=verified_count,
        rejected_count=len(records) - verified_count,
        records=tuple(records),
    )


def write_control_plane_event_sidecar_replay_report(
    *,
    event_root: Path | str,
    output_path: Path | str,
) -> ControlPlaneEventSidecarReplayReport:
    """Materialize the replay report as a projection artifact."""

    report = build_control_plane_event_sidecar_replay_report(event_root)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report.to_payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


@dataclass(frozen=True)
class JournaledControlPlaneEventRecord:
    """Control-plane event envelope discovered in the operator action journal."""

    action_event_id: str
    sequence_number: int | None
    event_id: str | None
    event_type: str | None
    producer: str | None
    payload_digest: str | None
    verified: bool
    issue_codes: tuple[str, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "action_event_id": self.action_event_id,
            "sequence_number": self.sequence_number,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "producer": self.producer,
            "payload_digest": self.payload_digest,
            "verified": self.verified,
            "issue_codes": list(self.issue_codes),
        }


@dataclass(frozen=True)
class ControlPlaneEventReconciliationRecord:
    """Join row comparing a sidecar event with its journaled counterpart."""

    event_id: str
    status: str
    sidecar_event_path: str | None
    journal_action_event_id: str | None
    sidecar_payload_digest: str | None
    journal_payload_digest: str | None
    issue_codes: tuple[str, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "status": self.status,
            "sidecar_event_path": self.sidecar_event_path,
            "journal_action_event_id": self.journal_action_event_id,
            "sidecar_payload_digest": self.sidecar_payload_digest,
            "journal_payload_digest": self.journal_payload_digest,
            "issue_codes": list(self.issue_codes),
        }


@dataclass(frozen=True)
class ControlPlaneEventReconciliationReport:
    """Projection joining verified sidecar events with journaled control-plane events."""

    schema_version: str
    event_root: str
    sidecar_event_count: int
    journal_event_count: int
    matched_count: int
    sidecar_only_count: int
    journal_only_count: int
    drift_count: int
    operator_journal_chain_ok: bool
    operator_journal_chain_issue_count: int
    records: tuple[ControlPlaneEventReconciliationRecord, ...]

    @property
    def ok(self) -> bool:
        return (
            self.sidecar_only_count == 0
            and self.journal_only_count == 0
            and self.drift_count == 0
            and self.operator_journal_chain_ok
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "event_root": self.event_root,
            "sidecar_event_count": self.sidecar_event_count,
            "journal_event_count": self.journal_event_count,
            "matched_count": self.matched_count,
            "sidecar_only_count": self.sidecar_only_count,
            "journal_only_count": self.journal_only_count,
            "drift_count": self.drift_count,
            "operator_journal_chain_ok": self.operator_journal_chain_ok,
            "operator_journal_chain_issue_count": self.operator_journal_chain_issue_count,
            "ok": self.ok,
            "records": [record.to_payload() for record in self.records],
        }


def _journal_record_from_operator_event(event: Any) -> JournaledControlPlaneEventRecord:
    try:
        payload = json.loads(event.target_payload_json)
        envelope = control_plane_event_envelope_from_payload(payload)
        verified, issues = verify_control_plane_event_envelope(envelope)
        return JournaledControlPlaneEventRecord(
            action_event_id=event.action_event_id,
            sequence_number=event.sequence_number,
            event_id=envelope.event_id,
            event_type=envelope.event_type,
            producer=envelope.producer,
            payload_digest=envelope.payload_digest,
            verified=verified,
            issue_codes=issues,
        )
    except Exception as exc:  # projection must report invalid journal payloads, not crash.
        return JournaledControlPlaneEventRecord(
            action_event_id=getattr(event, "action_event_id", "unknown"),
            sequence_number=getattr(event, "sequence_number", None),
            event_id=None,
            event_type=None,
            producer=None,
            payload_digest=None,
            verified=False,
            issue_codes=(f"CONTROL_PLANE_EVENT_JOURNAL_PAYLOAD_UNREADABLE:{type(exc).__name__}",),
        )


def build_control_plane_event_reconciliation_report(event_root: Path | str) -> ControlPlaneEventReconciliationReport:
    """Compare event sidecars on disk with journaled ``control-plane-event`` entries."""

    sidecar_report = build_control_plane_event_sidecar_replay_report(event_root)
    from strategy_validator.ledger.operator_actions import (
        read_operator_action_events,
        verify_operator_action_event_chain,
    )

    chain_report = verify_operator_action_event_chain()
    journal_records = tuple(
        _journal_record_from_operator_event(event)
        for event in read_operator_action_events()
        if event.action == "control-plane-event"
    )
    sidecars_by_id = {record.event_id: record for record in sidecar_report.records if record.event_id}
    journals_by_id = {record.event_id: record for record in journal_records if record.event_id}
    event_ids = sorted(set(sidecars_by_id) | set(journals_by_id))
    records: list[ControlPlaneEventReconciliationRecord] = []
    for event_id in event_ids:
        sidecar = sidecars_by_id.get(event_id)
        journal = journals_by_id.get(event_id)
        issues: list[str] = []
        if sidecar is None:
            status = "JOURNAL_ONLY"
            issues.append("CONTROL_PLANE_EVENT_MISSING_SIDECAR")
        elif journal is None:
            status = "SIDECAR_ONLY"
            issues.append("CONTROL_PLANE_EVENT_MISSING_JOURNAL_ENTRY")
        elif not sidecar.verified or not journal.verified:
            status = "INVALID"
            issues.extend(sidecar.issue_codes if sidecar else ())
            issues.extend(journal.issue_codes if journal else ())
        elif sidecar.payload_digest != journal.payload_digest:
            status = "DIGEST_MISMATCH"
            issues.append("CONTROL_PLANE_EVENT_PAYLOAD_DIGEST_MISMATCH")
        else:
            status = "MATCHED"
        records.append(
            ControlPlaneEventReconciliationRecord(
                event_id=event_id,
                status=status,
                sidecar_event_path=sidecar.event_path if sidecar else None,
                journal_action_event_id=journal.action_event_id if journal else None,
                sidecar_payload_digest=sidecar.payload_digest if sidecar else None,
                journal_payload_digest=journal.payload_digest if journal else None,
                issue_codes=tuple(issues),
            )
        )

    matched = sum(1 for record in records if record.status == "MATCHED")
    sidecar_only = sum(1 for record in records if record.status == "SIDECAR_ONLY")
    journal_only = sum(1 for record in records if record.status == "JOURNAL_ONLY")
    drift = sum(1 for record in records if record.status in {"DIGEST_MISMATCH", "INVALID"})
    return ControlPlaneEventReconciliationReport(
        schema_version="control_plane_event_reconciliation/v1",
        event_root=str(Path(event_root).resolve()),
        sidecar_event_count=sidecar_report.event_count,
        journal_event_count=len(journal_records),
        matched_count=matched,
        sidecar_only_count=sidecar_only,
        journal_only_count=journal_only,
        drift_count=drift,
        operator_journal_chain_ok=chain_report.ok,
        operator_journal_chain_issue_count=chain_report.issue_count,
        records=tuple(records),
    )


def write_control_plane_event_reconciliation_report(
    *,
    event_root: Path | str,
    output_path: Path | str,
) -> ControlPlaneEventReconciliationReport:
    """Materialize sidecar/journal reconciliation as a projection artifact."""

    report = build_control_plane_event_reconciliation_report(event_root)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report.to_payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


__all__ = [
    "ControlPlaneEventSidecarRecord",
    "JournaledControlPlaneEventRecord",
    "ControlPlaneEventReconciliationRecord",
    "ControlPlaneEventReconciliationReport",
    "ControlPlaneEventSidecarReplayReport",
    "build_control_plane_event_sidecar_replay_report",
    "write_control_plane_event_sidecar_replay_report",
    "build_control_plane_event_reconciliation_report",
    "write_control_plane_event_reconciliation_report",
]
