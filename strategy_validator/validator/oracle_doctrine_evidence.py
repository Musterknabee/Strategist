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


def generate_oracle_monthly_digest(*, lane_path: Path, window_size: int = 4, repo_root: Optional[Path] = None, search_root: Optional[Path] = None, now_utc: Optional[datetime] = None) -> OracleMonthlyDigestReport:
    lane_path = lane_path.resolve()
    entries: list[OracleDoctrineLaneEntry] = []
    if lane_path.exists():
        for raw in lane_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            entries.append(OracleDoctrineLaneEntry.model_validate(json.loads(raw)))
    window_entries = entries[-max(window_size, 1):]
    drift_classification_counts: dict[str, int] = {}
    observed_drift_ids: list[str] = []
    recurring_patterns: list[str] = []
    posture_counts: dict[str, int] = {}
    for entry in window_entries:
        observed_drift_ids.append(entry.drift_id)
        drift_classification_counts[entry.drift_classification] = drift_classification_counts.get(entry.drift_classification, 0) + 1
        posture_counts[entry.current_doctrine_posture] = posture_counts.get(entry.current_doctrine_posture, 0) + 1

    latest = window_entries[-1] if window_entries else None
    cadence_feedback = summarize_exact_cadence_feedback(repo_root=repo_root, search_root=search_root, window_size=max(window_size * 2, 1))
    evidence_gap_count = drift_classification_counts.get("DOCTRINE_EVIDENCE_GAP", 0)
    repair_count = drift_classification_counts.get("RECURRING_REPAIR", 0) + posture_counts.get("REPAIR_FIRST", 0)
    retrain_count = drift_classification_counts.get("RECURRING_RETRAIN", 0) + posture_counts.get("STRATEGY_RETRAIN_REVIEW", 0)
    escalation_count = drift_classification_counts.get("DOCTRINE_ESCALATION", 0)
    defensive_count = posture_counts.get("DEFENSIVE_RESEARCH_POSTURE", 0)
    heightened_count = posture_counts.get("HEIGHTENED_RESEARCH_POSTURE", 0)

    doctrine_memory_classification: OracleDoctrineMemoryClassification = "DOCTRINE_STABLE_BASELINE"
    if evidence_gap_count >= 1 or (latest is not None and latest.drift_classification == "DOCTRINE_EVIDENCE_GAP"):
        doctrine_memory_classification = "DOCTRINE_EVIDENCE_GAP"
        recurring_patterns.append("At least one doctrine comparison lost verification integrity; repair evidence chains before relying on monthly doctrine memory.")
    elif repair_count >= 2 or (latest is not None and latest.current_doctrine_posture == "REPAIR_FIRST"):
        doctrine_memory_classification = "DOCTRINE_REPAIR_PERSISTENT"
        recurring_patterns.append("Repair-first doctrine persisted across the monthly window, indicating sustained governance or evidence hygiene pressure.")
    elif retrain_count >= 2 or (latest is not None and latest.current_doctrine_posture == "STRATEGY_RETRAIN_REVIEW"):
        doctrine_memory_classification = "DOCTRINE_RETRAIN_PERSISTENT"
        recurring_patterns.append("Retrain pressure remained present across weekly doctrine windows and should be treated as a persisted monthly concern.")
    elif defensive_count >= 1 or (latest is not None and latest.current_doctrine_posture == "DEFENSIVE_RESEARCH_POSTURE"):
        doctrine_memory_classification = "DOCTRINE_DEFENSIVE_PERSISTENT"
        recurring_patterns.append("Defensive doctrine remained active within the monthly window, suggesting unresolved uncertainty or market-stress carryover.")
    elif escalation_count >= 2 or heightened_count >= 1 or (latest is not None and latest.current_doctrine_posture == "HEIGHTENED_RESEARCH_POSTURE"):
        doctrine_memory_classification = "DOCTRINE_HEIGHTENED_WATCH"
        recurring_patterns.append("Heightened doctrine watch persisted across the monthly window and warrants tighter monitoring cadence.")
    elif window_entries:
        recurring_patterns.append("Monthly doctrine memory stayed within stable baseline bounds.")
    else:
        recurring_patterns.append("No doctrine drift history exists yet for a monthly digest.")

    if drift_classification_counts.get("DOCTRINE_ESCALATION", 0) and drift_classification_counts.get("DOCTRINE_RELIEF", 0):
        recurring_patterns.append("Both escalation and relief occurred within the same monthly window; preserve the lane so doctrine reversals remain auditable.")
    if drift_classification_counts.get("RECURRING_REPAIR", 0) and drift_classification_counts.get("RECURRING_RETRAIN", 0):
        recurring_patterns.append("Repair recurrence and retrain recurrence overlapped within the same monthly window; fix evidence hygiene before over-allocating retrain confidence.")
    if cadence_feedback.exact_feedback_confirmation_count >= 3:
        recurring_patterns.append("Repeated exact sealed confirmations persisted across the monthly window; escalate review cadence for the directly supported clauses rather than treating the pressure as generic background noise.")
    elif cadence_feedback.exact_feedback_relief_count >= 3 and cadence_feedback.exact_feedback_confirmation_count == 0:
        recurring_patterns.append("Repeated exact sealed relieving outcomes persisted across the monthly window; keep doctrine active but allow bounded relaxation for the directly supported clauses.")

    operator_actions = [
        "Treat the monthly digest as advisory doctrine memory derived from signed doctrine-drift evidence and an append-only doctrine lane.",
        "Preserve the doctrine lane, doctrine-drift manifests, and linked weekly digest evidence together so monthly posture remains replayable.",
    ]
    if doctrine_memory_classification == "DOCTRINE_EVIDENCE_GAP":
        operator_actions.append("Repair or regenerate missing doctrine-drift evidence before relying on monthly doctrine summaries.")
    elif doctrine_memory_classification == "DOCTRINE_REPAIR_PERSISTENT":
        operator_actions.append("Prioritize evidence and lane hygiene work; persistent repair-first doctrine means the oracle cannot safely stabilize yet.")
    elif doctrine_memory_classification == "DOCTRINE_RETRAIN_PERSISTENT":
        operator_actions.append("Escalate strategy forensic and retrain review cadence; persisted retrain pressure should not be narratively minimized.")
    elif doctrine_memory_classification == "DOCTRINE_DEFENSIVE_PERSISTENT":
        operator_actions.append("Maintain defensive research posture and avoid confidence-heavy interpretation until uncertainty and doctrine stress recede.")
    elif doctrine_memory_classification == "DOCTRINE_HEIGHTENED_WATCH":
        operator_actions.append("Increase doctrine review cadence and compare the next verified weekly digest against the latest monthly drivers.")
    else:
        operator_actions.append("Maintain baseline review cadence; no monthly doctrine memory trigger currently requires escalation.")
    if cadence_feedback.exact_feedback_confirmation_count >= 3:
        operator_actions.append("Escalate monthly doctrine review cadence because repeated exact sealed confirmations are compounding live clause pressure.")
    elif cadence_feedback.exact_feedback_relief_count >= 3 and cadence_feedback.exact_feedback_confirmation_count == 0:
        operator_actions.append("Maintain monthly doctrine review but allow repeated exact sealed relieving outcomes to soften cadence only for the directly supported clauses.")
    elif cadence_feedback.exact_evidence_support_score >= 0.85:
        operator_actions.append("Anchor monthly doctrine cadence to the repeated exact sealed subjects instead of generalizing beyond the directly supported scope.")

    summary_line = (
        f"Oracle monthly digest={doctrine_memory_classification}; window_entries={len(window_entries)}; "
        f"evidence_gap={evidence_gap_count}; repair={repair_count}; retrain={retrain_count}; "
        f"defensive={defensive_count}; heightened={heightened_count}; escalations={escalation_count}; "
        f"exact_support={cadence_feedback.exact_evidence_support_score:.2f}; exact_confirm={cadence_feedback.exact_feedback_confirmation_count}; exact_relief={cadence_feedback.exact_feedback_relief_count}"
    )
    return OracleMonthlyDigestReport(
        generated_at_utc=now_utc or advisory_utc_now(),
        lane_id=lane_path.stem,
        exact_evidence_support_score=cadence_feedback.exact_evidence_support_score,
        exact_feedback_confirmation_count=cadence_feedback.exact_feedback_confirmation_count,
        exact_feedback_relief_count=cadence_feedback.exact_feedback_relief_count,
        window_entry_count=len(window_entries),
        window_start_sequence_number=window_entries[0].sequence_number if window_entries else None,
        window_end_sequence_number=window_entries[-1].sequence_number if window_entries else None,
        latest_drift_classification=latest.drift_classification if latest else None,
        latest_current_doctrine_posture=latest.current_doctrine_posture if latest else None,
        doctrine_memory_classification=doctrine_memory_classification,
        drift_classification_counts=drift_classification_counts,
        recurring_patterns=recurring_patterns,
        observed_drift_ids=observed_drift_ids,
        operator_actions=operator_actions,
        summary_line=summary_line,
    )

