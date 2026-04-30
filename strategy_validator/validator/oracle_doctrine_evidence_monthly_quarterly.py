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


from strategy_validator.validator.oracle_doctrine_evidence_foundations import (
    _ORACLE_ANNUAL_REVIEW_PAYLOAD_TYPE,
    _ORACLE_MONTHLY_DIGEST_PAYLOAD_TYPE,
    _ORACLE_QUARTERLY_REVIEW_PAYLOAD_TYPE,
    _ORACLE_SEMIANNUAL_AUDIT_PAYLOAD_TYPE,
    _count_valid_strategic_stack_manifests,
    _default_constitutional_search_root,
)

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

OracleMonthlyDigestReport.model_rebuild(force=True)
OracleMonthlyDigestEvidenceManifest.model_rebuild(force=True)
OracleMonthlyDigestEvidenceVerification.model_rebuild(force=True)
OracleMonthlyLaneEntry.model_rebuild(force=True)
OracleQuarterlyReviewReport.model_rebuild(force=True)
OracleQuarterlyReviewEvidenceManifest.model_rebuild(force=True)
OracleQuarterlyReviewEvidenceVerification.model_rebuild(force=True)
OracleQuarterlyLaneEntry.model_rebuild(force=True)

__all__ = [name for name in globals() if not name.startswith('__')]
