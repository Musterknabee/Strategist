from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from strategy_validator.contracts.operational import (
    ClosureSnapshotManifest,
    DsseEnvelope,
    DsseSignature,
    EvidenceResourceDescriptor,
)
from strategy_validator.contracts.oracle import (
    OracleAdvisoryInput,
    OracleEvidenceManifest,
    OracleEvidenceVerification,
    OracleMorningAttestation,
)


def load_oracle_input(path: Path) -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate(json.loads(path.read_text(encoding="utf-8")))


_ORACLE_EVIDENCE_PAYLOAD_TYPE = "application/vnd.strategy-validator.oracle-evidence.v1+json"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_path(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _resolve_existing_path(raw_path: str | Path, *, repo_root: Path, preferred_parent: Optional[Path] = None) -> Optional[Path]:
    candidate = Path(raw_path)
    candidates: list[Path] = []
    if candidate.is_absolute():
        candidates.append(candidate)
    else:
        if preferred_parent is not None:
            candidates.append((preferred_parent / candidate).resolve())
        candidates.append((repo_root / candidate).resolve())
        candidates.append(candidate.resolve())
    seen: set[str] = set()
    for item in candidates:
        key = _normalize_path(item)
        if key in seen:
            continue
        seen.add(key)
        if item.exists():
            return item
    return None


def _artifact_descriptor(path: Path, *, repo_root: Path) -> EvidenceResourceDescriptor:
    try:
        stored_path = _normalize_path(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        stored_path = _normalize_path(path.resolve())
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return EvidenceResourceDescriptor(
        name=path.name,
        path=stored_path,
        digest={"sha256": _sha256_file(path)},
        size_bytes=path.stat().st_size,
        media_type=media_type,
    )


def _load_private_key(path: Path) -> Ed25519PrivateKey:
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("oracle evidence signing requires an Ed25519 private key")
    return key


def _load_public_key(path: Path) -> Ed25519PublicKey:
    key = serialization.load_pem_public_key(path.read_bytes())
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("oracle evidence verification requires an Ed25519 public key")
    return key


def _public_key_id(public_key: Ed25519PublicKey) -> str:
    der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return _sha256_bytes(der)


def _dsse_pae(payload_type: str, payload: bytes) -> bytes:
    pt = payload_type.encode("utf-8")
    return b"DSSEv1 " + str(len(pt)).encode("ascii") + b" " + pt + b" " + str(len(payload)).encode("ascii") + b" " + payload


def _sign_dsse_payload(*, payload_type: str, payload: bytes, signing_private_key_path: Path) -> DsseEnvelope:
    private_key = _load_private_key(signing_private_key_path.resolve())
    signature = private_key.sign(_dsse_pae(payload_type, payload))
    return DsseEnvelope(
        payloadType=payload_type,
        payload=base64.b64encode(payload).decode("ascii"),
        signatures=[
            DsseSignature(
                keyid=_public_key_id(private_key.public_key()),
                sig=base64.b64encode(signature).decode("ascii"),
            )
        ],
    )


def _verify_dsse_envelope(*, envelope: DsseEnvelope, expected_payload: bytes, public_key_path: Path, expected_payload_type: str) -> None:
    if envelope.payloadType != expected_payload_type:
        raise ValueError(f"unexpected DSSE payloadType {envelope.payloadType!r}")
    actual_payload = base64.b64decode(envelope.payload.encode("ascii"))
    if actual_payload != expected_payload:
        raise ValueError("DSSE payload does not match oracle evidence manifest")
    if not envelope.signatures:
        raise ValueError("DSSE envelope does not contain any signatures")
    public_key = _load_public_key(public_key_path.resolve())
    expected_key_id = _public_key_id(public_key)
    for signature in envelope.signatures:
        if signature.keyid != expected_key_id:
            continue
        public_key.verify(base64.b64decode(signature.sig.encode("ascii")), _dsse_pae(envelope.payloadType, actual_payload))
        return
    raise ValueError("no matching DSSE signature for provided oracle evidence public key")


def build_oracle_evidence_bundle(
    *,
    input_path: Path,
    attestation_path: Path,
    markdown_path: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    closure_snapshot_path: Optional[Path] = None,
    signing_private_key_path: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> tuple[OracleEvidenceManifest, Optional[DsseEnvelope]]:
    repo_root = (repo_root or Path.cwd()).resolve()
    input_path = input_path.resolve()
    attestation_path = attestation_path.resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"oracle input payload not found: {input_path}")
    if not attestation_path.exists():
        raise FileNotFoundError(f"oracle attestation JSON not found: {attestation_path}")
    payload = load_oracle_input(input_path)
    attestation = OracleMorningAttestation.model_validate(json.loads(attestation_path.read_text(encoding="utf-8")))
    if attestation.input_timestamp_utc != payload.generated_for_utc:
        raise ValueError("oracle attestation input timestamp does not match the frozen input payload")
    if attestation.universe_label != payload.universe_label:
        raise ValueError("oracle attestation universe_label does not match the frozen input payload")
    if attestation.execution_authority != "ADVISORY_ONLY":
        raise ValueError("oracle evidence may only be emitted for ADVISORY_ONLY attestations")

    subjects = [
        _artifact_descriptor(input_path, repo_root=repo_root),
        _artifact_descriptor(attestation_path, repo_root=repo_root),
    ]
    missing_artifact_paths: list[str] = []
    if markdown_path is not None:
        markdown_path = markdown_path.resolve()
        if not markdown_path.exists():
            raise FileNotFoundError(f"oracle attestation markdown not found: {markdown_path}")
        subjects.append(_artifact_descriptor(markdown_path, repo_root=repo_root))

    linked_closure_id: str | None = None
    linked_closure_snapshot_stored_path: str | None = None
    if closure_snapshot_path is not None:
        closure_snapshot_path = closure_snapshot_path.resolve()
        if not closure_snapshot_path.exists():
            raise FileNotFoundError(f"linked closure snapshot not found: {closure_snapshot_path}")
        closure_manifest = ClosureSnapshotManifest.model_validate(json.loads(closure_snapshot_path.read_text(encoding="utf-8")))
        linked_closure_id = closure_manifest.closure_id
        linked_closure_snapshot_stored_path = _artifact_descriptor(closure_snapshot_path, repo_root=repo_root).path
        subjects.append(_artifact_descriptor(closure_snapshot_path, repo_root=repo_root))

    attestation_digest = _sha256_bytes(_json_canonical_bytes(attestation.model_dump(mode="json")))
    manifest = OracleEvidenceManifest(
        generated_at_utc=now_utc or _utc_now(),
        evidence_id=f"oracle-{attestation_digest[:20]}",
        universe_label=attestation.universe_label,
        input_timestamp_utc=attestation.input_timestamp_utc,
        dominant_regime=attestation.dominant_regime,
        recommended_global_action=attestation.recommended_global_action,
        epistemic_status=attestation.epistemic_uncertainty.status,
        linked_closure_id=linked_closure_id,
        linked_closure_snapshot_path=linked_closure_snapshot_stored_path,
        integrity_status="INCOMPLETE" if missing_artifact_paths else "VERIFIED",
        subjects=subjects,
        missing_artifact_paths=missing_artifact_paths,
        summary_line=attestation.summary_line,
    )
    envelope: Optional[DsseEnvelope] = None
    if signing_private_key_path is not None:
        manifest_bytes = _json_canonical_bytes(manifest.model_dump(mode="json"))
        envelope = _sign_dsse_payload(
            payload_type=_ORACLE_EVIDENCE_PAYLOAD_TYPE,
            payload=manifest_bytes,
            signing_private_key_path=signing_private_key_path,
        )
    return manifest, envelope


def verify_oracle_evidence_bundle(
    *,
    manifest_path: Path,
    repo_root: Optional[Path] = None,
    dsse_path: Optional[Path] = None,
    public_key_path: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> OracleEvidenceVerification:
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest_path = manifest_path.resolve()
    manifest = OracleEvidenceManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))

    digest_mismatches: list[str] = []
    missing_artifact_paths: list[str] = []
    verified_subject_count = 0
    for subject in manifest.subjects:
        resolved = _resolve_existing_path(subject.path, repo_root=repo_root, preferred_parent=manifest_path.parent)
        if resolved is None:
            missing_artifact_paths.append(subject.path)
            continue
        actual_sha = _sha256_file(resolved)
        expected_sha = subject.digest.get("sha256")
        if actual_sha != expected_sha:
            digest_mismatches.append(f"{subject.path}: expected {expected_sha}, got {actual_sha}")
            continue
        verified_subject_count += 1

    artifact_digests_verified = not missing_artifact_paths and not digest_mismatches
    notes: list[str] = []
    signature_verified = False
    manifest_bytes = _json_canonical_bytes(manifest.model_dump(mode="json"))
    if dsse_path is not None:
        if public_key_path is None:
            notes.append("DSSE envelope supplied without public key; signature was not verified")
        else:
            envelope = DsseEnvelope.model_validate(json.loads(dsse_path.resolve().read_text(encoding="utf-8")))
            _verify_dsse_envelope(
                envelope=envelope,
                expected_payload=manifest_bytes,
                public_key_path=public_key_path.resolve(),
                expected_payload_type=_ORACLE_EVIDENCE_PAYLOAD_TYPE,
            )
            signature_verified = True
    else:
        notes.append("oracle evidence manifest is unsigned or signature verification was skipped")

    status = "VERIFIED"
    if manifest.integrity_status == "INCOMPLETE" or missing_artifact_paths:
        status = "INCOMPLETE"
    elif not artifact_digests_verified or (dsse_path is not None and not signature_verified):
        status = "UNVERIFIED"
    elif dsse_path is None:
        status = "UNVERIFIED"

    return OracleEvidenceVerification(
        verified_at_utc=now_utc or _utc_now(),
        manifest_path=_normalize_path(manifest_path.relative_to(repo_root) if manifest_path.is_relative_to(repo_root) else manifest_path),
        status=status,
        artifact_digests_verified=artifact_digests_verified,
        signature_verified=signature_verified,
        linked_closure_present=manifest.linked_closure_snapshot_path is not None,
        verified_subject_count=verified_subject_count,
        digest_mismatches=digest_mismatches,
        missing_artifact_paths=missing_artifact_paths,
        notes=notes,
    )
