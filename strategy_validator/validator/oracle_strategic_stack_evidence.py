from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional

from strategy_validator.contracts.operational import DsseEnvelope
from strategy_validator.contracts.oracle_core import OracleAdvisoryInput
from strategy_validator.contracts.oracle_strategic_programs import (
    OracleStrategicBriefingReport,
    OracleStrategicStackEvidenceManifest,
    OracleStrategicStackEvidenceVerification,
)
from strategy_validator.validator.oracle_evidence_common import assemble_evidence_subjects, build_evidence_verification, sign_manifest_envelope
from strategy_validator.validator.rollout_ops import (
    _artifact_descriptor,
    _json_canonical_bytes,
    _normalize_path,
    _resolve_existing_path,
    _sha256_bytes,
    _sha256_file,
    _sign_dsse_payload,
    _verify_dsse_envelope,
)
from strategy_validator.validator.oracle_transition_common import _utc_now

_ORACLE_STRATEGIC_STACK_PAYLOAD_TYPE = "application/vnd.strategy-validator.oracle-strategic-stack-evidence.v1+json"


def _load_json(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _maybe_extract_universe_label(path: Path) -> str | None:
    try:
        payload = _load_json(path)
    except Exception:
        return None
    value = payload.get("universe_label")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _validate_optional_artifact_universe(*, artifact_paths: Iterable[Path], expected_universe_label: str) -> None:
    for artifact_path in artifact_paths:
        if not artifact_path.exists() or artifact_path.suffix.lower() != ".json":
            continue
        artifact_universe = _maybe_extract_universe_label(artifact_path)
        if artifact_universe is not None and artifact_universe != expected_universe_label:
            raise ValueError(
                f"oracle strategic stack evidence requires matching universe_label values; "
                f"{artifact_path.name} declared {artifact_universe!r} expected {expected_universe_label!r}"
            )


def build_oracle_strategic_stack_evidence_bundle(
    *,
    input_path: Path,
    briefing_report_path: Path,
    repo_root: Optional[Path] = None,
    markdown_path: Optional[Path] = None,
    artifact_paths: Iterable[Path] = (),
    signing_private_key_path: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> tuple[OracleStrategicStackEvidenceManifest, DsseEnvelope | None]:
    repo_root = (repo_root or Path.cwd()).resolve()
    input_path = input_path.resolve()
    briefing_report_path = briefing_report_path.resolve()
    markdown_path = markdown_path.resolve() if markdown_path is not None else None
    extra_artifacts = [Path(path).resolve() for path in artifact_paths]

    input_payload = OracleAdvisoryInput.model_validate(_load_json(input_path))
    briefing_report = OracleStrategicBriefingReport.model_validate(_load_json(briefing_report_path))

    if briefing_report.universe_label != input_payload.universe_label:
        raise ValueError("oracle strategic stack evidence requires matching universe_label values between input and briefing")

    _validate_optional_artifact_universe(
        artifact_paths=extra_artifacts,
        expected_universe_label=input_payload.universe_label,
    )

    ordered_paths: list[Path] = [input_path, briefing_report_path]
    if markdown_path is not None:
        ordered_paths.append(markdown_path)
    ordered_paths.extend(extra_artifacts)

    assembly = assemble_evidence_subjects(
        artifact_paths=ordered_paths,
        repo_root=repo_root,
        artifact_descriptor=_artifact_descriptor,
        normalize_path=_normalize_path,
    )
    stack_id = _sha256_bytes(
        _json_canonical_bytes(
            {
                "universe_label": input_payload.universe_label,
                "input_timestamp_utc": input_payload.generated_for_utc.isoformat(),
                "dominant_regime": briefing_report.dominant_regime,
                "strategic_posture": briefing_report.strategic_posture,
                "briefing_schema_version": briefing_report.schema_version,
            }
        )
    )
    manifest = OracleStrategicStackEvidenceManifest(
        generated_at_utc=now_utc or _utc_now(),
        stack_id=stack_id,
        oracle_run_id=getattr(briefing_report, "oracle_run_id", _sha256_bytes(_json_canonical_bytes({"universe_label": input_payload.universe_label, "input_timestamp_utc": input_payload.generated_for_utc.isoformat()}))),
        universe_label=input_payload.universe_label,
        input_timestamp_utc=input_payload.generated_for_utc,
        execution_authority="ADVISORY_ONLY",
        dominant_regime=briefing_report.dominant_regime,
        strategic_posture=briefing_report.strategic_posture,
        briefing_schema_version=briefing_report.schema_version,
        integrity_status=assembly.integrity_status,
        subjects=assembly.subjects,
        missing_artifact_paths=assembly.missing_artifact_paths,
        summary_line=(
            f"Strategic stack evidence for {input_payload.universe_label} at {input_payload.generated_for_utc.isoformat()} "
            f"sealed around posture={briefing_report.strategic_posture}, regime={briefing_report.dominant_regime}."
        ),
    )
    envelope = sign_manifest_envelope(
        manifest=manifest,
        payload_type=_ORACLE_STRATEGIC_STACK_PAYLOAD_TYPE,
        signing_private_key_path=signing_private_key_path,
        json_canonical_bytes=_json_canonical_bytes,
        sign_dsse_payload=_sign_dsse_payload,
    )
    return manifest, envelope


def verify_oracle_strategic_stack_evidence_bundle(
    *,
    manifest_path: Path,
    repo_root: Optional[Path] = None,
    dsse_path: Optional[Path] = None,
    public_key_path: Optional[Path] = None,
) -> OracleStrategicStackEvidenceVerification:
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest_path = manifest_path.resolve()
    manifest = OracleStrategicStackEvidenceManifest.model_validate(_load_json(manifest_path))
    return build_evidence_verification(
        manifest=manifest,
        manifest_path=manifest_path,
        repo_root=repo_root,
        resolver=_resolve_existing_path,
        sha256_file=_sha256_file,
        dsse_path=dsse_path,
        public_key_path=public_key_path,
        payload_type=_ORACLE_STRATEGIC_STACK_PAYLOAD_TYPE,
        json_canonical_bytes=_json_canonical_bytes,
        dsse_model=DsseEnvelope,
        verify_dsse_envelope=_verify_dsse_envelope,
        verification_factory=OracleStrategicStackEvidenceVerification,
        verified_at_utc=_utc_now(),
        normalize_path=_normalize_path,
    )
