from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from strategy_validator.ledger.operator_actions import (
    read_operator_action_events,
    read_operator_action_events_readonly,
    verify_operator_action_event_chain,
    verify_operator_action_event_chain_readonly,
)


@dataclass(frozen=True)
class OperatorActionEventIndexEntry:
    """Compact projection entry for one append-only operator action journal event."""

    action_event_id: str
    sequence_number: int | None
    action: str
    operator_id: str
    accepted: bool
    status: str
    event_hash: str
    previous_event_hash: str | None
    idempotency_key: str | None
    control_plane_event_id: str | None
    control_plane_payload_digest: str | None
    authorization_principal_id: str | None
    authorization_principal_source: str | None
    authorization_mode: str | None
    authorization_role: str | None
    authorization_scopes: tuple[str, ...]
    target_payload_digest: str | None
    issue_codes: tuple[str, ...]

    @property
    def chained(self) -> bool:
        return self.sequence_number is not None and not self.issue_codes

    def to_payload(self) -> dict[str, Any]:
        return {
            "action_event_id": self.action_event_id,
            "sequence_number": self.sequence_number,
            "action": self.action,
            "operator_id": self.operator_id,
            "accepted": self.accepted,
            "status": self.status,
            "event_hash": self.event_hash,
            "previous_event_hash": self.previous_event_hash,
            "idempotency_key": self.idempotency_key,
            "control_plane_event_id": self.control_plane_event_id,
            "control_plane_payload_digest": self.control_plane_payload_digest,
            "authorization_principal_id": self.authorization_principal_id,
            "authorization_principal_source": self.authorization_principal_source,
            "authorization_mode": self.authorization_mode,
            "authorization_role": self.authorization_role,
            "authorization_scopes": list(self.authorization_scopes),
            "target_payload_digest": self.target_payload_digest,
            "chained": self.chained,
            "issue_codes": list(self.issue_codes),
        }


@dataclass(frozen=True)
class OperatorActionEventProjectionIndex:
    """Replayable read index over all operator action journal entries."""

    schema_version: str
    database_path: str
    event_count: int
    chained_event_count: int
    legacy_event_count: int
    control_plane_event_count: int
    accepted_event_count: int
    rejected_event_count: int
    chain_ok: bool
    chain_issue_count: int
    chain_issues: tuple[str, ...]
    entries: tuple[OperatorActionEventIndexEntry, ...]

    @property
    def ok(self) -> bool:
        return self.chain_ok and self.legacy_event_count == 0 and self.chain_issue_count == 0

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "database_path": self.database_path,
            "event_count": self.event_count,
            "chained_event_count": self.chained_event_count,
            "legacy_event_count": self.legacy_event_count,
            "control_plane_event_count": self.control_plane_event_count,
            "accepted_event_count": self.accepted_event_count,
            "rejected_event_count": self.rejected_event_count,
            "chain_ok": self.chain_ok,
            "chain_issue_count": self.chain_issue_count,
            "chain_issues": list(self.chain_issues),
            "ok": self.ok,
            "entries": [entry.to_payload() for entry in self.entries],
        }


def _target_payload(event: Any) -> dict[str, Any]:
    try:
        payload = json.loads(event.target_payload_json)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def build_operator_action_event_projection_index(*, database_path: Path | str | None = None, readonly: bool = False) -> OperatorActionEventProjectionIndex:
    """Build a compact index over the durable operator action event journal."""

    events = read_operator_action_events_readonly() if readonly else read_operator_action_events()
    chain = verify_operator_action_event_chain_readonly() if readonly else verify_operator_action_event_chain()
    entries: list[OperatorActionEventIndexEntry] = []
    for event in events:
        payload = _target_payload(event)
        issue_codes: list[str] = []
        if event.sequence_number is None:
            issue_codes.append("LEGACY_UNCHAINED_EVENT")
        if event.action == "control-plane-event":
            if not payload.get("event_id"):
                issue_codes.append("CONTROL_PLANE_EVENT_ID_MISSING")
            if not payload.get("payload_digest"):
                issue_codes.append("CONTROL_PLANE_PAYLOAD_DIGEST_MISSING")
        authorization = payload.get("authorization")
        if not isinstance(authorization, dict):
            authorization = {}
        scopes = authorization.get("scopes")
        if isinstance(scopes, (list, tuple)):
            normalized_scopes = tuple(str(scope) for scope in scopes)
        else:
            normalized_scopes = ()
        entries.append(
            OperatorActionEventIndexEntry(
                action_event_id=event.action_event_id,
                sequence_number=event.sequence_number,
                action=event.action,
                operator_id=event.operator_id,
                accepted=event.accepted,
                status=event.status,
                event_hash=event.event_hash,
                previous_event_hash=event.previous_event_hash,
                idempotency_key=payload.get("idempotency_key"),
                control_plane_event_id=payload.get("event_id") if event.action == "control-plane-event" else None,
                control_plane_payload_digest=payload.get("payload_digest") if event.action == "control-plane-event" else None,
                authorization_principal_id=authorization.get("principal_id"),
                authorization_principal_source=authorization.get("principal_source"),
                authorization_mode=authorization.get("authorization_mode"),
                authorization_role=authorization.get("role"),
                authorization_scopes=normalized_scopes,
                target_payload_digest=payload.get("payload_digest"),
                issue_codes=tuple(issue_codes),
            )
        )

    database_path_text = "" if database_path is None else str(Path(database_path))
    return OperatorActionEventProjectionIndex(
        schema_version="operator_action_event_projection_index/v1",
        database_path=database_path_text,
        event_count=len(entries),
        chained_event_count=sum(1 for entry in entries if entry.sequence_number is not None),
        legacy_event_count=sum(1 for entry in entries if entry.sequence_number is None),
        control_plane_event_count=sum(1 for entry in entries if entry.action == "control-plane-event"),
        accepted_event_count=sum(1 for entry in entries if entry.accepted),
        rejected_event_count=sum(1 for entry in entries if not entry.accepted),
        chain_ok=chain.ok,
        chain_issue_count=chain.issue_count,
        chain_issues=tuple(chain.issues),
        entries=tuple(entries),
    )


def write_operator_action_event_projection_index(
    output_path: Path | str,
    *,
    database_path: Path | str | None = None,
    index: OperatorActionEventProjectionIndex | None = None,
    readonly: bool = False,
) -> OperatorActionEventProjectionIndex:
    """Materialize the operator action event projection index as JSON."""

    projection = index or build_operator_action_event_projection_index(database_path=database_path, readonly=readonly)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(projection.to_payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return projection
