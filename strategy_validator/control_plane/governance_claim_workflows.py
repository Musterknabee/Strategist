from __future__ import annotations

from datetime import datetime, timedelta

from strategy_validator.contracts.oracle import (
    OracleGovernanceClaimActionItem,
    OracleGovernanceClaimCode,
    OracleGovernanceClaimDisposition,
    OracleGovernanceClaimLeaseAction,
    OracleGovernanceClaimLeaseCoverage,
    OracleGovernanceClaimLeaseHealth,
    OracleGovernanceClaimLeaseMode,
    OracleGovernanceClaimLeaseRenewalPosture,
    OracleGovernanceClaimOperability,
    OracleGovernanceClaimProcessPosture,
    OracleGovernanceClaimWorkerLane,
    OracleGovernanceDispatchClaimUrgency,
    OracleGovernanceDispatchPosture,
    OracleGovernanceDispatchTimeliness,
    OracleGovernancePriorityBand,
    OracleGovernanceQueueKey,
    OracleGovernanceReviewTarget,
)
from strategy_validator.control_plane.governance_envelopes import (
    OracleGovernanceClaimEnvelope,
    OracleGovernanceDispatchEnvelope,
    sha256_text,
    unique_text,
)


def _governance_claim_codes(
    *,
    dispatch_posture: OracleGovernanceDispatchPosture,
    dispatch_timeliness: OracleGovernanceDispatchTimeliness,
    dispatch_claim_urgency: OracleGovernanceDispatchClaimUrgency,
) -> tuple[list[OracleGovernanceClaimCode], OracleGovernanceClaimCode | None]:
    codes: list[OracleGovernanceClaimCode] = []
    if dispatch_posture == "DISPATCH_BLOCKED":
        codes.append("CLAIM_PERMISSION_BLOCKED")
    if dispatch_timeliness == "DISPATCH_OVERDUE":
        codes.append("CLAIM_OVERDUE")
    elif dispatch_claim_urgency == "CLAIM_NOW":
        codes.append("CLAIM_IMMEDIATE")
    elif dispatch_claim_urgency == "CLAIM_SOON":
        codes.append("CLAIM_DUE_SOON")
    else:
        codes.append("CLAIM_ROUTINE")
    primary = codes[0] if codes else None
    return codes, primary


def _governance_claim_action_items(
    *,
    dispatch_posture: OracleGovernanceDispatchPosture,
    dispatch_timeliness: OracleGovernanceDispatchTimeliness,
    dispatch_claim_urgency: OracleGovernanceDispatchClaimUrgency,
    claim_primary_code: OracleGovernanceClaimCode | None,
) -> tuple[list[OracleGovernanceClaimActionItem], str]:
    items: list[OracleGovernanceClaimActionItem] = []
    if dispatch_posture == "DISPATCH_BLOCKED":
        items.append(
            OracleGovernanceClaimActionItem(
                code="CLAIM_PERMISSION_BLOCKED",
                severity="BLOCKED",
                action_text="Do not claim this handoff; hold it in blocked governance flow until dispatch restrictions are cleared.",
            )
        )
    elif dispatch_timeliness == "DISPATCH_OVERDUE":
        items.append(
            OracleGovernanceClaimActionItem(
                code="CLAIM_OVERDUE",
                severity="URGENT",
                action_text="Escalate this overdue claim immediately and re-materialize governed dispatch if the work still needs review.",
            )
        )
    elif dispatch_claim_urgency == "CLAIM_NOW":
        items.append(
            OracleGovernanceClaimActionItem(
                code=claim_primary_code or "CLAIM_IMMEDIATE",
                severity="URGENT",
                action_text="Claim this handoff immediately and place it into the immediate claim worker lane.",
            )
        )
    elif dispatch_claim_urgency == "CLAIM_SOON":
        items.append(
            OracleGovernanceClaimActionItem(
                code=claim_primary_code or "CLAIM_DUE_SOON",
                severity="PROMPT",
                action_text="Claim this handoff promptly and keep it moving through the near-due worker lane before the review deadline.",
            )
        )
    else:
        items.append(
            OracleGovernanceClaimActionItem(
                code=claim_primary_code or "CLAIM_ROUTINE",
                severity="ROUTINE",
                action_text="Process this handoff in routine governed claim flow.",
            )
        )
    primary_action_text = items[0].action_text if items else ""
    return items, primary_action_text