def _find_monthly_digest_report_path(*, manifest: OracleMonthlyDigestEvidenceManifest, manifest_path: Path, repo_root: Path) -> Path:
    for subject in manifest.subjects:
        if subject.name == "ORACLE_MONTHLY_DIGEST.json":
            resolved = advisory_resolve_existing_path(subject.path, repo_root=repo_root, preferred_parent=manifest_path.parent)
            if resolved is None:
                fallback = manifest_path.parent / Path(subject.path).name
                if fallback.exists():
                    return fallback.resolve()
                raise FileNotFoundError(f"oracle monthly digest report subject missing from evidence chain: {subject.path}")
            return resolved
    raise FileNotFoundError("oracle monthly digest evidence manifest does not include ORACLE_MONTHLY_DIGEST.json")

def _load_monthly_digest_report(*, manifest: OracleMonthlyDigestEvidenceManifest, manifest_path: Path, repo_root: Path) -> OracleMonthlyDigestReport:
    report_path = _find_monthly_digest_report_path(manifest=manifest, manifest_path=manifest_path, repo_root=repo_root)
    return OracleMonthlyDigestReport.model_validate(json.loads(report_path.read_text(encoding="utf-8")))

def build_oracle_monthly_digest_evidence_bundle(
    *,
    source_doctrine_lane_path: Path,
    digest_path: Path,
    markdown_path: Path,
    repo_root: Optional[Path] = None,
    signing_private_key_path: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> tuple[OracleMonthlyDigestEvidenceManifest, DsseEnvelope | None]:
    repo_root = (repo_root or Path.cwd()).resolve()
    source_doctrine_lane_path = source_doctrine_lane_path.resolve()
    digest_path = digest_path.resolve()
    markdown_path = markdown_path.resolve()

    digest = OracleMonthlyDigestReport.model_validate(json.loads(digest_path.read_text(encoding="utf-8")))
    monthly_digest_id = _sha256_bytes(
        _json_canonical_bytes(
            {
                "lane_id": digest.lane_id,
                "doctrine_memory_classification": digest.doctrine_memory_classification,
                "window_end_sequence_number": digest.window_end_sequence_number,
                "observed_drift_ids": digest.observed_drift_ids,
                "summary_line": digest.summary_line,
            }
        )
    )
    return build_signed_evidence_manifest(
        artifact_paths=(source_doctrine_lane_path, digest_path, markdown_path),
        repo_root=repo_root,
        artifact_descriptor=_artifact_descriptor,
        normalize_path=_normalize_path,
        manifest_factory=lambda *, subjects, missing_artifact_paths, integrity_status: OracleMonthlyDigestEvidenceManifest(
            generated_at_utc=now_utc or advisory_utc_now(),
            monthly_digest_id=monthly_digest_id,
            lane_id=digest.lane_id,
            execution_authority="ADVISORY_ONLY",
            source_doctrine_lane_path=_normalize_path(source_doctrine_lane_path),
            doctrine_memory_classification=digest.doctrine_memory_classification,
            window_entry_count=digest.window_entry_count,
            window_end_sequence_number=digest.window_end_sequence_number,
            latest_drift_classification=digest.latest_drift_classification,
            latest_current_doctrine_posture=digest.latest_current_doctrine_posture,
            integrity_status=integrity_status,
            subjects=subjects,
            missing_artifact_paths=missing_artifact_paths,
            summary_line=digest.summary_line,
        ),
        payload_type=_ORACLE_MONTHLY_DIGEST_PAYLOAD_TYPE,
        signing_private_key_path=signing_private_key_path,
        json_canonical_bytes=_json_canonical_bytes,
        sign_dsse_payload=_sign_dsse_payload,
    )

def verify_oracle_monthly_digest_evidence_bundle(
    *,
    manifest_path: Path,
    repo_root: Optional[Path] = None,
    dsse_path: Optional[Path] = None,
    public_key_path: Optional[Path] = None,
) -> OracleMonthlyDigestEvidenceVerification:
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest_path = manifest_path.resolve()
    manifest = OracleMonthlyDigestEvidenceManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    return build_evidence_verification(
        manifest=manifest,
        manifest_path=manifest_path,
        repo_root=repo_root,
        resolver=advisory_resolve_existing_path,
        sha256_file=_sha256_file,
        dsse_path=dsse_path,
        public_key_path=public_key_path,
        payload_type=_ORACLE_MONTHLY_DIGEST_PAYLOAD_TYPE,
        json_canonical_bytes=_json_canonical_bytes,
        dsse_model=DsseEnvelope,
        verify_dsse_envelope=_verify_dsse_envelope,
        verification_factory=OracleMonthlyDigestEvidenceVerification,
        verified_at_utc=advisory_utc_now(),
        normalize_path=_normalize_path,
    )

def append_oracle_monthly_digest_to_lane(
    *,
    manifest_path: Path,
    verification: OracleMonthlyDigestEvidenceVerification,
    lane_path: Path,
    repo_root: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> OracleMonthlyLaneEntry:
    if verification.status != "VERIFIED":
        raise ValueError("oracle monthly digest evidence must verify before it can be appended to the monthly lane")
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest_path = manifest_path.resolve()
    lane_path = lane_path.resolve()
    manifest = OracleMonthlyDigestEvidenceManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))

    entries: list[OracleMonthlyLaneEntry] = []
    if lane_path.exists():
        for raw in lane_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            entries.append(OracleMonthlyLaneEntry.model_validate(json.loads(raw)))

    sequence_number = len(entries)
    previous_entry_hash = entries[-1].entry_hash if entries else None
    lane_id = lane_path.stem
    entry_payload = {
        "lane_id": lane_id,
        "sequence_number": sequence_number,
        "monthly_digest_id": manifest.monthly_digest_id,
        "previous_entry_hash": previous_entry_hash,
        "manifest_sha256": _sha256_file(manifest_path),
        "doctrine_memory_classification": manifest.doctrine_memory_classification,
        "latest_drift_classification": manifest.latest_drift_classification,
        "evidence_status": verification.status,
        "summary_line": manifest.summary_line,
    }
    entry_hash = _sha256_bytes(_json_canonical_bytes(entry_payload))
    entry_id = _sha256_bytes(_json_canonical_bytes({"lane_id": lane_id, "sequence_number": sequence_number, "entry_hash": entry_hash}))
    try:
        manifest_ref = manifest_path.relative_to(repo_root)
    except ValueError:
        manifest_ref = manifest_path
    entry = OracleMonthlyLaneEntry(
        appended_at_utc=now_utc or advisory_utc_now(),
        lane_id=lane_id,
        sequence_number=sequence_number,
        entry_id=entry_id,
        monthly_digest_id=manifest.monthly_digest_id,
        previous_entry_hash=previous_entry_hash,
        entry_hash=entry_hash,
        manifest_path=_normalize_path(manifest_ref),
        manifest_sha256=_sha256_file(manifest_path),
        doctrine_memory_classification=manifest.doctrine_memory_classification,
        latest_drift_classification=manifest.latest_drift_classification,
        evidence_status=verification.status,
        summary_line=manifest.summary_line,
    )
    lane_path.parent.mkdir(parents=True, exist_ok=True)
    with lane_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry.model_dump(mode="json"), separators=(",", ":"), default=str) + "\n")
    return entry


