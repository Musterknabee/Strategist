from __future__ import annotations

from datetime import datetime, timedelta

from strategy_validator.contracts.oracle_types import (
    OracleGovernanceDimension,
    OracleGovernanceDispatchClaimUrgency,
    OracleGovernanceDispatchPosture,
    OracleGovernanceDispatchTimeliness,
    OracleGovernancePlaneStatus,
    OracleGovernancePrimarySeverity,
    OracleGovernancePriorityBand,
    OracleGovernanceReviewTarget,
)
from strategy_validator.contracts.oracle_core import OracleGovernanceQueueKey
from strategy_validator.control_plane.governance_envelopes import (
    OracleGovernanceDispatchEnvelope,
    OracleGovernanceReviewEnvelope,
    OracleGovernanceRoutingEnvelope,
    sha256_text,
)


def build_governance_review_sort_key(
    *,
    review_due_by_utc: datetime | None,
    priority_score: int,
    queue_key: OracleGovernanceQueueKey,
) -> str:
    due_component = review_due_by_utc.isoformat() if review_due_by_utc else "9999-12-31T23:59:59+00:00"
    inverted_priority = max(0, 100 - int(priority_score))
    return f"{due_component}::{inverted_priority:03d}::{queue_key}"


def _governance_review_envelope_vector(
    *,
    review_due_by_utc: datetime,
    priority_score: int,
    queue_key: OracleGovernanceQueueKey,
    review_sort_key: str,
) -> str:
    return '|'.join([
        f'review_due_by_utc={review_due_by_utc.isoformat()}',
        f'priority_score={priority_score}',
        f'queue_key={queue_key}',
        f'review_sort_key={review_sort_key}',
    ])


def _governance_routing_vector(
    *,
    review_target: OracleGovernanceReviewTarget,
    review_sla_hours: int,
    review_due_by_utc: datetime,
    queue_key: OracleGovernanceQueueKey,
    route_vector: str,
    review_envelope_vector: str,
) -> str:
    return '|'.join([
        f'review_target={review_target}',
        f'review_sla_hours={review_sla_hours}',
        f'review_due_by_utc={review_due_by_utc.isoformat()}',
        f'queue_key={queue_key}',
        f'route_vector={route_vector}',
        f'review_envelope_vector={review_envelope_vector}',
    ])


def materialize_governance_review_envelope(
    *,
    issued_at_utc: datetime,
    review_sla_hours: int,
    priority_score: int,
    queue_key: OracleGovernanceQueueKey,
) -> OracleGovernanceReviewEnvelope:
    review_due_by_utc = issued_at_utc + timedelta(hours=review_sla_hours)
    review_sort_key = build_governance_review_sort_key(
        review_due_by_utc=review_due_by_utc,
        priority_score=priority_score,
        queue_key=queue_key,
    )
    review_envelope_vector = _governance_review_envelope_vector(
        review_due_by_utc=review_due_by_utc,
        priority_score=priority_score,
        queue_key=queue_key,
        review_sort_key=review_sort_key,
    )
    return OracleGovernanceReviewEnvelope(
        governance_plane_review_due_by_utc=review_due_by_utc,
        governance_plane_review_sort_key=review_sort_key,
        governance_plane_review_envelope_vector=review_envelope_vector,
        governance_plane_review_envelope_sha256=sha256_text(review_envelope_vector),
    )


def materialize_governance_routing_envelope(
    *,
    review_target: OracleGovernanceReviewTarget,
    review_sla_hours: int,
    queue_key: OracleGovernanceQueueKey,
    route_vector: str,
    review_envelope: OracleGovernanceReviewEnvelope,
) -> OracleGovernanceRoutingEnvelope:
    routing_summary_line = (
        f'Governance routing envelope: target={review_target}; sla_hours={review_sla_hours}; '
        f'due_by_utc={review_envelope.governance_plane_review_due_by_utc.isoformat()}; queue_key={queue_key}.'
    )
    routing_vector = _governance_routing_vector(
        review_target=review_target,
        review_sla_hours=review_sla_hours,
        review_due_by_utc=review_envelope.governance_plane_review_due_by_utc,
        queue_key=queue_key,
        route_vector=route_vector,
        review_envelope_vector=review_envelope.governance_plane_review_envelope_vector,
    )
    return OracleGovernanceRoutingEnvelope(
        governance_plane_routing_summary_line=routing_summary_line,
        governance_plane_routing_vector=routing_vector,
        governance_plane_routing_sha256=sha256_text(routing_vector),
    )




