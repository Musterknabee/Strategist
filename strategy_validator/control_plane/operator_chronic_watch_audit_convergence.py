from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_normalization_bridge_activation import (
    OracleOperatorNormalizationBridgeActivation,
    build_operator_normalization_bridge_activation_request,
    materialize_operator_normalization_bridge_activation,
)


@dataclass(frozen=True)
class OracleOperatorChronicWatchAuditConvergenceRequest:
    convergence_root: Path
    board_label: str = 'default'
    converger_label: str = 'chronic-watch-audit-converger'
    converged_at_utc: datetime | None = None
    normalization_window_minutes: int = 60


@dataclass(frozen=True)
class OracleOperatorChronicWatchAuditConvergenceItem:
    convergence_key: str
    bridge_activation_key: str
    bridge_key: str
    work_item_key: str
    activation_state: str
    convergence_state: str
    return_monitoring_state: str
    restoration_audit_state: str
    normalization_state: str
    normalized_ready: bool
    reopen_required: bool
    return_monitoring_target: str
    restoration_audit_target: str
    convergence_reason_code: str
    converger_label: str
    converged_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorChronicWatchAuditConvergence:
    schema_version: str
    board_label: str
    convergence_root: str
    converger_label: str
    converged_at_utc: str
    item_count: int
    return_monitoring_converged_count: int
    restoration_audit_converged_count: int
    normalization_confirmed_count: int
    reopen_required_count: int
    blocked_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorChronicWatchAuditConvergenceItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'convergence_root': self.convergence_root,
            'converger_label': self.converger_label,
            'converged_at_utc': self.converged_at_utc,
            'item_count': self.item_count,
            'return_monitoring_converged_count': self.return_monitoring_converged_count,
            'restoration_audit_converged_count': self.restoration_audit_converged_count,
            'normalization_confirmed_count': self.normalization_confirmed_count,
            'reopen_required_count': self.reopen_required_count,
            'blocked_count': self.blocked_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_chronic_watch_audit_convergence_request(**kwargs: Any) -> OracleOperatorChronicWatchAuditConvergenceRequest:
    kwargs['convergence_root'] = Path(kwargs['convergence_root']).resolve()
    return OracleOperatorChronicWatchAuditConvergenceRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_item(item: Any, request: OracleOperatorChronicWatchAuditConvergenceRequest, converged_at_utc: datetime) -> OracleOperatorChronicWatchAuditConvergenceItem:
    started_at = datetime.fromisoformat(item.monitoring_started_at_utc)
    elapsed = max(0.0, (converged_at_utc - started_at).total_seconds() / 60.0)
    if item.activation_state == 'NORMALIZATION_BRIDGE_ACTIVATED' and elapsed >= request.normalization_window_minutes:
        convergence_state = 'CHRONIC_WATCH_CONVERGED_TO_RESTORATION_AUDIT'
        monitoring_state = 'MONITORING_ACTIVE'
        audit_state = 'RESTORATION_AUDIT_NORMALIZED'
        normalization_state = 'NORMALIZATION_CONFIRMED'
        normalized_ready = True
        reopen_required = False
        reason = 'CHRONIC_NORMALIZATION_BRIDGE_COMPLETED_WINDOW_AND_CONVERGED_INTO_STANDARD_RESTORATION_AUDIT'
    elif item.activation_state in ('NORMALIZATION_BRIDGE_ACTIVATED', 'NORMALIZATION_BRIDGE_CONTINUES_WATCH'):
        convergence_state = 'CHRONIC_WATCH_CONVERGED_TO_RETURN_MONITORING'
        monitoring_state = 'MONITORING_ACTIVE'
        audit_state = 'RESTORATION_AUDIT_MONITORED'
        normalization_state = 'NORMALIZATION_PENDING_MONITORING'
        normalized_ready = False
        reopen_required = False
        reason = 'CHRONIC_NORMALIZATION_BRIDGE_REENTERED_STANDARD_RETURN_MONITORING_WITHOUT_FULL_AUDIT_CONVERGENCE'
    elif item.activation_state == 'NORMALIZATION_BRIDGE_REOPEN_REQUIRED':
        convergence_state = 'CHRONIC_WATCH_CONVERGENCE_REOPEN_REQUIRED'
        monitoring_state = 'RETURN_NOT_RESTORED'
        audit_state = 'RESTORATION_AUDIT_REOPENED'
        normalization_state = 'REOPENED_AFTER_RESTORATION_ATTEMPT'
        normalized_ready = False
        reopen_required = True
        reason = 'CHRONIC_NORMALIZATION_BRIDGE_FAILED_AND_REQUIRES_REOPEN_INSTEAD_OF_AUDIT_CONVERGENCE'
    else:
        convergence_state = 'CHRONIC_WATCH_CONVERGENCE_BLOCKED'
        monitoring_state = 'RETURN_NOT_RESTORED'
        audit_state = 'RESTORATION_AUDIT_BLOCKED'
        normalization_state = 'RESTORATION_UNCONFIRMED'
        normalized_ready = False
        reopen_required = False
        reason = 'CHRONIC_NORMALIZATION_BRIDGE_DID_NOT_AUTHORIZE_CONVERGENCE_TO_STANDARD_AUDIT_PATH'

    return OracleOperatorChronicWatchAuditConvergenceItem(
        convergence_key=f'chronic_watch_audit_convergence:{item.bridge_activation_key}',
        bridge_activation_key=item.bridge_activation_key,
        bridge_key=item.bridge_key,
        work_item_key=item.work_item_key,
        activation_state=item.activation_state,
        convergence_state=convergence_state,
        return_monitoring_state=monitoring_state,
        restoration_audit_state=audit_state,
        normalization_state=normalization_state,
        normalized_ready=normalized_ready,
        reopen_required=reopen_required,
        return_monitoring_target=item.activated_return_monitoring_target,
        restoration_audit_target=item.activated_restoration_audit_target,
        convergence_reason_code=reason,
        converger_label=request.converger_label,
        converged_at_utc=converged_at_utc.isoformat(),
    )