def generate_oracle_quarterly_review(*, lane_path: Path, window_size: int = 3, repo_root: Optional[Path] = None, search_root: Optional[Path] = None, now_utc: Optional[datetime] = None) -> OracleQuarterlyReviewReport:
    lane_path = lane_path.resolve()
    entries: list[OracleMonthlyLaneEntry] = []
    if lane_path.exists():
        for raw in lane_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            entries.append(OracleMonthlyLaneEntry.model_validate(json.loads(raw)))
    window_entries = entries[-max(window_size, 1):]
    monthly_classification_counts: dict[str, int] = {}
    observed_monthly_digest_ids: list[str] = []
    recurring_patterns: list[str] = []
    for entry in window_entries:
        observed_monthly_digest_ids.append(entry.monthly_digest_id)
        monthly_classification_counts[entry.doctrine_memory_classification] = monthly_classification_counts.get(entry.doctrine_memory_classification, 0) + 1

    latest = window_entries[-1] if window_entries else None
    cadence_feedback = summarize_exact_cadence_feedback(repo_root=repo_root, search_root=search_root, window_size=max(window_size * 4, 1))
    evidence_gap_count = monthly_classification_counts.get("DOCTRINE_EVIDENCE_GAP", 0)
    repair_count = monthly_classification_counts.get("DOCTRINE_REPAIR_PERSISTENT", 0)
    retrain_count = monthly_classification_counts.get("DOCTRINE_RETRAIN_PERSISTENT", 0)
    defensive_count = monthly_classification_counts.get("DOCTRINE_DEFENSIVE_PERSISTENT", 0)
    heightened_count = monthly_classification_counts.get("DOCTRINE_HEIGHTENED_WATCH", 0)

    quarterly_classification = "QUARTERLY_STABLE_BASELINE"
    if evidence_gap_count >= 1 or (latest is not None and latest.evidence_status != "VERIFIED"):
        quarterly_classification = "QUARTERLY_EVIDENCE_GAP"
        recurring_patterns.append("At least one monthly doctrine digest lost verification integrity; repair monthly evidence before trusting quarterly review.")
    elif repair_count >= 2 or (latest is not None and latest.doctrine_memory_classification == "DOCTRINE_REPAIR_PERSISTENT"):
        quarterly_classification = "QUARTERLY_REPAIR_STRUCTURAL"
        recurring_patterns.append("Repair-persistent doctrine repeated across the quarterly window, indicating structural governance pressure rather than a transient week cluster.")
    elif retrain_count >= 2 or (latest is not None and latest.doctrine_memory_classification == "DOCTRINE_RETRAIN_PERSISTENT"):
        quarterly_classification = "QUARTERLY_RETRAIN_STRUCTURAL"
        recurring_patterns.append("Retrain-persistent doctrine repeated across the quarterly window and should be treated as structural strategy-health pressure.")
    elif defensive_count >= 2 or (latest is not None and latest.doctrine_memory_classification == "DOCTRINE_DEFENSIVE_PERSISTENT"):
        quarterly_classification = "QUARTERLY_DEFENSIVE_STRUCTURAL"
        recurring_patterns.append("Defensive doctrine persisted across multiple monthly windows; uncertainty or market-stress carryover appears structural.")
    elif heightened_count >= 2 or (latest is not None and latest.doctrine_memory_classification == "DOCTRINE_HEIGHTENED_WATCH"):
        quarterly_classification = "QUARTERLY_HEIGHTENED_WATCH"
        recurring_patterns.append("Heightened watch remained active across the quarterly window and warrants tighter review cadence before confidence restoration.")
    elif window_entries:
        recurring_patterns.append("Quarterly doctrine review remained within stable baseline bounds.")
    else:
        recurring_patterns.append("No monthly doctrine history exists yet for a quarterly review.")

    if repair_count and retrain_count:
        recurring_patterns.append("Repair-persistent and retrain-persistent doctrine overlapped within the same quarterly window; do not over-ascribe poor strategy health when evidence hygiene remains unstable.")
    if defensive_count and heightened_count:
        recurring_patterns.append("Both heightened watch and defensive doctrine appeared within the same quarterly window; preserve the monthly lane so stress persistence remains auditable.")

    operator_actions = [
        "Treat the quarterly review as advisory doctrine memory derived from signed monthly digest evidence and an append-only monthly lane.",
        "Preserve the monthly lane, monthly digest evidence manifests, and linked doctrine lane together so quarterly posture remains replayable.",
    ]
    if quarterly_classification == "QUARTERLY_EVIDENCE_GAP":
        operator_actions.append("Repair or regenerate missing monthly evidence before relying on quarterly doctrine summaries.")
    elif quarterly_classification == "QUARTERLY_REPAIR_STRUCTURAL":
        operator_actions.append("Escalate evidence and governance hygiene work; structural repair pressure means the oracle cannot safely stabilize yet.")
    elif quarterly_classification == "QUARTERLY_RETRAIN_STRUCTURAL":
        operator_actions.append("Escalate strategy forensic and retrain work as a structural quarterly concern rather than a temporary fluctuation.")
    elif quarterly_classification == "QUARTERLY_DEFENSIVE_STRUCTURAL":
        operator_actions.append("Maintain defensive research doctrine and avoid confidence-heavy interpretation until quarterly stress recedes.")
    elif quarterly_classification == "QUARTERLY_HEIGHTENED_WATCH":
        operator_actions.append("Increase quarterly doctrine review cadence and compare the next monthly digest against the latest structural drivers.")
    else:
        operator_actions.append("Maintain baseline quarterly doctrine review cadence; no structural trigger currently requires escalation.")
    if cadence_feedback.exact_feedback_confirmation_count >= 4:
        operator_actions.append("Escalate quarterly doctrine review cadence because repeated exact sealed confirmations are now structural rather than incidental.")
    elif cadence_feedback.exact_feedback_relief_count >= 4 and cadence_feedback.exact_feedback_confirmation_count == 0:
        operator_actions.append("Maintain quarterly doctrine review but allow repeated exact sealed relieving outcomes to soften cadence for the directly supported clauses.")
    elif cadence_feedback.exact_evidence_support_score >= 0.85:
        operator_actions.append("Anchor quarterly doctrine cadence to the repeated exact sealed subjects and keep the moderation scope bounded to those clauses.")

    summary_line = (
        f"Oracle quarterly review={quarterly_classification}; window_entries={len(window_entries)}; "
        f"evidence_gap={evidence_gap_count}; repair={repair_count}; retrain={retrain_count}; "
        f"defensive={defensive_count}; heightened={heightened_count}; "
        f"exact_support={cadence_feedback.exact_evidence_support_score:.2f}; exact_confirm={cadence_feedback.exact_feedback_confirmation_count}; exact_relief={cadence_feedback.exact_feedback_relief_count}"
    )
    return OracleQuarterlyReviewReport(
        generated_at_utc=now_utc or advisory_utc_now(),
        lane_id=lane_path.stem,
        exact_evidence_support_score=cadence_feedback.exact_evidence_support_score,
        exact_feedback_confirmation_count=cadence_feedback.exact_feedback_confirmation_count,
        exact_feedback_relief_count=cadence_feedback.exact_feedback_relief_count,
        window_entry_count=len(window_entries),
        window_start_sequence_number=window_entries[0].sequence_number if window_entries else None,
        window_end_sequence_number=window_entries[-1].sequence_number if window_entries else None,
        latest_monthly_digest_id=latest.monthly_digest_id if latest else None,
        latest_doctrine_memory_classification=latest.doctrine_memory_classification if latest else None,
        latest_drift_classification=latest.latest_drift_classification if latest else None,
        quarterly_review_classification=quarterly_classification,
        monthly_classification_counts=monthly_classification_counts,
        observed_monthly_digest_ids=observed_monthly_digest_ids,
        recurring_patterns=recurring_patterns,
        operator_actions=operator_actions,
        summary_line=summary_line,
    )

def _find_quarterly_review_report_path(*, manifest: OracleQuarterlyReviewEvidenceManifest, manifest_path: Path, repo_root: Path) -> Path:
    for subject in manifest.subjects:
        if subject.name == "ORACLE_QUARTERLY_REVIEW.json":
            resolved = advisory_resolve_existing_path(subject.path, repo_root=repo_root, preferred_parent=manifest_path.parent)
            if resolved is None:
                fallback = manifest_path.parent / Path(subject.path).name
                if fallback.exists():
                    return fallback.resolve()
                raise FileNotFoundError(f"oracle quarterly review report subject missing from evidence chain: {subject.path}")
            return resolved
    raise FileNotFoundError("oracle quarterly review evidence manifest does not include ORACLE_QUARTERLY_REVIEW.json")

def _load_quarterly_review_report(*, manifest: OracleQuarterlyReviewEvidenceManifest, manifest_path: Path, repo_root: Path) -> OracleQuarterlyReviewReport:
    report_path = _find_quarterly_review_report_path(manifest=manifest, manifest_path=manifest_path, repo_root=repo_root)
    return OracleQuarterlyReviewReport.model_validate(json.loads(report_path.read_text(encoding="utf-8")))

