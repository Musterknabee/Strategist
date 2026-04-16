from __future__ import annotations

from strategy_validator.contracts.oracle import (
    OracleAutomationPosture,
    OracleEscalationLane,
    OraclePropagationPosture,
    OracleReliancePosture,
)


def assess_automation_posture(
    *,
    propagation_posture: OraclePropagationPosture,
    operator_escalation_lane: OracleEscalationLane,
    operator_reliance_posture: OracleReliancePosture,
) -> tuple[OracleAutomationPosture, str, list[str]]:
    reasons: list[str] = []

    if (
        propagation_posture == 'LOCAL_ONLY_DO_NOT_PROPAGATE'
        or operator_escalation_lane == 'CONSTITUTIONAL_REPAIR_ESCALATION'
        or operator_reliance_posture == 'REPAIR_FIRST'
    ):
        status: OracleAutomationPosture = 'HUMAN_ONLY_NO_AUTOMATION'
    elif (
        propagation_posture == 'REVIEW_ONLY_PROPAGATION'
        or operator_escalation_lane == 'HEIGHTENED_OPERATOR_ESCALATION'
        or operator_reliance_posture == 'CAUTIOUS_ADVISORY_ONLY'
    ):
        status = 'AUTOMATION_REVIEW_REQUIRED'
    else:
        status = 'AUTOMATION_ELIGIBLE'

    if propagation_posture == 'LOCAL_ONLY_DO_NOT_PROPAGATE':
        reasons.append('Local-only strategist surfaces must not feed automated downstream workflows.')
    elif propagation_posture == 'REVIEW_ONLY_PROPAGATION':
        reasons.append('Review-only propagation requires human review before automation can consume the report.')
    else:
        reasons.append('Downstream propagation is permitted for this strategist surface.')

    if operator_escalation_lane == 'CONSTITUTIONAL_REPAIR_ESCALATION':
        reasons.append('Constitutional repair escalation blocks automated use until repair is complete.')
    elif operator_escalation_lane == 'HEIGHTENED_OPERATOR_ESCALATION':
        reasons.append('Heightened operator escalation requires review before automated advisory workflows consume the report.')
    else:
        reasons.append('Standard operator flow does not add extra automation restrictions.')

    if operator_reliance_posture == 'REPAIR_FIRST':
        reasons.append('Repair-first reliance posture forbids automation until trust issues are repaired.')
    elif operator_reliance_posture == 'CAUTIOUS_ADVISORY_ONLY':
        reasons.append('Cautious advisory-only reliance posture requires review before automation use.')
    else:
        reasons.append('Routine advisory posture is compatible with governed automation.')

    if status == 'HUMAN_ONLY_NO_AUTOMATION':
        summary = 'Human-only posture; keep this strategist surface out of automated advisory workflows.'
    elif status == 'AUTOMATION_REVIEW_REQUIRED':
        summary = 'Automation review required; do not feed this strategist surface into automated advisory workflows until review is completed.'
    else:
        summary = 'Automation eligible; this strategist surface may feed governed automated advisory workflows.'

    return status, summary, reasons