def _governance_dispatch_posture(
    *,
    governance_status: OracleGovernancePlaneStatus,
    review_target: OracleGovernanceReviewTarget,
    primary_dimension: OracleGovernanceDimension | None,
    primary_severity: OracleGovernancePrimarySeverity,
) -> tuple[OracleGovernanceDispatchPosture, bool, str, list[str]]:
    reasons: list[str] = []
    if governance_status == "GOVERNANCE_BLOCKED":
        reasons.append("Dispatch is blocked until constitutional repair clears the governance blocker.")
        if primary_dimension:
            reasons.append(f"Primary blocking dimension: {primary_dimension}.")
        return (
            "DISPATCH_BLOCKED",
            False,
            "Dispatch posture: DISPATCH_BLOCKED; do not hand this surface to downstream queue consumers yet.",
            reasons,
        )
    if governance_status == "GOVERNANCE_RESTRICTED":
        reasons.append("Dispatch is restricted to review-controlled handoff rather than routine downstream flow.")
        reasons.append(f"Review target: {review_target}.")
        if primary_dimension:
            reasons.append(f"Primary restricting dimension: {primary_dimension} ({primary_severity}).")
        return (
            "DISPATCH_REVIEW_ONLY",
            True,
            "Dispatch posture: DISPATCH_REVIEW_ONLY; handoff is permitted only into governed review queues.",
            reasons,
        )
    reasons.append("Dispatch is permitted for routine governed queue handoff.")
    reasons.append(f"Review target: {review_target}.")
    return (
        "DISPATCH_ALLOWED",
        True,
        "Dispatch posture: DISPATCH_ALLOWED; routine governed queue handoff is acceptable.",
        reasons,
    )


def _governance_dispatch_claim_key(
    *,
    queue_key: OracleGovernanceQueueKey,
    review_due_by_utc: datetime,
    dispatch_sha256: str,
) -> str:
    return f"{queue_key}::{review_due_by_utc.isoformat()}::{dispatch_sha256}"


def _governance_dispatch_timeliness(
    *,
    review_due_by_utc: datetime,
    now_utc: datetime,
    dispatch_permitted: bool,
) -> tuple[OracleGovernanceDispatchTimeliness, bool, str]:
    if not dispatch_permitted:
        return (
            "DISPATCH_OVERDUE",
            False,
            "Dispatch timeliness: DISPATCH_OVERDUE; claim is not permitted because dispatch itself is not currently permitted.",
        )
    remaining_seconds = (review_due_by_utc - now_utc).total_seconds()
    if remaining_seconds < 0:
        return (
            "DISPATCH_OVERDUE",
            False,
            "Dispatch timeliness: DISPATCH_OVERDUE; the governed dispatch claim window has passed.",
        )
    if remaining_seconds <= 4 * 3600:
        return (
            "DISPATCH_DUE_SOON",
            True,
            "Dispatch timeliness: DISPATCH_DUE_SOON; claim now and prioritize prompt governed review.",
        )
    return (
        "DISPATCH_ACTIVE",
        True,
        "Dispatch timeliness: DISPATCH_ACTIVE; governed claim is currently permissible.",
    )


def _governance_dispatch_claim_urgency(
    *,
    dispatch_permitted: bool,
    dispatch_claim_permitted_now: bool,
    dispatch_timeliness: OracleGovernanceDispatchTimeliness,
    priority_band: OracleGovernancePriorityBand,
) -> tuple[OracleGovernanceDispatchClaimUrgency, int, str]:
    if not dispatch_permitted or not dispatch_claim_permitted_now:
        return (
            "DO_NOT_CLAIM",
            0,
            "Dispatch claim urgency: DO_NOT_CLAIM; do not claim this handoff until governed dispatch becomes permissible again.",
        )
    if dispatch_timeliness == "DISPATCH_DUE_SOON":
        return (
            "CLAIM_NOW",
            100 if priority_band == "CRITICAL_PRIORITY" else 95,
            "Dispatch claim urgency: CLAIM_NOW; claim this handoff immediately and route it into governed review.",
        )
    if priority_band == "CRITICAL_PRIORITY":
        return (
            "CLAIM_NOW",
            92,
            "Dispatch claim urgency: CLAIM_NOW; critical governed priority justifies immediate claim even though the review window remains open.",
        )
    if priority_band == "ELEVATED_PRIORITY":
        return (
            "CLAIM_SOON",
            72,
            "Dispatch claim urgency: CLAIM_SOON; claim this handoff promptly under heightened review expectations.",
        )
    return (
        "CLAIM_SOON",
        48,
        "Dispatch claim urgency: CLAIM_SOON; routine governed claim is available and should be picked up in normal queue flow.",
    )


