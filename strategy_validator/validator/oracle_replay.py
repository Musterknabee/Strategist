from __future__ import annotations

import hashlib
import json
from pathlib import Path

from strategy_validator.contracts.oracle_operator_reports import (
    OracleCompactedStateInspectionReport,
    OracleCompactedStateRebuildReport,
    OracleReplayAuditReport,
    OracleReplayAuditSource,
)
from strategy_validator.contracts.oracle_evidence_events import (
    OracleDerivedViewCheckpointMetadata,
    OracleDerivedViewReport,
    OracleEventCheckpointManifest,
    OracleEventCheckpointVerification,
    OracleEventLogEntry,
)
from strategy_validator.validator.oracle_event_log import (
    _iter_jsonl_models_with_offsets,
    generate_oracle_derived_view,
    query_oracle_event_log,
    write_oracle_derived_view_checkpoint_metadata,
)
from strategy_validator.validator.oracle_schema_registry import validate_registered_schema
from strategy_validator.validator.oracle_transition_common import _utc_now


def _load_schema_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_registered_schema(payload, expected_families={"oracle"})
    return payload


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_oracle_checkpoint_metadata(path: Path) -> OracleDerivedViewCheckpointMetadata:
    return OracleDerivedViewCheckpointMetadata.model_validate(_load_schema_json(path))


def _sha256_json(payload: object) -> str:
    stable = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(stable).hexdigest()


def _window_digest(rows: list[OracleEventLogEntry]) -> str:
    return _sha256_json([row.model_dump(mode="json") for row in rows])


def _normalized_query_spec(metadata: OracleDerivedViewCheckpointMetadata):
    return metadata.query_spec.model_copy(update={"max_entries": metadata.window_size})


def _build_checkpoint_metadata_from_truth(
    *,
    lane_path: Path,
    metadata_template: OracleDerivedViewCheckpointMetadata,
) -> OracleDerivedViewCheckpointMetadata:
    rows, _ = query_oracle_event_log(
        lane_path=lane_path,
        query_spec=_normalized_query_spec(metadata_template),
        checkpoint_metadata_path=None,
        view_label=metadata_template.view_label,
    )
    current_file_size = lane_path.stat().st_size if lane_path.exists() else 0
    last_sequence = None
    last_hash = None
    last_offset = 0
    for row, next_offset in _iter_jsonl_models_with_offsets(lane_path):
        last_sequence = row.sequence_number
        last_hash = row.entry_hash
        last_offset = next_offset
    return OracleDerivedViewCheckpointMetadata(
        generated_at_utc=_utc_now(),
        lane_id=lane_path.stem,
        view_label=metadata_template.view_label,
        window_size=metadata_template.window_size,
        source_event_log_path=str(lane_path.resolve()),
        query_spec=_normalized_query_spec(metadata_template),
        file_size_bytes=current_file_size,
        file_offset_bytes=last_offset,
        last_event_log_sequence_number=last_sequence,
        last_event_log_entry_hash=last_hash,
        cached_window_entries=list(rows[-metadata_template.window_size:]),
        summary_line=f"Rebuilt {metadata_template.view_label} checkpoint metadata from canonical Event Log truth.",
    )


