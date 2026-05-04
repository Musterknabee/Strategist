from __future__ import annotations

import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

from strategy_validator.contracts.operational import DsseEnvelope
from strategy_validator.contracts.oracle_evidence_events import (
    OracleDerivedViewCheckpointMetadata,
    OracleDerivedViewReport,
    OracleEventCheckpointManifest,
    OracleEventCheckpointVerification,
    OracleEventLogEntry,
    OracleEventLogQuerySpec,
    OracleEvidenceManifest,
    OracleEvidenceVerification,
)
from strategy_validator.contracts.oracle_core import (
    OracleDerivedViewClassification,
    OracleMorningAttestation,
)
from strategy_validator.validator.oracle_schema_registry import validate_registered_schema
from strategy_validator.validator.oracle_advisory import (
    _artifact_descriptor,
    _json_canonical_bytes,
    _resolve_existing_path,
    _sha256_bytes,
    _sha256_file,
    _sign_dsse_payload,
    _verify_dsse_envelope,
)

from strategy_validator.validator.oracle_event_log_rendering import (
    render_oracle_derived_view_markdown,
    render_oracle_event_checkpoint_markdown,
    render_oracle_rolling_review_markdown,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


ORACLE_HORIZON_WINDOW_DEFAULTS: dict[str, int] = {
    "weekly": 7,
    "monthly": 28,
    "quarterly": 90,
    "semiannual": 180,
    "annual": 365,
    "constitutional": 1095,
    "rolling": 7,
}


def resolve_oracle_horizon_window(*, horizon: str, window_size: int | None = None) -> tuple[str, int]:
    normalized = horizon.strip().lower().replace("_", "-").replace(" ", "-")
    normalized = {
        "semi-annual": "semiannual",
    }.get(normalized, normalized)
    if normalized not in ORACLE_HORIZON_WINDOW_DEFAULTS:
        supported = ", ".join(sorted(ORACLE_HORIZON_WINDOW_DEFAULTS))
        raise ValueError(f"unsupported oracle horizon '{horizon}'; supported horizons: {supported}")
    resolved_window = window_size if window_size is not None else ORACLE_HORIZON_WINDOW_DEFAULTS[normalized]
    if resolved_window <= 0:
        raise ValueError("window_size must be positive")
    return normalized, resolved_window


def generate_oracle_horizon_view(
    *,
    lane_path: Path,
    horizon: str,
    window_size: int | None = None,
    checkpoint_metadata_path: Path | None = None,
) -> OracleDerivedViewReport:
    resolved_horizon, resolved_window = resolve_oracle_horizon_window(horizon=horizon, window_size=window_size)
    return generate_oracle_derived_view(
        lane_path=lane_path,
        view_label=resolved_horizon,
        window_size=resolved_window,
        checkpoint_metadata_path=checkpoint_metadata_path,
    )


def generate_oracle_rolling_review(
    *,
    lane_path: Path,
    horizon: str = "weekly",
    window_size: int | None = None,
    checkpoint_metadata_path: Path | None = None,
) -> OracleDerivedViewReport:
    """Preferred converged review path: derive a posture review directly from the canonical Oracle Event Log."""
    return generate_oracle_horizon_view(
        lane_path=lane_path,
        horizon=horizon,
        window_size=window_size,
        checkpoint_metadata_path=checkpoint_metadata_path,
    )


def legacy_compatibility_banner(*, legacy_surface: str, preferred_surface: str = "oracle-rolling-review / oracle-horizon-view on the canonical Oracle Event Log") -> str:
    return "\n".join([
        "> [!WARNING]",
        f"> Legacy compatibility surface: `{legacy_surface}`.",
        f"> Preferred converged surface: `{preferred_surface}`.",
        "> Direct legacy lane reads require explicit operator opt-in via `--allow-legacy-lane-read`.",
        "> This output remains supported for replay and migration, but it is no longer the architectural default.",
        "",
    ])


def _load_oracle_evidence_manifest(path: Path) -> OracleEvidenceManifest:
    return OracleEvidenceManifest.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _find_attestation_path(*, manifest: OracleEvidenceManifest, manifest_path: Path, repo_root: Path) -> Path:
    for subject in manifest.subjects:
        if subject.name == "ORACLE_MORNING_ATTESTATION.json":
            resolved = _resolve_existing_path(subject.path, repo_root=repo_root, preferred_parent=manifest_path.parent)
            if resolved is not None:
                return resolved
            raise FileNotFoundError(f"oracle attestation subject missing from evidence chain: {subject.path}")
    raise FileNotFoundError("oracle evidence manifest does not include ORACLE_MORNING_ATTESTATION.json")


def _load_attestation(*, manifest: OracleEvidenceManifest, manifest_path: Path, repo_root: Path) -> OracleMorningAttestation:
    attestation_path = _find_attestation_path(manifest=manifest, manifest_path=manifest_path, repo_root=repo_root)
    return OracleMorningAttestation.model_validate(json.loads(attestation_path.read_text(encoding="utf-8")))


def _canonical_entry_hash_payload(entry: dict) -> bytes:
    filtered = {key: value for key, value in entry.items() if key != "entry_hash"}
    return _json_canonical_bytes(filtered)


def _iter_jsonl_models_with_offsets(path: Path, *, start_offset: int = 0) -> Iterator[tuple[OracleEventLogEntry, int]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        handle.seek(start_offset)
        while True:
            line = handle.readline()
            if not line:
                break
            raw = line.strip()
            if not raw:
                continue
            payload = json.loads(raw)
            validate_registered_schema(payload, expected_families={"oracle"})
            yield OracleEventLogEntry.model_validate(payload), handle.tell()


def _read_jsonl_models(path: Path) -> list[OracleEventLogEntry]:
    if not path.exists():
        return []
    return [row for row, _ in _iter_jsonl_models_with_offsets(path)]


def _default_query_spec(*, max_entries: int | None = None) -> OracleEventLogQuerySpec:
    return OracleEventLogQuerySpec(max_entries=max_entries)


def _entry_matches_query(row: OracleEventLogEntry, query_spec: OracleEventLogQuerySpec) -> bool:
    if query_spec.start_input_timestamp_utc is not None and row.input_timestamp_utc < query_spec.start_input_timestamp_utc:
        return False
    if query_spec.end_input_timestamp_utc is not None and row.input_timestamp_utc > query_spec.end_input_timestamp_utc:
        return False
    if query_spec.strategy_ids and not any(strategy_id in set(row.strategy_ids) for strategy_id in query_spec.strategy_ids):
        return False
    if query_spec.dominant_regimes and row.dominant_regime not in set(query_spec.dominant_regimes):
        return False
    if query_spec.epistemic_statuses and row.epistemic_status not in set(query_spec.epistemic_statuses):
        return False
    return True


def _load_checkpoint_metadata(path: Path | None) -> OracleDerivedViewCheckpointMetadata | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_registered_schema(payload, expected_families={"oracle"})
    return OracleDerivedViewCheckpointMetadata.model_validate(payload)


def _checkpoint_compatible(
    metadata: OracleDerivedViewCheckpointMetadata | None,
    *,
    lane_path: Path,
    view_label: str,
    window_size: int,
    query_spec: OracleEventLogQuerySpec,
) -> bool:
    if metadata is None:
        return False
    if metadata.lane_id != lane_path.stem:
        return False
    if metadata.view_label != view_label:
        return False
    if metadata.window_size != window_size:
        return False
    expected_source = str(lane_path.resolve())
    if metadata.source_event_log_path != expected_source:
        return False
    return metadata.query_spec.model_dump(mode="json") == query_spec.model_dump(mode="json")


def write_oracle_derived_view_checkpoint_metadata(path: Path, metadata: OracleDerivedViewCheckpointMetadata) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata.model_dump(mode="json"), indent=2, default=str) + "\n", encoding="utf-8")


