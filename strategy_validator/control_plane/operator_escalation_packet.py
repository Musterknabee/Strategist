from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_decision_execution import (
    OracleOperatorDecisionExecution,
    build_operator_decision_execution_request,
    materialize_operator_decision_execution,
)
from strategy_validator.control_plane.operator_escalation_routing import (
    OracleOperatorEscalationRouting,
    build_operator_escalation_routing_request,
    materialize_operator_escalation_routing,
)
from strategy_validator.control_plane.operator_workboard_actions import (
    OracleOperatorWorkboardActionContract,
    materialize_operator_workboard_action_contract,
)


@dataclass(frozen=True)
class OracleOperatorEscalationPacketRequest:
    packet_root: Path
    board_label: str = 'default'


@dataclass(frozen=True)
class OracleOperatorEscalationPacketItem:
    packet_key: str
    routing_key: str
    execution_key: str
    action_contract_key: str
    work_item_key: str
    escalation_lane: str
    escalation_class: str
    routing_destination: str
    review_target: str
    priority_band: str
    policy_reason_code: str
    remediation_obligation: str
    review_checklist: tuple[str, ...]
    packet_status: str

    def to_payload(self) -> dict[str, Any]:
        return {
            'packet_key': self.packet_key,
            'routing_key': self.routing_key,
            'execution_key': self.execution_key,
            'action_contract_key': self.action_contract_key,
            'work_item_key': self.work_item_key,
            'escalation_lane': self.escalation_lane,
            'escalation_class': self.escalation_class,
            'routing_destination': self.routing_destination,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'policy_reason_code': self.policy_reason_code,
            'remediation_obligation': self.remediation_obligation,
            'review_checklist': list(self.review_checklist),
            'packet_status': self.packet_status,
        }


@dataclass(frozen=True)
class OracleOperatorEscalationPacket:
    schema_version: str
    board_label: str
    packet_root: str
    total_packet_count: int
    escalated_packet_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorEscalationPacketItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'packet_root': self.packet_root,
            'total_packet_count': self.total_packet_count,
            'escalated_packet_count': self.escalated_packet_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_escalation_packet_request(**kwargs: Any) -> OracleOperatorEscalationPacketRequest:
    kwargs['packet_root'] = Path(kwargs['packet_root']).resolve()
    return OracleOperatorEscalationPacketRequest(**kwargs)


def _build_review_checklist(*, reason_code: str, lane: str, obligation: str) -> tuple[str, ...]:
    steps = [
        f'Confirm escalation lane `{lane}` and destination ownership before reassignment.',
        f'Validate policy reason `{reason_code}` against the current operator transition policy.',
        obligation,
    ]
    if lane == 'CLAIM_REPAIR_LANE':
        steps.append('Repair claim operability blockers and re-run execution readiness before release.')
    elif lane == 'DISPATCH_REVIEW_LANE':
        steps.append('Resolve dispatch blockers or capture an explicit override memo before release.')
    elif lane == 'OPERATOR_SUPERVISOR_LANE':
        steps.append('Record supervisor decision and bounded next action before returning to the operator lane.')
    return tuple(steps)


def materialize_operator_escalation_packet(
    request: OracleOperatorEscalationPacketRequest,
    *,
    escalation_routing: OracleOperatorEscalationRouting | None = None,
    decision_execution: OracleOperatorDecisionExecution | None = None,
    action_contract: OracleOperatorWorkboardActionContract | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorEscalationPacket:
    if action_contract is None:
        action_contract = materialize_operator_workboard_action_contract(
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    if decision_execution is None:
        decision_execution = materialize_operator_decision_execution(
            build_operator_decision_execution_request(
                execution_root=request.packet_root / 'decision_execution',
                board_label=action_contract.board_label,
                desired_transition='EXECUTED',
            ),
            action_contract=action_contract,
        )
    if escalation_routing is None:
        escalation_routing = materialize_operator_escalation_routing(
            build_operator_escalation_routing_request(
                routing_root=request.packet_root / 'escalation_routing',
                board_label=action_contract.board_label,
            ),
            decision_execution=decision_execution,
            action_contract=action_contract,
        )

    contracts_by_key = {item.action_contract_key: item for item in action_contract.items}
    executions_by_key = {item.action_contract_key: item for item in decision_execution.items}
    items: list[OracleOperatorEscalationPacketItem] = []
    for route in escalation_routing.items:
        if not route.escalation_required:
            continue
        contract = contracts_by_key[route.action_contract_key]
        execution = executions_by_key[route.action_contract_key]
        checklist = _build_review_checklist(
            reason_code=route.policy_reason_code,
            lane=route.escalation_lane,
            obligation=route.remediation_obligation,
        )
        items.append(
            OracleOperatorEscalationPacketItem(
                packet_key=f'packet:{route.routing_key}',
                routing_key=route.routing_key,
                execution_key=execution.execution_key,
                action_contract_key=contract.action_contract_key,
                work_item_key=contract.work_item_key,
                escalation_lane=route.escalation_lane,
                escalation_class=route.escalation_class,
                routing_destination=route.routing_destination,
                review_target=contract.review_target,
                priority_band=contract.priority_band,
                policy_reason_code=route.policy_reason_code,
                remediation_obligation=route.remediation_obligation,
                review_checklist=checklist,
                packet_status='SUPERVISOR_REVIEW_REQUIRED',
            )
        )

    request.packet_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.packet_root / 'ORACLE_OPERATOR_ESCALATION_PACKET.json'
    markdown_output_path = request.packet_root / 'ORACLE_OPERATOR_ESCALATION_PACKET.md'
    report = OracleOperatorEscalationPacket(
        schema_version='oracle_operator_escalation_packet/v1',
        board_label=action_contract.board_label,
        packet_root=str(request.packet_root),
        total_packet_count=len(items),
        escalated_packet_count=len(items),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=tuple(items),
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + "\n", encoding="utf-8")
    markdown_output_path.write_text(
        "\n".join([
            '## Operator Escalation Packet',
            f"- Board label: `{report.board_label}`",
            f"- Escalation packets: `{report.escalated_packet_count}`",
            *[
                f"- {item.work_item_key}: {item.escalation_class} via {item.escalation_lane} -> {item.routing_destination}"
                for item in report.items
            ],
            '',
        ]),
        encoding='utf-8',
    )
    return report


__all__ = [
    'OracleOperatorEscalationPacket',
    'OracleOperatorEscalationPacketItem',
    'OracleOperatorEscalationPacketRequest',
    'build_operator_escalation_packet_request',
    'materialize_operator_escalation_packet',
]
