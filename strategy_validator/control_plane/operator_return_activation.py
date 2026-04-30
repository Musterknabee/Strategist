from __future__ import annotations
# convergence marker: write_json_markdown_artifacts

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.materialization import write_json_markdown_artifacts
from strategy_validator.control_plane.operator_return_authorization_ledger import (
    OracleOperatorReturnAuthorizationLedger,
    build_operator_return_authorization_ledger_request,
    materialize_operator_return_authorization_ledger,
)


@dataclass(frozen=True)
class OracleOperatorReturnActivationRequest:
    activation_root: Path
    board_label: str = 'default'
    activator_label: str = 'return-activator'
    activated_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorReturnActivationItem:
    activation_key: str
    ledger_entry_key: str
    disposition_key: str
    work_item_key: str
    remediation_class: str
    authorization_state: str
    activator_label: str
    activation_state: str
    activation_reason_code: str
    normal_flow_restored: bool
    monitoring_required: bool
    restored_queue_lane: str
    activated_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorReturnActivation:
    schema_version: str
    board_label: str
    activation_root: str
    activator_label: str
    activated_at_utc: str
    item_count: int
    activated_count: int
    denied_count: int
    rework_count: int
    escalated_count: int
    monitoring_required_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorReturnActivationItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'activation_root': self.activation_root,
            'activator_label': self.activator_label,
            'activated_at_utc': self.activated_at_utc,
            'item_count': self.item_count,
            'activated_count': self.activated_count,
            'denied_count': self.denied_count,
            'rework_count': self.rework_count,
            'escalated_count': self.escalated_count,
            'monitoring_required_count': self.monitoring_required_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_return_activation_request(**kwargs: Any) -> OracleOperatorReturnActivationRequest:
    kwargs['activation_root'] = Path(kwargs['activation_root']).resolve()
    return OracleOperatorReturnActivationRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_activation_item(item: Any, request: OracleOperatorReturnActivationRequest, activated_at_utc: datetime) -> OracleOperatorReturnActivationItem:
    activation_state = 'RETURN_REMAINED_BLOCKED'
    reason_code = 'AUTHORIZATION_NOT_GRANTED'
    normal_flow_restored = False
    monitoring_required = False
    restored_queue_lane = item.next_queue_lane

    if item.authorization_state == 'RETURN_AUTHORIZED' and item.authorized_return:
        activation_state = 'RETURN_ACTIVATED_TO_NORMAL_FLOW'
        reason_code = 'AUTHORIZED_RETURN_ACTIVATED'
        normal_flow_restored = True
        monitoring_required = item.remediation_class in {'ESCALATION_REMEDIATION', 'HIGH_RISK_REMEDIATION'}
        restored_queue_lane = 'OPERATOR_NORMAL_QUEUE'
    elif item.authorization_state == 'RETURN_REWORK_REQUIRED':
        activation_state = 'RETURN_HELD_FOR_REWORK'
        reason_code = 'REWORK_REQUIRED_BEFORE_NORMALIZATION'
        restored_queue_lane = 'REENTRY_QUEUE'
    elif item.authorization_state == 'RETURN_ESCALATED':
        activation_state = 'RETURN_HELD_FOR_SUPERVISOR'
        reason_code = 'SUPERVISOR_APPROVAL_STILL_REQUIRED'
        restored_queue_lane = 'SUPERVISOR_REVIEW_QUEUE'
    elif item.authorization_state == 'RETURN_DENIED':
        activation_state = 'RETURN_DENIED'
        reason_code = 'RETURN_NOT_CERTIFIED_BY_REVIEW'

    return OracleOperatorReturnActivationItem(
        activation_key=f'return_activation:{item.ledger_entry_key}',
        ledger_entry_key=item.ledger_entry_key,
        disposition_key=item.disposition_key,
        work_item_key=item.work_item_key,
        remediation_class=item.remediation_class,
        authorization_state=item.authorization_state,
        activator_label=request.activator_label,
        activation_state=activation_state,
        activation_reason_code=reason_code,
        normal_flow_restored=normal_flow_restored,
        monitoring_required=monitoring_required,
        restored_queue_lane=restored_queue_lane,
        activated_at_utc=activated_at_utc.isoformat(),
    )


def materialize_operator_return_activation(
    request: OracleOperatorReturnActivationRequest,
    *,
    return_authorization_ledger: OracleOperatorReturnAuthorizationLedger | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorReturnActivation:
    if return_authorization_ledger is None:
        return_authorization_ledger = materialize_operator_return_authorization_ledger(
            build_operator_return_authorization_ledger_request(
                ledger_root=request.activation_root / 'return_authorization_ledger',
                board_label=board_label,
                reviewer_label=request.activator_label,
                authorized_at_utc=request.activated_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )

    activated_at_utc = _normalize(request.activated_at_utc)
    items = tuple(_derive_activation_item(item, request, activated_at_utc) for item in return_authorization_ledger.items)
    request.activation_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.activation_root / 'ORACLE_OPERATOR_RETURN_ACTIVATION.json'
    markdown_output_path = request.activation_root / 'ORACLE_OPERATOR_RETURN_ACTIVATION.md'
    report = OracleOperatorReturnActivation(
        schema_version='oracle_operator_return_activation/v1',
        board_label=return_authorization_ledger.board_label,
        activation_root=str(request.activation_root),
        activator_label=request.activator_label,
        activated_at_utc=activated_at_utc.isoformat(),
        item_count=len(items),
        activated_count=len([item for item in items if item.activation_state == 'RETURN_ACTIVATED_TO_NORMAL_FLOW']),
        denied_count=len([item for item in items if item.activation_state == 'RETURN_DENIED']),
        rework_count=len([item for item in items if item.activation_state == 'RETURN_HELD_FOR_REWORK']),
        escalated_count=len([item for item in items if item.activation_state == 'RETURN_HELD_FOR_SUPERVISOR']),
        monitoring_required_count=len([item for item in items if item.monitoring_required]),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    write_json_markdown_artifacts(
        summary_output_path=summary_output_path,
        markdown_output_path=markdown_output_path,
        payload=report.to_payload(),
        markdown=[
            '## Operator Return Activation',
            f"- Board label: `{report.board_label}`",
            f"- Activator label: `{report.activator_label}`",
            f"- Activated: `{report.activated_count}`",
            f"- Rework held: `{report.rework_count}`",
            f"- Escalated held: `{report.escalated_count}`",
            f"- Monitoring required: `{report.monitoring_required_count}`",
            *[f"- {item.work_item_key}: {item.activation_state} -> {item.restored_queue_lane}" for item in report.items],
            '',
        ],
    )
    return report


__all__ = [
    'OracleOperatorReturnActivation',
    'OracleOperatorReturnActivationItem',
    'OracleOperatorReturnActivationRequest',
    'build_operator_return_activation_request',
    'materialize_operator_return_activation',
]
