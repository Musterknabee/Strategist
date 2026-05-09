from __future__ import annotations

import json
from collections import Counter
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
    created_at_utc: str
    action: str
    operator_id: str
    accepted: bool
    status: str
    summary_line: str
    event_hash: str
    previous_event_hash: str | None
    idempotency_key: str | None
    review_target: str | None
    work_item_key: str | None
    control_plane_event_id: str | None
    control_plane_event_type: str | None
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
            "created_at_utc": self.created_at_utc,
            "action": self.action,
            "operator_id": self.operator_id,
            "accepted": self.accepted,
            "status": self.status,
            "summary_line": self.summary_line,
            "event_hash": self.event_hash,
            "previous_event_hash": self.previous_event_hash,
            "idempotency_key": self.idempotency_key,
            "review_target": self.review_target,
            "work_item_key": self.work_item_key,
            "control_plane_event_id": self.control_plane_event_id,
            "control_plane_event_type": self.control_plane_event_type,
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
    """Replayable read index over operator action journal entries."""

    schema_version: str
    database_path: str
    readonly: bool
    filters: dict[str, Any]
    unfiltered_event_count: int
    event_count: int
    returned_event_count: int
    limit: int | None
    latest_sequence_number: int | None
    chained_event_count: int
    legacy_event_count: int
    control_plane_event_count: int
    accepted_event_count: int
    rejected_event_count: int
    action_counts: dict[str, int]
    status_counts: dict[str, int]
    operator_counts: dict[str, int]
    issue_code_counts: dict[str, int]
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
            "readonly": self.readonly,
            "filters": self.filters,
            "unfiltered_event_count": self.unfiltered_event_count,
            "event_count": self.event_count,
            "returned_event_count": self.returned_event_count,
            "limit": self.limit,
            "latest_sequence_number": self.latest_sequence_number,
            "chained_event_count": self.chained_event_count,
            "legacy_event_count": self.legacy_event_count,
            "control_plane_event_count": self.control_plane_event_count,
            "accepted_event_count": self.accepted_event_count,
            "rejected_event_count": self.rejected_event_count,
            "action_counts": dict(sorted(self.action_counts.items())),
            "status_counts": dict(sorted(self.status_counts.items())),
            "operator_counts": dict(sorted(self.operator_counts.items())),
            "issue_code_counts": dict(sorted(self.issue_code_counts.items())),
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


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_tuple(values: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    return tuple(str(value).strip() for value in (values or ()) if str(value).strip())


def _entry_matches(
    entry: OperatorActionEventIndexEntry,
    *,
    operator_id: str | None,
    actions: tuple[str, ...],
    statuses: tuple[str, ...],
    accepted: bool | None,
    control_plane_only: bool,
    issue_codes: tuple[str, ...],
    authorization_role: str | None,
    review_target: str | None,
    work_item_key: str | None,
) -> bool:
    if operator_id and entry.operator_id != operator_id:
        return False
    if actions and entry.action not in actions:
        return False
    if statuses and entry.status not in statuses:
        return False
    if accepted is not None and entry.accepted is not accepted:
        return False
    if control_plane_only and entry.action != "control-plane-event":
        return False
    if issue_codes and not any(code in entry.issue_codes for code in issue_codes):
        return False
    if authorization_role and entry.authorization_role != authorization_role:
        return False
    if review_target and entry.review_target != review_target:
        return False
    if work_item_key and entry.work_item_key != work_item_key:
        return False
    return True


def _limit_tail(entries: tuple[OperatorActionEventIndexEntry, ...], limit: int | None) -> tuple[OperatorActionEventIndexEntry, ...]:
    if limit is None or limit <= 0:
        return entries
    if len(entries) <= limit:
        return entries
    return entries[-limit:]


def build_operator_action_event_projection_index(
    *,
    database_path: Path | str | None = None,
    readonly: bool = False,
    operator_id: str | None = None,
    actions: tuple[str, ...] | list[str] | None = None,
    statuses: tuple[str, ...] | list[str] | None = None,
    accepted: bool | None = None,
    control_plane_only: bool = False,
    issue_codes: tuple[str, ...] | list[str] | None = None,
    authorization_role: str | None = None,
    review_target: str | None = None,
    work_item_key: str | None = None,
    limit: int | None = None,
) -> OperatorActionEventProjectionIndex:
    """Build a compact, filterable index over the durable operator action event journal."""

    normalized_actions = _normalize_tuple(actions)
    normalized_statuses = _normalize_tuple(statuses)
    normalized_issue_codes = _normalize_tuple(issue_codes)
    normalized_operator_id = _string_or_none(operator_id)
    normalized_authorization_role = _string_or_none(authorization_role)
    normalized_review_target = _string_or_none(review_target)
    normalized_work_item_key = _string_or_none(work_item_key)
    normalized_limit = None if limit is None else max(1, int(limit))

    events = read_operator_action_events_readonly() if readonly else read_operator_action_events()
    chain = verify_operator_action_event_chain_readonly() if readonly else verify_operator_action_event_chain()
    entries: list[OperatorActionEventIndexEntry] = []
    for event in events:
        payload = _target_payload(event)
        issue_codes_for_event: list[str] = []
        if event.sequence_number is None:
            issue_codes_for_event.append("LEGACY_UNCHAINED_EVENT")
        if event.action == "control-plane-event":
            if not payload.get("event_id"):
                issue_codes_for_event.append("CONTROL_PLANE_EVENT_ID_MISSING")
            if not payload.get("payload_digest"):
                issue_codes_for_event.append("CONTROL_PLANE_PAYLOAD_DIGEST_MISSING")
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
                created_at_utc=event.created_at_utc.isoformat(),
                action=event.action,
                operator_id=event.operator_id,
                accepted=event.accepted,
                status=event.status,
                summary_line=event.summary_line,
                event_hash=event.event_hash,
                previous_event_hash=event.previous_event_hash,
                idempotency_key=_string_or_none(payload.get("idempotency_key")),
                review_target=_string_or_none(payload.get("review_target")),
                work_item_key=_string_or_none(payload.get("work_item_key")),
                control_plane_event_id=_string_or_none(payload.get("event_id")) if event.action == "control-plane-event" else None,
                control_plane_event_type=_string_or_none(payload.get("event_type")) if event.action == "control-plane-event" else None,
                control_plane_payload_digest=_string_or_none(payload.get("payload_digest")) if event.action == "control-plane-event" else None,
                authorization_principal_id=_string_or_none(authorization.get("principal_id")),
                authorization_principal_source=_string_or_none(authorization.get("principal_source")),
                authorization_mode=_string_or_none(authorization.get("authorization_mode")),
                authorization_role=_string_or_none(authorization.get("role")),
                authorization_scopes=normalized_scopes,
                target_payload_digest=_string_or_none(payload.get("payload_digest")),
                issue_codes=tuple(issue_codes_for_event),
            )
        )

    unfiltered_entries = tuple(entries)
    filtered_entries = tuple(
        entry for entry in unfiltered_entries
        if _entry_matches(
            entry,
            operator_id=normalized_operator_id,
            actions=normalized_actions,
            statuses=normalized_statuses,
            accepted=accepted,
            control_plane_only=control_plane_only,
            issue_codes=normalized_issue_codes,
            authorization_role=normalized_authorization_role,
            review_target=normalized_review_target,
            work_item_key=normalized_work_item_key,
        )
    )
    returned_entries = _limit_tail(filtered_entries, normalized_limit)

    database_path_text = "" if database_path is None else str(Path(database_path))
    action_counts = Counter(entry.action for entry in filtered_entries)
    status_counts = Counter(entry.status for entry in filtered_entries)
    operator_counts = Counter(entry.operator_id for entry in filtered_entries)
    issue_counts: Counter[str] = Counter()
    for entry in filtered_entries:
        issue_counts.update(entry.issue_codes)

    return OperatorActionEventProjectionIndex(
        schema_version="operator_action_event_projection_index/v1",
        database_path=database_path_text,
        readonly=readonly,
        filters={
            "operator_id": normalized_operator_id,
            "actions": list(normalized_actions),
            "statuses": list(normalized_statuses),
            "accepted": accepted,
            "control_plane_only": control_plane_only,
            "issue_codes": list(normalized_issue_codes),
            "authorization_role": normalized_authorization_role,
            "review_target": normalized_review_target,
            "work_item_key": normalized_work_item_key,
            "limit": normalized_limit,
        },
        unfiltered_event_count=len(unfiltered_entries),
        event_count=len(filtered_entries),
        returned_event_count=len(returned_entries),
        limit=normalized_limit,
        latest_sequence_number=max((entry.sequence_number or 0 for entry in unfiltered_entries), default=0) or None,
        chained_event_count=sum(1 for entry in filtered_entries if entry.sequence_number is not None),
        legacy_event_count=sum(1 for entry in filtered_entries if entry.sequence_number is None),
        control_plane_event_count=sum(1 for entry in filtered_entries if entry.action == "control-plane-event"),
        accepted_event_count=sum(1 for entry in filtered_entries if entry.accepted),
        rejected_event_count=sum(1 for entry in filtered_entries if not entry.accepted),
        action_counts=dict(action_counts),
        status_counts=dict(status_counts),
        operator_counts=dict(operator_counts),
        issue_code_counts=dict(issue_counts),
        chain_ok=chain.ok,
        chain_issue_count=chain.issue_count,
        chain_issues=tuple(chain.issues),
        entries=returned_entries,
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
