from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional, TypeVar

from strategy_validator.contracts.operational import DsseEnvelope

ManifestT = TypeVar("ManifestT")
VerificationT = TypeVar("VerificationT")


@dataclass(frozen=True)
class EvidenceBundleVerificationSummary:
    status: str
    artifact_digests_verified: bool
    signature_verified: bool
    verified_subject_count: int
    digest_mismatches: list[str]
    missing_artifact_paths: list[str]
    notes: list[str]


@dataclass(frozen=True)
class EvidenceSubjectAssembly:
    subjects: list[object]
    missing_artifact_paths: list[str]
    integrity_status: str


def collect_evidence_subjects(
    *,
    artifact_paths: Iterable[Path],
    repo_root: Path,
    artifact_descriptor: Callable[..., object],
    normalize_path: Callable[[Path | str], str],
) -> tuple[list[object], list[str], str]:
    subjects: list[object] = []
    missing_artifact_paths: list[str] = []
    for artifact_path in artifact_paths:
        resolved = artifact_path.resolve()
        if resolved.exists():
            subjects.append(artifact_descriptor(resolved, repo_root=repo_root))
        else:
            missing_artifact_paths.append(normalize_path(resolved))
    integrity_status = "VERIFIED" if not missing_artifact_paths else "INCOMPLETE"
    return subjects, missing_artifact_paths, integrity_status


def assemble_evidence_subjects(
    *,
    artifact_paths: Iterable[Path],
    repo_root: Path,
    artifact_descriptor: Callable[..., object],
    normalize_path: Callable[[Path | str], str],
) -> EvidenceSubjectAssembly:
    subjects, missing_artifact_paths, integrity_status = collect_evidence_subjects(
        artifact_paths=artifact_paths,
        repo_root=repo_root,
        artifact_descriptor=artifact_descriptor,
        normalize_path=normalize_path,
    )
    return EvidenceSubjectAssembly(
        subjects=subjects,
        missing_artifact_paths=missing_artifact_paths,
        integrity_status=integrity_status,
    )


def sign_manifest_envelope(
    *,
    manifest: object,
    payload_type: str,
    signing_private_key_path: Optional[Path],
    json_canonical_bytes: Callable[[object], bytes],
    sign_dsse_payload: Callable[..., DsseEnvelope],
) -> DsseEnvelope | None:
    if signing_private_key_path is None:
        return None
    payload = json_canonical_bytes(manifest.model_dump(mode="json"))
    return sign_dsse_payload(
        payload_type=payload_type,
        payload=payload,
        signing_private_key_path=signing_private_key_path,
    )


def build_signed_evidence_manifest(
    *,
    artifact_paths: Iterable[Path],
    repo_root: Path,
    artifact_descriptor: Callable[..., object],
    normalize_path: Callable[[Path | str], str],
    manifest_factory: Callable[..., ManifestT],
    payload_type: str,
    signing_private_key_path: Optional[Path],
    json_canonical_bytes: Callable[[object], bytes],
    sign_dsse_payload: Callable[..., DsseEnvelope],
) -> tuple[ManifestT, DsseEnvelope | None]:
    assembly = assemble_evidence_subjects(
        artifact_paths=artifact_paths,
        repo_root=repo_root,
        artifact_descriptor=artifact_descriptor,
        normalize_path=normalize_path,
    )
    manifest = manifest_factory(
        subjects=assembly.subjects,
        missing_artifact_paths=assembly.missing_artifact_paths,
        integrity_status=assembly.integrity_status,
    )
    envelope = sign_manifest_envelope(
        manifest=manifest,
        payload_type=payload_type,
        signing_private_key_path=signing_private_key_path,
        json_canonical_bytes=json_canonical_bytes,
        sign_dsse_payload=sign_dsse_payload,
    )
    return manifest, envelope


