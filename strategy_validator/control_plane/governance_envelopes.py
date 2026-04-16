from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

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


@dataclass(frozen=True)
class OracleGovernanceReviewEnvelope:
    governance_plane_review_due_by_utc: datetime
    governance_plane_review_sort_key: str
    governance_plane_review_envelope_vector: str
    governance_plane_review_envelope_sha256: str


@dataclass(frozen=True)
class OracleGovernanceRoutingEnvelope:
    governance_plane_routing_summary_line: str
    governance_plane_routing_vector: str
    governance_plane_routing_sha256: str


@dataclass(frozen=True)
class OracleGovernanceDispatchEnvelope:
    governance_plane_dispatch_posture: OracleGovernanceDispatchPosture
    governance_plane_dispatch_permitted: bool
    governance_plane_dispatch_summary_line: str
    governance_plane_dispatch_reasons: list[str]
    governance_plane_dispatch_timeliness: OracleGovernanceDispatchTimeliness
    governance_plane_dispatch_claim_permitted_now: bool
    governance_plane_dispatch_timeliness_summary_line: str
    governance_plane_dispatch_claim_urgency: OracleGovernanceDispatchClaimUrgency
    governance_plane_dispatch_claim_score: int
    governance_plane_dispatch_claim_summary_line: str
    governance_plane_dispatch_vector: str
    governance_plane_dispatch_sha256: str
    governance_plane_dispatch_claim_key: str


@dataclass(frozen=True)
class OracleGovernanceClaimEnvelope:
    governance_plane_claim_summary_line: str
    governance_plane_claim_queue_key: OracleGovernanceQueueKey
    governance_plane_claim_review_target: OracleGovernanceReviewTarget
    governance_plane_claim_priority_band: OracleGovernancePriorityBand
    governance_plane_claim_review_due_by_utc: datetime
    governance_plane_claim_review_sort_key: str
    governance_plane_claim_route_sha256: str
    governance_plane_claim_review_envelope_sha256: str
    governance_plane_claim_routing_envelope_sha256: str
    governance_plane_claim_dispatch_claim_key: str
    governance_plane_claim_dispatch_sha256: str
    governance_plane_claim_codes: list[OracleGovernanceClaimCode]
    governance_plane_claim_primary_code: OracleGovernanceClaimCode | None
    governance_plane_claim_action_items: list[OracleGovernanceClaimActionItem]
    governance_plane_claim_primary_action_text: str
    governance_plane_claim_worker_lane: OracleGovernanceClaimWorkerLane
    governance_plane_claim_worker_summary_line: str
    governance_plane_claim_worker_sort_key: str
    governance_plane_claim_lease_key: str
    governance_plane_claim_lease_mode: OracleGovernanceClaimLeaseMode
    governance_plane_claim_lease_ttl_seconds: int
    governance_plane_claim_lease_expires_at_utc: datetime | None
    governance_plane_claim_lease_active_now: bool
    governance_plane_claim_lease_summary_line: str
    governance_plane_claim_lease_coverage: OracleGovernanceClaimLeaseCoverage
    governance_plane_claim_lease_coverage_summary_line: str
    governance_plane_claim_lease_health: OracleGovernanceClaimLeaseHealth
    governance_plane_claim_lease_health_summary_line: str
    governance_plane_claim_lease_renewal_posture: OracleGovernanceClaimLeaseRenewalPosture
    governance_plane_claim_lease_renewal_permitted_now: bool
    governance_plane_claim_lease_renewal_summary_line: str
    governance_plane_claim_lease_action: OracleGovernanceClaimLeaseAction
    governance_plane_claim_lease_action_summary_line: str
    governance_plane_claim_disposition: OracleGovernanceClaimDisposition
    governance_plane_claim_disposition_summary_line: str
    governance_plane_claim_process_posture: OracleGovernanceClaimProcessPosture
    governance_plane_claim_process_permitted_now: bool
    governance_plane_claim_process_summary_line: str
    governance_plane_claim_operability: OracleGovernanceClaimOperability
    governance_plane_claim_operability_summary_line: str
    governance_plane_claim_vector: str
    governance_plane_claim_sha256: str


def unique_text(items: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = str(item).strip()
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
