from __future__ import annotations

from typing import Iterable

from strategy_validator.contracts.oracle_types import (
    OracleConstitutionalTrustStatus,
    OracleEscalationLane,
    OraclePropagationPosture,
    OracleReliancePosture,
    OracleSupportChainRemediationStatus,
)


def _unique(items: Iterable[str]) -> list[str]:
    out: list[str] = []
    for item in items:
        value = str(item).strip()
        if value and value not in out:
            out.append(value)
    return out


def assess_operator_propagation_posture(
    *,
    operator_reliance_posture: OracleReliancePosture,
    operator_escalation_lane: OracleEscalationLane,
    support_chain_trust_status: OracleConstitutionalTrustStatus,
    support_chain_remediation_status: OracleSupportChainRemediationStatus,
) -> tuple[OraclePropagationPosture, str, list[str]]:
    reasons: list[str] = []
    posture: OraclePropagationPosture = 'DOWNSTREAM_PROPAGATION_ALLOWED'

    if (
        operator_reliance_posture == 'REPAIR_FIRST'
        or operator_escalation_lane == 'CONSTITUTIONAL_REPAIR_ESCALATION'
        or support_chain_trust_status == 'UNTRUSTED'
        or support_chain_remediation_status == 'REMEDIATION_REQUIRED'
    ):
        posture = 'LOCAL_ONLY_DO_NOT_PROPAGATE'
    elif (
        operator_reliance_posture == 'CAUTIOUS_ADVISORY_ONLY'
        or operator_escalation_lane == 'HEIGHTENED_OPERATOR_ESCALATION'
        or support_chain_trust_status == 'TRUST_RESTRICTED'
        or support_chain_remediation_status == 'REMEDIATION_RECOMMENDED'
    ):
        posture = 'REVIEW_ONLY_PROPAGATION'

    if operator_reliance_posture == 'REPAIR_FIRST':
        reasons.append('operator reliance posture is repair-first')
    elif operator_reliance_posture == 'CAUTIOUS_ADVISORY_ONLY':
        reasons.append('operator reliance posture is cautious advisory-only')

    if operator_escalation_lane == 'CONSTITUTIONAL_REPAIR_ESCALATION':
        reasons.append('operator escalation lane is constitutional repair escalation')
    elif operator_escalation_lane == 'HEIGHTENED_OPERATOR_ESCALATION':
        reasons.append('operator escalation lane is heightened operator escalation')

    if support_chain_trust_status == 'UNTRUSTED':
        reasons.append('support-chain trust is untrusted')
    elif support_chain_trust_status == 'TRUST_RESTRICTED':
        reasons.append('support-chain trust is restricted')

    if support_chain_remediation_status == 'REMEDIATION_REQUIRED':
        reasons.append('support-chain remediation is required')
    elif support_chain_remediation_status == 'REMEDIATION_RECOMMENDED':
        reasons.append('support-chain remediation is recommended')

    reasons = _unique(reasons)
    if posture == 'DOWNSTREAM_PROPAGATION_ALLOWED':
        reasons.append('this strategist surface may be propagated downstream within normal advisory provenance controls')

    summary = {
        'DOWNSTREAM_PROPAGATION_ALLOWED': 'Propagation posture allows downstream propagation: normal advisory circulation is acceptable with provenance retained.',
        'REVIEW_ONLY_PROPAGATION': 'Propagation posture is review-only: do not propagate downstream without explicit heightened review and provenance retention.',
        'LOCAL_ONLY_DO_NOT_PROPAGATE': 'Propagation posture is local-only: do not propagate this strategist surface downstream until the support chain is repaired or refreshed.',
    }[posture]
    return posture, summary, reasons