def build_oracle_quarterly_review_evidence_bundle(
    *,
    source_monthly_lane_path: Path,
    report_path: Path,
    markdown_path: Path,
    repo_root: Optional[Path] = None,
    signing_private_key_path: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> tuple[OracleQuarterlyReviewEvidenceManifest, DsseEnvelope | None]:
    repo_root = (repo_root or Path.cwd()).resolve()
    source_monthly_lane_path = source_monthly_lane_path.resolve()
    report_path = report_path.resolve()
    markdown_path = markdown_path.resolve()

    report = OracleQuarterlyReviewReport.model_validate(json.loads(report_path.read_text(encoding="utf-8")))
    quarterly_review_id = _sha256_bytes(
        _json_canonical_bytes(
            {
                "lane_id": report.lane_id,
                "quarterly_review_classification": report.quarterly_review_classification,
                "window_end_sequence_number": report.window_end_sequence_number,
                "observed_monthly_digest_ids": report.observed_monthly_digest_ids,
                "summary_line": report.summary_line,
            }
        )
    )
    return build_signed_evidence_manifest(
        artifact_paths=(source_monthly_lane_path, report_path, markdown_path),
        repo_root=repo_root,
        artifact_descriptor=_artifact_descriptor,
        normalize_path=_normalize_path,
        manifest_factory=lambda *, subjects, missing_artifact_paths, integrity_status: OracleQuarterlyReviewEvidenceManifest(
            generated_at_utc=now_utc or advisory_utc_now(),
            quarterly_review_id=quarterly_review_id,
            lane_id=report.lane_id,
            execution_authority="ADVISORY_ONLY",
            source_monthly_lane_path=_normalize_path(source_monthly_lane_path),
            quarterly_review_classification=report.quarterly_review_classification,
            window_entry_count=report.window_entry_count,
            window_end_sequence_number=report.window_end_sequence_number,
            latest_monthly_digest_id=report.latest_monthly_digest_id,
            latest_doctrine_memory_classification=report.latest_doctrine_memory_classification,
            latest_drift_classification=report.latest_drift_classification,
            integrity_status=integrity_status,
            subjects=subjects,
            missing_artifact_paths=missing_artifact_paths,
            summary_line=report.summary_line,
        ),
        payload_type=_ORACLE_QUARTERLY_REVIEW_PAYLOAD_TYPE,
        signing_private_key_path=signing_private_key_path,
        json_canonical_bytes=_json_canonical_bytes,
        sign_dsse_payload=_sign_dsse_payload,
    )

def verify_oracle_quarterly_review_evidence_bundle(
    *,
    manifest_path: Path,
    repo_root: Optional[Path] = None,
    dsse_path: Optional[Path] = None,
    public_key_path: Optional[Path] = None,
) -> OracleQuarterlyReviewEvidenceVerification:
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest_path = manifest_path.resolve()
    manifest = OracleQuarterlyReviewEvidenceManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    return build_evidence_verification(
        manifest=manifest,
        manifest_path=manifest_path,
        repo_root=repo_root,
        resolver=advisory_resolve_existing_path,
        sha256_file=_sha256_file,
        dsse_path=dsse_path,
        public_key_path=public_key_path,
        payload_type=_ORACLE_QUARTERLY_REVIEW_PAYLOAD_TYPE,
        json_canonical_bytes=_json_canonical_bytes,
        dsse_model=DsseEnvelope,
        verify_dsse_envelope=_verify_dsse_envelope,
        verification_factory=OracleQuarterlyReviewEvidenceVerification,
        verified_at_utc=advisory_utc_now(),
        normalize_path=_normalize_path,
    )

def append_oracle_quarterly_review_to_lane(
    *,
    manifest_path: Path,
    verification: OracleQuarterlyReviewEvidenceVerification,
    lane_path: Path,
    repo_root: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> OracleQuarterlyLaneEntry:
    if verification.status != "VERIFIED":
        raise ValueError("oracle quarterly review evidence must verify before it can be appended to the quarterly lane")
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest_path = manifest_path.resolve()
    lane_path = lane_path.resolve()
    manifest = OracleQuarterlyReviewEvidenceManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))

    entries: list[OracleQuarterlyLaneEntry] = []
    if lane_path.exists():
        for raw in lane_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            entries.append(OracleQuarterlyLaneEntry.model_validate(json.loads(raw)))

    sequence_number = len(entries)
    previous_entry_hash = entries[-1].entry_hash if entries else None
    lane_id = lane_path.stem
    entry_payload = {
        "lane_id": lane_id,
        "sequence_number": sequence_number,
        "quarterly_review_id": manifest.quarterly_review_id,
        "previous_entry_hash": previous_entry_hash,
        "manifest_sha256": _sha256_file(manifest_path),
        "quarterly_review_classification": manifest.quarterly_review_classification,
        "latest_monthly_digest_id": manifest.latest_monthly_digest_id,
        "evidence_status": verification.status,
        "summary_line": manifest.summary_line,
    }
    entry_hash = _sha256_bytes(_json_canonical_bytes(entry_payload))
    entry_id = _sha256_bytes(_json_canonical_bytes({"lane_id": lane_id, "sequence_number": sequence_number, "entry_hash": entry_hash}))
    try:
        manifest_ref = manifest_path.relative_to(repo_root)
    except ValueError:
        manifest_ref = manifest_path
    entry = OracleQuarterlyLaneEntry(
        appended_at_utc=now_utc or advisory_utc_now(),
        lane_id=lane_id,
        sequence_number=sequence_number,
        entry_id=entry_id,
        quarterly_review_id=manifest.quarterly_review_id,
        previous_entry_hash=previous_entry_hash,
        entry_hash=entry_hash,
        manifest_path=_normalize_path(manifest_ref),
        manifest_sha256=_sha256_file(manifest_path),
        quarterly_review_classification=manifest.quarterly_review_classification,
        latest_monthly_digest_id=manifest.latest_monthly_digest_id,
        evidence_status=verification.status,
        summary_line=manifest.summary_line,
    )
    lane_path.parent.mkdir(parents=True, exist_ok=True)
    with lane_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry.model_dump(mode="json"), separators=(",", ":"), default=str) + "\n")
    return entry


