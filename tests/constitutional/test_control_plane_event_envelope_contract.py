from __future__ import annotations

from datetime import UTC, datetime

from strategy_validator.contracts.control_plane_event_envelope import (
    build_control_plane_event_envelope,
    verify_control_plane_event_envelope,
)


def test_control_plane_event_envelope_digest_is_stable_for_same_inputs() -> None:
    payload = {"schema_version": "example/v1", "count": 2, "items": ["a", "b"]}
    kwargs = {
        "event_type": "operator.example.materialized",
        "producer": "tests.example",
        "payload": payload,
        "idempotency_key": "idem-1",
        "occurred_at_utc": datetime(2026, 1, 1, tzinfo=UTC),
    }

    first = build_control_plane_event_envelope(**kwargs)
    second = build_control_plane_event_envelope(**kwargs)

    assert first.event_id == second.event_id
    assert first.payload_digest == second.payload_digest
    ok, issues = verify_control_plane_event_envelope(first)
    assert ok is True
    assert issues == ()


def test_control_plane_event_envelope_detects_payload_digest_drift() -> None:
    envelope = build_control_plane_event_envelope(
        event_type="operator.example.materialized",
        producer="tests.example",
        payload={"status": "RECORDED"},
    )
    drifted = envelope.__class__(**{**envelope.to_payload(), "payload": {"status": "DRIFTED"}})

    ok, issues = verify_control_plane_event_envelope(drifted)

    assert ok is False
    assert "CONTROL_PLANE_EVENT_PAYLOAD_DIGEST_MISMATCH" in issues
