from __future__ import annotations

from datetime import datetime

from strategy_validator.contracts.oracle_core import (
    OracleGovernanceClaimActionItem,
    OracleGovernanceQueueKey,
)
from strategy_validator.contracts.oracle_types import (
    OracleGovernanceClaimCode,
    OracleGovernancePriorityBand,
    OracleGovernanceReviewTarget,
)
from strategy_validator.control_plane.governance_claim_foundations import (
    _governance_claim_action_items,
    _governance_claim_codes,
    _governance_claim_disposition,
    _governance_claim_lease_action,
    _governance_claim_lease_coverage,
    _governance_claim_lease_health,
    _governance_claim_lease_key,
    _governance_claim_lease_renewal,
    _governance_claim_operability,
    _governance_claim_process_posture,
    _governance_claim_vector,
    _governance_claim_worker_lane,
    _governance_claim_worker_sort_key,
)
from strategy_validator.control_plane.governance_envelopes import (
    OracleGovernanceClaimEnvelope,
    OracleGovernanceDispatchEnvelope,
    sha256_text,
)


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
        f"Governance claim envelope: queue_key={queue_key}; "
        f"review_target={review_target}; "
        f"priority_band={priority_band}; "
        f"due_by_utc={review_due_by_utc.isoformat()}; "
        f"sort_key={review_sort_key}; "
        f"claim_codes={','.join(claim_codes)}; "
        f"claim_primary_code={claim_primary_code or 'none'}; "
        f"claim_primary_action_text={claim_primary_action_text or 'none'}; "
        f"claim_worker_lane={claim_worker_lane}; "
        f"worker_sort_key={claim_worker_sort_key}; "
        f"lease_key={claim_lease_key}; "
        f"lease_mode={claim_lease_mode}; "
        f"lease_ttl_seconds={claim_lease_ttl_seconds}; "
        f"lease_expires_at_utc={(claim_lease_expires_at_utc.isoformat() if claim_lease_expires_at_utc else 'none')}; "
        f"lease_active_now={str(claim_lease_active_now).lower()}; "
        f"lease_coverage={claim_lease_coverage}; "
        f"lease_health={claim_lease_health}; "
        f"lease_renewal_posture={claim_lease_renewal_posture}; "
        f"lease_renewal_permitted_now={str(claim_lease_renewal_permitted_now).lower()}; "
        f"lease_action={claim_lease_action}; "
        f"disposition={claim_disposition}; "
        f"process_posture={claim_process_posture}; "
        f"claim_key={dispatch_envelope.governance_plane_dispatch_claim_key}; "
        f"posture={dispatch_envelope.governance_plane_dispatch_posture}; "
        f"timeliness={dispatch_envelope.governance_plane_dispatch_timeliness}; "
        f"urgency={dispatch_envelope.governance_plane_dispatch_claim_urgency}; "
        f"claim_permitted_now={str(dispatch_envelope.governance_plane_dispatch_claim_permitted_now).lower()}."
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
    due_component = review_due_by_utc.isoformat() if review_due_by_utc else "9999-12-31T23:59:59+00:00"
    inverted_priority = max(0, 100 - int(priority_score))
    return f"{due_component}::{inverted_priority:03d}::{queue_key}"


__all__ = [
    "OracleGovernanceClaimActionItem",
    "OracleGovernanceClaimCode",
    "_governance_claim_worker_sort_key",
    "build_governance_review_sort_key",
    "materialize_governance_claim_envelope",
]