def generate_oracle_semiannual_audit(*, lane_path: Path, window_size: int = 2, repo_root: Optional[Path] = None, search_root: Optional[Path] = None, now_utc: Optional[datetime] = None) -> OracleSemiannualAuditReport:
    lane_path = lane_path.resolve()
    entries: list[OracleQuarterlyLaneEntry] = []
    if lane_path.exists():
        for raw in lane_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            entries.append(OracleQuarterlyLaneEntry.model_validate(json.loads(raw)))
    window_entries = entries[-max(window_size, 1):]
    quarterly_classification_counts: dict[str, int] = {}
    observed_quarterly_review_ids: list[str] = []
    recurring_patterns: list[str] = []
    for entry in window_entries:
        observed_quarterly_review_ids.append(entry.quarterly_review_id)
        quarterly_classification_counts[entry.quarterly_review_classification] = quarterly_classification_counts.get(entry.quarterly_review_classification, 0) + 1

    latest = window_entries[-1] if window_entries else None
    exact_evidence_support_score = max((float(getattr(entry, "exact_evidence_support_score", 0.0) or 0.0) for entry in window_entries), default=0.0)
    exact_feedback_confirmation_count = sum(int(getattr(entry, "exact_feedback_confirmation_count", 0) or 0) for entry in window_entries)
    exact_feedback_relief_count = sum(int(getattr(entry, "exact_feedback_relief_count", 0) or 0) for entry in window_entries)
    strategic_search_root = _default_constitutional_search_root(lane_path=lane_path, repo_root=repo_root, search_root=search_root)
    strategic_stack_evidence_count = _count_valid_strategic_stack_manifests(search_root=strategic_search_root)
    strategic_stack_requirement_met = strategic_stack_evidence_count > 0
    strategic_backing_classification = "SEALED_STRATEGIC_STACK_BACKED" if strategic_stack_requirement_met else ("DOCTRINE_ONLY_LADDER_BACKED" if window_entries else "NO_STRATEGIC_STACK_HISTORY")
    cadence_feedback = summarize_exact_cadence_feedback(repo_root=repo_root, search_root=search_root, window_size=max(window_size * 8, 1))
    evidence_gap_count = quarterly_classification_counts.get("QUARTERLY_EVIDENCE_GAP", 0)
    repair_count = quarterly_classification_counts.get("QUARTERLY_REPAIR_STRUCTURAL", 0)
    retrain_count = quarterly_classification_counts.get("QUARTERLY_RETRAIN_STRUCTURAL", 0)
    defensive_count = quarterly_classification_counts.get("QUARTERLY_DEFENSIVE_STRUCTURAL", 0)
    heightened_count = quarterly_classification_counts.get("QUARTERLY_HEIGHTENED_WATCH", 0)

    semiannual_classification: OracleSemiannualAuditClassification = "SEMIANNUAL_STABLE_BASELINE"
    if evidence_gap_count >= 1 or (latest is not None and latest.evidence_status != "VERIFIED"):
        semiannual_classification = "SEMIANNUAL_EVIDENCE_GAP"
        recurring_patterns.append("At least one quarterly review lost verification integrity; repair quarterly evidence before trusting the semiannual audit.")
    elif repair_count >= 2 or (latest is not None and latest.quarterly_review_classification == "QUARTERLY_REPAIR_STRUCTURAL"):
        semiannual_classification = "SEMIANNUAL_REPAIR_STRUCTURAL"
        recurring_patterns.append("Repair-structural quarterly review repeated across the semiannual window, indicating sustained governance instability.")
    elif retrain_count >= 2 or (latest is not None and latest.quarterly_review_classification == "QUARTERLY_RETRAIN_STRUCTURAL"):
        semiannual_classification = "SEMIANNUAL_RETRAIN_STRUCTURAL"
        recurring_patterns.append("Retrain-structural quarterly review repeated across the semiannual window and should be treated as deepening model-health pressure.")
    elif defensive_count >= 2 or (latest is not None and latest.quarterly_review_classification == "QUARTERLY_DEFENSIVE_STRUCTURAL"):
        semiannual_classification = "SEMIANNUAL_DEFENSIVE_STRUCTURAL"
        recurring_patterns.append("Defensive quarterly doctrine persisted across the semiannual window; stress carryover appears sustained rather than cyclical.")
    elif heightened_count >= 2 or (latest is not None and latest.quarterly_review_classification == "QUARTERLY_HEIGHTENED_WATCH"):
        semiannual_classification = "SEMIANNUAL_HEIGHTENED_WATCH"
        recurring_patterns.append("Heightened-watch quarterly doctrine remained active across the semiannual window and warrants continued scrutiny before confidence restoration.")
    elif window_entries:
        recurring_patterns.append("Semiannual doctrine audit remained within stable baseline bounds.")
    else:
        recurring_patterns.append("No quarterly doctrine history exists yet for a semiannual audit.")

    if repair_count and retrain_count:
        recurring_patterns.append("Repair-structural and retrain-structural quarterly outcomes overlapped; do not over-ascribe model decay when governance hygiene remains unstable.")
    if defensive_count and heightened_count:
        recurring_patterns.append("Heightened-watch and defensive quarterly outcomes both appeared within the semiannual window; preserve the quarterly lane so sustained stress remains auditable.")
    if cadence_feedback.exact_feedback_confirmation_count >= 5:
        recurring_patterns.append("Repeated exact sealed confirmations persisted long enough to become a semiannual cadence trigger for the directly supported clauses.")
    elif cadence_feedback.exact_feedback_relief_count >= 5 and cadence_feedback.exact_feedback_confirmation_count == 0:
        recurring_patterns.append("Repeated exact sealed relieving outcomes persisted long enough to justify bounded semiannual cadence relaxation for the directly supported clauses.")
    if strategic_stack_requirement_met:
        recurring_patterns.append("Semiannual audit is backed by at least one sealed strategic stack evidence bundle, so medium-horizon doctrine remains tied to replayable strategist epochs.")
    elif window_entries:
        recurring_patterns.append("Semiannual audit is currently backed only by the doctrine ladder; seal strategic stack history before treating medium-horizon doctrine as strategist-grounded.")
    else:
        recurring_patterns.append("No indexed strategic stack history was found while building the semiannual audit.")

    operator_actions = [
        "Treat the semiannual audit as advisory governance memory derived from signed quarterly review evidence and an append-only quarterly lane.",
        "Preserve the quarterly lane, quarterly review evidence manifests, and linked monthly lane together so the semiannual audit remains replayable.",
    ]
    if semiannual_classification == "SEMIANNUAL_EVIDENCE_GAP":
        operator_actions.append("Repair or regenerate missing quarterly evidence before relying on semiannual doctrine summaries.")
    elif semiannual_classification == "SEMIANNUAL_REPAIR_STRUCTURAL":
        operator_actions.append("Escalate governance and evidence remediation as a sustained semiannual concern.")
    elif semiannual_classification == "SEMIANNUAL_RETRAIN_STRUCTURAL":
        operator_actions.append("Escalate strategy forensic and retrain review as a sustained semiannual concern rather than a temporary fluctuation.")
    elif semiannual_classification == "SEMIANNUAL_DEFENSIVE_STRUCTURAL":
        operator_actions.append("Maintain defensive research doctrine and avoid confidence-heavy interpretation until semiannual stress recedes.")
    elif semiannual_classification == "SEMIANNUAL_HEIGHTENED_WATCH":
        operator_actions.append("Increase semiannual doctrine review cadence and compare the next quarterly review against the latest structural drivers.")
    else:
        operator_actions.append("Maintain baseline semiannual doctrine review cadence; no sustained trigger currently requires escalation.")
    if cadence_feedback.exact_feedback_confirmation_count >= 5:
        operator_actions.append("Escalate semiannual doctrine review cadence because repeated exact sealed confirmations have become a sustained structural signal.")
    elif cadence_feedback.exact_feedback_relief_count >= 5 and cadence_feedback.exact_feedback_confirmation_count == 0:
        operator_actions.append("Maintain semiannual doctrine review but allow repeated exact sealed relieving outcomes to soften cadence for the directly supported clauses.")
    elif cadence_feedback.exact_evidence_support_score >= 0.85:
        operator_actions.append("Anchor semiannual doctrine cadence to the repeated exact sealed subjects rather than broadening the response across unsupported clauses.")
    if strategic_stack_requirement_met:
        operator_actions.append("Treat semiannual doctrine summaries as strategist-grounded only because sealed strategic stack history is present alongside the quarterly ladder.")
    elif window_entries:
        operator_actions.append("Do not treat semiannual doctrine summaries as strategist-grounded yet; this audit is doctrine-only until sealed strategic stack history is indexed.")
    else:
        operator_actions.append("Index and seal strategic stack evidence before relying on semiannual doctrine summaries for strategist claims.")

    summary_line = (
        f"Oracle semiannual audit={semiannual_classification}; backing={strategic_backing_classification}; window_entries={len(window_entries)}; strategic_stack={strategic_stack_evidence_count}; "
        f"evidence_gap={evidence_gap_count}; repair={repair_count}; retrain={retrain_count}; "
        f"defensive={defensive_count}; heightened={heightened_count}; "
        f"exact_support={cadence_feedback.exact_evidence_support_score:.2f}; exact_confirm={cadence_feedback.exact_feedback_confirmation_count}; exact_relief={cadence_feedback.exact_feedback_relief_count}"
    )
    return OracleSemiannualAuditReport(
        generated_at_utc=now_utc or advisory_utc_now(),
        lane_id=lane_path.stem,
        exact_evidence_support_score=cadence_feedback.exact_evidence_support_score,
        exact_feedback_confirmation_count=cadence_feedback.exact_feedback_confirmation_count,
        exact_feedback_relief_count=cadence_feedback.exact_feedback_relief_count,
        window_entry_count=len(window_entries),
        window_start_sequence_number=window_entries[0].sequence_number if window_entries else None,
        window_end_sequence_number=window_entries[-1].sequence_number if window_entries else None,
        latest_quarterly_review_id=latest.quarterly_review_id if latest else None,
        latest_quarterly_review_classification=latest.quarterly_review_classification if latest else None,
        semiannual_audit_classification=semiannual_classification,
        strategic_backing_classification=strategic_backing_classification,
        strategic_stack_evidence_count=strategic_stack_evidence_count,
        strategic_stack_requirement_met=strategic_stack_requirement_met,
        quarterly_classification_counts=quarterly_classification_counts,
        observed_quarterly_review_ids=observed_quarterly_review_ids,
        recurring_patterns=recurring_patterns,
        operator_actions=operator_actions,
        summary_line=summary_line,
    )

def _find_semiannual_audit_report_path(*, manifest: OracleSemiannualAuditEvidenceManifest, manifest_path: Path, repo_root: Path) -> Path:
    for subject in manifest.subjects:
        if subject.name == "ORACLE_SEMIANNUAL_AUDIT.json":
            resolved = advisory_resolve_existing_path(subject.path, repo_root=repo_root, preferred_parent=manifest_path.parent)
            if resolved is None:
                fallback = manifest_path.parent / Path(subject.path).name
                if fallback.exists():
                    return fallback.resolve()
                raise FileNotFoundError(f"oracle semiannual audit report subject missing from evidence chain: {subject.path}")
            return resolved
    raise FileNotFoundError("oracle semiannual audit evidence manifest does not include ORACLE_SEMIANNUAL_AUDIT.json")

