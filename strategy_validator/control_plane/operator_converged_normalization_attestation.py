from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_chronic_watch_audit_convergence import (
    OracleOperatorChronicWatchAuditConvergence,
    build_operator_chronic_watch_audit_convergence_request,
    materialize_operator_chronic_watch_audit_convergence,
)


@dataclass(frozen=True)
class OracleOperatorConvergedNormalizationAttestationRequest:
    attestation_root: Path
    board_label: str = 'default'
    attestor_label: str = 'converged-normalization-attestor'
    attested_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorConvergedNormalizationAttestationItem:
    attestation_key: str
    convergence_key: str
    bridge_activation_key: str
    work_item_key: str
    convergence_state: str
    normalization_state: str
    attestation_state: str
    attestation_reason_code: str
    chronic_origin_preserved: bool
    attested_safe_to_resume: bool
    attestor_label: str
    attested_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorConvergedNormalizationAttestation:
    schema_version: str
    board_label: str
    attestation_root: str
    attestor_label: str
    attested_at_utc: str
    attestation_count: int
    return_ready_count: int
    monitored_resume_count: int
    held_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorConvergedNormalizationAttestationItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'attestation_root': self.attestation_root,
            'attestor_label': self.attestor_label,
            'attested_at_utc': self.attested_at_utc,
            'attestation_count': self.attestation_count,
            'return_ready_count': self.return_ready_count,
            'monitored_resume_count': self.monitored_resume_count,
            'held_count': self.held_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_converged_normalization_attestation_request(**kwargs: Any) -> OracleOperatorConvergedNormalizationAttestationRequest:
    kwargs['attestation_root'] = Path(kwargs['attestation_root']).resolve()
    return OracleOperatorConvergedNormalizationAttestationRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_item(item: Any, request: OracleOperatorConvergedNormalizationAttestationRequest, attested_at_utc: datetime) -> OracleOperatorConvergedNormalizationAttestationItem:
    if item.convergence_state == 'CHRONIC_WATCH_CONVERGED_TO_RESTORATION_AUDIT' and item.normalized_ready:
        state = 'CONVERGED_NORMALIZATION_ATTESTED_RETURN_READY'
        reason = 'CHRONIC_ORIGIN_NORMALIZATION_COMPLETED_AND_ATTESTED_SAFE_TO_RESUME_STANDARD_FLOW'
        safe = True
    elif item.convergence_state == 'CHRONIC_WATCH_CONVERGED_TO_RETURN_MONITORING':
        state = 'CONVERGED_NORMALIZATION_ATTESTED_MONITORED_RESUME'
        reason = 'CHRONIC_ORIGIN_NORMALIZATION_REENTERED_STANDARD_MONITORING_WITH_ATTESTED_GUARDRAILS'
        safe = True
    else:
        state = 'CONVERGED_NORMALIZATION_ATTESTATION_HELD'
        reason = 'CHRONIC_ORIGIN_NORMALIZATION_DID_NOT_CONVERGE_CLEANLY_ENOUGH_FOR_ATTESTED_RESUME'
        safe = False
    return OracleOperatorConvergedNormalizationAttestationItem(
        attestation_key=f'converged_normalization_attestation:{item.convergence_key}',
        convergence_key=item.convergence_key,
        bridge_activation_key=item.bridge_activation_key,
        work_item_key=item.work_item_key,
        convergence_state=item.convergence_state,
        normalization_state=item.normalization_state,
        attestation_state=state,
        attestation_reason_code=reason,
        chronic_origin_preserved=True,
        attested_safe_to_resume=safe,
        attestor_label=request.attestor_label,
        attested_at_utc=attested_at_utc.isoformat(),
    )


def materialize_operator_converged_normalization_attestation(
    request: OracleOperatorConvergedNormalizationAttestationRequest,
    *,
    chronic_watch_audit_convergence: OracleOperatorChronicWatchAuditConvergence | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorConvergedNormalizationAttestation:
    if chronic_watch_audit_convergence is None:
        chronic_watch_audit_convergence = materialize_operator_chronic_watch_audit_convergence(
            build_operator_chronic_watch_audit_convergence_request(
                convergence_root=request.attestation_root / 'chronic_watch_audit_convergence',
                board_label=board_label,
                converger_label=request.attestor_label,
                converged_at_utc=request.attested_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    attested_at_utc = _normalize(request.attested_at_utc)
    items = tuple(_derive_item(i, request, attested_at_utc) for i in chronic_watch_audit_convergence.items)
    request.attestation_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.attestation_root / 'ORACLE_OPERATOR_CONVERGED_NORMALIZATION_ATTESTATION.json'
    markdown_output_path = request.attestation_root / 'ORACLE_OPERATOR_CONVERGED_NORMALIZATION_ATTESTATION.md'
    report = OracleOperatorConvergedNormalizationAttestation(
        schema_version='oracle_operator_converged_normalization_attestation/v1',
        board_label=chronic_watch_audit_convergence.board_label,
        attestation_root=str(request.attestation_root),
        attestor_label=request.attestor_label,
        attested_at_utc=attested_at_utc.isoformat(),
        attestation_count=len(items),
        return_ready_count=len([i for i in items if i.attestation_state == 'CONVERGED_NORMALIZATION_ATTESTED_RETURN_READY']),
        monitored_resume_count=len([i for i in items if i.attestation_state == 'CONVERGED_NORMALIZATION_ATTESTED_MONITORED_RESUME']),
        held_count=len([i for i in items if i.attestation_state == 'CONVERGED_NORMALIZATION_ATTESTATION_HELD']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text('\n'.join([
        '## Operator Converged Normalization Attestation',
        f"- Board label: `{report.board_label}`",
        f"- Attestor label: `{report.attestor_label}`",
        f"- Return-ready count: `{report.return_ready_count}`",
        f"- Monitored resume count: `{report.monitored_resume_count}`",
        f"- Held count: `{report.held_count}`",
        *[f"- {i.work_item_key}: {i.attestation_state} [{i.normalization_state}]" for i in report.items],
        '',
    ]), encoding='utf-8')
    return report


__all__ = [
    'OracleOperatorConvergedNormalizationAttestation',
    'OracleOperatorConvergedNormalizationAttestationItem',
    'OracleOperatorConvergedNormalizationAttestationRequest',
    'build_operator_converged_normalization_attestation_request',
    'materialize_operator_converged_normalization_attestation',
]
