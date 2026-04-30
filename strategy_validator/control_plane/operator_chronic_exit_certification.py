from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.materialization import write_json_markdown_artifacts

from strategy_validator.control_plane.operator_freeze_release_attestation import (
    OracleOperatorFreezeReleaseAttestation,
    build_operator_freeze_release_attestation_request,
    materialize_operator_freeze_release_attestation,
)


@dataclass(frozen=True)
class OracleOperatorChronicExitCertificationRequest:
    certification_root: Path
    board_label: str = 'default'
    certifier_label: str = 'chronic-exit-certifier'
    certified_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorChronicExitCertificationItem:
    certification_key: str
    attestation_key: str
    gate_key: str
    work_item_key: str
    recurrence_class: str
    chronic_instability_class: str
    attestation_state: str
    certification_state: str
    certification_reason_code: str
    chronic_exit_certified: bool
    return_path_state: str
    next_queue_lane: str
    certifier_label: str
    certified_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorChronicExitCertification:
    schema_version: str
    board_label: str
    certification_root: str
    certifier_label: str
    certified_at_utc: str
    certification_count: int
    certified_count: int
    monitoring_certified_count: int
    held_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorChronicExitCertificationItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'certification_root': self.certification_root,
            'certifier_label': self.certifier_label,
            'certified_at_utc': self.certified_at_utc,
            'certification_count': self.certification_count,
            'certified_count': self.certified_count,
            'monitoring_certified_count': self.monitoring_certified_count,
            'held_count': self.held_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_chronic_exit_certification_request(**kwargs: Any) -> OracleOperatorChronicExitCertificationRequest:
    kwargs['certification_root'] = Path(kwargs['certification_root']).resolve()
    return OracleOperatorChronicExitCertificationRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_item(item: Any, request: OracleOperatorChronicExitCertificationRequest, certified_at_utc: datetime) -> OracleOperatorChronicExitCertificationItem:
    state = 'CHRONIC_EXIT_CERTIFIED'
    reason = 'CHRONIC_EXIT_CERTIFIED_SAFE_TO_REJOIN_RETURN_PATH'
    certified = True
    return_path_state = 'RETURN_PATH_REJOIN_AUTHORIZED'
    next_lane = 'RETURN_AUTHORIZATION_REENTRY_QUEUE'
    if 'SUPERVISOR' in item.attestation_state:
        state = 'CHRONIC_EXIT_CERTIFIED_WITH_MONITORING'
        reason = 'CHRONIC_EXIT_CERTIFIED_WITH_SUPERVISOR_MONITORING'
        return_path_state = 'RETURN_PATH_REJOIN_AUTHORIZED_WITH_MONITORING'
        next_lane = 'SUPERVISOR_RETURN_AUTHORIZATION_QUEUE'
    if not item.attested_safe_to_rejoin:
        state = 'CHRONIC_EXIT_CERTIFICATION_HELD'
        reason = 'CHRONIC_EXIT_NOT_SAFE_TO_REJOIN'
        certified = False
        return_path_state = 'RETURN_PATH_REJOIN_BLOCKED'
        next_lane = 'CHRONIC_REMEDIATION_QUEUE'
    return OracleOperatorChronicExitCertificationItem(
        certification_key=f'chronic_exit_certification:{item.attestation_key}',
        attestation_key=item.attestation_key,
        gate_key=item.gate_key,
        work_item_key=item.work_item_key,
        recurrence_class=item.recurrence_class,
        chronic_instability_class=item.chronic_instability_class,
        attestation_state=item.attestation_state,
        certification_state=state,
        certification_reason_code=reason,
        chronic_exit_certified=certified,
        return_path_state=return_path_state,
        next_queue_lane=next_lane,
        certifier_label=request.certifier_label,
        certified_at_utc=certified_at_utc.isoformat(),
    )


def materialize_operator_chronic_exit_certification(
    request: OracleOperatorChronicExitCertificationRequest,
    *,
    freeze_release_attestation: OracleOperatorFreezeReleaseAttestation | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorChronicExitCertification:
    if freeze_release_attestation is None:
        freeze_release_attestation = materialize_operator_freeze_release_attestation(
            build_operator_freeze_release_attestation_request(
                attestation_root=request.certification_root / 'freeze_release_attestation',
                board_label=board_label,
                certifier_label=request.certifier_label,
                attested_at_utc=request.certified_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    certified_at_utc = _normalize(request.certified_at_utc)
    items = tuple(_derive_item(item, request, certified_at_utc) for item in freeze_release_attestation.items)
    request.certification_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.certification_root / 'ORACLE_OPERATOR_CHRONIC_EXIT_CERTIFICATION.json'
    markdown_output_path = request.certification_root / 'ORACLE_OPERATOR_CHRONIC_EXIT_CERTIFICATION.md'
    report = OracleOperatorChronicExitCertification(
        schema_version='oracle_operator_chronic_exit_certification/v1',
        board_label=freeze_release_attestation.board_label,
        certification_root=str(request.certification_root),
        certifier_label=request.certifier_label,
        certified_at_utc=certified_at_utc.isoformat(),
        certification_count=len(items),
        certified_count=len([i for i in items if i.chronic_exit_certified and 'WITH_MONITORING' not in i.certification_state]),
        monitoring_certified_count=len([i for i in items if 'WITH_MONITORING' in i.certification_state]),
        held_count=len([i for i in items if not i.chronic_exit_certified]),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    write_json_markdown_artifacts(
        summary_output_path=summary_output_path,
        markdown_output_path=markdown_output_path,
        payload=report.to_payload(),
        markdown=[
        '## Operator Chronic Exit Certification',
        f"- Board label: `{report.board_label}`",
        f"- Certifier label: `{report.certifier_label}`",
        f"- Certified count: `{report.certified_count}`",
        f"- Monitoring-certified count: `{report.monitoring_certified_count}`",
        f"- Held count: `{report.held_count}`",
        *[f"- {item.work_item_key}: {item.certification_state} -> {item.next_queue_lane}" for item in report.items],
        '',
    ],
    )
    return report


__all__ = [
    'OracleOperatorChronicExitCertification',
    'OracleOperatorChronicExitCertificationItem',
    'OracleOperatorChronicExitCertificationRequest',
    'build_operator_chronic_exit_certification_request',
    'materialize_operator_chronic_exit_certification',
]
