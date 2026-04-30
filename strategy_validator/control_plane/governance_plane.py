from __future__ import annotations

from dataclasses import dataclass

from strategy_validator.contracts.oracle_core import (
    OracleGovernanceActionItem,
    OracleGovernanceCode,
    OracleGovernanceQueueKey,
)
from strategy_validator.contracts.oracle_types import (
    OracleConstitutionalTrustStatus,
    OracleGovernanceDimension,
    OracleGovernanceDispatchClaimUrgency,
    OracleGovernanceDispatchPosture,
    OracleGovernanceDispatchTimeliness,
    OracleGovernancePlaneStatus,
    OracleGovernancePrimarySeverity,
    OracleGovernancePriorityBand,
    OracleGovernanceReviewTarget,
    OracleOperatorReadiness,
    OracleSupportChainRemediationStatus,
)
from strategy_validator.control_plane.control_plane import assess_control_plane
from strategy_validator.control_plane.governance_plane_foundations import (
    _governance_dispatch_posture,
    _governance_plane_vector,
    _governance_priority,
    _governance_queue_key,
    _governance_review_target,
    _governance_route_vector,
    _primary_governance_driver,
    _sha256_text,
    _unique,
    _unique_action_items,
    _unique_codes,
)
from strategy_validator.control_plane.trust_plane import assess_trust_plane
from strategy_validator.control_plane.workflows import (
    OracleGovernanceClaimEnvelope,
    OracleGovernanceDispatchEnvelope,
    OracleGovernanceReviewEnvelope,
    OracleGovernanceRoutingEnvelope,
    _governance_claim_worker_sort_key,
    build_governance_review_sort_key,
    materialize_governance_claim_envelope,
    materialize_governance_dispatch_envelope,
    materialize_governance_review_envelope,
    materialize_governance_routing_envelope,
)


@dataclass(frozen=True)
class OracleGovernancePlaneAssessment:
    governance_plane_status: OracleGovernancePlaneStatus
    governance_plane_summary_line: str
    governance_plane_reasons: list[str]
    governance_plane_codes: list[OracleGovernanceCode]
    governance_plane_blocking_dimensions: list[OracleGovernanceDimension]
    governance_plane_restricted_dimensions: list[OracleGovernanceDimension]
    governance_plane_primary_dimension: OracleGovernanceDimension | None
    governance_plane_primary_severity: OracleGovernancePrimarySeverity
    governance_plane_primary_action_text: str
    governance_plane_priority_band: OracleGovernancePriorityBand
    governance_plane_priority_score: int
    governance_plane_priority_summary_line: str
    governance_plane_review_target: OracleGovernanceReviewTarget
    governance_plane_review_sla_hours: int
    governance_plane_review_summary_line: str
    governance_plane_review_sort_key: str
    governance_plane_queue_key: OracleGovernanceQueueKey
    governance_plane_route_vector: str
    governance_plane_route_sha256: str
    governance_plane_vector: str
    governance_plane_sha256: str
    trust_plane_summary_line: str
    trust_plane_actions: list[str]
    operator_reliance_posture: str
    operator_reliance_summary_line: str
    operator_reliance_reasons: list[str]
    operator_escalation_lane: str
    operator_escalation_summary_line: str
    operator_escalation_reasons: list[str]
    propagation_posture: str
    propagation_summary_line: str
    propagation_reasons: list[str]
    automation_posture: str
    automation_summary_line: str
    automation_reasons: list[str]
    control_plane_summary_line: str
    control_plane_actions: list[str]
    governance_plane_actions: list[str]
    governance_plane_action_items: list[OracleGovernanceActionItem]
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