def _load_semiannual_audit_report(*, manifest: OracleSemiannualAuditEvidenceManifest, manifest_path: Path, repo_root: Path) -> OracleSemiannualAuditReport:
    report_path = _find_semiannual_audit_report_path(manifest=manifest, manifest_path=manifest_path, repo_root=repo_root)
    return OracleSemiannualAuditReport.model_validate(json.loads(report_path.read_text(encoding="utf-8")))

def build_oracle_semiannual_audit_evidence_bundle(
    *,
    source_quarterly_lane_path: Path,
    report_path: Path,
    markdown_path: Path,
    repo_root: Optional[Path] = None,
    signing_private_key_path: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> tuple[OracleSemiannualAuditEvidenceManifest, DsseEnvelope | None]:
    repo_root = (repo_root or Path.cwd()).resolve()
    source_quarterly_lane_path = source_quarterly_lane_path.resolve()
    report_path = report_path.resolve()
    markdown_path = markdown_path.resolve()

    report = OracleSemiannualAuditReport.model_validate(json.loads(report_path.read_text(encoding="utf-8")))
    semiannual_audit_id = _sha256_bytes(
        _json_canonical_bytes(
            {
                "lane_id": report.lane_id,
                "semiannual_audit_classification": report.semiannual_audit_classification,
                "window_end_sequence_number": report.window_end_sequence_number,
                "observed_quarterly_review_ids": report.observed_quarterly_review_ids,
                "summary_line": report.summary_line,
            }
        )
    )
    return build_signed_evidence_manifest(
        artifact_paths=(source_quarterly_lane_path, report_path, markdown_path),
        repo_root=repo_root,
        artifact_descriptor=_artifact_descriptor,
        normalize_path=_normalize_path,
        manifest_factory=lambda *, subjects, missing_artifact_paths, integrity_status: OracleSemiannualAuditEvidenceManifest(
            generated_at_utc=now_utc or advisory_utc_now(),
            semiannual_audit_id=semiannual_audit_id,
            lane_id=report.lane_id,
            execution_authority="ADVISORY_ONLY",
            source_quarterly_lane_path=_normalize_path(source_quarterly_lane_path),
            semiannual_audit_classification=report.semiannual_audit_classification,
            strategic_backing_classification=report.strategic_backing_classification,
            strategic_stack_evidence_count=report.strategic_stack_evidence_count,
            strategic_stack_requirement_met=report.strategic_stack_requirement_met,
            window_entry_count=report.window_entry_count,
            window_end_sequence_number=report.window_end_sequence_number,
            latest_quarterly_review_id=report.latest_quarterly_review_id,
            latest_quarterly_review_classification=report.latest_quarterly_review_classification,
            integrity_status=integrity_status,
            subjects=subjects,
            missing_artifact_paths=missing_artifact_paths,
            summary_line=report.summary_line,
        ),
        payload_type=_ORACLE_SEMIANNUAL_AUDIT_PAYLOAD_TYPE,
        signing_private_key_path=signing_private_key_path,
        json_canonical_bytes=_json_canonical_bytes,
        sign_dsse_payload=_sign_dsse_payload,
    )

def verify_oracle_semiannual_audit_evidence_bundle(
    *,
    manifest_path: Path,
    repo_root: Optional[Path] = None,
    dsse_path: Optional[Path] = None,
    public_key_path: Optional[Path] = None,
) -> OracleSemiannualAuditEvidenceVerification:
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest_path = manifest_path.resolve()
    manifest = OracleSemiannualAuditEvidenceManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    return build_evidence_verification(
        manifest=manifest,
        manifest_path=manifest_path,
        repo_root=repo_root,
        resolver=advisory_resolve_existing_path,
        sha256_file=_sha256_file,
        dsse_path=dsse_path,
        public_key_path=public_key_path,
        payload_type=_ORACLE_SEMIANNUAL_AUDIT_PAYLOAD_TYPE,
        json_canonical_bytes=_json_canonical_bytes,
        dsse_model=DsseEnvelope,
        verify_dsse_envelope=_verify_dsse_envelope,
        verification_factory=OracleSemiannualAuditEvidenceVerification,
        verified_at_utc=advisory_utc_now(),
        normalize_path=_normalize_path,
    )

def append_oracle_semiannual_audit_to_lane(
    *,
    manifest_path: Path,
    verification: OracleSemiannualAuditEvidenceVerification,
    lane_path: Path,
    repo_root: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> OracleSemiannualLaneEntry:
    if verification.status != "VERIFIED":
        raise ValueError("oracle semiannual audit evidence must verify before it can be appended to the semiannual lane")
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest_path = manifest_path.resolve()
    lane_path = lane_path.resolve()
    manifest = OracleSemiannualAuditEvidenceManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))

    entries: list[OracleSemiannualLaneEntry] = []
    if lane_path.exists():
        for raw in lane_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            entries.append(OracleSemiannualLaneEntry.model_validate(json.loads(raw)))

    sequence_number = len(entries)
    previous_entry_hash = entries[-1].entry_hash if entries else None
    lane_id = lane_path.stem
    entry_payload = {
        "lane_id": lane_id,
        "sequence_number": sequence_number,
        "semiannual_audit_id": manifest.semiannual_audit_id,
        "previous_entry_hash": previous_entry_hash,
        "manifest_sha256": _sha256_file(manifest_path),
        "semiannual_audit_classification": manifest.semiannual_audit_classification,
        "strategic_backing_classification": manifest.strategic_backing_classification,
        "strategic_stack_evidence_count": manifest.strategic_stack_evidence_count,
        "strategic_stack_requirement_met": manifest.strategic_stack_requirement_met,
        "latest_quarterly_review_id": manifest.latest_quarterly_review_id,
        "evidence_status": verification.status,
        "summary_line": manifest.summary_line,
    }
    entry_hash = _sha256_bytes(_json_canonical_bytes(entry_payload))
    entry_id = _sha256_bytes(_json_canonical_bytes({"lane_id": lane_id, "sequence_number": sequence_number, "entry_hash": entry_hash}))
    try:
        manifest_ref = manifest_path.relative_to(repo_root)
    except ValueError:
        manifest_ref = manifest_path
    entry = OracleSemiannualLaneEntry(
        appended_at_utc=now_utc or advisory_utc_now(),
        lane_id=lane_id,
        sequence_number=sequence_number,
        entry_id=entry_id,
        semiannual_audit_id=manifest.semiannual_audit_id,
        previous_entry_hash=previous_entry_hash,
        entry_hash=entry_hash,
        manifest_path=_normalize_path(manifest_ref),
        manifest_sha256=_sha256_file(manifest_path),
        semiannual_audit_classification=manifest.semiannual_audit_classification,
        strategic_backing_classification=manifest.strategic_backing_classification,
        strategic_stack_evidence_count=manifest.strategic_stack_evidence_count,
        strategic_stack_requirement_met=manifest.strategic_stack_requirement_met,
        latest_quarterly_review_id=manifest.latest_quarterly_review_id,
        evidence_status=verification.status,
        summary_line=manifest.summary_line,
    )
    lane_path.parent.mkdir(parents=True, exist_ok=True)
    with lane_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry.model_dump(mode="json"), separators=(",", ":"), default=str) + "\n")
    return entry


