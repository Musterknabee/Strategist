from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional

from strategy_validator.contracts.operational import DsseEnvelope
from strategy_validator.contracts.oracle import (
    OracleDoctrineAdaptationReport,
    OracleResearchPriorityReport,
    OracleStrategicArtifactEvidenceManifest,
    OracleStrategicArtifactEvidenceVerification,
    OracleStrategicCampaignExecutionReport,
    OracleStrategicCampaignReport,
    OracleStrategicInterventionReport,
)
from strategy_validator.validator.oracle_evidence_common import assemble_evidence_subjects, build_evidence_verification, sign_manifest_envelope
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.oracle_schema_registry import iter_registered_artifacts, load_artifact_payload, load_registered_artifact
from strategy_validator.validator.rollout_ops import (
    _artifact_descriptor,
    _json_canonical_bytes,
    _normalize_path,
    _resolve_existing_path,
    _sha256_file,
    _sign_dsse_payload,
    _verify_dsse_envelope,
)


def _load_json(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")))

_ORACLE_STRATEGIC_ARTIFACT_PAYLOAD_TYPE = "application/vnd.strategy-validator.oracle-strategic-artifact-evidence.v1+json"

_ARTIFACT_KINDS: dict[str, tuple[str, type]] = {
    "oracle_doctrine_adaptation_report/v1": ("doctrine_adaptation", OracleDoctrineAdaptationReport),
    "oracle_research_priority_report/v1": ("research_priorities", OracleResearchPriorityReport),
    "oracle_strategic_intervention_report/v1": ("strategic_intervention", OracleStrategicInterventionReport),
    "oracle_strategic_campaign_report/v1": ("strategic_campaign", OracleStrategicCampaignReport),
    "oracle_strategic_campaign_execution_report/v1": ("strategic_campaign_execution", OracleStrategicCampaignExecutionReport),
}


def _load_supported_report(path: Path):
    registration, _, report = load_registered_artifact(path, expected_schemas=set(_ARTIFACT_KINDS), expected_families={"oracle"})
    artifact_kind, _ = _ARTIFACT_KINDS[registration.schema_version]
    return artifact_kind, report


def _maybe_extract_universe_label(path: Path) -> str | None:
    try:
        payload = load_artifact_payload(path)
    except Exception:
        return None
    value = payload.get("universe_label")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _maybe_extract_oracle_run_id(path: Path) -> str | None:
    try:
        payload = load_artifact_payload(path)
    except Exception:
        return None
    value = payload.get("oracle_run_id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _validate_optional_artifacts(*, artifact_paths: Iterable[Path], expected_universe_label: str, expected_oracle_run_id: str) -> None:
    for artifact_path in artifact_paths:
        if not artifact_path.exists() or artifact_path.suffix.lower() != ".json":
            continue
        artifact_universe = _maybe_extract_universe_label(artifact_path)
        if artifact_universe is not None and artifact_universe != expected_universe_label:
            raise ValueError(
                "oracle strategic artifact evidence requires matching universe_label values; "
                f"{artifact_path.name} declared {artifact_universe!r} expected {expected_universe_label!r}"
            )
        artifact_run_id = _maybe_extract_oracle_run_id(artifact_path)
        if artifact_run_id is not None and artifact_run_id != expected_oracle_run_id:
            raise ValueError(
                "oracle strategic artifact evidence requires matching oracle_run_id values; "
                f"{artifact_path.name} declared {artifact_run_id!r} expected {expected_oracle_run_id!r}"
            )




def _verification_status_for_manifest(manifest_path: Path) -> str | None:
    verification_path = manifest_path.with_name(f"{manifest_path.stem}.verification.json")
    if not verification_path.exists():
        return None
    try:
        payload = load_artifact_payload(verification_path)
    except Exception:
        return None
    status = payload.get("status")
    return status if isinstance(status, str) and status.strip() else None


def discover_preferred_strategic_artifact_evidence(
    *,
    report_path: Path,
    repo_root: Path,
    search_root: Path | None = None,
) -> dict[str, str] | None:
    """Find the strongest artifact-evidence manifest that seals the given report path."""
    resolved_report_path = report_path.resolve()
    resolved_repo_root = repo_root.resolve()
    resolved_search_root = (search_root or repo_root).resolve()
    candidates: list[tuple[int, float, dict[str, str]]] = []
    if not resolved_search_root.exists():
        return None
    for candidate, _, _, manifest in iter_registered_artifacts(
        roots=[resolved_search_root],
        expected_schemas={"oracle_strategic_artifact_evidence_manifest/v1"},
        expected_families={"oracle"},
    ):
        if not isinstance(manifest, OracleStrategicArtifactEvidenceManifest):
            continue
        matched = False
        for subject in manifest.subjects:
            try:
                subject_path = (resolved_repo_root / subject.path).resolve()
            except Exception:
                continue
            if subject_path == resolved_report_path:
                matched = True
                break
        if not matched:
            continue
        verification_status = _verification_status_for_manifest(candidate)
        if verification_status == 'VERIFIED':
            score = 3
        elif manifest.integrity_status == 'VERIFIED':
            score = 2
        else:
            score = 1
        candidates.append((score, candidate.stat().st_mtime, {
            'manifest_path': str(candidate),
            'artifact_kind': manifest.artifact_kind,
            'evidence_status': verification_status or manifest.integrity_status,
            'preferred_strategic_backing_source': manifest.preferred_strategic_backing_source or '',
            'preferred_strategic_backing_classification': manifest.preferred_strategic_backing_classification or '',
        }))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1], item[2]['manifest_path']))
    return candidates[-1][2]


