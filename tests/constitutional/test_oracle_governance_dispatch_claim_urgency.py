from datetime import UTC, datetime

from strategy_validator.validator.oracle_governance_plane import (
    materialize_governance_dispatch_envelope,
    materialize_governance_review_envelope,
    materialize_governance_routing_envelope,
)


def test_dispatch_envelope_exposes_claim_now_for_due_soon_critical_work() -> None:
    issued_at = datetime(2026, 4, 14, 8, 0, tzinfo=UTC)
    review = materialize_governance_review_envelope(
        issued_at_utc=issued_at,
        review_sla_hours=1,
        priority_score=95,
        queue_key="CONSTITUTIONAL_REPAIR_QUEUE::CRITICAL_PRIORITY::REMEDIATION::BLOCKING",
    )
    routing = materialize_governance_routing_envelope(
        review_target="CONSTITUTIONAL_REPAIR_QUEUE",
        review_sla_hours=1,
        queue_key="CONSTITUTIONAL_REPAIR_QUEUE::CRITICAL_PRIORITY::REMEDIATION::BLOCKING",
        route_vector="priority=CRITICAL_PRIORITY|priority_score=95|review_target=CONSTITUTIONAL_REPAIR_QUEUE",
        review_envelope=review,
    )
    dispatch = materialize_governance_dispatch_envelope(
        queue_key="CONSTITUTIONAL_REPAIR_QUEUE::CRITICAL_PRIORITY::REMEDIATION::BLOCKING",
        route_sha256="d" * 64,
        review_envelope=review,
        routing_envelope=routing,
        dispatch_posture="DISPATCH_ALLOWED",
        dispatch_permitted=True,
        dispatch_summary_line="Dispatch posture: DISPATCH_ALLOWED; routine governed queue handoff is acceptable.",
        dispatch_reasons=["Dispatch is permitted for routine governed queue handoff."],
        priority_band="CRITICAL_PRIORITY",
        now_utc=issued_at,
    )
    assert dispatch.governance_plane_dispatch_claim_urgency == "CLAIM_NOW"
    assert dispatch.governance_plane_dispatch_claim_score >= 90
    assert "claim this handoff immediately" in dispatch.governance_plane_dispatch_claim_summary_line.lower()


def test_dispatch_envelope_exposes_do_not_claim_when_dispatch_blocked() -> None:
    issued_at = datetime(2026, 4, 14, 8, 0, tzinfo=UTC)
    review = materialize_governance_review_envelope(
        issued_at_utc=issued_at,
        review_sla_hours=24,
        priority_score=40,
        queue_key="ROUTINE_REVIEW_QUEUE::ROUTINE_PRIORITY::READINESS::READY",
    )
    routing = materialize_governance_routing_envelope(
        review_target="ROUTINE_REVIEW_QUEUE",
        review_sla_hours=24,
        queue_key="ROUTINE_REVIEW_QUEUE::ROUTINE_PRIORITY::READINESS::READY",
        route_vector="priority=ROUTINE_PRIORITY|priority_score=40|review_target=ROUTINE_REVIEW_QUEUE",
        review_envelope=review,
    )
    dispatch = materialize_governance_dispatch_envelope(
        queue_key="ROUTINE_REVIEW_QUEUE::ROUTINE_PRIORITY::READINESS::READY",
        route_sha256="e" * 64,
        review_envelope=review,
        routing_envelope=routing,
        dispatch_posture="DISPATCH_BLOCKED",
        dispatch_permitted=False,
        dispatch_summary_line="Dispatch posture: DISPATCH_BLOCKED; governed queue handoff must not proceed.",
        dispatch_reasons=["Governance is blocked."],
        priority_band="ROUTINE_PRIORITY",
        now_utc=issued_at,
    )
    assert dispatch.governance_plane_dispatch_claim_urgency == "DO_NOT_CLAIM"
    assert dispatch.governance_plane_dispatch_claim_score == 0
    assert "do not claim" in dispatch.governance_plane_dispatch_claim_summary_line.lower()