def query_oracle_event_log(
    *,
    lane_path: Path,
    query_spec: OracleEventLogQuerySpec | None = None,
    checkpoint_metadata_path: Path | None = None,
    view_label: str = "rolling",
) -> tuple[list[OracleEventLogEntry], OracleDerivedViewCheckpointMetadata | None]:
    spec = query_spec or _default_query_spec()
    max_entries = spec.max_entries
    if max_entries is not None and max_entries <= 0:
        raise ValueError("max_entries must be positive")

    current_size = lane_path.stat().st_size if lane_path.exists() else 0
    existing_metadata = _load_checkpoint_metadata(checkpoint_metadata_path)
    if (
        checkpoint_metadata_path is not None
        and _checkpoint_compatible(existing_metadata, lane_path=lane_path, view_label=view_label, window_size=max_entries or 1, query_spec=spec)
        and current_size >= existing_metadata.file_offset_bytes
    ):
        window = deque(existing_metadata.cached_window_entries, maxlen=max_entries or None)
        last_sequence = existing_metadata.last_event_log_sequence_number
        last_hash = existing_metadata.last_event_log_entry_hash
        last_offset = existing_metadata.file_offset_bytes
        for row, next_offset in _iter_jsonl_models_with_offsets(lane_path, start_offset=last_offset):
            if last_sequence is not None and row.sequence_number <= last_sequence:
                continue
            if _entry_matches_query(row, spec):
                window.append(row)
            last_sequence = row.sequence_number
            last_hash = row.entry_hash
            last_offset = next_offset
        metadata = OracleDerivedViewCheckpointMetadata(
            generated_at_utc=_utc_now(),
            lane_id=lane_path.stem,
            view_label=view_label,
            window_size=max_entries or max(1, existing_metadata.window_size),
            source_event_log_path=str(lane_path.resolve()),
            query_spec=spec,
            file_size_bytes=current_size,
            file_offset_bytes=last_offset,
            last_event_log_sequence_number=last_sequence,
            last_event_log_entry_hash=last_hash,
            cached_window_entries=list(window),
            summary_line=f"Incrementally refreshed {view_label} checkpoint metadata from byte offset {existing_metadata.file_offset_bytes} to {last_offset}.",
        )
        write_oracle_derived_view_checkpoint_metadata(checkpoint_metadata_path, metadata)
        return list(window), metadata

    window = deque(maxlen=max_entries or None)
    last_sequence: int | None = None
    last_hash: str | None = None
    last_offset = 0
    for row, next_offset in _iter_jsonl_models_with_offsets(lane_path):
        if _entry_matches_query(row, spec):
            window.append(row)
        last_sequence = row.sequence_number
        last_hash = row.entry_hash
        last_offset = next_offset
    metadata = None
    if checkpoint_metadata_path is not None:
        metadata = OracleDerivedViewCheckpointMetadata(
            generated_at_utc=_utc_now(),
            lane_id=lane_path.stem,
            view_label=view_label,
            window_size=max_entries or max(1, len(window) or ORACLE_HORIZON_WINDOW_DEFAULTS.get(view_label, 1)),
            source_event_log_path=str(lane_path.resolve()),
            query_spec=spec,
            file_size_bytes=current_size,
            file_offset_bytes=last_offset,
            last_event_log_sequence_number=last_sequence,
            last_event_log_entry_hash=last_hash,
            cached_window_entries=list(window),
            summary_line=f"Built {view_label} checkpoint metadata from the canonical Oracle Event Log.",
        )
        write_oracle_derived_view_checkpoint_metadata(checkpoint_metadata_path, metadata)
    return list(window), metadata