def inspect_oracle_compacted_state(*, lane_path: Path, checkpoint_metadata_path: Path) -> OracleCompactedStateInspectionReport:
    metadata = load_oracle_checkpoint_metadata(checkpoint_metadata_path)
    current_file_size = lane_path.stat().st_size if lane_path.exists() else 0
    findings: list[str] = []
    operator_actions: list[str] = []

    if not lane_path.exists():
        replay_status = "SOURCE_MISSING"
        findings.append("canonical Oracle Event Log path is missing from disk")
        operator_actions.append("restore the canonical Oracle Event Log before relying on compacted checkpoint state")
    elif metadata.source_event_log_path != str(lane_path.resolve()):
        replay_status = "CORRUPTED"
        findings.append("checkpoint metadata source_event_log_path does not match the requested canonical Event Log")
        operator_actions.append("rebuild checkpoint metadata against the canonical Oracle Event Log")
    elif metadata.file_offset_bytes > current_file_size:
        replay_status = "CORRUPTED"
        findings.append("checkpoint metadata offset exceeds current Event Log size")
        operator_actions.append("discard and rebuild compacted checkpoint metadata from canonical Event Log truth")
    elif current_file_size > metadata.file_offset_bytes:
        replay_status = "STALE"
        findings.append("canonical Event Log has grown beyond the compacted checkpoint offset")
        operator_actions.append("refresh compacted checkpoint metadata before relying on replay state")
    else:
        replay_status = "CURRENT"
        findings.append("checkpoint metadata offset is current with the canonical Event Log")
        operator_actions.append("continue using compacted checkpoint state for operator inspection")

    summary_line = (
        f"Compacted checkpoint `{checkpoint_metadata_path.name}` is {replay_status.lower()} "
        f"against `{lane_path.name}` with {len(metadata.cached_window_entries)} cached entries."
    )
    return OracleCompactedStateInspectionReport(
        generated_at_utc=_utc_now(),
        lane_path=str(lane_path.resolve()),
        checkpoint_metadata_path=str(checkpoint_metadata_path.resolve()),
        view_label=metadata.view_label,
        source_event_log_path=metadata.source_event_log_path,
        replay_status=replay_status,
        current_file_size_bytes=current_file_size,
        metadata_file_size_bytes=metadata.file_size_bytes,
        metadata_file_offset_bytes=metadata.file_offset_bytes,
        last_event_log_sequence_number=metadata.last_event_log_sequence_number,
        last_event_log_entry_hash=metadata.last_event_log_entry_hash,
        cached_window_entry_count=len(metadata.cached_window_entries),
        cached_window_entry_ids=[row.entry_id for row in metadata.cached_window_entries],
        query_spec=metadata.query_spec,
        compacted_window_digest_sha256=_window_digest(metadata.cached_window_entries),
        summary_line=summary_line,
        findings=findings,
        operator_actions=operator_actions,
    )


def _resolve_subject_path(base_path: Path, subject_path: str) -> Path:
    candidate = Path(subject_path)
    if candidate.is_absolute():
        return candidate
    for parent in (base_path.parent, *base_path.parents):
        resolved = (parent / candidate).resolve()
        if resolved.exists():
            return resolved
    return (base_path.parent / candidate).resolve()