def assess_governance_plane(
    *,
    evidence_freshness_status: str,
    evidence_integrity_status: str,
    evidence_coverage_status: str,
    support_verification_status: str,
    support_chain_trust_status: OracleConstitutionalTrustStatus,
    support_chain_remediation_status: OracleSupportChainRemediationStatus,
    support_chain_remediation_actions: list[str] | None = None,
    operator_readiness: OracleOperatorReadiness,
    surface_label: str = 'this strategist surface',
) -> OracleGovernancePlaneAssessment:
    trust_plane = assess_trust_plane(
        evidence_freshness_status=evidence_freshness_status,
        evidence_integrity_status=evidence_integrity_status,
        evidence_coverage_status=evidence_coverage_status,
        support_verification_status=support_verification_status,
        support_chain_trust_status=support_chain_trust_status,
        support_chain_remediation_status=support_chain_remediation_status,
        support_chain_remediation_actions=support_chain_remediation_actions,
        surface_label=surface_label,
    )
    control_plane = assess_control_plane(
        operator_readiness=operator_readiness,
        support_chain_trust_status=support_chain_trust_status,
        support_chain_remediation_status=support_chain_remediation_status,
        surface_label=surface_label,
    )

    reasons: list[str] = []
    codes: list[OracleGovernanceCode] = []
    blocking_dimensions: list[OracleGovernanceDimension] = []
    restricted_dimensions: list[OracleGovernanceDimension] = []
    action_items: list[OracleGovernanceActionItem] = []

    if support_chain_trust_status == 'UNTRUSTED':
        blocking_dimensions.append('SUPPORT_CHAIN_TRUST')
        codes.append('UNTRUSTED_SUPPORT_CHAIN')
        action_items.append(OracleGovernanceActionItem(
            dimension='SUPPORT_CHAIN_TRUST',
            severity='BLOCKING',
            action_text=f'Do not materially rely on {surface_label} until support-chain trust defects are repaired.',
        ))
    elif support_chain_trust_status != 'TRUSTED':
        restricted_dimensions.append('SUPPORT_CHAIN_TRUST')
        codes.append('TRUST_RESTRICTED_SUPPORT_CHAIN')
        action_items.append(OracleGovernanceActionItem(
            dimension='SUPPORT_CHAIN_TRUST',
            severity='RESTRICTING',
            action_text=f'Treat {surface_label} as trust-restricted until support-chain cautions are resolved.',
        ))

    if support_chain_remediation_status == 'REMEDIATION_REQUIRED':
        blocking_dimensions.append('REMEDIATION')
        codes.append('REMEDIATION_REQUIRED')
        reasons.append('support-chain remediation is required before broader reliance or propagation')
        for action in support_chain_remediation_actions or ['Complete the required support-chain remediation work before broader reliance or propagation.']:
            action_items.append(OracleGovernanceActionItem(dimension='REMEDIATION', severity='BLOCKING', action_text=action))
    elif support_chain_remediation_status == 'REMEDIATION_RECOMMENDED':
        restricted_dimensions.append('REMEDIATION')
        codes.append('REMEDIATION_RECOMMENDED')
        reasons.append('support-chain remediation is recommended before expanding reliance')
        for action in support_chain_remediation_actions or ['Complete the recommended support-chain remediation work before expanding reliance.']:
            action_items.append(OracleGovernanceActionItem(dimension='REMEDIATION', severity='RESTRICTING', action_text=action))

    if operator_readiness == 'HOLD_FOR_REFRESH':
        blocking_dimensions.append('READINESS')
        codes.append('READINESS_HOLD')
        reasons.append('operator readiness is currently holding the surface for refresh or repair')
        action_items.append(OracleGovernanceActionItem(
            dimension='READINESS',
            severity='BLOCKING',
            action_text=f'Hold {surface_label} for evidence refresh or repair before broader use.',
        ))
    elif operator_readiness == 'REVIEW_WITH_CAUTION':
        restricted_dimensions.append('READINESS')
        codes.append('READINESS_CAUTION')
        reasons.append('operator readiness is limited to cautious review')
        action_items.append(OracleGovernanceActionItem(
            dimension='READINESS',
            severity='RESTRICTING',
            action_text=f'Keep {surface_label} in cautious operator review until readiness constraints ease.',
        ))

    if control_plane.operator_reliance_posture == 'REPAIR_FIRST':
        blocking_dimensions.append('RELIANCE')
        codes.append('RELIANCE_REPAIR_FIRST')
        action_items.append(OracleGovernanceActionItem(
            dimension='RELIANCE',
            severity='BLOCKING',
            action_text=f'Do not move beyond repair-first reliance on {surface_label} yet.',
        ))
    elif control_plane.operator_reliance_posture != 'ROUTINE_ADVISORY':
        restricted_dimensions.append('RELIANCE')
        codes.append('RELIANCE_CAUTION')
        action_items.append(OracleGovernanceActionItem(
            dimension='RELIANCE',
            severity='RESTRICTING',
            action_text=f'Limit {surface_label} to cautious advisory reliance until restrictions clear.',
        ))

    if control_plane.operator_escalation_lane == 'CONSTITUTIONAL_REPAIR_ESCALATION':
        blocking_dimensions.append('ESCALATION')
        codes.append('ESCALATION_CONSTITUTIONAL_REPAIR')
        action_items.append(OracleGovernanceActionItem(
            dimension='ESCALATION',
            severity='BLOCKING',
            action_text=f'Escalate {surface_label} into constitutional repair review before further reliance or propagation.',
        ))
    elif control_plane.operator_escalation_lane != 'STANDARD_OPERATOR_FLOW':
        restricted_dimensions.append('ESCALATION')
        codes.append('ESCALATION_HEIGHTENED')
        action_items.append(OracleGovernanceActionItem(
            dimension='ESCALATION',
            severity='RESTRICTING',
            action_text=f'Escalate {surface_label} through a heightened operator review lane before increasing reliance.',
        ))

    if control_plane.propagation_posture == 'LOCAL_ONLY_DO_NOT_PROPAGATE':
        blocking_dimensions.append('PROPAGATION')
        codes.append('PROPAGATION_LOCAL_ONLY')
        action_items.append(OracleGovernanceActionItem(
            dimension='PROPAGATION',
            severity='BLOCKING',
            action_text=f'Keep {surface_label} local-only and do not propagate it downstream until repair is complete.',
        ))
    elif control_plane.propagation_posture != 'DOWNSTREAM_PROPAGATION_ALLOWED':
        restricted_dimensions.append('PROPAGATION')
        codes.append('PROPAGATION_REVIEW_ONLY')
        action_items.append(OracleGovernanceActionItem(
            dimension='PROPAGATION',
            severity='RESTRICTING',
            action_text=f'Restrict downstream propagation of {surface_label} until heightened review is completed.',
        ))

    if control_plane.automation_posture == 'HUMAN_ONLY_NO_AUTOMATION':
        blocking_dimensions.append('AUTOMATION')
        codes.append('AUTOMATION_HUMAN_ONLY')
        action_items.append(OracleGovernanceActionItem(
            dimension='AUTOMATION',
            severity='BLOCKING',
            action_text=f'Keep {surface_label} out of automated advisory workflows until repair and operator review are complete.',
        ))
    elif control_plane.automation_posture != 'AUTOMATION_ELIGIBLE':
        restricted_dimensions.append('AUTOMATION')
        codes.append('AUTOMATION_REVIEW_REQUIRED')
        action_items.append(OracleGovernanceActionItem(
            dimension='AUTOMATION',
            severity='RESTRICTING',
            action_text=f'Do not feed {surface_label} into automated advisory workflows until heightened review is completed.',
        ))

    blocking_dimensions = _unique(blocking_dimensions)
    restricted_dimensions = [d for d in _unique(restricted_dimensions) if d not in blocking_dimensions]

    status: OracleGovernancePlaneStatus = 'GOVERNANCE_RESTRICTED'
    if blocking_dimensions:
        status = 'GOVERNANCE_BLOCKED'
        reasons.insert(0, 'support chain is not yet fit for meaningful strategist reliance')
    elif not restricted_dimensions:
        status = 'GOVERNANCE_READY'
        reasons.append('trust and control planes both permit routine governed advisory use')
    else:
        reasons.insert(0, 'trust or control posture still imposes governed restrictions before broader use')

    governance_plane_codes = _unique_codes(codes)
    governance_plane_summary_line = (
        f'Governance plane: status={status}; trust={support_chain_trust_status}; '
        f'reliance={control_plane.operator_reliance_posture}; escalation={control_plane.operator_escalation_lane}; '
        f'propagation={control_plane.propagation_posture}; automation={control_plane.automation_posture}.'
    )
    governance_plane_action_items = _unique_action_items(action_items)
    governance_plane_actions = [item.action_text for item in governance_plane_action_items]
    governance_plane_primary_dimension, governance_plane_primary_severity, governance_plane_primary_action_text = _primary_governance_driver(
        status=status,
        action_items=governance_plane_action_items,
        blocking_dimensions=blocking_dimensions,
        restricted_dimensions=restricted_dimensions,
    )
    governance_plane_priority_band, governance_plane_priority_score, governance_plane_priority_summary_line = _governance_priority(
        status=status,
        primary_severity=governance_plane_primary_severity,
        blocking_dimensions=blocking_dimensions,
        restricted_dimensions=restricted_dimensions,
        governance_codes=governance_plane_codes,
    )
    governance_plane_review_target, governance_plane_review_sla_hours, governance_plane_review_summary_line = _governance_review_target(
        status=status,
        priority_band=governance_plane_priority_band,
    )
    governance_plane_queue_key = _governance_queue_key(
        review_target=governance_plane_review_target,
        priority_band=governance_plane_priority_band,
        primary_dimension=governance_plane_primary_dimension,
        primary_severity=governance_plane_primary_severity,
    )
    governance_plane_review_sort_key = build_governance_review_sort_key(
        review_due_by_utc=None,
        priority_score=governance_plane_priority_score,
        queue_key=governance_plane_queue_key,
    )
    governance_plane_route_vector = _governance_route_vector(
        priority_band=governance_plane_priority_band,
        priority_score=governance_plane_priority_score,
        review_target=governance_plane_review_target,
        review_sla_hours=governance_plane_review_sla_hours,
        queue_key=governance_plane_queue_key,
        primary_dimension=governance_plane_primary_dimension,
        primary_severity=governance_plane_primary_severity,
    )
    governance_plane_route_sha256 = _sha256_text(governance_plane_route_vector)
    governance_plane_dispatch_posture, governance_plane_dispatch_permitted, governance_plane_dispatch_summary_line, governance_plane_dispatch_reasons = _governance_dispatch_posture(
        governance_status=status,
        review_target=governance_plane_review_target,
        primary_dimension=governance_plane_primary_dimension,
        primary_severity=governance_plane_primary_severity,
    )
    governance_plane_vector = _governance_plane_vector(
        governance_plane_status=status,
        support_chain_trust_status=support_chain_trust_status,
        support_chain_remediation_status=support_chain_remediation_status,
        operator_readiness=operator_readiness,
        operator_reliance_posture=control_plane.operator_reliance_posture,
        operator_escalation_lane=control_plane.operator_escalation_lane,
        propagation_posture=control_plane.propagation_posture,
        automation_posture=control_plane.automation_posture,
        blocking_dimensions=blocking_dimensions,
        restricted_dimensions=restricted_dimensions,
        governance_codes=governance_plane_codes,
        primary_dimension=governance_plane_primary_dimension,
        primary_severity=governance_plane_primary_severity,
        priority_band=governance_plane_priority_band,
        review_target=governance_plane_review_target,
        queue_key=governance_plane_queue_key,
    )
    governance_plane_sha256 = _sha256_text(governance_plane_vector)

    return OracleGovernancePlaneAssessment(
        governance_plane_status=status,
        governance_plane_summary_line=governance_plane_summary_line,
        governance_plane_reasons=_unique(reasons),
        governance_plane_codes=governance_plane_codes,
        governance_plane_blocking_dimensions=blocking_dimensions,
        governance_plane_restricted_dimensions=restricted_dimensions,
        governance_plane_primary_dimension=governance_plane_primary_dimension,
        governance_plane_primary_severity=governance_plane_primary_severity,
        governance_plane_primary_action_text=governance_plane_primary_action_text,
        governance_plane_priority_band=governance_plane_priority_band,
        governance_plane_priority_score=governance_plane_priority_score,
        governance_plane_priority_summary_line=governance_plane_priority_summary_line,
        governance_plane_review_target=governance_plane_review_target,
        governance_plane_review_sla_hours=governance_plane_review_sla_hours,
        governance_plane_review_summary_line=governance_plane_review_summary_line,
        governance_plane_review_sort_key=governance_plane_review_sort_key,
        governance_plane_queue_key=governance_plane_queue_key,
        governance_plane_route_vector=governance_plane_route_vector,
        governance_plane_route_sha256=governance_plane_route_sha256,
        governance_plane_vector=governance_plane_vector,
        governance_plane_sha256=governance_plane_sha256,
        trust_plane_summary_line=trust_plane.trust_plane_summary_line,
        trust_plane_actions=trust_plane.trust_plane_actions,
        operator_reliance_posture=control_plane.operator_reliance_posture,
        operator_reliance_summary_line=control_plane.operator_reliance_summary_line,
        operator_reliance_reasons=control_plane.operator_reliance_reasons,
        operator_escalation_lane=control_plane.operator_escalation_lane,
        operator_escalation_summary_line=control_plane.operator_escalation_summary_line,
        operator_escalation_reasons=control_plane.operator_escalation_reasons,
        propagation_posture=control_plane.propagation_posture,
        propagation_summary_line=control_plane.propagation_summary_line,
        propagation_reasons=control_plane.propagation_reasons,
        automation_posture=control_plane.automation_posture,
        automation_summary_line=control_plane.automation_summary_line,
        automation_reasons=control_plane.automation_reasons,
        control_plane_summary_line=control_plane.control_plane_summary_line,
        control_plane_actions=control_plane.control_plane_actions,
        governance_plane_actions=governance_plane_actions,
        governance_plane_action_items=governance_plane_action_items,
        governance_plane_dispatch_posture=governance_plane_dispatch_posture,
        governance_plane_dispatch_permitted=governance_plane_dispatch_permitted,
        governance_plane_dispatch_summary_line=governance_plane_dispatch_summary_line,
        governance_plane_dispatch_reasons=governance_plane_dispatch_reasons,
        governance_plane_dispatch_timeliness=("DISPATCH_ACTIVE" if governance_plane_dispatch_permitted else "DISPATCH_OVERDUE"),
        governance_plane_dispatch_claim_permitted_now=governance_plane_dispatch_permitted,
        governance_plane_dispatch_timeliness_summary_line=(
            "Dispatch timeliness: DISPATCH_ACTIVE; governed claim is currently permissible."
            if governance_plane_dispatch_permitted
            else "Dispatch timeliness: DISPATCH_OVERDUE; claim is not permitted because dispatch itself is not currently permitted."
        ),
        governance_plane_dispatch_claim_urgency=("CLAIM_SOON" if governance_plane_dispatch_permitted else "DO_NOT_CLAIM"),
        governance_plane_dispatch_claim_score=(48 if governance_plane_dispatch_permitted else 0),
        governance_plane_dispatch_claim_summary_line=(
            "Dispatch claim urgency: CLAIM_SOON; routine governed claim is available and should be picked up in normal queue flow."
            if governance_plane_dispatch_permitted
            else "Dispatch claim urgency: DO_NOT_CLAIM; do not claim this handoff until governed dispatch becomes permissible again."
        ),
    )


__all__ = [
    'OracleGovernancePlaneAssessment',
    'OracleGovernanceClaimEnvelope',
    'OracleGovernanceDispatchEnvelope',
    'OracleGovernanceReviewEnvelope',
    'OracleGovernanceRoutingEnvelope',
    '_governance_claim_worker_sort_key',
    'assess_governance_plane',
    'build_governance_review_sort_key',
    'materialize_governance_claim_envelope',
    'materialize_governance_dispatch_envelope',
    'materialize_governance_review_envelope',
    'materialize_governance_routing_envelope',
]