def _governance_claim_worker_lane(
    *,
    dispatch_posture: OracleGovernanceDispatchPosture,
    dispatch_claim_urgency: OracleGovernanceDispatchClaimUrgency,
) -> tuple[OracleGovernanceClaimWorkerLane, str]:
    if dispatch_posture == "DISPATCH_BLOCKED":
        return (
            "BLOCKED_CLAIM_HOLDING",
            "Governance claim worker lane: BLOCKED_CLAIM_HOLDING; do not claim until governance restrictions are cleared.",
        )
    if dispatch_claim_urgency == "CLAIM_NOW":
        return (
            "IMMEDIATE_CLAIM_WORKER",
            "Governance claim worker lane: IMMEDIATE_CLAIM_WORKER; prioritize immediate claim handling.",
        )
    if dispatch_claim_urgency == "CLAIM_SOON":
        return (
            "NEAR_DUE_CLAIM_WORKER",
            "Governance claim worker lane: NEAR_DUE_CLAIM_WORKER; claim soon before the review deadline.",
        )
    return (
        "ROUTINE_CLAIM_WORKER",
        "Governance claim worker lane: ROUTINE_CLAIM_WORKER; process in routine claim flow.",
    )


def _governance_claim_lease_action(
    *,
    lease_mode: OracleGovernanceClaimLeaseMode,
    lease_active_now: bool,
    lease_renewal_posture: OracleGovernanceClaimLeaseRenewalPosture,
    dispatch_claim_permitted_now: bool,
) -> tuple[OracleGovernanceClaimLeaseAction, str]:
    if lease_mode == "NO_LEASE" or not dispatch_claim_permitted_now:
        return (
            "NO_LEASE_ACTION",
            "Governance claim lease action: NO_LEASE_ACTION; do not acquire or maintain a lease while claim handoff is not permitted.",
        )
    if not lease_active_now:
        return (
            "ACQUIRE_LEASE_NOW",
            "Governance claim lease action: ACQUIRE_LEASE_NOW; acquire a governed lease before claim processing continues.",
        )
    if lease_renewal_posture == "RENEW_NOW":
        return (
            "RENEW_LEASE_NOW",
            "Governance claim lease action: RENEW_LEASE_NOW; renew the governed lease immediately so coverage outlasts the review window.",
        )
    if lease_renewal_posture == "RENEW_SOON":
        return (
            "MAINTAIN_LEASE",
            "Governance claim lease action: MAINTAIN_LEASE; keep the lease active and prepare renewal before review coverage expires.",
        )
    return (
        "MAINTAIN_LEASE",
        "Governance claim lease action: MAINTAIN_LEASE; current governed lease coverage is sufficient for ongoing claim handling.",
    )


def _governance_claim_disposition(
    *,
    dispatch_posture: OracleGovernanceDispatchPosture,
    dispatch_timeliness: OracleGovernanceDispatchTimeliness,
    dispatch_claim_urgency: OracleGovernanceDispatchClaimUrgency,
) -> tuple[OracleGovernanceClaimDisposition, str]:
    if dispatch_posture == "DISPATCH_BLOCKED":
        return (
            "CLAIM_HOLD",
            "Governance claim disposition: CLAIM_HOLD; keep this handoff on hold until governance dispatch restrictions are cleared.",
        )
    if dispatch_timeliness == "DISPATCH_OVERDUE":
        return (
            "CLAIM_ESCALATE",
            "Governance claim disposition: CLAIM_ESCALATE; escalate this overdue handoff immediately before further queueing.",
        )
    if dispatch_claim_urgency == "CLAIM_NOW":
        return (
            "CLAIM_PRIORITIZE",
            "Governance claim disposition: CLAIM_PRIORITIZE; claim and prioritize this handoff immediately.",
        )
    if dispatch_claim_urgency == "CLAIM_SOON":
        return (
            "CLAIM_QUEUE_PROMPT",
            "Governance claim disposition: CLAIM_QUEUE_PROMPT; queue this handoff promptly ahead of near-due work.",
        )
    return (
        "CLAIM_QUEUE_ROUTINE",
        "Governance claim disposition: CLAIM_QUEUE_ROUTINE; queue this handoff in routine governed claim flow.",
    )

def _governance_claim_worker_sort_key(
    *,
    claim_worker_lane: OracleGovernanceClaimWorkerLane,
    review_due_by_utc: datetime,
    dispatch_claim_score: int,
    claim_primary_code: OracleGovernanceClaimCode | None,
    dispatch_claim_key: str,
) -> str:
    inverted_score = max(0, 100 - int(dispatch_claim_score))
    return '::'.join([
        claim_worker_lane,
        review_due_by_utc.isoformat(),
        f'{inverted_score:03d}',
        claim_primary_code or 'none',
        dispatch_claim_key,
    ])

