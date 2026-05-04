from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.materialization import write_json_markdown_artifacts

from strategy_validator.control_plane.operator_converged_normalization_attestation import (
    OracleOperatorConvergedNormalizationAttestation,
    build_operator_converged_normalization_attestation_request,
    materialize_operator_converged_normalization_attestation,
)


@dataclass(frozen=True)
class OracleOperatorChronicOriginRestorationProvenanceRequest:
    provenance_root: Path
    board_label: str = 'default'
    provenance_label: str = 'chronic-origin-provenance-recorder'
    recorded_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorChronicOriginRestorationProvenanceItem:
    provenance_key: str
    attestation_key: str
    convergence_key: str
    work_item_key: str
    chronic_origin_restoration_path: str
    provenance_state: str
    provenance_reason_code: str
    provenance_chain: tuple[str, ...]
    eligible_for_standard_restoration_audit: bool
    recorder_label: str
    recorded_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        payload = self.__dict__.copy()
        payload['provenance_chain'] = list(self.provenance_chain)
        return payload


@dataclass(frozen=True)
class OracleOperatorChronicOriginRestorationProvenance:
    schema_version: str
    board_label: str
    provenance_root: str
    provenance_label: str
    recorded_at_utc: str
    provenance_count: int
    chronic_path_count: int
    standard_restoration_eligible_count: int
    held_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorChronicOriginRestorationProvenanceItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'provenance_root': self.provenance_root,
            'provenance_label': self.provenance_label,
            'recorded_at_utc': self.recorded_at_utc,
            'provenance_count': self.provenance_count,
            'chronic_path_count': self.chronic_path_count,
            'standard_restoration_eligible_count': self.standard_restoration_eligible_count,
            'held_count': self.held_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_chronic_origin_restoration_provenance_request(**kwargs: Any) -> OracleOperatorChronicOriginRestorationProvenanceRequest:
    kwargs['provenance_root'] = Path(kwargs['provenance_root']).resolve()
    return OracleOperatorChronicOriginRestorationProvenanceRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_item(item: Any, request: OracleOperatorChronicOriginRestorationProvenanceRequest, recorded_at_utc: datetime) -> OracleOperatorChronicOriginRestorationProvenanceItem:
    eligible = item.attested_safe_to_resume
    if eligible:
        state = 'CHRONIC_ORIGIN_PROVENANCE_RECORDED'
        reason = 'CHRONIC_BRANCH_CONVERGED_AND_REJOINED_STANDARD_RESTORATION_PATH_WITH_PROVENANCE_PRESERVED'
    else:
        state = 'CHRONIC_ORIGIN_PROVENANCE_HELD'
        reason = 'CHRONIC_BRANCH_REMAINED_NON_STANDARD_AND_CANNOT_YET_REJOIN_STANDARD_RESTORATION_PATH'
    if item.attestation_state == 'CONVERGED_NORMALIZATION_ATTESTED_MONITORED_RESUME':
        path = 'CHRONIC_BRANCH_MONITORED_RESTORATION'
    elif item.attestation_state == 'CONVERGED_NORMALIZATION_ATTESTED_RETURN_READY':
        path = 'CHRONIC_BRANCH_NORMALIZED_RESTORATION'
    else:
        path = 'CHRONIC_BRANCH_HELD'
    return OracleOperatorChronicOriginRestorationProvenanceItem(
        provenance_key=f'chronic_origin_restoration_provenance:{item.attestation_key}',
        attestation_key=item.attestation_key,
        convergence_key=item.convergence_key,
        work_item_key=item.work_item_key,
        chronic_origin_restoration_path=path,
        provenance_state=state,
        provenance_reason_code=reason,
        provenance_chain=(
            'chronic_watch_handoff',
            'chronic_watch_outcome',
            'monitored_rejoin_normalization_bridge',
            'normalization_bridge_activation',
            'chronic_watch_audit_convergence',
            'converged_normalization_attestation',
            'chronic_origin_restoration_provenance',
        ),
        eligible_for_standard_restoration_audit=eligible,
        recorder_label=request.provenance_label,
        recorded_at_utc=recorded_at_utc.isoformat(),
    )


def materialize_operator_chronic_origin_restoration_provenance(
    request: OracleOperatorChronicOriginRestorationProvenanceRequest,
    *,
    converged_normalization_attestation: OracleOperatorConvergedNormalizationAttestation | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorChronicOriginRestorationProvenance:
    if converged_normalization_attestation is None:
        converged_normalization_attestation = materialize_operator_converged_normalization_attestation(
            build_operator_converged_normalization_attestation_request(
                attestation_root=request.provenance_root / 'converged_normalization_attestation',
                board_label=board_label,
                attestor_label=request.provenance_label,
                attested_at_utc=request.recorded_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    recorded_at_utc = _normalize(request.recorded_at_utc)
    items = tuple(_derive_item(i, request, recorded_at_utc) for i in converged_normalization_attestation.items)
    request.provenance_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.provenance_root / 'ORACLE_OPERATOR_CHRONIC_ORIGIN_RESTORATION_PROVENANCE.json'
    markdown_output_path = request.provenance_root / 'ORACLE_OPERATOR_CHRONIC_ORIGIN_RESTORATION_PROVENANCE.md'
    report = OracleOperatorChronicOriginRestorationProvenance(
        schema_version='oracle_operator_chronic_origin_restoration_provenance/v1',
        board_label=converged_normalization_attestation.board_label,
        provenance_root=str(request.provenance_root),
        provenance_label=request.provenance_label,
        recorded_at_utc=recorded_at_utc.isoformat(),
        provenance_count=len(items),
        chronic_path_count=len(items),
        standard_restoration_eligible_count=len([i for i in items if i.eligible_for_standard_restoration_audit]),
        held_count=len([i for i in items if not i.eligible_for_standard_restoration_audit]),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    write_json_markdown_artifacts(
        summary_output_path=summary_output_path,
        markdown_output_path=markdown_output_path,
        payload=report.to_payload(),
        markdown=[
        '## Operator Chronic Origin Restoration Provenance',
        f"- Board label: `{report.board_label}`",
        f"- Recorder label: `{report.provenance_label}`",
        f"- Eligible for standard restoration audit: `{report.standard_restoration_eligible_count}`",
        f"- Held count: `{report.held_count}`",
        *[f"- {i.work_item_key}: {i.provenance_state} [{i.chronic_origin_restoration_path}]" for i in report.items],
        '',
    ],
    )
    return report


__all__ = [
    'OracleOperatorChronicOriginRestorationProvenance',
    'OracleOperatorChronicOriginRestorationProvenanceItem',
    'OracleOperatorChronicOriginRestorationProvenanceRequest',
    'build_operator_chronic_origin_restoration_provenance_request',
    'materialize_operator_chronic_origin_restoration_provenance',
]