def generate_oracle_annual_review(*, lane_path: Path, window_size: int = 2, repo_root: Optional[Path] = None, search_root: Optional[Path] = None, now_utc: Optional[datetime] = None) -> OracleAnnualReviewReport:
    lane_path = lane_path.resolve()
    entries: list[OracleSemiannualLaneEntry] = []
    if lane_path.exists():
        for raw in lane_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            entries.append(OracleSemiannualLaneEntry.model_validate(json.loads(raw)))
    window_entries = entries[-max(window_size, 1):]
    semiannual_classification_counts: dict[str, int] = {}
    observed_semiannual_audit_ids: list[str] = []
    recurring_patterns: list[str] = []
    for entry in window_entries:
        observed_semiannual_audit_ids.append(entry.semiannual_audit_id)
        semiannual_classification_counts[entry.semiannual_audit_classification] = semiannual_classification_counts.get(entry.semiannual_audit_classification, 0) + 1

    latest = window_entries[-1] if window_entries else None
    exact_evidence_support_score = max((float(getattr(entry, "exact_evidence_support_score", 0.0) or 0.0) for entry in window_entries), default=0.0)
    exact_feedback_confirmation_count = sum(int(getattr(entry, "exact_feedback_confirmation_count", 0) or 0) for entry in window_entries)
    exact_feedback_relief_count = sum(int(getattr(entry, "exact_feedback_relief_count", 0) or 0) for entry in window_entries)
    strategic_search_root = _default_constitutional_search_root(lane_path=lane_path, repo_root=repo_root, search_root=search_root)
    strategic_stack_evidence_count = _count_valid_strategic_stack_manifests(search_root=strategic_search_root)
    strategic_stack_requirement_met = strategic_stack_evidence_count > 0
    strategic_backing_classification = "SEALED_STRATEGIC_STACK_BACKED" if strategic_stack_requirement_met else ("DOCTRINE_ONLY_LADDER_BACKED" if window_entries else "NO_STRATEGIC_STACK_HISTORY")
    cadence_feedback = summarize_exact_cadence_feedback(repo_root=repo_root, search_root=search_root, window_size=max(window_size * 12, 1))
    evidence_gap_count = semiannual_classification_counts.get("SEMIANNUAL_EVIDENCE_GAP", 0)
    repair_count = semiannual_classification_counts.get("SEMIANNUAL_REPAIR_STRUCTURAL", 0)
    retrain_count = semiannual_classification_counts.get("SEMIANNUAL_RETRAIN_STRUCTURAL", 0)
    defensive_count = semiannual_classification_counts.get("SEMIANNUAL_DEFENSIVE_STRUCTURAL", 0)
    heightened_count = semiannual_classification_counts.get("SEMIANNUAL_HEIGHTENED_WATCH", 0)

    annual_classification: OracleAnnualReviewClassification = "ANNUAL_STABLE_BASELINE"
    if evidence_gap_count >= 1 or (latest is not None and latest.evidence_status != "VERIFIED"):
        annual_classification = "ANNUAL_EVIDENCE_GAP"
        recurring_patterns.append("At least one semiannual audit lost verification integrity; repair semiannual evidence before trusting the annual review.")
    elif repair_count >= 2 or (latest is not None and latest.semiannual_audit_classification == "SEMIANNUAL_REPAIR_STRUCTURAL"):
        annual_classification = "ANNUAL_REPAIR_STRUCTURAL"
        recurring_patterns.append("Repair-structural semiannual audit repeated across the annual window, indicating chronic governance instability.")
    elif retrain_count >= 2 or (latest is not None and latest.semiannual_audit_classification == "SEMIANNUAL_RETRAIN_STRUCTURAL"):
        annual_classification = "ANNUAL_RETRAIN_STRUCTURAL"
        recurring_patterns.append("Retrain-structural semiannual audit repeated across the annual window and should be treated as chronic model-health pressure.")
    elif defensive_count >= 2 or (latest is not None and latest.semiannual_audit_classification == "SEMIANNUAL_DEFENSIVE_STRUCTURAL"):
        annual_classification = "ANNUAL_DEFENSIVE_STRUCTURAL"
        recurring_patterns.append("Defensive semiannual doctrine persisted across the annual window; stress appears durable rather than cyclical.")
    elif heightened_count >= 2 or (latest is not None and latest.semiannual_audit_classification == "SEMIANNUAL_HEIGHTENED_WATCH"):
        annual_classification = "ANNUAL_HEIGHTENED_WATCH"
        recurring_patterns.append("Heightened-watch semiannual doctrine remained active across the annual window and warrants continued scrutiny before confidence restoration.")
    elif window_entries:
        recurring_patterns.append("Annual doctrine review remained within stable baseline bounds.")
    else:
        recurring_patterns.append("No semiannual doctrine history exists yet for an annual review.")

    if repair_count and retrain_count:
        recurring_patterns.append("Repair-structural and retrain-structural semiannual outcomes overlapped; do not over-ascribe chronic model decay when evidence hygiene remains unstable.")
    if defensive_count and heightened_count:
        recurring_patterns.append("Heightened-watch and defensive semiannual outcomes both appeared within the annual window; preserve the semiannual lane so durable stress remains auditable.")
    if cadence_feedback.exact_feedback_confirmation_count >= 6:
        recurring_patterns.append("Repeated exact sealed confirmations persisted long enough to become a chronic annual cadence signal for the directly supported clauses.")
    elif cadence_feedback.exact_feedback_relief_count >= 6 and cadence_feedback.exact_feedback_confirmation_count == 0:
        recurring_patterns.append("Repeated exact sealed relieving outcomes persisted long enough to justify bounded annual cadence relaxation for the directly supported clauses.")
    if strategic_stack_requirement_met:
        recurring_patterns.append("Annual review is backed by at least one sealed strategic stack evidence bundle, so long-horizon doctrine remains tied to replayable strategist epochs.")
    elif window_entries:
        recurring_patterns.append("Annual review is currently backed only by the doctrine ladder; seal strategic stack history before treating chronic doctrine as strategist-grounded.")
    else:
        recurring_patterns.append("No indexed strategic stack history was found while building the annual review.")

    operator_actions = [
        "Treat the annual review as advisory governance memory derived from signed semiannual audit evidence and an append-only semiannual lane.",
        "Preserve the semiannual lane, semiannual audit evidence manifests, and linked quarterly lane together so the annual review remains replayable.",
    ]
    if annual_classification == "ANNUAL_EVIDENCE_GAP":
        operator_actions.append("Repair or regenerate missing semiannual evidence before relying on annual doctrine summaries.")
    elif annual_classification == "ANNUAL_REPAIR_STRUCTURAL":
        operator_actions.append("Escalate governance and evidence remediation as a chronic annual concern.")
    elif annual_classification == "ANNUAL_RETRAIN_STRUCTURAL":
        operator_actions.append("Escalate strategy forensic and retrain review as a chronic annual concern rather than a temporary fluctuation.")
    elif annual_classification == "ANNUAL_DEFENSIVE_STRUCTURAL":
        operator_actions.append("Maintain defensive research doctrine and avoid confidence-heavy interpretation until annual stress materially recedes.")
    elif annual_classification == "ANNUAL_HEIGHTENED_WATCH":
        operator_actions.append("Increase annual doctrine review cadence and compare the next semiannual audit against the latest structural drivers.")
    else:
        operator_actions.append("Maintain baseline annual doctrine review cadence; no chronic trigger currently requires escalation.")
    if cadence_feedback.exact_feedback_confirmation_count >= 6:
        operator_actions.append("Escalate annual doctrine review cadence because repeated exact sealed confirmations now represent chronic supported pressure.")
    elif cadence_feedback.exact_feedback_relief_count >= 6 and cadence_feedback.exact_feedback_confirmation_count == 0:
        operator_actions.append("Maintain annual doctrine review but allow repeated exact sealed relieving outcomes to soften cadence for the directly supported clauses.")
    elif cadence_feedback.exact_evidence_support_score >= 0.85:
        operator_actions.append("Anchor annual doctrine cadence to the repeated exact sealed subjects instead of broadening chronic conclusions beyond supported clauses.")
    if strategic_stack_requirement_met:
        operator_actions.append("Treat chronic annual doctrine summaries as strategist-grounded only because sealed strategic stack history is present alongside the semiannual ladder.")
    elif window_entries:
        operator_actions.append("Do not treat chronic annual doctrine summaries as strategist-grounded yet; this review is doctrine-only until sealed strategic stack history is indexed.")
    else:
        operator_actions.append("Index and seal strategic stack evidence before relying on annual doctrine summaries for strategist claims.")

    summary_line = (
        f"Oracle annual review={annual_classification}; backing={strategic_backing_classification}; window_entries={len(window_entries)}; strategic_stack={strategic_stack_evidence_count}; "
        f"evidence_gap={evidence_gap_count}; repair={repair_count}; retrain={retrain_count}; "
        f"defensive={defensive_count}; heightened={heightened_count}; "
        f"exact_support={cadence_feedback.exact_evidence_support_score:.2f}; exact_confirm={cadence_feedback.exact_feedback_confirmation_count}; exact_relief={cadence_feedback.exact_feedback_relief_count}"
    )
    return OracleAnnualReviewReport(
        generated_at_utc=now_utc or advisory_utc_now(),
        lane_id=lane_path.stem,
        exact_evidence_support_score=cadence_feedback.exact_evidence_support_score,
        exact_feedback_confirmation_count=cadence_feedback.exact_feedback_confirmation_count,
        exact_feedback_relief_count=cadence_feedback.exact_feedback_relief_count,
        window_entry_count=len(window_entries),
        window_start_sequence_number=window_entries[0].sequence_number if window_entries else None,
        window_end_sequence_number=window_entries[-1].sequence_number if window_entries else None,
        latest_semiannual_audit_id=latest.semiannual_audit_id if latest else None,
        latest_semiannual_audit_classification=latest.semiannual_audit_classification if latest else None,
        annual_review_classification=annual_classification,
        strategic_backing_classification=strategic_backing_classification,
        strategic_stack_evidence_count=strategic_stack_evidence_count,
        strategic_stack_requirement_met=strategic_stack_requirement_met,
        semiannual_classification_counts=semiannual_classification_counts,
        observed_semiannual_audit_ids=observed_semiannual_audit_ids,
        recurring_patterns=recurring_patterns,
        operator_actions=operator_actions,
        summary_line=summary_line,
    )

