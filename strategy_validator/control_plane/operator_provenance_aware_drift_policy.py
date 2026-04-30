from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_chronic_origin_restoration_audit_overlay import (
    OracleOperatorChronicOriginRestorationAuditOverlay,
    build_operator_chronic_origin_restoration_audit_overlay_request,
    materialize_operator_chronic_origin_restoration_audit_overlay,
)


@dataclass(frozen=True)
class OracleOperatorProvenanceAwareDriftPolicyRequest:
    policy_root: Path
    board_label: str = 'default'
    policy_label: str = 'provenance-aware-drift-policy'
    evaluated_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorProvenanceAwareDriftPolicyItem:
    policy_key: str
    overlay_key: str
    work_item_key: str
    overlay_state: str
    audit_intensity: str
    drift_sensitivity: str
    reopen_threshold: str
    supervisor_watch_posture: str
    policy_state: str
    policy_reason_code: str
    next_queue_lane: str
    policy_label: str
    evaluated_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorProvenanceAwareDriftPolicy:
    schema_version: str
    board_label: str
    policy_root: str
    policy_label: str
    evaluated_at_utc: str
    policy_count: int
    heightened_policy_count: int
    guarded_policy_count: int
    blocked_policy_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorProvenanceAwareDriftPolicyItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'policy_root': self.policy_root,
            'policy_label': self.policy_label,
            'evaluated_at_utc': self.evaluated_at_utc,
            'policy_count': self.policy_count,
            'heightened_policy_count': self.heightened_policy_count,
            'guarded_policy_count': self.guarded_policy_count,
            'blocked_policy_count': self.blocked_policy_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_provenance_aware_drift_policy_request(**kwargs: Any) -> OracleOperatorProvenanceAwareDriftPolicyRequest:
    kwargs['policy_root'] = Path(kwargs['policy_root']).resolve()
    return OracleOperatorProvenanceAwareDriftPolicyRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_item(item: Any, request: OracleOperatorProvenanceAwareDriftPolicyRequest, at: datetime) -> OracleOperatorProvenanceAwareDriftPolicyItem:
    if item.overlay_state == 'CHRONIC_ORIGIN_AUDIT_OVERLAY_HEIGHTENED':
        sensitivity='HIGH'
        threshold='ONE_STRIKE_REOPEN'
        watch='SUPERVISOR_WATCH_ACTIVE'
        state='PROVENANCE_AWARE_DRIFT_POLICY_HEIGHTENED'
        reason='CHRONIC_ORIGIN_HISTORY_REQUIRES_HEIGHTENED_DRIFT_SENSITIVITY_AND_FAST_REOPEN'
        lane='HEIGHTENED_RETURN_MONITORING'
    elif item.overlay_state == 'CHRONIC_ORIGIN_AUDIT_OVERLAY_STANDARD_WITH_PROVENANCE':
        sensitivity='GUARDED'
        threshold='LOW_THRESHOLD_REOPEN'
        watch='PROVENANCE_GUARDED_WATCH'
        state='PROVENANCE_AWARE_DRIFT_POLICY_GUARDED'
        reason='CHRONIC_ORIGIN_PROVENANCE_REQUIRES_GUARDED_DRIFT_POLICY_UNDER_STANDARD_RESTORATION'
        lane='OPERATOR_NORMAL_QUEUE'
    else:
        sensitivity='BLOCKED'
        threshold='NO_REJOIN'
        watch='SUPERVISOR_HOLD'
        state='PROVENANCE_AWARE_DRIFT_POLICY_BLOCKED'
        reason='CHRONIC_ORIGIN_AUDIT_OVERLAY_HELD_SO_DRIFT_POLICY_REMAINS_BLOCKED'
        lane='SUPERVISOR_REVIEW_QUEUE'
    return OracleOperatorProvenanceAwareDriftPolicyItem(
        policy_key=f'provenance_aware_drift_policy:{item.overlay_key}',
        overlay_key=item.overlay_key,
        work_item_key=item.work_item_key,
        overlay_state=item.overlay_state,
        audit_intensity=item.audit_intensity,
        drift_sensitivity=sensitivity,
        reopen_threshold=threshold,
        supervisor_watch_posture=watch,
        policy_state=state,
        policy_reason_code=reason,
        next_queue_lane=lane,
        policy_label=request.policy_label,
        evaluated_at_utc=at.isoformat(),
    )


def materialize_operator_provenance_aware_drift_policy(
    request: OracleOperatorProvenanceAwareDriftPolicyRequest,
    *,
    chronic_origin_restoration_audit_overlay: OracleOperatorChronicOriginRestorationAuditOverlay | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorProvenanceAwareDriftPolicy:
    if chronic_origin_restoration_audit_overlay is None:
        chronic_origin_restoration_audit_overlay = materialize_operator_chronic_origin_restoration_audit_overlay(
            build_operator_chronic_origin_restoration_audit_overlay_request(
                overlay_root=request.policy_root / 'chronic_origin_restoration_audit_overlay',
                board_label=board_label,
                overlay_label=request.policy_label,
                overlaid_at_utc=request.evaluated_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    at = _normalize(request.evaluated_at_utc)
    items = tuple(_derive_item(i, request, at) for i in chronic_origin_restoration_audit_overlay.items)
    request.policy_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.policy_root / 'ORACLE_OPERATOR_PROVENANCE_AWARE_DRIFT_POLICY.json'
    markdown_output_path = request.policy_root / 'ORACLE_OPERATOR_PROVENANCE_AWARE_DRIFT_POLICY.md'
    report = OracleOperatorProvenanceAwareDriftPolicy(
        schema_version='oracle_operator_provenance_aware_drift_policy/v1',
        board_label=board_label,
        policy_root=str(request.policy_root),
        policy_label=request.policy_label,
        evaluated_at_utc=at.isoformat(),
        policy_count=len(items),
        heightened_policy_count=sum(i.policy_state == 'PROVENANCE_AWARE_DRIFT_POLICY_HEIGHTENED' for i in items),
        guarded_policy_count=sum(i.policy_state == 'PROVENANCE_AWARE_DRIFT_POLICY_GUARDED' for i in items),
        blocked_policy_count=sum(i.policy_state == 'PROVENANCE_AWARE_DRIFT_POLICY_BLOCKED' for i in items),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text('\n'.join([
        '## Operator Provenance-Aware Drift Policy',
        f"- Board label: `{report.board_label}`",
        f"- Heightened policy count: `{report.heightened_policy_count}`",
        f"- Guarded policy count: `{report.guarded_policy_count}`",
        f"- Blocked policy count: `{report.blocked_policy_count}`",
        *[f"- {i.work_item_key}: {i.policy_state} -> {i.drift_sensitivity}" for i in report.items],
        '',
    ]), encoding='utf-8')
    return report


__all__ = [
    'OracleOperatorProvenanceAwareDriftPolicy',
    'OracleOperatorProvenanceAwareDriftPolicyItem',
    'OracleOperatorProvenanceAwareDriftPolicyRequest',
    'build_operator_provenance_aware_drift_policy_request',
    'materialize_operator_provenance_aware_drift_policy',
]
