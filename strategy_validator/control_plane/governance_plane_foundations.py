from __future__ import annotations

import hashlib
from typing import Iterable

from strategy_validator.contracts.oracle_core import (
    OracleGovernanceActionItem,
    OracleGovernanceCode,
    OracleGovernanceQueueKey,
)
from strategy_validator.contracts.oracle_types import (
    OracleConstitutionalTrustStatus,
    OracleGovernanceDimension,
    OracleGovernanceDispatchPosture,
    OracleGovernancePlaneStatus,
    OracleGovernancePrimarySeverity,
    OracleGovernancePriorityBand,
    OracleGovernanceReviewTarget,
    OracleOperatorReadiness,
    OracleSupportChainRemediationStatus,
)


def _unique(items: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = str(item).strip()
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _unique_action_items(items: Iterable[OracleGovernanceActionItem]) -> list[OracleGovernanceActionItem]:
    out: list[OracleGovernanceActionItem] = []
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        key = (item.dimension, item.severity, item.action_text.strip())
        if not key[2] or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _unique_codes(items: Iterable[OracleGovernanceCode]) -> list[OracleGovernanceCode]:
    out: list[OracleGovernanceCode] = []
    seen: set[str] = set()
    for item in items:
        value = str(item).strip()
        if value and value not in seen:
            seen.add(value)
            out.append(item)
    return out


def _join_or_none(items: Iterable[str]) -> str:
    values = _unique(items)
    return ",".join(values) if values else "none"


def _governance_plane_vector(
    *,
    governance_plane_status: OracleGovernancePlaneStatus,
    support_chain_trust_status: OracleConstitutionalTrustStatus,
    support_chain_remediation_status: OracleSupportChainRemediationStatus,
    operator_readiness: OracleOperatorReadiness,
    operator_reliance_posture: str,
    operator_escalation_lane: str,
    propagation_posture: str,
    automation_posture: str,
    blocking_dimensions: list[OracleGovernanceDimension],
    restricted_dimensions: list[OracleGovernanceDimension],
    governance_codes: list[OracleGovernanceCode],
    primary_dimension: OracleGovernanceDimension | None,
    primary_severity: OracleGovernancePrimarySeverity,
    priority_band: OracleGovernancePriorityBand,
    review_target: OracleGovernanceReviewTarget,
    queue_key: OracleGovernanceQueueKey,
) -> str:
    return "|".join([
        f"status={governance_plane_status}",
        f"trust={support_chain_trust_status}",
        f"remediation={support_chain_remediation_status}",
        f"readiness={operator_readiness}",
        f"reliance={operator_reliance_posture}",
        f"escalation={operator_escalation_lane}",
        f"propagation={propagation_posture}",
        f"automation={automation_posture}",
        f"blocking={_join_or_none(blocking_dimensions)}",
        f"restricted={_join_or_none(restricted_dimensions)}",
        f"codes={_join_or_none(governance_codes)}",
        f"primary_dimension={primary_dimension or 'none'}",
        f"primary_severity={primary_severity}",
        f"priority={priority_band}",
        f"review_target={review_target}",
        f"queue_key={queue_key}",
    ])


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _primary_governance_driver(
    *,
    status: OracleGovernancePlaneStatus,
    action_items: list[OracleGovernanceActionItem],
    blocking_dimensions: list[OracleGovernanceDimension],
    restricted_dimensions: list[OracleGovernanceDimension],
) -> tuple[OracleGovernanceDimension | None, OracleGovernancePrimarySeverity, str]:
    if status == "GOVERNANCE_READY":
        return None, "READY", "Governance plane is ready for routine governed use."
    for item in action_items:
        if item.severity == "BLOCKING":
            return item.dimension, "BLOCKING", item.action_text
    if blocking_dimensions:
        return blocking_dimensions[0], "BLOCKING", f"Address the blocking {blocking_dimensions[0].lower()} governance constraint first."
    for item in action_items:
        if item.severity == "RESTRICTING":
            return item.dimension, "RESTRICTING", item.action_text
    if restricted_dimensions:
        return restricted_dimensions[0], "RESTRICTING", f"Address the restricting {restricted_dimensions[0].lower()} governance constraint first."
    return None, "READY", "Governance plane is ready for routine governed use."


def _governance_priority(
    *,
    status: OracleGovernancePlaneStatus,
    primary_severity: OracleGovernancePrimarySeverity,
    blocking_dimensions: list[OracleGovernanceDimension],
    restricted_dimensions: list[OracleGovernanceDimension],
    governance_codes: list[OracleGovernanceCode],
) -> tuple[OracleGovernancePriorityBand, int, str]:
    if status == "GOVERNANCE_BLOCKED" or primary_severity == "BLOCKING":
        score = min(100, 90 + (len(blocking_dimensions) * 2) + min(len(governance_codes), 4))
        band: OracleGovernancePriorityBand = "CRITICAL_PRIORITY"
        return band, score, f"Governance queue priority: {band}; score={score}; blocking governance repair is required before broader use."
    if status == "GOVERNANCE_RESTRICTED" or primary_severity == "RESTRICTING":
        score = min(89, 55 + (len(restricted_dimensions) * 3) + min(len(governance_codes), 6))
        band = "ELEVATED_PRIORITY"
        return band, score, f"Governance queue priority: {band}; score={score}; restricted surfaces should be triaged ahead of routine governed flows."
    band = "ROUTINE_PRIORITY"
    score = 10
    return band, score, f"Governance queue priority: {band}; score={score}; routine governed processing is acceptable."


def _governance_queue_key(
    *,
    review_target: OracleGovernanceReviewTarget,
    priority_band: OracleGovernancePriorityBand,
    primary_dimension: OracleGovernanceDimension | None,
    primary_severity: OracleGovernancePrimarySeverity,
) -> OracleGovernanceQueueKey:
    dimension = primary_dimension or "READY"
    return f"{review_target}::{priority_band}::{dimension}::{primary_severity}"


def _governance_route_vector(
    *,
    priority_band: OracleGovernancePriorityBand,
    priority_score: int,
    review_target: OracleGovernanceReviewTarget,
    review_sla_hours: int,
    queue_key: OracleGovernanceQueueKey,
    primary_dimension: OracleGovernanceDimension | None,
    primary_severity: OracleGovernancePrimarySeverity,
) -> str:
    return "|".join([
        f"priority={priority_band}",
        f"priority_score={priority_score}",
        f"review_target={review_target}",
        f"review_sla_hours={review_sla_hours}",
        f"queue_key={queue_key}",
        f"primary_dimension={primary_dimension or 'none'}",
        f"primary_severity={primary_severity}",
    ])


def _governance_review_target(
    *,
    status: OracleGovernancePlaneStatus,
    priority_band: OracleGovernancePriorityBand,
) -> tuple[OracleGovernanceReviewTarget, int, str]:
    if status == "GOVERNANCE_BLOCKED" or priority_band == "CRITICAL_PRIORITY":
        target: OracleGovernanceReviewTarget = "CONSTITUTIONAL_REPAIR_QUEUE"
        return target, 4, f"Governance review target: {target}; sla_hours=4; immediate constitutional repair review is required."
    if status == "GOVERNANCE_RESTRICTED" or priority_band == "ELEVATED_PRIORITY":
        target = "HEIGHTENED_REVIEW_QUEUE"
        return target, 24, f"Governance review target: {target}; sla_hours=24; heightened governed review is required before broader use."
    target = "ROUTINE_REVIEW_QUEUE"
    return target, 72, f"Governance review target: {target}; sla_hours=72; routine governed review is acceptable."


def _governance_dispatch_posture(
    *,
    governance_status: OracleGovernancePlaneStatus,
    review_target: OracleGovernanceReviewTarget,
    primary_dimension: OracleGovernanceDimension | None,
    primary_severity: OracleGovernancePrimarySeverity,
) -> tuple[OracleGovernanceDispatchPosture, bool, str, list[str]]:
    reasons: list[str] = []
    if governance_status == "GOVERNANCE_BLOCKED":
        posture: OracleGovernanceDispatchPosture = "DISPATCH_BLOCKED"
        reasons.append("governance plane remains blocked and cannot dispatch routine work")
        if primary_dimension:
            reasons.append(f"primary blocking dimension is {primary_dimension.lower()}")
        return posture, False, f"Governance dispatch posture: {posture}; governed dispatch is blocked until {primary_severity.lower()} issues are cleared.", reasons
    if governance_status == "GOVERNANCE_RESTRICTED":
        posture = "DISPATCH_REVIEW_ONLY"
        reasons.append(f"review target is {review_target.lower()}")
        return posture, True, f"Governance dispatch posture: {posture}; governed dispatch is available only through review-controlled handling.", reasons
    posture = "DISPATCH_ALLOWED"
    reasons.append(f"review target is {review_target.lower()}")
    return posture, True, f"Governance dispatch posture: {posture}; governed dispatch is available for operator handling.", reasons


__all__ = [
    "_governance_dispatch_posture",
    "_governance_plane_vector",
    "_governance_priority",
    "_governance_queue_key",
    "_governance_review_target",
    "_governance_route_vector",
    "_join_or_none",
    "_primary_governance_driver",
    "_sha256_text",
    "_unique",
    "_unique_action_items",
    "_unique_codes",
]