def materialize_operator_chronic_watch_audit_convergence(
    request: OracleOperatorChronicWatchAuditConvergenceRequest,
    *,
    normalization_bridge_activation: OracleOperatorNormalizationBridgeActivation | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorChronicWatchAuditConvergence:
    if normalization_bridge_activation is None:
        normalization_bridge_activation = materialize_operator_normalization_bridge_activation(
            build_operator_normalization_bridge_activation_request(
                activation_root=request.convergence_root / 'normalization_bridge_activation',
                board_label=board_label,
                activator_label=request.converger_label,
                activated_at_utc=request.converged_at_utc,
                monitoring_started_at_utc=request.converged_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    converged_at_utc = _normalize(request.converged_at_utc)
    items = tuple(_derive_item(item, request, converged_at_utc) for item in normalization_bridge_activation.items)
    request.convergence_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.convergence_root / 'ORACLE_OPERATOR_CHRONIC_WATCH_AUDIT_CONVERGENCE.json'
    markdown_output_path = request.convergence_root / 'ORACLE_OPERATOR_CHRONIC_WATCH_AUDIT_CONVERGENCE.md'
    report = OracleOperatorChronicWatchAuditConvergence(
        schema_version='oracle_operator_chronic_watch_audit_convergence/v1',
        board_label=normalization_bridge_activation.board_label,
        convergence_root=str(request.convergence_root),
        converger_label=request.converger_label,
        converged_at_utc=converged_at_utc.isoformat(),
        item_count=len(items),
        return_monitoring_converged_count=len([i for i in items if i.convergence_state == 'CHRONIC_WATCH_CONVERGED_TO_RETURN_MONITORING']),
        restoration_audit_converged_count=len([i for i in items if i.convergence_state == 'CHRONIC_WATCH_CONVERGED_TO_RESTORATION_AUDIT']),
        normalization_confirmed_count=len([i for i in items if i.normalized_ready]),
        reopen_required_count=len([i for i in items if i.reopen_required]),
        blocked_count=len([i for i in items if i.convergence_state == 'CHRONIC_WATCH_CONVERGENCE_BLOCKED']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text(
        '\n'.join([
            '## Operator Chronic Watch Audit Convergence',
            f"- Board label: `{report.board_label}`",
            f"- Converger label: `{report.converger_label}`",
            f"- Return monitoring converged: `{report.return_monitoring_converged_count}`",
            f"- Restoration audit converged: `{report.restoration_audit_converged_count}`",
            f"- Normalization confirmed: `{report.normalization_confirmed_count}`",
            *[f"- {i.work_item_key}: {i.convergence_state} -> {i.restoration_audit_state}" for i in report.items],
            '',
        ]),
        encoding='utf-8',
    )
    return report


__all__ = [
    'OracleOperatorChronicWatchAuditConvergence',
    'OracleOperatorChronicWatchAuditConvergenceItem',
    'OracleOperatorChronicWatchAuditConvergenceRequest',
    'build_operator_chronic_watch_audit_convergence_request',
    'materialize_operator_chronic_watch_audit_convergence',
]
