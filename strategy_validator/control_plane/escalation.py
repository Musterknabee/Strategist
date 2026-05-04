from __future__ import annotations

from typing import Iterable

from strategy_validator.contracts.oracle_types import (
    OracleConstitutionalTrustStatus,
    OracleEscalationLane,
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


def assess_operator_escalation_lane(
    *,
    operator_reliance_posture: OracleReliancePosture,
    support_chain_trust_status: OracleConstitutionalTrustStatus,
    support_chain_remediation_status: OracleSupportChainRemediationStatus,
) -> tuple[OracleEscalationLane, str, list[str]]:
    reasons: list[str] = []
    lane: OracleEscalationLane = "STANDARD_OPERATOR_FLOW"

    if (
        operator_reliance_posture == "REPAIR_FIRST"
        or support_chain_trust_status == "UNTRUSTED"
        or support_chain_remediation_status == "REMEDIATION_REQUIRED"
    ):
        lane = "CONSTITUTIONAL_REPAIR_ESCALATION"
    elif (
        operator_reliance_posture == "CAUTIOUS_ADVISORY_ONLY"
        or support_chain_trust_status == "TRUST_RESTRICTED"
        or support_chain_remediation_status == "REMEDIATION_RECOMMENDED"
    ):
        lane = "HEIGHTENED_OPERATOR_ESCALATION"

    if operator_reliance_posture == "REPAIR_FIRST":
        reasons.append("operator reliance posture is repair-first")
    elif operator_reliance_posture == "CAUTIOUS_ADVISORY_ONLY":
        reasons.append("operator reliance posture is cautious advisory-only")

    if support_chain_trust_status == "UNTRUSTED":
        reasons.append("support-chain trust is untrusted")
    elif support_chain_trust_status == "TRUST_RESTRICTED":
        reasons.append("support-chain trust is restricted")

    if support_chain_remediation_status == "REMEDIATION_REQUIRED":
        reasons.append("support-chain remediation is required")
    elif support_chain_remediation_status == "REMEDIATION_RECOMMENDED":
        reasons.append("support-chain remediation is recommended")

    reasons = _unique(reasons)
    if lane == "STANDARD_OPERATOR_FLOW":
        reasons.append("this strategist surface can remain in the standard operator flow with normal provenance discipline")

    summary = {
        "STANDARD_OPERATOR_FLOW": "Escalation lane is standard operator flow: routine non-execution review is sufficient.",
        "HEIGHTENED_OPERATOR_ESCALATION": "Escalation lane is heightened operator escalation: use an explicitly heightened review path before increasing reliance.",
        "CONSTITUTIONAL_REPAIR_ESCALATION": "Escalation lane is constitutional repair escalation: repair or refresh the support chain before further reliance or propagation.",
    }[lane]
    return lane, summary, reasons