def _governance_claim_lease_key(
    *,
    claim_worker_lane: OracleGovernanceClaimWorkerLane,
    queue_key: OracleGovernanceQueueKey,
    review_due_by_utc: datetime,
    dispatch_claim_key: str,
    now_utc: datetime,
) -> tuple[str, OracleGovernanceClaimLeaseMode, int, datetime | None, bool, str]:
    lease_key = '::'.join([
        claim_worker_lane,
        queue_key,
        review_due_by_utc.isoformat(),
        dispatch_claim_key,
    ])
    if claim_worker_lane == 'BLOCKED_CLAIM_HOLDING':
        lease_mode: OracleGovernanceClaimLeaseMode = 'NO_LEASE'
        lease_ttl_seconds = 0
    elif claim_worker_lane == 'ROUTINE_CLAIM_WORKER':
        lease_mode = 'STANDARD_LEASE'
        lease_ttl_seconds = 7200
    else:
        lease_mode = 'SHORT_LEASE'
        lease_ttl_seconds = 1800 if claim_worker_lane == 'NEAR_DUE_CLAIM_WORKER' else 900
    lease_expires_at_utc = None if lease_ttl_seconds <= 0 else now_utc + timedelta(seconds=lease_ttl_seconds)
    lease_active_now = lease_ttl_seconds > 0
    lease_summary_line = (
        f'Governance claim lease: lane={claim_worker_lane}; '
        f'queue_key={queue_key}; '
        f'lease_mode={lease_mode}; '
        f'lease_ttl_seconds={lease_ttl_seconds}; '
        f'lease_expires_at_utc={(lease_expires_at_utc.isoformat() if lease_expires_at_utc else "none")}; '
        f'lease_active_now={str(lease_active_now).lower()}; '
        f'due_by_utc={review_due_by_utc.isoformat()}; '
        f'dispatch_claim_key={dispatch_claim_key}.'
    )
    return lease_key, lease_mode, lease_ttl_seconds, lease_expires_at_utc, lease_active_now, lease_summary_line



def _governance_claim_lease_coverage(
    *,
    lease_mode: OracleGovernanceClaimLeaseMode,
    lease_active_now: bool,
    lease_expires_at_utc: datetime | None,
    review_due_by_utc: datetime,
) -> tuple[OracleGovernanceClaimLeaseCoverage, str]:
    if lease_mode == "NO_LEASE" or not lease_active_now or lease_expires_at_utc is None:
        return (
            "NO_LEASE_COVERAGE",
            "Governance claim lease coverage: NO_LEASE_COVERAGE; there is no active governed lease covering claim work.",
        )
    if lease_expires_at_utc < review_due_by_utc:
        return (
            "LEASE_PARTIAL_COVERAGE",
            f"Governance claim lease coverage: LEASE_PARTIAL_COVERAGE; current lease expires at {lease_expires_at_utc.isoformat()} before the governed review window closes at {review_due_by_utc.isoformat()}.",
        )
    return (
        "LEASE_FULL_COVERAGE",
        f"Governance claim lease coverage: LEASE_FULL_COVERAGE; current lease remains valid through the governed review window ending at {review_due_by_utc.isoformat()}.",
    )


def _governance_claim_lease_health(
    *,
    lease_mode: OracleGovernanceClaimLeaseMode,
    lease_active_now: bool,
    lease_coverage: OracleGovernanceClaimLeaseCoverage,
    lease_renewal_posture: OracleGovernanceClaimLeaseRenewalPosture,
    lease_action: OracleGovernanceClaimLeaseAction,
    dispatch_claim_permitted_now: bool,
) -> tuple[OracleGovernanceClaimLeaseHealth, str]:
    if lease_mode == "NO_LEASE" or not dispatch_claim_permitted_now:
        return (
            "LEASE_BLOCKED",
            "Governance claim lease health: LEASE_BLOCKED; claim handoff is not currently permitted for active lease operations.",
        )
    if not lease_active_now or lease_coverage == "NO_LEASE_COVERAGE":
        return (
            "LEASE_BLOCKED",
            "Governance claim lease health: LEASE_BLOCKED; no active governed lease currently covers claim work.",
        )
    if lease_coverage == "LEASE_PARTIAL_COVERAGE" or lease_renewal_posture in {"RENEW_SOON", "RENEW_NOW"} or lease_action == "RENEW_LEASE_NOW":
        return (
            "LEASE_DEGRADED",
            "Governance claim lease health: LEASE_DEGRADED; current lease remains active but will not fully cover the governed review window without renewal attention.",
        )
    return (
        "LEASE_HEALTHY",
        "Governance claim lease health: LEASE_HEALTHY; current governed lease remains active and fully covers the review window.",
    )