def append_oracle_event_log(
    *,
    manifest_path: Path,
    verification: OracleEvidenceVerification,
    lane_path: Path,
    repo_root: Path | None = None,
) -> OracleEventLogEntry:
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest_path = manifest_path.resolve()
    if verification.status != "VERIFIED":
        raise ValueError("oracle event log append requires VERIFIED oracle evidence")
    manifest = _load_oracle_evidence_manifest(manifest_path)
    attestation = _load_attestation(manifest=manifest, manifest_path=manifest_path, repo_root=repo_root)
    existing = _read_jsonl_models(lane_path)
    sequence_number = len(existing)
    previous_entry_hash = existing[-1].entry_hash if existing else None
    strategy_ids = sorted({advisory.strategy_id for advisory in attestation.strategy_advisories})
    maintain_count = sum(1 for advisory in attestation.strategy_advisories if advisory.action == "MAINTAIN")
    canary_count = sum(1 for advisory in attestation.strategy_advisories if advisory.action == "CANARY")
    hibernate_count = sum(1 for advisory in attestation.strategy_advisories if advisory.action == "HIBERNATE")
    confidence_values = [advisory.posterior_edge_confidence for advisory in attestation.strategy_advisories]
    avg_conf = sum(confidence_values) / len(confidence_values) if confidence_values else 1.0
    payload = {
        "schema_version": "oracle_event_log_entry/v1",
        "appended_at_utc": _utc_now().isoformat(),
        "lane_id": lane_path.stem,
        "sequence_number": sequence_number,
        "entry_id": f"{manifest.evidence_id}:{sequence_number}",
        "evidence_id": manifest.evidence_id,
        "previous_entry_hash": previous_entry_hash,
        "manifest_path": str(manifest_path.relative_to(repo_root)) if manifest_path.is_relative_to(repo_root) else str(manifest_path),
        "manifest_sha256": _sha256_file(manifest_path),
        "linked_closure_id": manifest.linked_closure_id,
        "input_timestamp_utc": manifest.input_timestamp_utc.isoformat(),
        "dominant_regime": manifest.dominant_regime,
        "recommended_global_action": manifest.recommended_global_action,
        "epistemic_status": manifest.epistemic_status,
        "average_posterior_edge_confidence": round(avg_conf, 6),
        "maintain_count": maintain_count,
        "canary_count": canary_count,
        "hibernate_count": hibernate_count,
        "strategy_ids": strategy_ids,
        "evidence_status": verification.status,
        "summary_line": manifest.summary_line,
    }
    payload["entry_hash"] = _sha256_bytes(_canonical_entry_hash_payload(payload))
    entry = OracleEventLogEntry.model_validate(payload)
    lane_path.parent.mkdir(parents=True, exist_ok=True)
    with lane_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry.model_dump(mode="json"), separators=(",", ":"), default=str) + "\n")
    return entry


