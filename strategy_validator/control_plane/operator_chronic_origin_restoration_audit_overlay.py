from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_chronic_origin_restoration_provenance import (
    OracleOperatorChronicOriginRestorationProvenance,
    build_operator_chronic_origin_restoration_provenance_request,
    materialize_operator_chronic_origin_restoration_provenance,
)
from strategy_validator.control_plane.operator_restoration_audit import (
    OracleOperatorRestorationAudit,
    build_operator_restoration_audit_request,
    materialize_operator_restoration_audit,
)


@dataclass(frozen=True)
class OracleOperatorChronicOriginRestorationAuditOverlayRequest:
    overlay_root: Path
    board_label: str = 'default'
    overlay_label: str = 'chronic-origin-audit-overlay'
    overlaid_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorChronicOriginRestorationAuditOverlayItem:
    overlay_key: str
    provenance_key: str
    audit_key: str
    work_item_key: str
    chronic_origin_restoration_path: str
    restoration_audit_state: str
    audit_intensity: str
    supervisor_watch_required: bool
    overlay_state: str
    overlay_reason_code: str
    overlay_label: str
    overlaid_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorChronicOriginRestorationAuditOverlay:
    schema_version: str
    board_label: str
    overlay_root: str
    overlay_label: str
    overlaid_at_utc: str
    overlay_count: int
    heightened_count: int
    standard_count: int
    held_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorChronicOriginRestorationAuditOverlayItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'overlay_root': self.overlay_root,
            'overlay_label': self.overlay_label,
            'overlaid_at_utc': self.overlaid_at_utc,
            'overlay_count': self.overlay_count,
            'heightened_count': self.heightened_count,
            'standard_count': self.standard_count,
            'held_count': self.held_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_chronic_origin_restoration_audit_overlay_request(**kwargs: Any) -> OracleOperatorChronicOriginRestorationAuditOverlayRequest:
    kwargs['overlay_root'] = Path(kwargs['overlay_root']).resolve()
    return OracleOperatorChronicOriginRestorationAuditOverlayRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_item(prov: Any, audit: Any, request: OracleOperatorChronicOriginRestorationAuditOverlayRequest, at: datetime) -> OracleOperatorChronicOriginRestorationAuditOverlayItem:
    if prov.eligible_for_standard_restoration_audit and audit.audit_state in {'RESTORATION_AUDIT_NORMALIZED','RESTORATION_AUDIT_MONITORED'}:
        if 'CHRONIC_MONITORED' in prov.chronic_origin_restoration_path or 'MONITORED' in prov.chronic_origin_restoration_path:
            intensity='HEIGHTENED'
            watch=True
            state='CHRONIC_ORIGIN_AUDIT_OVERLAY_HEIGHTENED'
            reason='CHRONIC_ORIGIN_REJOIN_REQUIRES_HEIGHTENED_RESTORATION_AUDIT_AND_SUPERVISOR_WATCH'
        else:
            intensity='STANDARD_WITH_PROVENANCE'
            watch=False
            state='CHRONIC_ORIGIN_AUDIT_OVERLAY_STANDARD_WITH_PROVENANCE'
            reason='CHRONIC_ORIGIN_REJOIN_ELIGIBLE_FOR_STANDARD_RESTORATION_AUDIT_WITH_PROVENANCE_NOTE'
    else:
        intensity='HELD'
        watch=True
        state='CHRONIC_ORIGIN_AUDIT_OVERLAY_HELD'
        reason='CHRONIC_ORIGIN_PROVENANCE_NOT_ELIGIBLE_FOR_STANDARD_RESTORATION_AUDIT'
    return OracleOperatorChronicOriginRestorationAuditOverlayItem(
        overlay_key=f'chronic_origin_restoration_audit_overlay:{prov.provenance_key}',
        provenance_key=prov.provenance_key,
        audit_key=audit.audit_key,
        work_item_key=prov.work_item_key,
        chronic_origin_restoration_path=prov.chronic_origin_restoration_path,
        restoration_audit_state=audit.audit_state,
        audit_intensity=intensity,
        supervisor_watch_required=watch,
        overlay_state=state,
        overlay_reason_code=reason,
        overlay_label=request.overlay_label,
        overlaid_at_utc=at.isoformat(),
    )


def materialize_operator_chronic_origin_restoration_audit_overlay(
    request: OracleOperatorChronicOriginRestorationAuditOverlayRequest,
    *,
    chronic_origin_restoration_provenance: OracleOperatorChronicOriginRestorationProvenance | None = None,
    restoration_audit: OracleOperatorRestorationAudit | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorChronicOriginRestorationAuditOverlay:
    if chronic_origin_restoration_provenance is None:
        chronic_origin_restoration_provenance = materialize_operator_chronic_origin_restoration_provenance(
            build_operator_chronic_origin_restoration_provenance_request(
                provenance_root=request.overlay_root / 'chronic_origin_restoration_provenance',
                board_label=board_label,
                provenance_label=request.overlay_label,
                recorded_at_utc=request.overlaid_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    if restoration_audit is None:
        restoration_audit = materialize_operator_restoration_audit(
            build_operator_restoration_audit_request(
                audit_root=request.overlay_root / 'restoration_audit',
                board_label=board_label,
                auditor_label=request.overlay_label,
                audited_at_utc=request.overlaid_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    at = _normalize(request.overlaid_at_utc)
    audits = {i.work_item_key: i for i in restoration_audit.items}
    items = tuple(_derive_item(p, audits[p.work_item_key], request, at) for p in chronic_origin_restoration_provenance.items if p.work_item_key in audits)
    request.overlay_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.overlay_root / 'ORACLE_OPERATOR_CHRONIC_ORIGIN_RESTORATION_AUDIT_OVERLAY.json'
    markdown_output_path = request.overlay_root / 'ORACLE_OPERATOR_CHRONIC_ORIGIN_RESTORATION_AUDIT_OVERLAY.md'
    report = OracleOperatorChronicOriginRestorationAuditOverlay(
        schema_version='oracle_operator_chronic_origin_restoration_audit_overlay/v1',
        board_label=board_label,
        overlay_root=str(request.overlay_root),
        overlay_label=request.overlay_label,
        overlaid_at_utc=at.isoformat(),
        overlay_count=len(items),
        heightened_count=sum(i.overlay_state == 'CHRONIC_ORIGIN_AUDIT_OVERLAY_HEIGHTENED' for i in items),
        standard_count=sum(i.overlay_state == 'CHRONIC_ORIGIN_AUDIT_OVERLAY_STANDARD_WITH_PROVENANCE' for i in items),
        held_count=sum(i.overlay_state == 'CHRONIC_ORIGIN_AUDIT_OVERLAY_HELD' for i in items),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text('\n'.join([
        '## Operator Chronic-Origin Restoration Audit Overlay',
        f"- Board label: `{report.board_label}`",
        f"- Heightened overlays: `{report.heightened_count}`",
        f"- Standard overlays: `{report.standard_count}`",
        f"- Held overlays: `{report.held_count}`",
        *[f"- {i.work_item_key}: {i.overlay_state} -> {i.audit_intensity}" for i in report.items],
        '',
    ]), encoding='utf-8')
    return report


__all__ = [
    'OracleOperatorChronicOriginRestorationAuditOverlay',
    'OracleOperatorChronicOriginRestorationAuditOverlayItem',
    'OracleOperatorChronicOriginRestorationAuditOverlayRequest',
    'build_operator_chronic_origin_restoration_audit_overlay_request',
    'materialize_operator_chronic_origin_restoration_audit_overlay',
]
