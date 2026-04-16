"""Read-only ledger access."""

from __future__ import annotations

import hashlib
import json
from typing import Dict, List, Optional

from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.core.enums import PromotionState
from strategy_validator.ledger._append_only import LedgerEvent, read_events


def _canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _compute_event_hash(event: LedgerEvent) -> str:
    hash_input = _canonical_json(
        {
            "experiment_id": event.experiment_id,
            "sequence_number": event.sequence_number,
            "event_type": event.event_type,
            "promotion_state": event.promotion_state,
            "event_payload_json": event.event_payload_json,
            "manifest_hash": event.manifest_hash,
            "previous_event_hash": event.previous_event_hash,
            "created_at_utc": event.created_at_utc.isoformat(),
            "writer_identity": event.writer_identity,
        }
    )
    return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()


def get_history(experiment_id: str) -> List[LedgerEvent]:
    return list(read_events(experiment_id))


def hash_chain_is_valid(experiment_id: str) -> bool:
    previous_hash: str | None = None
    expected_sequence = 1
    for event in read_events(experiment_id):
        if event.sequence_number != expected_sequence:
            return False
        if event.previous_event_hash != previous_hash:
            return False
        if _compute_event_hash(event) != event.event_hash:
            return False
        previous_hash = event.event_hash
        expected_sequence += 1
    return True


def get_experiment(experiment_id: str) -> Optional[ExperimentManifest]:
    """Return latest manifest snapshot for an experiment_id, if any."""
    if not hash_chain_is_valid(experiment_id):
        return None
    rows = read_events(experiment_id)
    if not rows:
        return None
    last = rows[-1]
    data = last.event_payload
    return ExperimentManifest.model_validate(data)


def list_promoted_strategies() -> List[ExperimentManifest]:
    latest: Dict[str, ExperimentManifest] = {}
    event_stream = list(read_events())
    experiment_ids = sorted({event.experiment_id for event in event_stream})
    valid_experiments = {eid for eid in experiment_ids if hash_chain_is_valid(eid)}
    
    # Track latest manifest for each valid experiment
    for event in event_stream:
        if event.experiment_id not in valid_experiments:
            continue
        try:
            m = ExperimentManifest.model_validate(event.event_payload)
            latest[m.experiment_id] = m
        except Exception:
            continue
            
    # Filter to only those currently PROMOTABLE
    return [m for m in latest.values() if m.state == PromotionState.PROMOTABLE]


from strategy_validator.application.evidence_verification import compute_payload_digest
from strategy_validator.contracts.events import EventEnvelope


def iter_event_envelopes(experiment_id: str | None = None) -> tuple[EventEnvelope, ...]:
    envelopes: list[EventEnvelope] = []
    for event in read_events(experiment_id):
        payload = event.event_payload
        envelopes.append(
            EventEnvelope(
                event_id=event.event_hash,
                event_type=event.event_type,
                stream_family='promotion_state_stream',
                aggregate_id=event.experiment_id,
                occurred_at=event.created_at_utc,
                recorded_at=event.created_at_utc,
                actor_id=event.writer_identity,
                authority='ledger.reader',
                payload_digest_sha256=compute_payload_digest(payload),
                payload=payload,
            )
        )
    return tuple(envelopes)
