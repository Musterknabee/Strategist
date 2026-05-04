from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

_SCHEMA_VERSION = "control_plane_event_envelope/v1"


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str, allow_nan=True)


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _normalize_timestamp(value: datetime | None) -> datetime:
    observed = value or datetime.now(tz=UTC).replace(microsecond=0)
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=UTC)
    return observed.astimezone(UTC).replace(microsecond=0)


@dataclass(frozen=True)
class ControlPlaneEventEnvelope:
    """Canonical transport-neutral envelope for control-plane output events."""

    schema_version: str
    event_id: str
    event_type: str
    producer: str
    occurred_at_utc: str
    payload_digest: str
    payload: dict[str, Any]
    actor_id: str | None = None
    target: dict[str, Any] = field(default_factory=dict)
    policy_fingerprint: str | None = None
    idempotency_key: str | None = None
    evidence_refs: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "producer": self.producer,
            "occurred_at_utc": self.occurred_at_utc,
            "actor_id": self.actor_id,
            "target": dict(self.target),
            "policy_fingerprint": self.policy_fingerprint,
            "idempotency_key": self.idempotency_key,
            "evidence_refs": list(self.evidence_refs),
            "payload_digest": self.payload_digest,
            "payload": self.payload,
        }


def build_control_plane_event_envelope(
    *,
    event_type: str,
    producer: str,
    payload: dict[str, Any],
    occurred_at_utc: datetime | None = None,
    actor_id: str | None = None,
    target: dict[str, Any] | None = None,
    policy_fingerprint: str | None = None,
    idempotency_key: str | None = None,
    evidence_refs: tuple[str, ...] | list[str] = (),
) -> ControlPlaneEventEnvelope:
    """Build a deterministic event id from event metadata plus payload digest."""

    observed_at = _normalize_timestamp(occurred_at_utc)
    payload_digest = _sha256_payload(payload)
    normalized_target = {} if target is None else dict(target)
    normalized_refs = tuple(str(ref) for ref in evidence_refs)
    seed = {
        "schema_version": _SCHEMA_VERSION,
        "event_type": event_type,
        "producer": producer,
        "occurred_at_utc": observed_at.isoformat(),
        "actor_id": actor_id,
        "target": normalized_target,
        "policy_fingerprint": policy_fingerprint,
        "idempotency_key": idempotency_key,
        "evidence_refs": list(normalized_refs),
        "payload_digest": payload_digest,
    }
    event_id = f"control-plane-event-{_sha256_payload(seed)[:24]}"
    return ControlPlaneEventEnvelope(
        schema_version=_SCHEMA_VERSION,
        event_id=event_id,
        event_type=event_type,
        producer=producer,
        occurred_at_utc=observed_at.isoformat(),
        actor_id=actor_id,
        target=normalized_target,
        policy_fingerprint=policy_fingerprint,
        idempotency_key=idempotency_key,
        evidence_refs=normalized_refs,
        payload_digest=payload_digest,
        payload=payload,
    )


def control_plane_event_envelope_from_payload(payload: dict[str, Any]) -> ControlPlaneEventEnvelope:
    """Parse a serialized control-plane event envelope payload."""

    if not isinstance(payload, dict):
        raise TypeError("control-plane event envelope payload must be a dictionary")
    return ControlPlaneEventEnvelope(
        schema_version=str(payload.get("schema_version", "")),
        event_id=str(payload.get("event_id", "")),
        event_type=str(payload.get("event_type", "")),
        producer=str(payload.get("producer", "")),
        occurred_at_utc=str(payload.get("occurred_at_utc", "")),
        actor_id=payload.get("actor_id"),
        target=dict(payload.get("target") or {}),
        policy_fingerprint=payload.get("policy_fingerprint"),
        idempotency_key=payload.get("idempotency_key"),
        evidence_refs=tuple(str(ref) for ref in (payload.get("evidence_refs") or ())),
        payload_digest=str(payload.get("payload_digest", "")),
        payload=dict(payload.get("payload") or {}),
    )


def verify_control_plane_event_envelope(envelope: ControlPlaneEventEnvelope) -> tuple[bool, tuple[str, ...]]:
    """Verify envelope schema and payload digest without external state."""

    issues: list[str] = []
    if envelope.schema_version != _SCHEMA_VERSION:
        issues.append("CONTROL_PLANE_EVENT_SCHEMA_VERSION_UNSUPPORTED")
    if not envelope.event_type:
        issues.append("CONTROL_PLANE_EVENT_TYPE_MISSING")
    if not envelope.producer:
        issues.append("CONTROL_PLANE_EVENT_PRODUCER_MISSING")
    expected_digest = _sha256_payload(envelope.payload)
    if envelope.payload_digest != expected_digest:
        issues.append("CONTROL_PLANE_EVENT_PAYLOAD_DIGEST_MISMATCH")
    try:
        observed_at = datetime.fromisoformat(envelope.occurred_at_utc)
    except ValueError:
        issues.append("CONTROL_PLANE_EVENT_OCCURRED_AT_INVALID")
    else:
        expected = build_control_plane_event_envelope(
            event_type=envelope.event_type,
            producer=envelope.producer,
            payload=envelope.payload,
            occurred_at_utc=observed_at,
            actor_id=envelope.actor_id,
            target=envelope.target,
            policy_fingerprint=envelope.policy_fingerprint,
            idempotency_key=envelope.idempotency_key,
            evidence_refs=envelope.evidence_refs,
        )
        if envelope.event_id != expected.event_id:
            issues.append("CONTROL_PLANE_EVENT_ID_MISMATCH")
    return (not issues, tuple(issues))


__all__ = [
    "ControlPlaneEventEnvelope",
    "control_plane_event_envelope_from_payload",
    "build_control_plane_event_envelope",
    "verify_control_plane_event_envelope",
]