def _governance_claim_lease_renewal(
    *,
    lease_mode: OracleGovernanceClaimLeaseMode,
    lease_active_now: bool,
    lease_expires_at_utc: datetime | None,
    now_utc: datetime,
    review_due_by_utc: datetime,
) -> tuple[OracleGovernanceClaimLeaseRenewalPosture, bool, str]:
    if lease_mode == 'NO_LEASE' or not lease_active_now or lease_expires_at_utc is None:
        posture: OracleGovernanceClaimLeaseRenewalPosture = 'NO_RENEWAL'
        permitted = False
        summary = 'Governance claim lease renewal: posture=NO_RENEWAL; renewal_permitted_now=false; no active lease is present to renew.'
        return posture, permitted, summary
    seconds_remaining = max(0, int((lease_expires_at_utc - now_utc).total_seconds()))
    seconds_until_review_due = int((review_due_by_utc - now_utc).total_seconds())
    if lease_expires_at_utc < review_due_by_utc:
        if seconds_remaining <= 300:
            posture = 'RENEW_NOW'
            permitted = True
            summary = f'Governance claim lease renewal: posture=RENEW_NOW; renewal_permitted_now=true; lease_seconds_remaining={seconds_remaining}; review_due_in_seconds={seconds_until_review_due}; renew immediately because the lease expires before the governed review window closes.'
            return posture, permitted, summary
        posture = 'RENEW_SOON'
        permitted = True
        summary = f'Governance claim lease renewal: posture=RENEW_SOON; renewal_permitted_now=true; lease_seconds_remaining={seconds_remaining}; review_due_in_seconds={seconds_until_review_due}; renew soon because the lease expires before the governed review window closes.'
        return posture, permitted, summary
    posture = 'NO_RENEWAL'
    permitted = False
    summary = f'Governance claim lease renewal: posture=NO_RENEWAL; renewal_permitted_now=false; lease_seconds_remaining={seconds_remaining}; review_due_in_seconds={seconds_until_review_due}; current lease window remains sufficient.'
    return posture, permitted, summary

def _governance_claim_process_posture(
    *,
    dispatch_claim_permitted_now: bool,
    claim_disposition: OracleGovernanceClaimDisposition,
    claim_lease_action: OracleGovernanceClaimLeaseAction,
) -> tuple[OracleGovernanceClaimProcessPosture, bool, str]:
    if not dispatch_claim_permitted_now or claim_disposition in {"CLAIM_HOLD", "CLAIM_ESCALATE"}:
        return (
            "PROCESS_BLOCKED",
            False,
            "Governance claim process posture: PROCESS_BLOCKED; claim work must not proceed until governance restrictions or escalation conditions are cleared.",
        )
    if claim_lease_action in {"ACQUIRE_LEASE_NOW", "RENEW_LEASE_NOW"}:
        return (
            "PROCESS_READY_AFTER_LEASE",
            False,
            "Governance claim process posture: PROCESS_READY_AFTER_LEASE; complete the required lease operation before claim work proceeds.",
        )
    if claim_disposition in {"CLAIM_PRIORITIZE", "CLAIM_QUEUE_PROMPT"}:
        return (
            "PROCESS_READY_NOW",
            True,
            "Governance claim process posture: PROCESS_READY_NOW; claim work may proceed immediately in governed worker flow.",
        )
    return (
        "PROCESS_QUEUE_ONLY",
        True,
        "Governance claim process posture: PROCESS_QUEUE_ONLY; claim work may proceed in routine queued governed flow.",
    )


def _governance_claim_operability(
    *,
    claim_process_posture: OracleGovernanceClaimProcessPosture,
    claim_process_permitted_now: bool,
    claim_lease_health: OracleGovernanceClaimLeaseHealth,
    claim_disposition: OracleGovernanceClaimDisposition,
) -> tuple[OracleGovernanceClaimOperability, str]:
    if not claim_process_permitted_now or claim_process_posture == "PROCESS_BLOCKED":
        return (
            "CLAIM_INOPERABLE",
            "Governance claim operability: CLAIM_INOPERABLE; claim work must not proceed until governance restrictions are cleared.",
        )
    if claim_process_posture == "PROCESS_READY_AFTER_LEASE" or claim_lease_health == "LEASE_DEGRADED":
        return (
            "CLAIM_CONSTRAINED",
            "Governance claim operability: CLAIM_CONSTRAINED; claim work is allowed but remains constrained by lease coverage or required lease operations.",
        )
    if claim_lease_health == "LEASE_HEALTHY" and claim_process_posture in {"PROCESS_READY_NOW", "PROCESS_QUEUE_ONLY"}:
        return (
            "CLAIM_OPERABLE",
            "Governance claim operability: CLAIM_OPERABLE; claim work may proceed under the current governed lease and process posture.",
        )
    return (
        "CLAIM_CONSTRAINED",
        "Governance claim operability: CLAIM_CONSTRAINED; claim work is allowed but remains operationally constrained by the current governed posture.",
    )


