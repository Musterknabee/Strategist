"""Read-only ledger access."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.core.enums import PromotionState
from strategy_validator.ledger._append_only import LedgerEvent, read_events, read_events_readonly


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




@dataclass(frozen=True)
class LedgerHashChainIssue:
    experiment_id: str
    sequence_number: int | None
    code: str
    message: str

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class LedgerHashChainVerificationReport:
    schema_version: str
    ok: bool
    checked_experiment_count: int
    checked_event_count: int
    issue_count: int
    issues: tuple[LedgerHashChainIssue, ...]

    def to_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload["issues"] = [issue.to_payload() for issue in self.issues]
        return payload


def verify_hash_chain(experiment_id: str | None = None, *, readonly: bool = False) -> LedgerHashChainVerificationReport:
    """Return a forensic, read-only verification report for the ledger hash chain.

    Validation is scoped per experiment stream because sequence numbers and
    previous_event_hash values are per experiment. The verifier detects sequence
    gaps, previous-hash mismatches, recomputed event-hash mismatches, and duplicate
    event hashes.
    """
    event_reader = read_events_readonly if readonly else read_events
    events = list(event_reader(experiment_id))
    streams: dict[str, list[LedgerEvent]] = {}
    for event in events:
        streams.setdefault(event.experiment_id, []).append(event)

    issues: list[LedgerHashChainIssue] = []
    seen_event_hashes: dict[str, tuple[str, int]] = {}

    for stream_id, stream_events in sorted(streams.items()):
        previous_hash: str | None = None
        expected_sequence = 1
        for event in stream_events:
            if event.sequence_number != expected_sequence:
                issues.append(LedgerHashChainIssue(
                    experiment_id=stream_id,
                    sequence_number=event.sequence_number,
                    code="SEQUENCE_GAP",
                    message=f"Expected sequence_number={expected_sequence}, got {event.sequence_number}.",
                ))
            if event.previous_event_hash != previous_hash:
                issues.append(LedgerHashChainIssue(
                    experiment_id=stream_id,
                    sequence_number=event.sequence_number,
                    code="PREVIOUS_HASH_MISMATCH",
                    message="previous_event_hash does not match the prior event hash in this experiment stream.",
                ))
            recomputed = _compute_event_hash(event)
            if recomputed != event.event_hash:
                issues.append(LedgerHashChainIssue(
                    experiment_id=stream_id,
                    sequence_number=event.sequence_number,
                    code="EVENT_HASH_MISMATCH",
                    message="Stored event_hash does not match the recomputed event hash.",
                ))
            prior = seen_event_hashes.get(event.event_hash)
            if prior is not None:
                issues.append(LedgerHashChainIssue(
                    experiment_id=stream_id,
                    sequence_number=event.sequence_number,
                    code="DUPLICATE_EVENT_HASH",
                    message=f"event_hash duplicates {prior[0]} sequence {prior[1]}.",
                ))
            else:
                seen_event_hashes[event.event_hash] = (stream_id, event.sequence_number)
            previous_hash = event.event_hash
            expected_sequence += 1

    return LedgerHashChainVerificationReport(
        schema_version="ledger_hash_chain_verification/v1",
        ok=not issues,
        checked_experiment_count=len(streams),
        checked_event_count=len(events),
        issue_count=len(issues),
        issues=tuple(issues),
    )


def verify_hash_chain_readonly(experiment_id: str | None = None) -> LedgerHashChainVerificationReport:
    """Verify the ledger hash chain without creating/applying ledger storage."""
    return verify_hash_chain(experiment_id, readonly=True)


def get_history(experiment_id: str, *, readonly: bool = False) -> List[LedgerEvent]:
    reader = read_events_readonly if readonly else read_events
    return list(reader(experiment_id))


def get_history_readonly(experiment_id: str) -> List[LedgerEvent]:
    return get_history(experiment_id, readonly=True)


def hash_chain_is_valid(experiment_id: str, *, readonly: bool = False) -> bool:
    return verify_hash_chain(experiment_id, readonly=readonly).ok


def get_experiment(experiment_id: str, *, readonly: bool = False) -> Optional[ExperimentManifest]:
    """Return latest manifest snapshot for an experiment_id, if any."""
    if not hash_chain_is_valid(experiment_id, readonly=readonly):
        return None
    rows = get_history(experiment_id, readonly=readonly)
    if not rows:
        return None
    last = rows[-1]
    data = last.event_payload
    return ExperimentManifest.model_validate(data)


def list_promoted_strategies(*, readonly: bool = False) -> List[ExperimentManifest]:
    latest: Dict[str, ExperimentManifest] = {}
    reader = read_events_readonly if readonly else read_events
    event_stream = list(reader())
    experiment_ids = sorted({event.experiment_id for event in event_stream})
    valid_experiments = {eid for eid in experiment_ids if hash_chain_is_valid(eid, readonly=readonly)}
    
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


def iter_event_envelopes(experiment_id: str | None = None, *, readonly: bool = False) -> tuple[EventEnvelope, ...]:
    envelopes: list[EventEnvelope] = []
    reader = read_events_readonly if readonly else read_events
    for event in reader(experiment_id):
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
