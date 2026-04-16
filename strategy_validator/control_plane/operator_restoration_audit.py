from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_return_monitoring import (
    OracleOperatorReturnMonitoring,
    build_operator_return_monitoring_request,
    materialize_operator_return_monitoring,
)


@dataclass(frozen=True)
class OracleOperatorRestorationAuditRequest:
    audit_root: Path
    board_label: str = 'default'
    auditor_label: str = 'restoration-auditor'
    audited_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorRestorationAuditItem:
    audit_key: str
    monitoring_key: str
    activation_key: str
    work_item_key: str
    remediation_class: str
    monitoring_state: str
    normalized_ready: bool
    audit_state: str
    audit_reason_code: str
    normalization_state: str
    reopened_after_restoration: bool
    auditor_label: str
    audited_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorRestorationAudit:
    schema_version: str
    board_label: str
    audit_root: str
    auditor_label: str
    audited_at_utc: str
    item_count: int
    normalized_count: int
    monitored_count: int
    reopened_count: int
    blocked_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorRestorationAuditItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'audit_root': self.audit_root,
            'auditor_label': self.auditor_label,
            'audited_at_utc': self.audited_at_utc,
            'item_count': self.item_count,
            'normalized_count': self.normalized_count,
            'monitored_count': self.monitored_count,
            'reopened_count': self.reopened_count,
            'blocked_count': self.blocked_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_restoration_audit_request(**kwargs: Any) -> OracleOperatorRestorationAuditRequest:
    kwargs['audit_root'] = Path(kwargs['audit_root']).resolve()
    return OracleOperatorRestorationAuditRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_audit_item(item: Any, request: OracleOperatorRestorationAuditRequest, audited_at_utc: datetime) -> OracleOperatorRestorationAuditItem:
    audit_state = 'RESTORATION_AUDIT_BLOCKED'
    reason = 'RETURN_NOT_YET_NORMALIZED'
    normalization_state = 'RESTORATION_UNCONFIRMED'
    reopened = False
    if item.normalized_ready:
        audit_state = 'RESTORATION_AUDIT_NORMALIZED'
        reason = 'POST_RETURN_MONITORING_COMPLETED'
        normalization_state = 'NORMALIZATION_CONFIRMED'
    elif item.monitoring_state == 'MONITORING_ACTIVE':
        audit_state = 'RESTORATION_AUDIT_MONITORED'
        reason = 'MONITORING_WINDOW_STILL_ACTIVE'
        normalization_state = 'NORMALIZATION_PENDING_MONITORING'
    elif item.monitoring_state == 'RETURN_NOT_RESTORED':
        audit_state = 'RESTORATION_AUDIT_REOPENED'
        reason = 'RETURN_NEVER_RESTORED_TO_NORMAL_FLOW'
        normalization_state = 'REOPENED_AFTER_RESTORATION_ATTEMPT'
        reopened = True

    return OracleOperatorRestorationAuditItem(
        audit_key=f'restoration_audit:{item.monitoring_key}',
        monitoring_key=item.monitoring_key,
        activation_key=item.activation_key,
        work_item_key=item.work_item_key,
        remediation_class=item.remediation_class,
        monitoring_state=item.monitoring_state,
        normalized_ready=item.normalized_ready,
        audit_state=audit_state,
        audit_reason_code=reason,
        normalization_state=normalization_state,
        reopened_after_restoration=reopened,
        auditor_label=request.auditor_label,
        audited_at_utc=audited_at_utc.isoformat(),
    )


def materialize_operator_restoration_audit(
    request: OracleOperatorRestorationAuditRequest,
    *,
    return_monitoring: OracleOperatorReturnMonitoring | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorRestorationAudit:
    if return_monitoring is None:
        return_monitoring = materialize_operator_return_monitoring(
            build_operator_return_monitoring_request(
                monitoring_root=request.audit_root / 'return_monitoring',
                board_label=board_label,
                monitor_label=request.auditor_label,
                evaluated_at_utc=request.audited_at_utc,
                monitoring_started_at_utc=request.audited_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    audited_at_utc = _normalize(request.audited_at_utc)
    items = tuple(_derive_audit_item(i, request, audited_at_utc) for i in return_monitoring.items)
    request.audit_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.audit_root / 'ORACLE_OPERATOR_RESTORATION_AUDIT.json'
    markdown_output_path = request.audit_root / 'ORACLE_OPERATOR_RESTORATION_AUDIT.md'
    report = OracleOperatorRestorationAudit(
        schema_version='oracle_operator_restoration_audit/v1',
        board_label=return_monitoring.board_label,
        audit_root=str(request.audit_root),
        auditor_label=request.auditor_label,
        audited_at_utc=audited_at_utc.isoformat(),
        item_count=len(items),
        normalized_count=len([i for i in items if i.audit_state == 'RESTORATION_AUDIT_NORMALIZED']),
        monitored_count=len([i for i in items if i.audit_state == 'RESTORATION_AUDIT_MONITORED']),
        reopened_count=len([i for i in items if i.reopened_after_restoration]),
        blocked_count=len([i for i in items if i.audit_state == 'RESTORATION_AUDIT_BLOCKED']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text('\n'.join([
        '## Operator Restoration Audit',
        f"- Board label: `{report.board_label}`",
        f"- Auditor label: `{report.auditor_label}`",
        f"- Normalized: `{report.normalized_count}`",
        f"- Monitored: `{report.monitored_count}`",
        f"- Reopened: `{report.reopened_count}`",
        *[f"- {i.work_item_key}: {i.audit_state} -> {i.normalization_state}" for i in report.items],
        '',
    ]), encoding='utf-8')
    return report


__all__ = [
    'OracleOperatorRestorationAudit',
    'OracleOperatorRestorationAuditItem',
    'OracleOperatorRestorationAuditRequest',
    'build_operator_restoration_audit_request',
    'materialize_operator_restoration_audit',
]