def _governance_claim_vector(
    *,
    queue_key: OracleGovernanceQueueKey,
    review_target: OracleGovernanceReviewTarget,
    priority_band: OracleGovernancePriorityBand,
    review_due_by_utc: datetime,
    review_sort_key: str,
    route_sha256: str,
    review_envelope_sha256: str,
    routing_envelope_sha256: str,
    claim_codes: list[OracleGovernanceClaimCode],
    claim_primary_code: OracleGovernanceClaimCode | None,
    claim_action_items: list[OracleGovernanceClaimActionItem],
    claim_primary_action_text: str,
    claim_worker_lane: OracleGovernanceClaimWorkerLane,
    claim_worker_sort_key: str,
    claim_lease_key: str,
    claim_lease_mode: OracleGovernanceClaimLeaseMode,
    claim_lease_ttl_seconds: int,
    claim_lease_expires_at_utc: datetime | None,
    claim_lease_active_now: bool,
    claim_lease_coverage: OracleGovernanceClaimLeaseCoverage,
    claim_lease_coverage_summary_line: str,
    claim_lease_health: OracleGovernanceClaimLeaseHealth,
    claim_lease_health_summary_line: str,
    claim_lease_renewal_posture: OracleGovernanceClaimLeaseRenewalPosture,
    claim_lease_renewal_permitted_now: bool,
    claim_lease_renewal_summary_line: str,
    claim_lease_action: OracleGovernanceClaimLeaseAction,
    claim_lease_action_summary_line: str,
    claim_disposition: OracleGovernanceClaimDisposition,
    claim_disposition_summary_line: str,
    claim_process_posture: OracleGovernanceClaimProcessPosture,
    claim_process_permitted_now: bool,
    claim_process_summary_line: str,
    claim_operability: OracleGovernanceClaimOperability,
    claim_operability_summary_line: str,
    dispatch_claim_key: str,
    dispatch_posture: OracleGovernanceDispatchPosture,
    dispatch_permitted: bool,
    dispatch_timeliness: OracleGovernanceDispatchTimeliness,
    dispatch_claim_permitted_now: bool,
    dispatch_claim_urgency: OracleGovernanceDispatchClaimUrgency,
    dispatch_claim_score: int,
    dispatch_sha256: str,
) -> str:
    return '|'.join([
        f'queue_key={queue_key}',
        f'review_target={review_target}',
        f'priority_band={priority_band}',
        f'review_due_by_utc={review_due_by_utc.isoformat()}',
        f'review_sort_key={review_sort_key}',
        f'route_sha256={route_sha256}',
        f'review_envelope_sha256={review_envelope_sha256}',
        f'routing_envelope_sha256={routing_envelope_sha256}',
        f'claim_codes={','.join(claim_codes)}',
        f'claim_primary_code={claim_primary_code or 'none'}',
        f'claim_action_items={';'.join(f'{item.code}:{item.severity}:{item.action_text}' for item in claim_action_items)}',
        f'claim_primary_action_text={claim_primary_action_text or 'none'}',
        f'claim_worker_lane={claim_worker_lane}',
        f'claim_worker_sort_key={claim_worker_sort_key}',
        f'claim_lease_key={claim_lease_key}',
        f'claim_lease_mode={claim_lease_mode}',
        f'claim_lease_ttl_seconds={claim_lease_ttl_seconds}',
        f'claim_lease_expires_at_utc={(claim_lease_expires_at_utc.isoformat() if claim_lease_expires_at_utc else "none")}',
        f'claim_lease_active_now={str(claim_lease_active_now).lower()}',
        f'claim_lease_coverage={claim_lease_coverage}',
        f'claim_lease_coverage_summary_line={claim_lease_coverage_summary_line}',
        f'claim_lease_health={claim_lease_health}',
        f'claim_lease_health_summary_line={claim_lease_health_summary_line}',
        f'claim_lease_renewal_posture={claim_lease_renewal_posture}',
        f'claim_lease_renewal_permitted_now={str(claim_lease_renewal_permitted_now).lower()}',
        f'claim_lease_renewal_summary_line={claim_lease_renewal_summary_line}',
        f'claim_lease_action={claim_lease_action}',
        f'claim_lease_action_summary_line={claim_lease_action_summary_line}',
        f'claim_disposition={claim_disposition}',
        f'claim_disposition_summary_line={claim_disposition_summary_line}',
        f'claim_process_posture={claim_process_posture}',
        f'claim_process_permitted_now={str(claim_process_permitted_now).lower()}',
        f'claim_process_summary_line={claim_process_summary_line}',
        f'claim_operability={claim_operability}',
        f'claim_operability_summary_line={claim_operability_summary_line}',
        f'dispatch_claim_key={dispatch_claim_key}',
        f'dispatch_posture={dispatch_posture}',
        f'dispatch_permitted={str(dispatch_permitted).lower()}',
        f'dispatch_timeliness={dispatch_timeliness}',
        f'dispatch_claim_permitted_now={str(dispatch_claim_permitted_now).lower()}',
        f'dispatch_claim_urgency={dispatch_claim_urgency}',
        f'dispatch_claim_score={dispatch_claim_score}',
        f'dispatch_sha256={dispatch_sha256}',
    ])


