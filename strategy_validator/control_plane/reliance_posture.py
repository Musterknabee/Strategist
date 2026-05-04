from __future__ import annotations

from typing import Iterable

from strategy_validator.contracts.oracle_types import (
    OracleConstitutionalTrustStatus,
    OracleOperatorReadiness,
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


def assess_operator_reliance_posture(
    *,
    operator_readiness: OracleOperatorReadiness,
    support_chain_trust_status: OracleConstitutionalTrustStatus,
    support_chain_remediation_status: OracleSupportChainRemediationStatus,
) -> tuple[OracleReliancePosture, str, list[str]]:
    reasons: list[str] = []
    posture: OracleReliancePosture = 'ROUTINE_ADVISORY'

    if (
        operator_readiness == 'HOLD_FOR_REFRESH'
        or support_chain_trust_status == 'UNTRUSTED'
        or support_chain_remediation_status == 'REMEDIATION_REQUIRED'
    ):
        posture = 'REPAIR_FIRST'
    elif (
        operator_readiness == 'REVIEW_WITH_CAUTION'
        or support_chain_trust_status == 'TRUST_RESTRICTED'
        or support_chain_remediation_status == 'REMEDIATION_RECOMMENDED'
    ):
        posture = 'CAUTIOUS_ADVISORY_ONLY'

    if operator_readiness == 'HOLD_FOR_REFRESH':
        reasons.append('operator readiness is blocked pending refresh or repair')
    elif operator_readiness == 'REVIEW_WITH_CAUTION':
        reasons.append('operator readiness requires explicit review friction')

    if support_chain_trust_status == 'UNTRUSTED':
        reasons.append('support-chain trust is untrusted')
    elif support_chain_trust_status == 'TRUST_RESTRICTED':
        reasons.append('support-chain trust is restricted')

    if support_chain_remediation_status == 'REMEDIATION_REQUIRED':
        reasons.append('support-chain remediation is required before increasing reliance')
    elif support_chain_remediation_status == 'REMEDIATION_RECOMMENDED':
        reasons.append('support-chain remediation is recommended before increasing reliance')

    reasons = _unique(reasons)
    if posture == 'ROUTINE_ADVISORY':
        reasons.append('this strategist surface is fit for routine advisory reliance within non-execution boundaries')

    summary = {
        'ROUTINE_ADVISORY': 'Reliance posture is routine advisory: this strategist surface is suitable for normal non-execution use.',
        'CAUTIOUS_ADVISORY_ONLY': 'Reliance posture is cautious advisory-only: use this strategist surface with explicit review friction and provenance discipline.',
        'REPAIR_FIRST': 'Reliance posture is repair-first: refresh or repair the support chain before relying on this strategist surface.',
    }[posture]
    return posture, summary, reasons