def _audit_manifest(
    *,
    manifest_path: Path | None,
    verification_path: Path | None,
    metadata_path: Path,
    canonical_rows: list[OracleEventLogEntry],
    view_label: str,
) -> tuple[list[OracleReplayAuditSource], list[str], str | None]:
    sources: list[OracleReplayAuditSource] = []
    findings: list[str] = []
    report_path: str | None = None

    if manifest_path is None:
        sources.append(
            OracleReplayAuditSource(
                source_id="checkpoint_manifest",
                status="SKIPPED",
                summary_line="No checkpoint manifest provided for replay audit.",
            )
        )
    else:
        manifest_payload = _load_schema_json(manifest_path)
        manifest = OracleEventCheckpointManifest.model_validate(manifest_payload)
        details: list[str] = []
        status = "CONSISTENT"
        report_subject = next(
            (
                _resolve_subject_path(manifest_path, subject.path)
                for subject in manifest.subjects
                if Path(subject.path).suffix == ".json" and Path(subject.path).name != metadata_path.name
            ),
            None,
        )
        if report_subject is None:
            status = "DRIFTED"
            findings.append("checkpoint manifest is missing the derived view report subject")
        else:
            report_path = str(report_subject)
            details.append(f"report_path={report_path}")
        if manifest.view_label != view_label:
            status = "DRIFTED"
            findings.append("checkpoint manifest view_label does not match checkpoint metadata")
            details.append(f"view_label={manifest.view_label}")
        if manifest.window_entry_count != len(canonical_rows):
            status = "DRIFTED"
            findings.append("checkpoint manifest window_entry_count does not match canonical replay window")
            details.append(f"window_entry_count={manifest.window_entry_count}")
        canonical_last_hash = canonical_rows[-1].entry_hash if canonical_rows else None
        if manifest.last_entry_hash != canonical_last_hash:
            status = "DRIFTED"
            findings.append("checkpoint manifest last_entry_hash does not match canonical replay window")
            details.append(f"last_entry_hash={manifest.last_entry_hash}")
        metadata_subject_names = {Path(subject.path).name for subject in manifest.subjects}
        if metadata_path.name not in metadata_subject_names:
            status = "DRIFTED"
            findings.append("checkpoint manifest is missing the checkpoint metadata sidecar subject")
        sources.append(
            OracleReplayAuditSource(
                source_id="checkpoint_manifest",
                status=status,
                summary_line=f"Checkpoint manifest is {status.lower()} against canonical replay.",
                details=details,
            )
        )

    if verification_path is None:
        sources.append(
            OracleReplayAuditSource(
                source_id="checkpoint_verification",
                status="SKIPPED",
                summary_line="No checkpoint verification payload provided for replay audit.",
            )
        )
    else:
        verification_payload = _load_json(verification_path)
        verification = OracleEventCheckpointVerification.model_validate(verification_payload)
        if verification.status == "VERIFIED":
            status = "CONSISTENT"
            details = [f"verified_subject_count={verification.verified_subject_count}"]
        else:
            status = "CORRUPTED"
            details = [
                f"missing={','.join(verification.missing_artifact_paths) if verification.missing_artifact_paths else 'none'}",
                f"digest_mismatches={','.join(verification.digest_mismatches) if verification.digest_mismatches else 'none'}",
            ]
            findings.append("checkpoint verification payload is not VERIFIED")
        sources.append(
            OracleReplayAuditSource(
                source_id="checkpoint_verification",
                status=status,
                summary_line=f"Checkpoint verification payload is {verification.status.lower()}.",
                details=details,
            )
        )
    return sources, findings, report_path


def _audit_derived_view_report(
    *,
    report_path: Path,
    lane_path: Path,
    metadata_template: OracleDerivedViewCheckpointMetadata,
) -> tuple[OracleReplayAuditSource, list[str]]:
    findings: list[str] = []
    if not report_path.exists():
        findings.append("derived view report referenced by the checkpoint manifest is missing")
        return (
            OracleReplayAuditSource(
                source_id="derived_view_report",
                status="CORRUPTED",
                summary_line="Derived view report is missing from the checkpoint bundle.",
                details=[f"report_path={report_path}"],
            ),
            findings,
        )

    payload = _load_schema_json(report_path)
    if payload.get("schema_version") != "oracle_derived_view_report/v1":
        findings.append("derived view report subject is not an oracle_derived_view_report/v1 artifact")
        return (
            OracleReplayAuditSource(
                source_id="derived_view_report",
                status="DRIFTED",
                summary_line="Derived view report subject uses an unexpected schema.",
                details=[f"schema_version={payload.get('schema_version', 'unknown')}", f"report_path={report_path}"],
            ),
            findings,
        )

    reported = OracleDerivedViewReport.model_validate(payload)
    expected = generate_oracle_derived_view(
        lane_path=lane_path,
        view_label=metadata_template.view_label,
        window_size=metadata_template.window_size,
        query_spec=_normalized_query_spec(metadata_template),
        checkpoint_metadata_path=None,
    )
    details: list[str] = [f"report_path={report_path}"]
    mismatches: list[str] = []
    fields = [
        "view_label",
        "window_entry_count",
        "window_start_sequence_number",
        "window_end_sequence_number",
        "latest_event_id",
        "latest_dominant_regime",
        "latest_global_action",
        "latest_epistemic_status",
        "derived_classification",
        "evidence_gap_count",
        "elevated_or_unknown_count",
        "defensive_posture_count",
        "retrain_pressure_count",
        "average_posterior_edge_confidence",
        "summary_line",
    ]
    for field in fields:
        if getattr(reported, field) != getattr(expected, field):
            mismatches.append(f"{field}={getattr(reported, field)!r} expected {getattr(expected, field)!r}")
    if reported.observed_entry_ids != expected.observed_entry_ids:
        mismatches.append(
            f"observed_entry_ids={reported.observed_entry_ids!r} expected {expected.observed_entry_ids!r}"
        )
    if reported.operator_actions != expected.operator_actions:
        mismatches.append(
            f"operator_actions={reported.operator_actions!r} expected {expected.operator_actions!r}"
        )
    if mismatches:
        findings.append("derived view report does not match deterministic replay from the canonical Event Log")
        details.extend(mismatches[:8])
        status = "DRIFTED"
        summary_line = "Derived view report drifted from deterministic replay of the canonical Event Log."
    else:
        status = "CONSISTENT"
        summary_line = "Derived view report matches deterministic replay from the canonical Event Log."
    return (
        OracleReplayAuditSource(
            source_id="derived_view_report",
            status=status,
            summary_line=summary_line,
            details=details,
        ),
        findings,
    )