def _count(items: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts


def generate_oracle_derived_view(
    *,
    lane_path: Path,
    view_label: str,
    window_size: int = 7,
    query_spec: OracleEventLogQuerySpec | None = None,
    checkpoint_metadata_path: Path | None = None,
) -> OracleDerivedViewReport:
    if window_size <= 0:
        raise ValueError("window_size must be positive")
    spec = query_spec or _default_query_spec(max_entries=window_size)
    if spec.max_entries is None:
        spec = OracleEventLogQuerySpec(**{**spec.model_dump(mode="json"), "max_entries": window_size})
    rows, _ = query_oracle_event_log(
        lane_path=lane_path,
        query_spec=spec,
        checkpoint_metadata_path=checkpoint_metadata_path,
        view_label=view_label,
    )
    window = rows[-window_size:] if rows else []
    latest = window[-1] if window else None
    evidence_gap_count = sum(1 for row in window if row.evidence_status != "VERIFIED")
    elevated_or_unknown_count = sum(1 for row in window if row.epistemic_status in {"ELEVATED", "UNKNOWN_UNKNOWNS"})
    defensive_posture_count = sum(1 for row in window if row.recommended_global_action == "DEFENSIVE_POSTURE")
    retrain_pressure_count = sum(
        1
        for row in window
        if row.hibernate_count > 0 or row.canary_count > row.maintain_count or row.average_posterior_edge_confidence < 0.55
    )
    avg_conf = round(sum(row.average_posterior_edge_confidence for row in window) / len(window), 6) if window else 0.0
    if evidence_gap_count > 0:
        classification: OracleDerivedViewClassification = "EVIDENCE_GAP"
        operator_actions = ["Repair missing or unverifiable oracle evidence before relying on derived views."]
    elif latest and (latest.epistemic_status == "UNKNOWN_UNKNOWNS" or latest.recommended_global_action == "DEFENSIVE_POSTURE" or defensive_posture_count >= max(1, len(window) // 2)):
        classification = "DEFENSIVE_POSTURE"
        operator_actions = ["Treat the oracle as defensive and avoid escalating authority."]
    elif latest and (retrain_pressure_count >= max(1, len(window) // 2) or latest.hibernate_count > 0 or avg_conf < 0.45):
        classification = "RETRAIN_REVIEW"
        operator_actions = ["Review strategy-health degradation and queue retrain investigation."]
    elif latest and (latest.epistemic_status == "ELEVATED" or latest.recommended_global_action == "CANARY_REVIEW" or elevated_or_unknown_count > 0):
        classification = "HEIGHTENED_WATCH"
        operator_actions = ["Maintain advisory-only posture and heighten operator monitoring."]
    else:
        classification = "STABLE_BASELINE"
        operator_actions = ["Continue observation; no additional doctrine escalation is indicated."]
    summary_line = (
        f"{view_label} derived view is {classification}; "
        f"window={len(window)} evidence_gaps={evidence_gap_count} defensive={defensive_posture_count} retrain_pressure={retrain_pressure_count}."
    )
    return OracleDerivedViewReport(
        generated_at_utc=_utc_now(),
        lane_id=lane_path.stem,
        view_label=view_label,
        window_entry_count=len(window),
        window_start_sequence_number=window[0].sequence_number if window else None,
        window_end_sequence_number=window[-1].sequence_number if window else None,
        first_input_timestamp_utc=window[0].input_timestamp_utc if window else None,
        last_input_timestamp_utc=window[-1].input_timestamp_utc if window else None,
        latest_event_id=latest.entry_id if latest else None,
        latest_dominant_regime=latest.dominant_regime if latest else None,
        latest_global_action=latest.recommended_global_action if latest else None,
        latest_epistemic_status=latest.epistemic_status if latest else None,
        derived_classification=classification,
        classification_counts=_count(row.evidence_status for row in window),
        regime_counts=_count(row.dominant_regime for row in window),
        global_action_counts=_count(row.recommended_global_action for row in window),
        epistemic_counts=_count(row.epistemic_status for row in window),
        evidence_gap_count=evidence_gap_count,
        elevated_or_unknown_count=elevated_or_unknown_count,
        defensive_posture_count=defensive_posture_count,
        retrain_pressure_count=retrain_pressure_count,
        average_posterior_edge_confidence=avg_conf,
        observed_entry_ids=[row.entry_id for row in window],
        operator_actions=operator_actions,
        summary_line=summary_line,
    )


def build_oracle_event_checkpoint_bundle(
    *,
    lane_path: Path,
    report_path: Path,
    repo_root: Path,
    view_label: str,
    window_size: int = 7,
    signing_private_key_path: Path | None = None,
    checkpoint_metadata_path: Path | None = None,
) -> tuple[OracleEventCheckpointManifest, DsseEnvelope | None, OracleEventCheckpointVerification, OracleDerivedViewReport]:
    report = generate_oracle_derived_view(
        lane_path=lane_path,
        view_label=view_label,
        window_size=window_size,
        checkpoint_metadata_path=checkpoint_metadata_path,
    )
    window, _ = query_oracle_event_log(
        lane_path=lane_path,
        query_spec=OracleEventLogQuerySpec(max_entries=window_size),
        checkpoint_metadata_path=checkpoint_metadata_path,
        view_label=view_label,
    )
    missing: list[str] = []
    subjects = []
    for candidate in (lane_path, report_path, checkpoint_metadata_path):
        if candidate is None:
            continue
        candidate = candidate.resolve()
        if candidate.exists():
            subjects.append(_artifact_descriptor(candidate, repo_root=repo_root))
        else:
            missing.append(str(candidate))
    integrity_status = "VERIFIED" if not missing else "INCOMPLETE"
    manifest = OracleEventCheckpointManifest(
        generated_at_utc=_utc_now(),
        checkpoint_id=f"{lane_path.stem}:{report.view_label}:{report.window_end_sequence_number if report.window_end_sequence_number is not None else 'empty'}",
        lane_id=lane_path.stem,
        view_label=view_label,
        source_event_log_path=_artifact_descriptor(lane_path.resolve(), repo_root=repo_root).path if lane_path.exists() else str(lane_path),
        derived_classification=report.derived_classification,
        window_entry_count=report.window_entry_count,
        window_start_sequence_number=report.window_start_sequence_number,
        window_end_sequence_number=report.window_end_sequence_number,
        last_entry_hash=window[-1].entry_hash if window else None,
        latest_event_id=report.latest_event_id,
        integrity_status=integrity_status,
        subjects=subjects,
        missing_artifact_paths=missing,
        summary_line=f"{view_label} checkpoint is {integrity_status.lower()} with classification {report.derived_classification} over {report.window_entry_count} entries.",
    )
    payload = manifest.model_dump(mode="json")
    envelope = None
    signature_verified = False
    if signing_private_key_path is not None:
        envelope = _sign_dsse_payload(
            payload_type="application/vnd.strategy-validator.oracle-event-checkpoint+json",
            payload=_json_canonical_bytes(payload),
            signing_private_key_path=signing_private_key_path,
        )
        signature_verified = True
    verification = OracleEventCheckpointVerification(
        verified_at_utc=_utc_now(),
        manifest_path=str(report_path.with_name("ORACLE_EVENT_CHECKPOINT.json")),
        status="VERIFIED" if integrity_status == "VERIFIED" else "INCOMPLETE",
        artifact_digests_verified=integrity_status == "VERIFIED",
        signature_verified=signature_verified,
        verified_subject_count=len(subjects),
        missing_artifact_paths=missing,
        notes=[] if integrity_status == "VERIFIED" else ["checkpoint bundle missing one or more referenced artifacts"],
    )
    return manifest, envelope, verification, report


def verify_oracle_event_checkpoint_bundle(
    *,
    manifest_path: Path,
    repo_root: Path | None = None,
    dsse_path: Path | None = None,
    public_key_path: Path | None = None,
) -> OracleEventCheckpointVerification:
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest_path = manifest_path.resolve()
    manifest = OracleEventCheckpointManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    mismatches: list[str] = []
    missing: list[str] = []
    verified_subject_count = 0
    for subject in manifest.subjects:
        resolved = _resolve_existing_path(subject.path, repo_root=repo_root, preferred_parent=manifest_path.parent)
        if resolved is None:
            missing.append(subject.path)
            continue
        digest = _sha256_file(resolved)
        if digest != subject.digest["sha256"]:
            mismatches.append(subject.path)
            continue
        verified_subject_count += 1
    signature_verified = False
    notes: list[str] = []
    if dsse_path is not None:
        if public_key_path is None:
            raise ValueError("public_key_path is required when verifying a DSSE envelope")
        envelope = DsseEnvelope.model_validate(json.loads(dsse_path.read_text(encoding="utf-8")))
        _verify_dsse_envelope(
            envelope=envelope,
            expected_payload=_json_canonical_bytes(manifest.model_dump(mode="json")),
            public_key_path=public_key_path,
            expected_payload_type="application/vnd.strategy-validator.oracle-event-checkpoint+json",
        )
        signature_verified = True
    status = "VERIFIED" if not missing and not mismatches else "INCOMPLETE"
    if missing:
        notes.append("checkpoint subjects missing from filesystem")
    if mismatches:
        notes.append("checkpoint subject digest mismatch detected")
    return OracleEventCheckpointVerification(
        verified_at_utc=_utc_now(),
        manifest_path=str(manifest_path),
        status=status,
        artifact_digests_verified=not missing and not mismatches,
        signature_verified=signature_verified,
        verified_subject_count=verified_subject_count,
        digest_mismatches=mismatches,
        missing_artifact_paths=missing,
        notes=notes,
    )