def _governance_dispatch_vector(
    *,
    queue_key: OracleGovernanceQueueKey,
    review_due_by_utc: datetime,
    review_sort_key: str,
    route_sha256: str,
    review_envelope_sha256: str,
    routing_envelope_sha256: str,
    dispatch_posture: OracleGovernanceDispatchPosture,
    dispatch_permitted: bool,
    dispatch_timeliness: OracleGovernanceDispatchTimeliness,
    dispatch_claim_permitted_now: bool,
    dispatch_claim_urgency: OracleGovernanceDispatchClaimUrgency,
    dispatch_claim_score: int,
) -> str:
    return '|'.join([
        f'queue_key={queue_key}',
        f'review_due_by_utc={review_due_by_utc.isoformat()}',
        f'review_sort_key={review_sort_key}',
        f'dispatch_posture={dispatch_posture}',
        f'dispatch_permitted={str(dispatch_permitted).lower()}',
        f'dispatch_timeliness={dispatch_timeliness}',
        f'dispatch_claim_permitted_now={str(dispatch_claim_permitted_now).lower()}',
        f'dispatch_claim_urgency={dispatch_claim_urgency}',
        f'dispatch_claim_score={dispatch_claim_score}',
        f'route_sha256={route_sha256}',
        f'review_envelope_sha256={review_envelope_sha256}',
        f'routing_envelope_sha256={routing_envelope_sha256}',
    ])


def materialize_governance_dispatch_envelope(
    *,
    queue_key: OracleGovernanceQueueKey,
    route_sha256: str,
    review_envelope: OracleGovernanceReviewEnvelope,
    routing_envelope: OracleGovernanceRoutingEnvelope,
    dispatch_posture: OracleGovernanceDispatchPosture,
    dispatch_permitted: bool,
    dispatch_summary_line: str,
    dispatch_reasons: list[str],
    priority_band: OracleGovernancePriorityBand,
    now_utc: datetime | None = None,
) -> OracleGovernanceDispatchEnvelope:
    effective_now_utc = now_utc or datetime.now(review_envelope.governance_plane_review_due_by_utc.tzinfo)
    dispatch_timeliness, dispatch_claim_permitted_now, dispatch_timeliness_summary_line = _governance_dispatch_timeliness(
        review_due_by_utc=review_envelope.governance_plane_review_due_by_utc,
        now_utc=effective_now_utc,
        dispatch_permitted=dispatch_permitted,
    )
    dispatch_claim_urgency, dispatch_claim_score, dispatch_claim_summary_line = _governance_dispatch_claim_urgency(
        dispatch_permitted=dispatch_permitted,
        dispatch_claim_permitted_now=dispatch_claim_permitted_now,
        dispatch_timeliness=dispatch_timeliness,
        priority_band=priority_band,
    )
    dispatch_vector = _governance_dispatch_vector(
        queue_key=queue_key,
        review_due_by_utc=review_envelope.governance_plane_review_due_by_utc,
        review_sort_key=review_envelope.governance_plane_review_sort_key,
        route_sha256=route_sha256,
        review_envelope_sha256=review_envelope.governance_plane_review_envelope_sha256,
        routing_envelope_sha256=routing_envelope.governance_plane_routing_sha256,
        dispatch_posture=dispatch_posture,
        dispatch_permitted=dispatch_permitted,
        dispatch_timeliness=dispatch_timeliness,
        dispatch_claim_permitted_now=dispatch_claim_permitted_now,
        dispatch_claim_urgency=dispatch_claim_urgency,
        dispatch_claim_score=dispatch_claim_score,
    )
    dispatch_sha256 = sha256_text(dispatch_vector)
    dispatch_claim_key = _governance_dispatch_claim_key(
        queue_key=queue_key,
        review_due_by_utc=review_envelope.governance_plane_review_due_by_utc,
        dispatch_sha256=dispatch_sha256,
    )
    dispatch_summary_line = dispatch_summary_line or (
        f'Governance dispatch envelope: queue_key={queue_key}; '
        f'due_by_utc={review_envelope.governance_plane_review_due_by_utc.isoformat()}; '
        f'claim_key={dispatch_claim_key}; '
        f'route_sha256={route_sha256}; '
        f'review_envelope_sha256={review_envelope.governance_plane_review_envelope_sha256}; '
        f'routing_envelope_sha256={routing_envelope.governance_plane_routing_sha256}.'
    )
    return OracleGovernanceDispatchEnvelope(
        governance_plane_dispatch_posture=dispatch_posture,
        governance_plane_dispatch_permitted=dispatch_permitted,
        governance_plane_dispatch_summary_line=dispatch_summary_line,
        governance_plane_dispatch_reasons=list(dispatch_reasons),
        governance_plane_dispatch_timeliness=dispatch_timeliness,
        governance_plane_dispatch_claim_permitted_now=dispatch_claim_permitted_now,
        governance_plane_dispatch_timeliness_summary_line=dispatch_timeliness_summary_line,
        governance_plane_dispatch_claim_urgency=dispatch_claim_urgency,
        governance_plane_dispatch_claim_score=dispatch_claim_score,
        governance_plane_dispatch_claim_summary_line=dispatch_claim_summary_line,
        governance_plane_dispatch_vector=dispatch_vector,
        governance_plane_dispatch_sha256=dispatch_sha256,
        governance_plane_dispatch_claim_key=dispatch_claim_key,
    )