def materialize_governance_claim_envelope(
    *,
    dispatch_envelope: OracleGovernanceDispatchEnvelope,
    queue_key: OracleGovernanceQueueKey,
    review_target: OracleGovernanceReviewTarget,
    priority_band: OracleGovernancePriorityBand,
    review_due_by_utc: datetime,
    review_sort_key: str,
    route_sha256: str,
    review_envelope_sha256: str,
    routing_envelope_sha256: str,
    now_utc: datetime | None = None,
) -> OracleGovernanceClaimEnvelope:
    claim_codes, claim_primary_code = _governance_claim_codes(
        dispatch_posture=dispatch_envelope.governance_plane_dispatch_posture,
        dispatch_timeliness=dispatch_envelope.governance_plane_dispatch_timeliness,
        dispatch_claim_urgency=dispatch_envelope.governance_plane_dispatch_claim_urgency,
    )
    claim_action_items, claim_primary_action_text = _governance_claim_action_items(
        dispatch_posture=dispatch_envelope.governance_plane_dispatch_posture,
        dispatch_timeliness=dispatch_envelope.governance_plane_dispatch_timeliness,
        dispatch_claim_urgency=dispatch_envelope.governance_plane_dispatch_claim_urgency,
        claim_primary_code=claim_primary_code,
    )
    claim_worker_lane, claim_worker_summary_line = _governance_claim_worker_lane(
        dispatch_posture=dispatch_envelope.governance_plane_dispatch_posture,
        dispatch_claim_urgency=dispatch_envelope.governance_plane_dispatch_claim_urgency,
    )
    claim_worker_sort_key = _governance_claim_worker_sort_key(
        claim_worker_lane=claim_worker_lane,
        review_due_by_utc=review_due_by_utc,
        dispatch_claim_score=dispatch_envelope.governance_plane_dispatch_claim_score,
        claim_primary_code=claim_primary_code,
        dispatch_claim_key=dispatch_envelope.governance_plane_dispatch_claim_key,
    )

    effective_now_utc = now_utc or review_due_by_utc
    claim_lease_key, claim_lease_mode, claim_lease_ttl_seconds, claim_lease_expires_at_utc, claim_lease_active_now, claim_lease_summary_line = _governance_claim_lease_key(
        claim_worker_lane=claim_worker_lane,
        queue_key=queue_key,
        review_due_by_utc=review_due_by_utc,
        dispatch_claim_key=dispatch_envelope.governance_plane_dispatch_claim_key,
        now_utc=effective_now_utc,
    )
    claim_lease_coverage, claim_lease_coverage_summary_line = _governance_claim_lease_coverage(
        lease_mode=claim_lease_mode,
        lease_active_now=claim_lease_active_now,
        lease_expires_at_utc=claim_lease_expires_at_utc,
        review_due_by_utc=review_due_by_utc,
    )
    claim_lease_renewal_posture, claim_lease_renewal_permitted_now, claim_lease_renewal_summary_line = _governance_claim_lease_renewal(
        lease_mode=claim_lease_mode,
        lease_active_now=claim_lease_active_now,
        lease_expires_at_utc=claim_lease_expires_at_utc,
        now_utc=effective_now_utc,
        review_due_by_utc=review_due_by_utc,
    )
    claim_lease_action, claim_lease_action_summary_line = _governance_claim_lease_action(
        lease_mode=claim_lease_mode,
        lease_active_now=claim_lease_active_now,
        lease_renewal_posture=claim_lease_renewal_posture,
        dispatch_claim_permitted_now=dispatch_envelope.governance_plane_dispatch_claim_permitted_now,
    )
    claim_lease_health, claim_lease_health_summary_line = _governance_claim_lease_health(
        lease_mode=claim_lease_mode,
        lease_active_now=claim_lease_active_now,
        lease_coverage=claim_lease_coverage,
        lease_renewal_posture=claim_lease_renewal_posture,
        lease_action=claim_lease_action,
        dispatch_claim_permitted_now=dispatch_envelope.governance_plane_dispatch_claim_permitted_now,
    )

    claim_disposition, claim_disposition_summary_line = _governance_claim_disposition(
        dispatch_posture=dispatch_envelope.governance_plane_dispatch_posture,
        dispatch_timeliness=dispatch_envelope.governance_plane_dispatch_timeliness,
        dispatch_claim_urgency=dispatch_envelope.governance_plane_dispatch_claim_urgency,
    )
    claim_process_posture, claim_process_permitted_now, claim_process_summary_line = _governance_claim_process_posture(
        dispatch_claim_permitted_now=dispatch_envelope.governance_plane_dispatch_claim_permitted_now,
        claim_disposition=claim_disposition,
        claim_lease_action=claim_lease_action,
    )
    claim_operability, claim_operability_summary_line = _governance_claim_operability(
        claim_process_posture=claim_process_posture,
        claim_process_permitted_now=claim_process_permitted_now,
        claim_lease_health=claim_lease_health,
        claim_disposition=claim_disposition,
    )

    claim_summary_line = (
        f'Governance claim envelope: queue_key={queue_key}; '
        f'review_target={review_target}; '
        f'priority_band={priority_band}; '
        f'due_by_utc={review_due_by_utc.isoformat()}; '
        f'sort_key={review_sort_key}; '
        f'claim_codes={','.join(claim_codes)}; '
        f'claim_primary_code={claim_primary_code or 'none'}; '
        f'claim_primary_action_text={claim_primary_action_text or 'none'}; '
        f'claim_worker_lane={claim_worker_lane}; '
        f'worker_sort_key={claim_worker_sort_key}; '
        f'lease_key={claim_lease_key}; '
        f'lease_mode={claim_lease_mode}; '
        f'lease_ttl_seconds={claim_lease_ttl_seconds}; '
        f'lease_expires_at_utc={(claim_lease_expires_at_utc.isoformat() if claim_lease_expires_at_utc else "none")}; '
        f'lease_active_now={str(claim_lease_active_now).lower()}; '
        f'lease_coverage={claim_lease_coverage}; '
        f'lease_health={claim_lease_health}; '
        f'lease_renewal_posture={claim_lease_renewal_posture}; '
        f'lease_renewal_permitted_now={str(claim_lease_renewal_permitted_now).lower()}; '
        f'lease_action={claim_lease_action}; '
        f'disposition={claim_disposition}; '
        f'process_posture={claim_process_posture}; '
        f'claim_key={dispatch_envelope.governance_plane_dispatch_claim_key}; '
        f'posture={dispatch_envelope.governance_plane_dispatch_posture}; '
        f'timeliness={dispatch_envelope.governance_plane_dispatch_timeliness}; '
        f'urgency={dispatch_envelope.governance_plane_dispatch_claim_urgency}; '
        f'claim_permitted_now={str(dispatch_envelope.governance_plane_dispatch_claim_permitted_now).lower()}.'
    )
    claim_vector = _governance_claim_vector(
        queue_key=queue_key,
        review_target=review_target,
        priority_band=priority_band,
        review_due_by_utc=review_due_by_utc,
        review_sort_key=review_sort_key,
        route_sha256=route_sha256,
        review_envelope_sha256=review_envelope_sha256,
        routing_envelope_sha256=routing_envelope_sha256,
        claim_codes=claim_codes,
        claim_primary_code=claim_primary_code,
        claim_action_items=claim_action_items,
        claim_primary_action_text=claim_primary_action_text,
        claim_worker_lane=claim_worker_lane,
        claim_worker_sort_key=claim_worker_sort_key,
        claim_lease_key=claim_lease_key,
        claim_lease_mode=claim_lease_mode,
        claim_lease_ttl_seconds=claim_lease_ttl_seconds,
        claim_lease_expires_at_utc=claim_lease_expires_at_utc,
        claim_lease_active_now=claim_lease_active_now,
        claim_lease_coverage=claim_lease_coverage,
        claim_lease_coverage_summary_line=claim_lease_coverage_summary_line,
        claim_lease_health=claim_lease_health,
        claim_lease_health_summary_line=claim_lease_health_summary_line,
        claim_lease_renewal_posture=claim_lease_renewal_posture,
        claim_lease_renewal_permitted_now=claim_lease_renewal_permitted_now,
        claim_lease_renewal_summary_line=claim_lease_renewal_summary_line,
        claim_lease_action=claim_lease_action,
        claim_lease_action_summary_line=claim_lease_action_summary_line,
        claim_disposition=claim_disposition,
        claim_disposition_summary_line=claim_disposition_summary_line,
        claim_process_posture=claim_process_posture,
        claim_process_permitted_now=claim_process_permitted_now,
        claim_process_summary_line=claim_process_summary_line,
        claim_operability=claim_operability,
        claim_operability_summary_line=claim_operability_summary_line,
        dispatch_claim_key=dispatch_envelope.governance_plane_dispatch_claim_key,
        dispatch_posture=dispatch_envelope.governance_plane_dispatch_posture,
        dispatch_permitted=dispatch_envelope.governance_plane_dispatch_permitted,
        dispatch_timeliness=dispatch_envelope.governance_plane_dispatch_timeliness,
        dispatch_claim_permitted_now=dispatch_envelope.governance_plane_dispatch_claim_permitted_now,
        dispatch_claim_urgency=dispatch_envelope.governance_plane_dispatch_claim_urgency,
        dispatch_claim_score=dispatch_envelope.governance_plane_dispatch_claim_score,
        dispatch_sha256=dispatch_envelope.governance_plane_dispatch_sha256,
    )
    return OracleGovernanceClaimEnvelope(
        governance_plane_claim_summary_line=claim_summary_line,
        governance_plane_claim_queue_key=queue_key,
        governance_plane_claim_review_target=review_target,
        governance_plane_claim_priority_band=priority_band,
        governance_plane_claim_review_due_by_utc=review_due_by_utc,
        governance_plane_claim_review_sort_key=review_sort_key,
        governance_plane_claim_route_sha256=route_sha256,
        governance_plane_claim_review_envelope_sha256=review_envelope_sha256,
        governance_plane_claim_routing_envelope_sha256=routing_envelope_sha256,
        governance_plane_claim_dispatch_claim_key=dispatch_envelope.governance_plane_dispatch_claim_key,
        governance_plane_claim_dispatch_sha256=dispatch_envelope.governance_plane_dispatch_sha256,
        governance_plane_claim_codes=claim_codes,
        governance_plane_claim_primary_code=claim_primary_code,
        governance_plane_claim_action_items=claim_action_items,
        governance_plane_claim_primary_action_text=claim_primary_action_text,
        governance_plane_claim_worker_lane=claim_worker_lane,
        governance_plane_claim_worker_summary_line=claim_worker_summary_line,
        governance_plane_claim_worker_sort_key=claim_worker_sort_key,
        governance_plane_claim_lease_key=claim_lease_key,
        governance_plane_claim_lease_mode=claim_lease_mode,
        governance_plane_claim_lease_ttl_seconds=claim_lease_ttl_seconds,
        governance_plane_claim_lease_expires_at_utc=claim_lease_expires_at_utc,
        governance_plane_claim_lease_active_now=claim_lease_active_now,
        governance_plane_claim_lease_summary_line=claim_lease_summary_line,
        governance_plane_claim_lease_coverage=claim_lease_coverage,
        governance_plane_claim_lease_coverage_summary_line=claim_lease_coverage_summary_line,
        governance_plane_claim_lease_health=claim_lease_health,
        governance_plane_claim_lease_health_summary_line=claim_lease_health_summary_line,
        governance_plane_claim_lease_renewal_posture=claim_lease_renewal_posture,
        governance_plane_claim_lease_renewal_permitted_now=claim_lease_renewal_permitted_now,
        governance_plane_claim_lease_renewal_summary_line=claim_lease_renewal_summary_line,
        governance_plane_claim_lease_action=claim_lease_action,
        governance_plane_claim_lease_action_summary_line=claim_lease_action_summary_line,
        governance_plane_claim_disposition=claim_disposition,
        governance_plane_claim_disposition_summary_line=claim_disposition_summary_line,
        governance_plane_claim_process_posture=claim_process_posture,
        governance_plane_claim_process_permitted_now=claim_process_permitted_now,
        governance_plane_claim_process_summary_line=claim_process_summary_line,
        governance_plane_claim_operability=claim_operability,
        governance_plane_claim_operability_summary_line=claim_operability_summary_line,
        governance_plane_claim_vector=claim_vector,
        governance_plane_claim_sha256=sha256_text(claim_vector),
    )



def build_governance_review_sort_key(
    *,
    review_due_by_utc: datetime | None,
    priority_score: int,
    queue_key: OracleGovernanceQueueKey,
) -> str:
    due_component = review_due_by_utc.isoformat() if review_due_by_utc else '9999-12-31T23:59:59+00:00'
    inverted_priority = max(0, 100 - int(priority_score))
    return f"{due_component}::{inverted_priority:03d}::{queue_key}"
