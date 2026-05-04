from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.materialization import write_json_markdown_artifacts

from strategy_validator.control_plane.operator_freeze_release_gate import (
    OracleOperatorFreezeReleaseGate,
    build_operator_freeze_release_gate_request,
    materialize_operator_freeze_release_gate,
)


@dataclass(frozen=True)
class OracleOperatorFreezeReleaseAttestationRequest:
    attestation_root: Path
    board_label: str = 'default'
    certifier_label: str = 'freeze-release-attestor'
    attested_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorFreezeReleaseAttestationItem:
    attestation_key: str
    gate_key: str
    satisfaction_key: str
    work_item_key: str
    recurrence_class: str
    chronic_instability_class: str
    gate_state: str
    freeze_release_posture: str
    attestation_state: str
    attestation_reason_code: str
    attested_safe_to_rejoin: bool
    evidence_posture: str
    certifier_label: str
    attested_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorFreezeReleaseAttestation:
    schema_version: str
    board_label: str
    attestation_root: str
    certifier_label: str
    attested_at_utc: str
    attestation_count: int
    return_ready_count: int
    supervisor_monitoring_count: int
    held_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorFreezeReleaseAttestationItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'attestation_root': self.attestation_root,
            'certifier_label': self.certifier_label,
            'attested_at_utc': self.attested_at_utc,
            'attestation_count': self.attestation_count,
            'return_ready_count': self.return_ready_count,
            'supervisor_monitoring_count': self.supervisor_monitoring_count,
            'held_count': self.held_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_freeze_release_attestation_request(**kwargs: Any) -> OracleOperatorFreezeReleaseAttestationRequest:
    kwargs['attestation_root'] = Path(kwargs['attestation_root']).resolve()
    return OracleOperatorFreezeReleaseAttestationRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_item(item: Any, request: OracleOperatorFreezeReleaseAttestationRequest, attested_at_utc: datetime) -> OracleOperatorFreezeReleaseAttestationItem:
    attestation_state = 'FREEZE_RELEASE_ATTESTED_RETURN_READY'
    reason = 'FREEZE_RELEASE_CERTIFIED_SAFE_TO_REJOIN'
    safe = True
    evidence = 'CHRONIC_EXIT_EVIDENCE_ATTESTED'
    if 'SUPERVISOR' in item.gate_state:
        attestation_state = 'FREEZE_RELEASE_ATTESTED_WITH_SUPERVISOR_MONITORING'
        reason = 'FREEZE_RELEASE_CERTIFIED_WITH_SUPERVISOR_MONITORING'
        evidence = 'SUPERVISOR_CHRONIC_EXIT_EVIDENCE_ATTESTED'
    if not item.release_authorized:
        attestation_state = 'FREEZE_RELEASE_ATTESTATION_HELD'
        reason = 'FREEZE_RELEASE_NOT_AUTHORIZED'
        safe = False
        evidence = 'CHRONIC_EXIT_EVIDENCE_INSUFFICIENT'
    return OracleOperatorFreezeReleaseAttestationItem(
        attestation_key=f'freeze_release_attestation:{item.gate_key}',
        gate_key=item.gate_key,
        satisfaction_key=item.satisfaction_key,
        work_item_key=item.work_item_key,
        recurrence_class=item.recurrence_class,
        chronic_instability_class=item.chronic_instability_class,
        gate_state=item.gate_state,
        freeze_release_posture=item.freeze_release_posture,
        attestation_state=attestation_state,
        attestation_reason_code=reason,
        attested_safe_to_rejoin=safe,
        evidence_posture=evidence,
        certifier_label=request.certifier_label,
        attested_at_utc=attested_at_utc.isoformat(),
    )


def materialize_operator_freeze_release_attestation(
    request: OracleOperatorFreezeReleaseAttestationRequest,
    *,
    freeze_release_gate: OracleOperatorFreezeReleaseGate | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorFreezeReleaseAttestation:
    if freeze_release_gate is None:
        freeze_release_gate = materialize_operator_freeze_release_gate(
            build_operator_freeze_release_gate_request(
                gate_root=request.attestation_root / 'freeze_release_gate',
                board_label=board_label,
                reviewer_label=request.certifier_label,
                reviewed_at_utc=request.attested_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    attested_at_utc = _normalize(request.attested_at_utc)
    items = tuple(_derive_item(item, request, attested_at_utc) for item in freeze_release_gate.items)
    request.attestation_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.attestation_root / 'ORACLE_OPERATOR_FREEZE_RELEASE_ATTESTATION.json'
    markdown_output_path = request.attestation_root / 'ORACLE_OPERATOR_FREEZE_RELEASE_ATTESTATION.md'
    report = OracleOperatorFreezeReleaseAttestation(
        schema_version='oracle_operator_freeze_release_attestation/v1',
        board_label=freeze_release_gate.board_label,
        attestation_root=str(request.attestation_root),
        certifier_label=request.certifier_label,
        attested_at_utc=attested_at_utc.isoformat(),
        attestation_count=len(items),
        return_ready_count=len([i for i in items if i.attested_safe_to_rejoin and 'SUPERVISOR' not in i.attestation_state]),
        supervisor_monitoring_count=len([i for i in items if 'SUPERVISOR' in i.attestation_state]),
        held_count=len([i for i in items if not i.attested_safe_to_rejoin]),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    write_json_markdown_artifacts(
        summary_output_path=summary_output_path,
        markdown_output_path=markdown_output_path,
        payload=report.to_payload(),
        markdown=[
        '## Operator Freeze Release Attestation',
        f"- Board label: `{report.board_label}`",
        f"- Certifier label: `{report.certifier_label}`",
        f"- Return-ready attestations: `{report.return_ready_count}`",
        f"- Supervisor-monitoring attestations: `{report.supervisor_monitoring_count}`",
        f"- Held attestations: `{report.held_count}`",
        *[f"- {item.work_item_key}: {item.attestation_state} [{item.evidence_posture}]" for item in report.items],
        '',
    ],
    )
    return report


__all__ = [
    'OracleOperatorFreezeReleaseAttestation',
    'OracleOperatorFreezeReleaseAttestationItem',
    'OracleOperatorFreezeReleaseAttestationRequest',
    'build_operator_freeze_release_attestation_request',
    'materialize_operator_freeze_release_attestation',
]
