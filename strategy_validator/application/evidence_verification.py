from __future__ import annotations

import hashlib
import json
from typing import Any

from strategy_validator.contracts.events import EventEnvelope
from strategy_validator.contracts.projection_snapshots import ProjectionSnapshotManifest


def compute_payload_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode('utf-8')).hexdigest()


def verify_event_envelope(envelope: EventEnvelope) -> bool:
    return envelope.payload_digest_sha256 == compute_payload_digest(envelope.payload)


def verify_projection_snapshot(snapshot: ProjectionSnapshotManifest, payload: dict[str, Any]) -> bool:
    return snapshot.digest_sha256 == compute_payload_digest(payload)