def audit_oracle_replay(
    *,
    lane_path: Path,
    checkpoint_metadata_path: Path,
    checkpoint_manifest_path: Path | None = None,
    checkpoint_verification_path: Path | None = None,
    rebuild_parity: bool = False,
) -> OracleReplayAuditReport:
    inspection = inspect_oracle_compacted_state(lane_path=lane_path, checkpoint_metadata_path=checkpoint_metadata_path)
    metadata = load_oracle_checkpoint_metadata(checkpoint_metadata_path)

    if inspection.replay_status == "SOURCE_MISSING":
        return OracleReplayAuditReport(
            generated_at_utc=_utc_now(),
            lane_path=str(lane_path.resolve()),
            checkpoint_metadata_path=str(checkpoint_metadata_path.resolve()),
            checkpoint_manifest_path=str(checkpoint_manifest_path.resolve()) if checkpoint_manifest_path else None,
            checkpoint_verification_path=str(checkpoint_verification_path.resolve()) if checkpoint_verification_path else None,
            replay_status="SOURCE_MISSING",
            compacted_window_digest_sha256=inspection.compacted_window_digest_sha256,
            rebuilt_window_digest_sha256="",
            findings=list(inspection.findings),
            operator_actions=list(inspection.operator_actions),
            sources=[
                OracleReplayAuditSource(
                    source_id="checkpoint_metadata",
                    status="CORRUPTED",
                    summary_line="Checkpoint metadata cannot be trusted because the canonical Event Log is missing.",
                    details=list(inspection.findings),
                )
            ],
            summary_line="Replay audit could not proceed because the canonical Oracle Event Log is missing.",
        )

    canonical_rows, _ = query_oracle_event_log(
        lane_path=lane_path,
        query_spec=_normalized_query_spec(metadata),
        checkpoint_metadata_path=None,
        view_label=metadata.view_label,
    )
    canonical_window = canonical_rows[-metadata.window_size:]
    canonical_digest = _window_digest(canonical_window)
    compacted_digest = _window_digest(metadata.cached_window_entries)

    findings: list[str] = []
    operator_actions: list[str] = []
    metadata_status = "CONSISTENT"
    metadata_details = [f"window_entries={len(metadata.cached_window_entries)}", f"offset={metadata.file_offset_bytes}"]

    if inspection.replay_status == "CORRUPTED":
        metadata_status = "CORRUPTED"
        findings.extend(inspection.findings)
        operator_actions.extend(inspection.operator_actions)
    elif canonical_digest != compacted_digest:
        metadata_status = "STALE" if inspection.replay_status == "STALE" else "DRIFTED"
        findings.append("cached checkpoint window does not match canonical Event Log replay")
        operator_actions.append("rebuild compacted checkpoint metadata and regenerate derived checkpoint artifacts")
    elif inspection.replay_status == "STALE":
        metadata_status = "STALE"
        findings.extend(inspection.findings)
        operator_actions.extend(inspection.operator_actions)

    sources = [
        OracleReplayAuditSource(
            source_id="canonical_event_log",
            status="CONSISTENT",
            summary_line="Canonical Event Log replay completed successfully.",
            details=[f"window_entries={len(canonical_window)}", f"window_digest={canonical_digest}"],
        ),
        OracleReplayAuditSource(
            source_id="checkpoint_metadata",
            status=metadata_status,
            summary_line=f"Checkpoint metadata is {metadata_status.lower()} against canonical replay.",
            details=metadata_details + [f"window_digest={compacted_digest}"],
        ),
    ]

    manifest_sources, manifest_findings, report_path = _audit_manifest(
        manifest_path=checkpoint_manifest_path,
        verification_path=checkpoint_verification_path,
        metadata_path=checkpoint_metadata_path,
        canonical_rows=canonical_window,
        view_label=metadata.view_label,
    )
    sources.extend(manifest_sources)
    findings.extend(manifest_findings)

    rebuilt_digest = ""
    if rebuild_parity:
        rebuilt_metadata = _build_checkpoint_metadata_from_truth(lane_path=lane_path, metadata_template=metadata)
        rebuilt_digest = _window_digest(rebuilt_metadata.cached_window_entries)
        rebuilt_status = "CONSISTENT"
        rebuilt_details = [f"window_entries={len(rebuilt_metadata.cached_window_entries)}", f"window_digest={rebuilt_digest}"]
        if rebuilt_digest != canonical_digest:
            rebuilt_status = "CORRUPTED"
            findings.append("rebuilt checkpoint metadata does not match deterministic replay from the canonical Event Log")
            operator_actions.append("repair replay logic before relying on rebuilt compacted checkpoint state")
        elif rebuilt_digest != compacted_digest:
            rebuilt_status = "DRIFTED"
            findings.append("stored checkpoint metadata does not match a fresh deterministic rebuild from canonical Event Log truth")
            operator_actions.append("rewrite compacted checkpoint metadata from canonical Event Log truth")
        sources.append(
            OracleReplayAuditSource(
                source_id="rebuilt_checkpoint_metadata",
                status=rebuilt_status,
                summary_line=f"Freshly rebuilt checkpoint metadata is {rebuilt_status.lower()} against the stored compacted state.",
                details=rebuilt_details,
            )
        )
    else:
        sources.append(
            OracleReplayAuditSource(
                source_id="rebuilt_checkpoint_metadata",
                status="SKIPPED",
                summary_line="Deterministic rebuild parity was not requested.",
            )
        )

    if report_path is not None:
        report_source, report_findings = _audit_derived_view_report(
            report_path=Path(report_path),
            lane_path=lane_path,
            metadata_template=metadata,
        )
        sources.append(report_source)
        findings.extend(report_findings)
        if report_source.status != "CONSISTENT":
            operator_actions.append("re-emit the canonical derived view report from Event Log truth before relying on checkpoint bundles")
    else:
        sources.append(
            OracleReplayAuditSource(
                source_id="derived_view_report",
                status="SKIPPED",
                summary_line="No derived view report was available for deterministic replay comparison.",
            )
        )

    status_order = [source.status for source in sources if source.status != "SKIPPED"]
    if "CORRUPTED" in status_order:
        replay_status = "CORRUPTED"
    elif "DRIFTED" in status_order:
        replay_status = "DRIFTED"
    elif "STALE" in status_order:
        replay_status = "STALE"
    else:
        replay_status = "CONSISTENT"

    if replay_status == "CONSISTENT":
        operator_actions.append("continue using compacted checkpoint and checkpoint bundle surfaces")
        summary_line = "Replay audit is consistent across canonical replay, compacted state, and deterministic bundle surfaces."
    elif replay_status == "STALE":
        summary_line = "Replay audit detected stale compacted state relative to the canonical Event Log."
    elif replay_status == "DRIFTED":
        summary_line = "Replay audit detected drift between canonical Event Log replay and compacted/checkpoint artifacts."
    else:
        summary_line = "Replay audit detected corruption in compacted/checkpoint artifacts."

    return OracleReplayAuditReport(
        generated_at_utc=_utc_now(),
        lane_path=str(lane_path.resolve()),
        checkpoint_metadata_path=str(checkpoint_metadata_path.resolve()),
        report_path=report_path,
        checkpoint_manifest_path=str(checkpoint_manifest_path.resolve()) if checkpoint_manifest_path else None,
        checkpoint_verification_path=str(checkpoint_verification_path.resolve()) if checkpoint_verification_path else None,
        replay_status=replay_status,
        canonical_window_digest_sha256=canonical_digest,
        compacted_window_digest_sha256=compacted_digest,
        rebuilt_window_digest_sha256=rebuilt_digest,
        compared_entry_ids=[row.entry_id for row in canonical_window],
        findings=sorted(set(findings)),
        operator_actions=sorted(set(operator_actions)) if operator_actions else [],
        sources=sources,
        summary_line=summary_line,
    )



