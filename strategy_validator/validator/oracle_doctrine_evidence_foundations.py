from __future__ import annotations

from strategy_validator.validator.oracle_transition_common import *  # noqa: F401,F403
from strategy_validator.validator.oracle_transition_common import (
    _artifact_descriptor,
    _doctrine_rank,
    _drift_level_from_score,
    _json_canonical_bytes,
    _normalize_path,
    _sha256_bytes,
    _sha256_file,
    _sign_dsse_payload,
    _verify_dsse_envelope,
)

from strategy_validator.validator.oracle_cadence_feedback import summarize_exact_cadence_feedback

_ORACLE_DOCTRINE_DRIFT_PAYLOAD_TYPE = "application/vnd.strategy-validator.oracle-doctrine-drift.v1+json"
_ORACLE_MONTHLY_DIGEST_PAYLOAD_TYPE = "application/vnd.strategy-validator.oracle-monthly-digest.v1+json"
_ORACLE_QUARTERLY_REVIEW_PAYLOAD_TYPE = "application/vnd.strategy-validator.oracle-quarterly-review.v1+json"
_ORACLE_SEMIANNUAL_AUDIT_PAYLOAD_TYPE = "application/vnd.strategy-validator.oracle-semiannual-audit.v1+json"
_ORACLE_ANNUAL_REVIEW_PAYLOAD_TYPE = "application/vnd.strategy-validator.oracle-annual-review.v1+json"


def _default_constitutional_search_root(*, lane_path: Path, repo_root: Optional[Path] = None, search_root: Optional[Path] = None) -> Path:
    if search_root is not None:
        return search_root.resolve()
    lane_path = lane_path.resolve()
    if repo_root is not None:
        return (repo_root.resolve() / "docs" / "artifacts").resolve()
    parents = lane_path.parents
    if len(parents) >= 2:
        return parents[1].resolve()
    return lane_path.parent.resolve()


def _count_valid_strategic_stack_manifests(*, search_root: Path) -> int:
    if not search_root.exists():
        return 0
    count = 0
    for path in sorted(p for p in search_root.rglob("ORACLE_STRATEGIC_STACK_EVIDENCE.json") if p.is_file()):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("schema_version") != "oracle_strategic_stack_evidence_manifest/v1":
            continue
        if payload.get("integrity_status") != "VERIFIED":
            continue
        if payload.get("missing_artifact_paths"):
            continue
        count += 1
    return count

def _find_doctrine_drift_report_path(*, manifest: OracleDoctrineDriftEvidenceManifest, manifest_path: Path, repo_root: Path) -> Path:
    for subject in manifest.subjects:
        if subject.name == "ORACLE_DOCTRINE_DRIFT_REPORT.json":
            resolved = advisory_resolve_existing_path(subject.path, repo_root=repo_root, preferred_parent=manifest_path.parent)
            if resolved is None:
                fallback = manifest_path.parent / Path(subject.path).name
                if fallback.exists():
                    return fallback.resolve()
                raise FileNotFoundError(f"oracle doctrine drift report subject missing from evidence chain: {subject.path}")
            return resolved
    raise FileNotFoundError("oracle doctrine drift evidence manifest does not include ORACLE_DOCTRINE_DRIFT_REPORT.json")

def _load_doctrine_drift_report(*, manifest: OracleDoctrineDriftEvidenceManifest, manifest_path: Path, repo_root: Path) -> OracleDoctrineDriftReport:
    report_path = _find_doctrine_drift_report_path(manifest=manifest, manifest_path=manifest_path, repo_root=repo_root)
    return OracleDoctrineDriftReport.model_validate(json.loads(report_path.read_text(encoding="utf-8")))

