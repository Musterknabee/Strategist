from __future__ import annotations

from dataclasses import dataclass
from typing import List

from strategy_validator.contracts.oracle_types import (
    OracleAutomationPosture,
    OracleConstitutionalTrustStatus,
    OracleEscalationLane,
    OracleOperatorReadiness,
    OraclePropagationPosture,
    OracleReliancePosture,
    OracleSupportChainRemediationStatus,
)
from strategy_validator.control_plane.automation_posture import assess_automation_posture
from strategy_validator.control_plane.escalation import assess_operator_escalation_lane
from strategy_validator.control_plane.propagation_posture import assess_operator_propagation_posture
from strategy_validator.control_plane.reliance_posture import assess_operator_reliance_posture


@dataclass(frozen=True)
class OracleControlPlaneAssessment:
    operator_reliance_posture: OracleReliancePosture
    operator_reliance_summary_line: str
    operator_reliance_reasons: List[str]
    operator_escalation_lane: OracleEscalationLane
    operator_escalation_summary_line: str
    operator_escalation_reasons: List[str]
    propagation_posture: OraclePropagationPosture
    propagation_summary_line: str
    propagation_reasons: List[str]
    automation_posture: OracleAutomationPosture
    automation_summary_line: str
    automation_reasons: List[str]
    control_plane_summary_line: str
    control_plane_actions: List[str]


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def assess_control_plane(
    *,
    operator_readiness: OracleOperatorReadiness,
    support_chain_trust_status: OracleConstitutionalTrustStatus,
    support_chain_remediation_status: OracleSupportChainRemediationStatus,
    surface_label: str = 'this strategist surface',
) -> OracleControlPlaneAssessment:
    operator_reliance_posture, operator_reliance_summary_line, operator_reliance_reasons = assess_operator_reliance_posture(
        operator_readiness=operator_readiness,
        support_chain_trust_status=support_chain_trust_status,
        support_chain_remediation_status=support_chain_remediation_status,
    )
    operator_escalation_lane, operator_escalation_summary_line, operator_escalation_reasons = assess_operator_escalation_lane(
        operator_reliance_posture=operator_reliance_posture,
        support_chain_trust_status=support_chain_trust_status,
        support_chain_remediation_status=support_chain_remediation_status,
    )
    propagation_posture, propagation_summary_line, propagation_reasons = assess_operator_propagation_posture(
        operator_reliance_posture=operator_reliance_posture,
        operator_escalation_lane=operator_escalation_lane,
        support_chain_trust_status=support_chain_trust_status,
        support_chain_remediation_status=support_chain_remediation_status,
    )
    automation_posture, automation_summary_line, automation_reasons = assess_automation_posture(
        propagation_posture=propagation_posture,
        operator_escalation_lane=operator_escalation_lane,
        operator_reliance_posture=operator_reliance_posture,
    )

    actions: list[str] = []
    if propagation_posture == 'REVIEW_ONLY_PROPAGATION':
        actions.append(f'Restrict downstream propagation of {surface_label} until a heightened operator review is completed.')
    elif propagation_posture == 'LOCAL_ONLY_DO_NOT_PROPAGATE':
        actions.append(f'Keep {surface_label} local-only and do not propagate it downstream until support-chain repair is complete.')

    if automation_posture == 'AUTOMATION_REVIEW_REQUIRED':
        actions.append(f'Do not feed {surface_label} into automated advisory workflows until heightened operator review is completed.')
    elif automation_posture == 'HUMAN_ONLY_NO_AUTOMATION':
        actions.append(f'Keep {surface_label} out of automated advisory workflows until repair and operator review are complete.')

    if operator_escalation_lane == 'HEIGHTENED_OPERATOR_ESCALATION':
        actions.append(f'Escalate {surface_label} through a heightened operator review lane before increasing reliance.')
    elif operator_escalation_lane == 'CONSTITUTIONAL_REPAIR_ESCALATION':
        actions.append(f'Escalate {surface_label} into constitutional repair review before further reliance or propagation.')

    control_plane_summary_line = (
        f'Control plane: reliance={operator_reliance_posture}; escalation={operator_escalation_lane}; '
        f'propagation={propagation_posture}; automation={automation_posture}.'
    )

    return OracleControlPlaneAssessment(
        operator_reliance_posture=operator_reliance_posture,
        operator_reliance_summary_line=operator_reliance_summary_line,
        operator_reliance_reasons=operator_reliance_reasons,
        operator_escalation_lane=operator_escalation_lane,
        operator_escalation_summary_line=operator_escalation_summary_line,
        operator_escalation_reasons=operator_escalation_reasons,
        propagation_posture=propagation_posture,
        propagation_summary_line=propagation_summary_line,
        propagation_reasons=propagation_reasons,
        automation_posture=automation_posture,
        automation_summary_line=automation_summary_line,
        automation_reasons=automation_reasons,
        control_plane_summary_line=control_plane_summary_line,
        control_plane_actions=_unique(actions),
    )
