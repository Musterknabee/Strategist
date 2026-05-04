from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.materialization import write_json_markdown_artifacts

from strategy_validator.control_plane.operator_decision_execution import (
    OracleOperatorDecisionExecution,
    build_operator_decision_execution_request,
    materialize_operator_decision_execution,
)
from strategy_validator.control_plane.operator_workboard_actions import (
    OracleOperatorWorkboardActionContract,
    materialize_operator_workboard_action_contract,
)


@dataclass(frozen=True)
class OracleOperatorEscalationRoutingRequest:
    routing_root: Path
    board_label: str = 'default'


@dataclass(frozen=True)
class OracleOperatorEscalationRoutingItem:
    routing_key: str
    action_contract_key: str
    work_item_key: str
    execution_key: str
    escalation_required: bool
    escalation_lane: str
    escalation_class: str
    routing_destination: str
    remediation_obligation: str
    policy_reason_code: str
    routing_status: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorEscalationRouting:
    schema_version: str
    board_label: str
    routing_root: str
    total_route_count: int
    escalation_route_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorEscalationRoutingItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'routing_root': self.routing_root,
            'total_route_count': self.total_route_count,
            'escalation_route_count': self.escalation_route_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_escalation_routing_request(**kwargs: Any) -> OracleOperatorEscalationRoutingRequest:
    kwargs['routing_root'] = Path(kwargs['routing_root']).resolve()
    return OracleOperatorEscalationRoutingRequest(**kwargs)


def _route_for(contract, execution) -> OracleOperatorEscalationRoutingItem:
    escalation_required = execution.execution_status == 'EXECUTION_ESCALATED'
    if not escalation_required:
        return OracleOperatorEscalationRoutingItem(
            routing_key=f'route:{contract.action_contract_key}',
            action_contract_key=contract.action_contract_key,
            work_item_key=contract.work_item_key,
            execution_key=execution.execution_key,
            escalation_required=False,
            escalation_lane='STANDARD_OPERATOR_FLOW',
            escalation_class='NO_ESCALATION',
            routing_destination=contract.review_target,
            remediation_obligation='none',
            policy_reason_code='DIRECT_EXECUTION_PERMITTED',
            routing_status='ROUTE_NOT_REQUIRED',
        )

    if contract.claim_operability == 'CLAIM_INOPERABLE':
        escalation_class = 'CLAIM_OPERABILITY_ESCALATION'
        reason_code = 'CLAIM_INOPERABLE'
        lane = 'CLAIM_REPAIR_LANE'
        obligation = 'Clear claim operability blockers before re-requesting execution.'
    elif contract.dispatch_posture == 'DISPATCH_BLOCKED':
        escalation_class = 'DISPATCH_BLOCK_ESCALATION'
        reason_code = 'DISPATCH_BLOCKED'
        lane = 'DISPATCH_REVIEW_LANE'
        obligation = 'Resolve dispatch blockers or obtain explicit override before execution.'
    else:
        escalation_class = 'POLICY_REVIEW_ESCALATION'
        reason_code = execution.policy_decision
        lane = 'OPERATOR_SUPERVISOR_LANE'
        obligation = 'Supervisor review is required before continuing this work item.'

    return OracleOperatorEscalationRoutingItem(
        routing_key=f'route:{contract.action_contract_key}',
        action_contract_key=contract.action_contract_key,
        work_item_key=contract.work_item_key,
        execution_key=execution.execution_key,
        escalation_required=True,
        escalation_lane=lane,
        escalation_class=escalation_class,
        routing_destination=f'{contract.review_target}:{lane.lower()}',
        remediation_obligation=obligation,
        policy_reason_code=reason_code,
        routing_status='ROUTED_FOR_ESCALATION',
    )


def materialize_operator_escalation_routing(
    request: OracleOperatorEscalationRoutingRequest,
    *,
    decision_execution: OracleOperatorDecisionExecution | None = None,
    action_contract: OracleOperatorWorkboardActionContract | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorEscalationRouting:
    if action_contract is None:
        action_contract = materialize_operator_workboard_action_contract(
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    if decision_execution is None:
        decision_execution = materialize_operator_decision_execution(
            build_operator_decision_execution_request(
                execution_root=request.routing_root / 'decision_execution',
                board_label=action_contract.board_label,
                desired_transition='EXECUTED',
            ),
            action_contract=action_contract,
        )

    execution_by_contract = {item.action_contract_key: item for item in decision_execution.items}
    items = tuple(_route_for(contract, execution_by_contract[contract.action_contract_key]) for contract in action_contract.items)

    request.routing_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.routing_root / 'ORACLE_OPERATOR_ESCALATION_ROUTING.json'
    markdown_output_path = request.routing_root / 'ORACLE_OPERATOR_ESCALATION_ROUTING.md'
    report = OracleOperatorEscalationRouting(
        schema_version='oracle_operator_escalation_routing/v1',
        board_label=action_contract.board_label,
        routing_root=str(request.routing_root),
        total_route_count=len(items),
        escalation_route_count=len([item for item in items if item.escalation_required]),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    write_json_markdown_artifacts(
        summary_output_path=summary_output_path,
        markdown_output_path=markdown_output_path,
        payload=report.to_payload(),
        markdown=[
            '## Operator Escalation Routing',
            f"- Board label: `{report.board_label}`",
            f"- Escalation routes: `{report.escalation_route_count}` / `{report.total_route_count}`",
            *[f"- {item.work_item_key}: {item.routing_status} via {item.escalation_lane} -> {item.routing_destination}" for item in report.items],
            '',
        ],
    )
    return report


__all__ = [
    'OracleOperatorEscalationRouting',
    'OracleOperatorEscalationRoutingItem',
    'OracleOperatorEscalationRoutingRequest',
    'build_operator_escalation_routing_request',
    'materialize_operator_escalation_routing',
]