def verify_evidence_bundle(
    *,
    manifest_path: Path,
    repo_root: Path,
    subjects: Iterable[object],
    manifest_missing_artifact_paths: Iterable[str],
    resolver: Callable[..., Path | None],
    sha256_file: Callable[[Path], str],
    dsse_path: Optional[Path],
    public_key_path: Optional[Path],
    payload_type: str,
    expected_payload: bytes,
    dsse_model: type[DsseEnvelope],
    verify_dsse_envelope: Callable[..., None],
) -> EvidenceBundleVerificationSummary:
    digest_mismatches: list[str] = []
    missing_artifact_paths: list[str] = list(manifest_missing_artifact_paths)
    notes: list[str] = []
    verified_subject_count = 0

    for subject in subjects:
        resolved = resolver(subject.path, repo_root=repo_root, preferred_parent=manifest_path.parent)
        if resolved is None:
            missing_artifact_paths.append(subject.path)
            continue
        actual_sha = sha256_file(resolved)
        expected_sha = subject.digest.get("sha256")
        if actual_sha != expected_sha:
            digest_mismatches.append(subject.path)
            continue
        verified_subject_count += 1

    signature_verified = False
    if dsse_path is not None and dsse_path.exists():
        envelope = dsse_model.model_validate_json(dsse_path.read_text(encoding="utf-8"))
        if public_key_path is None:
            notes.append("DSSE envelope supplied without public key; signature was not verified")
        else:
            verify_dsse_envelope(
                envelope=envelope,
                expected_payload=expected_payload,
                public_key_path=public_key_path.resolve(),
                expected_payload_type=payload_type,
            )
            signature_verified = True
    elif dsse_path is not None and not dsse_path.exists():
        notes.append(f"DSSE envelope path not found: {dsse_path}")

    artifact_digests_verified = not missing_artifact_paths and not digest_mismatches
    status = "VERIFIED"
    if missing_artifact_paths:
        status = "INCOMPLETE"
    elif digest_mismatches:
        status = "UNVERIFIED"
    elif dsse_path is not None and public_key_path is not None and not signature_verified:
        status = "UNVERIFIED"

    return EvidenceBundleVerificationSummary(
        status=status,
        artifact_digests_verified=artifact_digests_verified,
        signature_verified=signature_verified,
        verified_subject_count=verified_subject_count,
        digest_mismatches=digest_mismatches,
        missing_artifact_paths=sorted(set(missing_artifact_paths)),
        notes=notes,
    )


def build_evidence_verification(
    *,
    manifest: object,
    manifest_path: Path,
    repo_root: Path,
    resolver: Callable[..., Path | None],
    sha256_file: Callable[[Path], str],
    dsse_path: Optional[Path],
    public_key_path: Optional[Path],
    payload_type: str,
    json_canonical_bytes: Callable[[object], bytes],
    dsse_model: type[DsseEnvelope],
    verify_dsse_envelope: Callable[..., None],
    verification_factory: Callable[..., VerificationT],
    verified_at_utc: object,
    normalize_path: Callable[[Path | str], str],
) -> VerificationT:
    summary = verify_evidence_bundle(
        manifest_path=manifest_path,
        repo_root=repo_root,
        subjects=manifest.subjects,
        manifest_missing_artifact_paths=manifest.missing_artifact_paths,
        resolver=resolver,
        sha256_file=sha256_file,
        dsse_path=dsse_path,
        public_key_path=public_key_path,
        payload_type=payload_type,
        expected_payload=json_canonical_bytes(manifest.model_dump(mode="json")),
        dsse_model=dsse_model,
        verify_dsse_envelope=verify_dsse_envelope,
    )
    return verification_factory(
        verified_at_utc=verified_at_utc,
        manifest_path=normalize_path(manifest_path),
        status=summary.status,
        artifact_digests_verified=summary.artifact_digests_verified,
        signature_verified=summary.signature_verified,
        verified_subject_count=summary.verified_subject_count,
        digest_mismatches=summary.digest_mismatches,
        missing_artifact_paths=summary.missing_artifact_paths,
        notes=summary.notes,
    )