def _find_annual_review_report_path(*, manifest: OracleAnnualReviewEvidenceManifest, manifest_path: Path, repo_root: Path) -> Path:
    for subject in manifest.subjects:
        if subject.path.endswith("ORACLE_ANNUAL_REVIEW.json"):
            resolved = advisory_resolve_existing_path(subject.path, repo_root=repo_root, preferred_parent=manifest_path.parent)
            if resolved is None:
                raise FileNotFoundError(f"oracle annual review report subject missing from evidence chain: {subject.path}")
            return resolved
    raise FileNotFoundError("oracle annual review evidence manifest does not include ORACLE_ANNUAL_REVIEW.json")

def _load_annual_review_report(*, manifest: OracleAnnualReviewEvidenceManifest, manifest_path: Path, repo_root: Path) -> OracleAnnualReviewReport:
    report_path = _find_annual_review_report_path(manifest=manifest, manifest_path=manifest_path, repo_root=repo_root)
    return OracleAnnualReviewReport.model_validate(json.loads(report_path.read_text(encoding="utf-8")))

def build_oracle_annual_review_evidence_bundle(
    *,
    source_semiannual_lane_path: Path,
    report_path: Path,
    markdown_path: Path,
    repo_root: Optional[Path] = None,
    signing_private_key_path: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> tuple[OracleAnnualReviewEvidenceManifest, DsseEnvelope | None]:
    repo_root = (repo_root or Path.cwd()).resolve()
    source_semiannual_lane_path = source_semiannual_lane_path.resolve()
    report_path = report_path.resolve()
    markdown_path = markdown_path.resolve()

    report = OracleAnnualReviewReport.model_validate(json.loads(report_path.read_text(encoding="utf-8")))
    annual_review_id = _sha256_bytes(
        _json_canonical_bytes(
            {
                "lane_id": report.lane_id,
                "annual_review_classification": report.annual_review_classification,
                "window_end_sequence_number": report.window_end_sequence_number,
                "observed_semiannual_audit_ids": report.observed_semiannual_audit_ids,
                "summary_line": report.summary_line,
            }
        )
    )
    return build_signed_evidence_manifest(
        artifact_paths=(source_semiannual_lane_path, report_path, markdown_path),
        repo_root=repo_root,
        artifact_descriptor=_artifact_descriptor,
        normalize_path=_normalize_path,
        manifest_factory=lambda *, subjects, missing_artifact_paths, integrity_status: OracleAnnualReviewEvidenceManifest(
            generated_at_utc=now_utc or advisory_utc_now(),
            annual_review_id=annual_review_id,
            lane_id=report.lane_id,
            execution_authority="ADVISORY_ONLY",
            source_semiannual_lane_path=_normalize_path(source_semiannual_lane_path),
            annual_review_classification=report.annual_review_classification,
            strategic_backing_classification=report.strategic_backing_classification,
            strategic_stack_evidence_count=report.strategic_stack_evidence_count,
            strategic_stack_requirement_met=report.strategic_stack_requirement_met,
            window_entry_count=report.window_entry_count,
            window_end_sequence_number=report.window_end_sequence_number,
            latest_semiannual_audit_id=report.latest_semiannual_audit_id,
            latest_semiannual_audit_classification=report.latest_semiannual_audit_classification,
            integrity_status=integrity_status,
            subjects=subjects,
            missing_artifact_paths=missing_artifact_paths,
            summary_line=report.summary_line,
        ),
        payload_type=_ORACLE_ANNUAL_REVIEW_PAYLOAD_TYPE,
        signing_private_key_path=signing_private_key_path,
        json_canonical_bytes=_json_canonical_bytes,
        sign_dsse_payload=_sign_dsse_payload,
    )

def verify_oracle_annual_review_evidence_bundle(
    *,
    manifest_path: Path,
    repo_root: Optional[Path] = None,
    dsse_path: Optional[Path] = None,
    public_key_path: Optional[Path] = None,
) -> OracleAnnualReviewEvidenceVerification:
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest_path = manifest_path.resolve()
    manifest = OracleAnnualReviewEvidenceManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    return build_evidence_verification(
        manifest=manifest,
        manifest_path=manifest_path,
        repo_root=repo_root,
        resolver=advisory_resolve_existing_path,
        sha256_file=_sha256_file,
        dsse_path=dsse_path,
        public_key_path=public_key_path,
        payload_type=_ORACLE_ANNUAL_REVIEW_PAYLOAD_TYPE,
        json_canonical_bytes=_json_canonical_bytes,
        dsse_model=DsseEnvelope,
        verify_dsse_envelope=_verify_dsse_envelope,
        verification_factory=OracleAnnualReviewEvidenceVerification,
        verified_at_utc=advisory_utc_now(),
        normalize_path=_normalize_path,
    )

def append_oracle_annual_review_to_lane(
    *,
    manifest_path: Path,
    verification: OracleAnnualReviewEvidenceVerification,
    lane_path: Path,
    repo_root: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> OracleAnnualLaneEntry:
    if verification.status != "VERIFIED":
        raise ValueError("oracle annual review evidence must verify before it can be appended to the annual lane")
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest_path = manifest_path.resolve()
    lane_path = lane_path.resolve()
    manifest = OracleAnnualReviewEvidenceManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))

    entries: list[OracleAnnualLaneEntry] = []
    if lane_path.exists():
        for raw in lane_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            entries.append(OracleAnnualLaneEntry.model_validate(json.loads(raw)))

    sequence_number = len(entries)
    previous_entry_hash = entries[-1].entry_hash if entries else None
    lane_id = lane_path.stem
    entry_payload = {
        "lane_id": lane_id,
        "sequence_number": sequence_number,
        "annual_review_id": manifest.annual_review_id,
        "previous_entry_hash": previous_entry_hash,
        "manifest_sha256": _sha256_file(manifest_path),
        "annual_review_classification": manifest.annual_review_classification,
        "strategic_backing_classification": manifest.strategic_backing_classification,
        "strategic_stack_evidence_count": manifest.strategic_stack_evidence_count,
        "strategic_stack_requirement_met": manifest.strategic_stack_requirement_met,
        "latest_semiannual_audit_id": manifest.latest_semiannual_audit_id,
        "evidence_status": verification.status,
        "summary_line": manifest.summary_line,
    }
    entry_hash = _sha256_bytes(_json_canonical_bytes(entry_payload))
    entry_id = _sha256_bytes(_json_canonical_bytes({"lane_id": lane_id, "sequence_number": sequence_number, "entry_hash": entry_hash}))
    try:
        manifest_ref = manifest_path.relative_to(repo_root)
    except ValueError:
        manifest_ref = manifest_path
    entry = OracleAnnualLaneEntry(
        appended_at_utc=now_utc or advisory_utc_now(),
        lane_id=lane_id,
        sequence_number=sequence_number,
        entry_id=entry_id,
        annual_review_id=manifest.annual_review_id,
        previous_entry_hash=previous_entry_hash,
        entry_hash=entry_hash,
        manifest_path=_normalize_path(manifest_ref),
        manifest_sha256=_sha256_file(manifest_path),
        annual_review_classification=manifest.annual_review_classification,
        strategic_backing_classification=manifest.strategic_backing_classification,
        strategic_stack_evidence_count=manifest.strategic_stack_evidence_count,
        strategic_stack_requirement_met=manifest.strategic_stack_requirement_met,
        latest_semiannual_audit_id=manifest.latest_semiannual_audit_id,
        evidence_status=verification.status,
        summary_line=manifest.summary_line,
    )
    lane_path.parent.mkdir(parents=True, exist_ok=True)
    with lane_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry.model_dump(mode="json"), separators=(",", ":"), default=str) + "\n")
    return entry