def rebuild_oracle_compacted_state(*, lane_path: Path, checkpoint_metadata_path: Path) -> OracleCompactedStateRebuildReport:
    previous_metadata_found = checkpoint_metadata_path.exists()
    previous_replay_status = None
    findings: list[str] = []
    if previous_metadata_found:
        previous_inspection = inspect_oracle_compacted_state(lane_path=lane_path, checkpoint_metadata_path=checkpoint_metadata_path)
        previous_replay_status = previous_inspection.replay_status
        findings.extend(previous_inspection.findings)
        metadata = load_oracle_checkpoint_metadata(checkpoint_metadata_path)
    else:
        raise FileNotFoundError(f"checkpoint metadata path `{checkpoint_metadata_path}` does not exist")

    rebuilt_metadata = _build_checkpoint_metadata_from_truth(lane_path=lane_path, metadata_template=metadata)
    write_oracle_derived_view_checkpoint_metadata(checkpoint_metadata_path, rebuilt_metadata)

    operator_actions = [
        "re-run compacted-state inspection or replay audit to confirm the rebuilt checkpoint is current",
        "regenerate any derived checkpoint bundles that depended on the previous compacted state",
    ]
    summary_line = (
        f"Rebuilt compacted checkpoint `{checkpoint_metadata_path.name}` from canonical Event Log truth "
        f"with {len(rebuilt_metadata.cached_window_entries)} cached entries."
    )
    return OracleCompactedStateRebuildReport(
        generated_at_utc=_utc_now(),
        lane_path=str(lane_path.resolve()),
        checkpoint_metadata_path=str(checkpoint_metadata_path.resolve()),
        source_event_log_path=str(lane_path.resolve()),
        view_label=metadata.view_label,
        previous_replay_status=previous_replay_status,
        previous_metadata_found=previous_metadata_found,
        rebuilt_window_entry_count=len(rebuilt_metadata.cached_window_entries),
        rebuilt_entry_ids=[row.entry_id for row in rebuilt_metadata.cached_window_entries],
        rebuilt_file_offset_bytes=rebuilt_metadata.file_offset_bytes,
        rebuilt_last_event_log_sequence_number=rebuilt_metadata.last_event_log_sequence_number,
        rebuilt_last_event_log_entry_hash=rebuilt_metadata.last_event_log_entry_hash,
        compacted_window_digest_sha256=_window_digest(rebuilt_metadata.cached_window_entries),
        summary_line=summary_line,
        findings=sorted(set(findings)),
        operator_actions=operator_actions,
    )

from strategy_validator.validator.oracle_replay_rendering import (
    render_oracle_compacted_state_inspection_markdown,
    render_oracle_compacted_state_rebuild_markdown,
    render_oracle_replay_audit_markdown,
)
