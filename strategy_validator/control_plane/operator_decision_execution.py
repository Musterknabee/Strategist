from __future__ import annotations
# convergence marker: write_json_markdown_artifacts

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.materialization import (
    write_event_backed_json_markdown_artifacts,
)
from strategy_validator.control_plane.operator_transition_policy import (
    OracleOperatorTransitionPolicy,
    materialize_operator_transition_policy,
)
from strategy_validator.control_plane.operator_workboard_actions import (
    OracleOperatorWorkboardActionContract,
    materialize_operator_workboard_action_contract,
)


@dataclass(frozen=True)
class OracleOperatorDecisionExecutionRequest:
    execution_root: Path
    board_label: str = 'default'
    desired_transition: str = 'EXECUTED'
    actor_label: str = 'operator'
    note: str = ''
    emitted_at_utc: datetime | None = None
    record_event_to_operator_journal: bool = False


@dataclass(frozen=True)
class OracleOperatorDecisionExecutionItem:
    execution_key: str
    action_contract_key: str
    work_item_key: str
    requested_transition: str
    effective_transition: str
    execution_status: str
    transition_allowed: bool
    actor_label: str
    note: str
    emitted_at_utc: str
    policy_decision: str
    rationale: str
    escalation_lane: str
    escalation_class: str
    remediation_obligation: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorDecisionExecution:
    schema_version: str
    board_label: str
    execution_root: str
    execution_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorDecisionExecutionItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'execution_root': self.execution_root,
            'execution_count': self.execution_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_decision_execution_request(**kwargs: Any) -> OracleOperatorDecisionExecutionRequest:
    kwargs['execution_root'] = Path(kwargs['execution_root']).resolve()
    return OracleOperatorDecisionExecutionRequest(**kwargs)


def materialize_operator_decision_execution(
    request: OracleOperatorDecisionExecutionRequest,
    transition_policy: OracleOperatorTransitionPolicy | None = None,
    action_contract: OracleOperatorWorkboardActionContract | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorDecisionExecution:
    if action_contract is None:
        action_contract = materialize_operator_workboard_action_contract(
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    if transition_policy is None:
        transition_policy = materialize_operator_transition_policy(
            action_contract=action_contract,
            board_label=action_contract.board_label,
        )

    emitted = request.emitted_at_utc or datetime.now(UTC).replace(microsecond=0)
    if emitted.tzinfo is None:
        emitted = emitted.replace(tzinfo=UTC)

    policy_by_contract = {item.action_contract_key: item for item in transition_policy.items}
    items: list[OracleOperatorDecisionExecutionItem] = []
    for contract in action_contract.items:
        policy = policy_by_contract[contract.action_contract_key]
        allowed = request.desired_transition in policy.allowed_transitions
        if allowed:
            effective = request.desired_transition
            status = 'EXECUTION_ACCEPTED'
        elif 'ESCALATED' in policy.allowed_transitions:
            effective = 'ESCALATED'
            status = 'EXECUTION_ESCALATED'
        else:
            effective = policy.default_transition
            status = 'EXECUTION_BLOCKED'
        if status == 'EXECUTION_ESCALATED':
            escalation_lane = 'CLAIM_REPAIR_LANE' if contract.claim_operability == 'CLAIM_INOPERABLE' else 'DISPATCH_REVIEW_LANE' if contract.dispatch_posture == 'DISPATCH_BLOCKED' else 'OPERATOR_SUPERVISOR_LANE'
            escalation_class = 'CLAIM_OPERABILITY_ESCALATION' if contract.claim_operability == 'CLAIM_INOPERABLE' else 'DISPATCH_BLOCK_ESCALATION' if contract.dispatch_posture == 'DISPATCH_BLOCKED' else 'POLICY_REVIEW_ESCALATION'
            remediation_obligation = 'Operator escalation review is required before this work item can continue.'
        else:
            escalation_lane = 'STANDARD_OPERATOR_FLOW'
            escalation_class = 'NO_ESCALATION'
            remediation_obligation = 'none'
        items.append(
            OracleOperatorDecisionExecutionItem(
                execution_key=f'execution:{contract.action_contract_key}',
                action_contract_key=contract.action_contract_key,
                work_item_key=contract.work_item_key,
                requested_transition=request.desired_transition,
                effective_transition=effective,
                execution_status=status,
                transition_allowed=allowed,
                actor_label=request.actor_label,
                note=request.note,
                emitted_at_utc=emitted.isoformat(),
                policy_decision=policy.policy_decision,
                rationale=policy.rationale,
                escalation_lane=escalation_lane,
                escalation_class=escalation_class,
                remediation_obligation=remediation_obligation,
            )
        )

    request.execution_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.execution_root / 'ORACLE_OPERATOR_DECISION_EXECUTION.json'
    markdown_output_path = request.execution_root / 'ORACLE_OPERATOR_DECISION_EXECUTION.md'
    report = OracleOperatorDecisionExecution(
        schema_version='oracle_operator_decision_execution/v1',
        board_label=action_contract.board_label,
        execution_root=str(request.execution_root),
        execution_count=len(items),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=tuple(items),
    )
    report_payload = report.to_payload()
    event_output_path = request.execution_root / 'ORACLE_OPERATOR_DECISION_EXECUTION.event.json'
    write_event_backed_json_markdown_artifacts(
        summary_output_path=summary_output_path,
        markdown_output_path=markdown_output_path,
        event_output_path=event_output_path,
        event_type='oracle.operator_decision_execution.materialized',
        producer='strategy_validator.control_plane.operator_decision_execution',
        payload=report_payload,
        actor_id=request.actor_label,
        target={
            'board_label': action_contract.board_label,
            'desired_transition': request.desired_transition,
        },
        idempotency_key=f'{action_contract.board_label}:{request.actor_label}:{request.desired_transition}:{emitted.isoformat()}',
        append_to_operator_journal=request.record_event_to_operator_journal,
        markdown=[
            '## Operator Decision Execution',
            f"- Board label: `{report.board_label}`",
            f"- Execution count: `{report.execution_count}`",
            *[f"- {item.work_item_key}: {item.execution_status} -> {item.effective_transition}" for item in report.items],
            '',
        ],
    )
    return report


__all__ = [
    'OracleOperatorDecisionExecution',
    'OracleOperatorDecisionExecutionItem',
    'OracleOperatorDecisionExecutionRequest',
    'build_operator_decision_execution_request',
    'materialize_operator_decision_execution',
]