def build_oracle_doctrine_drift_evidence_bundle(
    *,
    source_previous_digest_path: Path,
    source_current_digest_path: Path,
    report_path: Path,
    markdown_path: Path,
    repo_root: Optional[Path] = None,
    signing_private_key_path: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> tuple[OracleDoctrineDriftEvidenceManifest, DsseEnvelope | None]:
    repo_root = (repo_root or Path.cwd()).resolve()
    source_previous_digest_path = source_previous_digest_path.resolve()
    source_current_digest_path = source_current_digest_path.resolve()
    report_path = report_path.resolve()
    markdown_path = markdown_path.resolve()

    report = OracleDoctrineDriftReport.model_validate(json.loads(report_path.read_text(encoding="utf-8")))
    drift_id = _sha256_bytes(
        _json_canonical_bytes(
            {
                "lane_id": report.lane_id,
                "previous_digest_id": report.previous_digest_id,
                "current_digest_id": report.current_digest_id,
                "drift_classification": report.drift_classification,
                "drift_level": report.drift_level,
                "summary_line": report.summary_line,
            }
        )
    )
    return build_signed_evidence_manifest(
        artifact_paths=(source_previous_digest_path, source_current_digest_path, report_path, markdown_path),
        repo_root=repo_root,
        artifact_descriptor=_artifact_descriptor,
        normalize_path=_normalize_path,
        manifest_factory=lambda *, subjects, missing_artifact_paths, integrity_status: OracleDoctrineDriftEvidenceManifest(
            generated_at_utc=now_utc or advisory_utc_now(),
            drift_id=drift_id,
            lane_id=report.lane_id,
            execution_authority="ADVISORY_ONLY",
            source_previous_digest_path=_normalize_path(source_previous_digest_path),
            source_current_digest_path=_normalize_path(source_current_digest_path),
            drift_classification=report.drift_classification,
            drift_level=report.drift_level,
            previous_doctrine_posture=report.previous_doctrine_posture,
            current_doctrine_posture=report.current_doctrine_posture,
            integrity_status=integrity_status,
            subjects=subjects,
            missing_artifact_paths=missing_artifact_paths,
            summary_line=report.summary_line,
        ),
        payload_type=_ORACLE_DOCTRINE_DRIFT_PAYLOAD_TYPE,
        signing_private_key_path=signing_private_key_path,
        json_canonical_bytes=_json_canonical_bytes,
        sign_dsse_payload=_sign_dsse_payload,
    )

def verify_oracle_doctrine_drift_evidence_bundle(
    *,
    manifest_path: Path,
    repo_root: Optional[Path] = None,
    dsse_path: Optional[Path] = None,
    public_key_path: Optional[Path] = None,
) -> OracleDoctrineDriftEvidenceVerification:
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest_path = manifest_path.resolve()
    manifest = OracleDoctrineDriftEvidenceManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    return build_evidence_verification(
        manifest=manifest,
        manifest_path=manifest_path,
        repo_root=repo_root,
        resolver=advisory_resolve_existing_path,
        sha256_file=_sha256_file,
        dsse_path=dsse_path,
        public_key_path=public_key_path,
        payload_type=_ORACLE_DOCTRINE_DRIFT_PAYLOAD_TYPE,
        json_canonical_bytes=_json_canonical_bytes,
        dsse_model=DsseEnvelope,
        verify_dsse_envelope=_verify_dsse_envelope,
        verification_factory=OracleDoctrineDriftEvidenceVerification,
        verified_at_utc=advisory_utc_now(),
        normalize_path=_normalize_path,
    )

def append_oracle_doctrine_drift_to_lane(
    *,
    manifest_path: Path,
    verification: OracleDoctrineDriftEvidenceVerification,
    lane_path: Path,
    repo_root: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> OracleDoctrineLaneEntry:
    manifest_path = manifest_path.resolve()
    lane_path = lane_path.resolve()
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest = OracleDoctrineDriftEvidenceManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    if verification.status != "VERIFIED":
        raise ValueError("oracle doctrine lane only accepts VERIFIED doctrine drift evidence")
    _ = _load_doctrine_drift_report(manifest=manifest, manifest_path=manifest_path, repo_root=repo_root)

    entries: list[OracleDoctrineLaneEntry] = []
    if lane_path.exists():
        for raw in lane_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            entries.append(OracleDoctrineLaneEntry.model_validate(json.loads(raw)))
    sequence_number = len(entries)
    previous_entry_hash = entries[-1].entry_hash if entries else None
    lane_id = lane_path.stem
    entry_seed = {
        "lane_id": lane_id,
        "sequence_number": sequence_number,
        "drift_id": manifest.drift_id,
        "previous_entry_hash": previous_entry_hash or "GENESIS",
        "manifest_sha256": _sha256_file(manifest_path),
        "drift_classification": manifest.drift_classification,
        "drift_level": manifest.drift_level,
        "current_doctrine_posture": manifest.current_doctrine_posture,
        "evidence_status": verification.status,
    }
    entry_hash = _sha256_bytes(_json_canonical_bytes(entry_seed))
    entry = OracleDoctrineLaneEntry(
        appended_at_utc=now_utc or advisory_utc_now(),
        lane_id=lane_id,
        sequence_number=sequence_number,
        entry_id=_sha256_bytes(_json_canonical_bytes({"lane_id": lane_id, "sequence_number": sequence_number, "entry_hash": entry_hash})),
        drift_id=manifest.drift_id,
        previous_entry_hash=previous_entry_hash,
        entry_hash=entry_hash,
        manifest_path=_normalize_path(manifest_path),
        manifest_sha256=_sha256_file(manifest_path),
        drift_classification=manifest.drift_classification,
        drift_level=manifest.drift_level,
        current_doctrine_posture=manifest.current_doctrine_posture,
        evidence_status=verification.status,
        summary_line=manifest.summary_line,
    )
    lane_path.parent.mkdir(parents=True, exist_ok=True)
    with lane_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry.model_dump(mode="json"), separators=(",", ":"), default=str) + "\n")
    return entry