def strategic_artifact_evidence_support_score(artifact_evidence: dict[str, str] | None) -> float:
    if artifact_evidence is None:
        return 0.0
    status = str(artifact_evidence.get("evidence_status") or "").upper()
    classification = str(artifact_evidence.get("preferred_strategic_backing_classification") or "").upper()
    status_weight = {"VERIFIED": 1.0, "INCOMPLETE": 0.35, "UNVERIFIED": 0.2}.get(status, 0.0)
    classification_weight = {
        "SEALED_STRATEGIC_STACK_BACKED": 1.0,
        "DOCTRINE_ONLY_LADDER_BACKED": 0.6,
        "NO_STRATEGIC_STACK_HISTORY": 0.2,
    }.get(classification, 0.0)
    return round(status_weight * classification_weight, 6)


def preferred_artifact_evidence_fact(prefix: str, artifact_evidence: dict[str, str] | None) -> list[str]:
    if artifact_evidence is None:
        return []
    manifest_path = artifact_evidence.get("manifest_path") or ""
    evidence_status = artifact_evidence.get("evidence_status") or ""
    classification = artifact_evidence.get("preferred_strategic_backing_classification") or ""
    facts: list[str] = []
    if manifest_path:
        facts.append(f"{prefix}_artifact_evidence_manifest={manifest_path}")
    if evidence_status:
        facts.append(f"{prefix}_artifact_evidence_status={evidence_status}")
    if classification:
        facts.append(f"{prefix}_artifact_evidence_classification={classification}")
    facts.append(f"{prefix}_artifact_evidence_support_score={strategic_artifact_evidence_support_score(artifact_evidence):.2f}")
    return facts

def build_oracle_strategic_artifact_evidence_bundle(
    *,
    report_path: Path,
    repo_root: Optional[Path] = None,
    markdown_path: Optional[Path] = None,
    artifact_paths: Iterable[Path] = (),
    signing_private_key_path: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> tuple[OracleStrategicArtifactEvidenceManifest, DsseEnvelope | None]:
    repo_root = (repo_root or Path.cwd()).resolve()
    report_path = report_path.resolve()
    markdown_path = markdown_path.resolve() if markdown_path is not None else None
    extra_artifacts = [Path(path).resolve() for path in artifact_paths]

    artifact_kind, report = _load_supported_report(report_path)
    _validate_optional_artifacts(
        artifact_paths=extra_artifacts,
        expected_universe_label=report.universe_label,
        expected_oracle_run_id=report.oracle_run_id,
    )

    ordered_paths: list[Path] = [report_path]
    if markdown_path is not None:
        ordered_paths.append(markdown_path)
    ordered_paths.extend(extra_artifacts)

    assembly = assemble_evidence_subjects(
        artifact_paths=ordered_paths,
        repo_root=repo_root,
        artifact_descriptor=_artifact_descriptor,
        normalize_path=_normalize_path,
    )
    manifest = OracleStrategicArtifactEvidenceManifest(
        generated_at_utc=now_utc or _utc_now(),
        artifact_kind=artifact_kind,
        report_schema_version=report.schema_version,
        oracle_run_id=report.oracle_run_id,
        universe_label=report.universe_label,
        input_timestamp_utc=report.input_timestamp_utc,
        execution_authority="ADVISORY_ONLY",
        preferred_strategic_backing_source=getattr(report, "preferred_strategic_backing_source", None),
        preferred_strategic_backing_classification=getattr(report, "preferred_strategic_backing_classification", None),
        integrity_status=assembly.integrity_status,
        subjects=assembly.subjects,
        missing_artifact_paths=assembly.missing_artifact_paths,
        summary_line=(
            f"Strategic artifact evidence for {artifact_kind} on {report.universe_label} "
            f"at {report.input_timestamp_utc.isoformat()} with backing="
            f"{getattr(report, 'preferred_strategic_backing_classification', None) or 'UNSPECIFIED'}."
        ),
    )
    envelope = sign_manifest_envelope(
        manifest=manifest,
        payload_type=_ORACLE_STRATEGIC_ARTIFACT_PAYLOAD_TYPE,
        signing_private_key_path=signing_private_key_path,
        json_canonical_bytes=_json_canonical_bytes,
        sign_dsse_payload=_sign_dsse_payload,
    )
    return manifest, envelope


def verify_oracle_strategic_artifact_evidence_bundle(
    *,
    manifest_path: Path,
    repo_root: Optional[Path] = None,
    dsse_path: Optional[Path] = None,
    public_key_path: Optional[Path] = None,
) -> OracleStrategicArtifactEvidenceVerification:
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest_path = manifest_path.resolve()
    manifest = OracleStrategicArtifactEvidenceManifest.model_validate(_load_json(manifest_path))
    return build_evidence_verification(
        manifest=manifest,
        manifest_path=manifest_path,
        repo_root=repo_root,
        resolver=_resolve_existing_path,
        sha256_file=_sha256_file,
        dsse_path=dsse_path,
        public_key_path=public_key_path,
        payload_type=_ORACLE_STRATEGIC_ARTIFACT_PAYLOAD_TYPE,
        json_canonical_bytes=_json_canonical_bytes,
        dsse_model=DsseEnvelope,
        verify_dsse_envelope=_verify_dsse_envelope,
        verification_factory=OracleStrategicArtifactEvidenceVerification,
        verified_at_utc=_utc_now(),
        normalize_path=_normalize_path,
    )
