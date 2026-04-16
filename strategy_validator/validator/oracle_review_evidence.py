from __future__ import annotations

from strategy_validator.validator.oracle_transition_common import *  # noqa: F401,F403
from strategy_validator.validator.oracle_cadence_feedback import summarize_exact_cadence_feedback

from strategy_validator.validator.oracle_transition_common import (
    _artifact_descriptor,
    _json_canonical_bytes,
    _load_transition_report,
    _normalize_path,
    _sha256_bytes,
    _sha256_file,
    _sign_dsse_payload,
    _verify_dsse_envelope,
)

_ORACLE_TRANSITION_PAYLOAD_TYPE = "application/vnd.strategy-validator.oracle-transition.v1+json"


def build_oracle_transition_evidence_bundle(
    *,
    previous_manifest_path: Path,
    current_manifest_path: Path,
    report_path: Path,
    markdown_path: Path,
    repo_root: Optional[Path] = None,
    signing_private_key_path: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> tuple[OracleTransitionEvidenceManifest, DsseEnvelope | None]:
    repo_root = (repo_root or Path.cwd()).resolve()
    previous_manifest_path = previous_manifest_path.resolve()
    current_manifest_path = current_manifest_path.resolve()
    report_path = report_path.resolve()
    markdown_path = markdown_path.resolve()

    report = OracleStateTransitionReport.model_validate(json.loads(report_path.read_text(encoding="utf-8")))
    assembly = assemble_evidence_subjects(
        artifact_paths=(previous_manifest_path, current_manifest_path, report_path, markdown_path),
        repo_root=repo_root,
        artifact_descriptor=_artifact_descriptor,
        normalize_path=_normalize_path,
    )
    transition_id = _sha256_bytes(
        _json_canonical_bytes(
            {
                "previous_evidence_id": report.previous_evidence_id,
                "current_evidence_id": report.current_evidence_id,
                "transition_classification": report.transition_classification,
                "drift_score": report.drift_score,
                "current_input_timestamp_utc": report.current_input_timestamp_utc.isoformat(),
            }
        )
    )
    manifest = OracleTransitionEvidenceManifest(
        generated_at_utc=now_utc or advisory_utc_now(),
        transition_id=transition_id,
        universe_label=report.universe_label,
        execution_authority=report.execution_authority,
        previous_evidence_id=report.previous_evidence_id,
        current_evidence_id=report.current_evidence_id,
        previous_linked_closure_id=report.previous_linked_closure_id,
        current_linked_closure_id=report.current_linked_closure_id,
        transition_classification=report.transition_classification,
        drift_score=report.drift_score,
        integrity_status=assembly.integrity_status,
        subjects=assembly.subjects,
        missing_artifact_paths=assembly.missing_artifact_paths,
        summary_line=report.summary_line,
    )
    envelope = sign_manifest_envelope(
        manifest=manifest,
        payload_type=_ORACLE_TRANSITION_PAYLOAD_TYPE,
        signing_private_key_path=signing_private_key_path,
        json_canonical_bytes=_json_canonical_bytes,
        sign_dsse_payload=_sign_dsse_payload,
    )
    return manifest, envelope



def verify_oracle_transition_evidence_bundle(
    *,
    manifest_path: Path,
    repo_root: Optional[Path] = None,
    dsse_path: Optional[Path] = None,
    public_key_path: Optional[Path] = None,
) -> OracleTransitionEvidenceVerification:
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest_path = manifest_path.resolve()
    manifest = OracleTransitionEvidenceManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    return build_evidence_verification(
        manifest=manifest,
        manifest_path=manifest_path,
        repo_root=repo_root,
        resolver=advisory_resolve_existing_path,
        sha256_file=_sha256_file,
        dsse_path=dsse_path,
        public_key_path=public_key_path,
        payload_type=_ORACLE_TRANSITION_PAYLOAD_TYPE,
        json_canonical_bytes=_json_canonical_bytes,
        dsse_model=DsseEnvelope,
        verify_dsse_envelope=_verify_dsse_envelope,
        verification_factory=OracleTransitionEvidenceVerification,
        verified_at_utc=advisory_utc_now(),
        normalize_path=_normalize_path,
    )



def append_oracle_transition_to_lane(
    *,
    manifest_path: Path,
    verification: OracleTransitionEvidenceVerification,
    lane_path: Path,
    repo_root: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> OracleMemoryLaneEntry:
    manifest_path = manifest_path.resolve()
    lane_path = lane_path.resolve()
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest = OracleTransitionEvidenceManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    report = _load_transition_report(manifest=manifest, manifest_path=manifest_path, repo_root=repo_root)
    if verification.status != "VERIFIED":
        raise ValueError("oracle memory lane only accepts VERIFIED transition evidence")

    entries: list[OracleMemoryLaneEntry] = []
    if lane_path.exists():
        for raw in lane_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            entries.append(OracleMemoryLaneEntry.model_validate(json.loads(raw)))
    sequence_number = len(entries)
    previous_entry_hash = entries[-1].entry_hash if entries else None
    lane_id = lane_path.stem
    entry_seed = {
        "lane_id": lane_id,
        "sequence_number": sequence_number,
        "transition_id": manifest.transition_id,
        "previous_entry_hash": previous_entry_hash or "GENESIS",
        "manifest_sha256": _sha256_file(manifest_path),
        "transition_classification": manifest.transition_classification,
        "drift_score": manifest.drift_score,
        "current_input_timestamp_utc": report.current_input_timestamp_utc.isoformat(),
        "current_epistemic_status": report.current_epistemic_status,
        "current_recommended_global_action": report.current_recommended_global_action,
        "evidence_status": verification.status,
    }
    entry_hash = _sha256_bytes(_json_canonical_bytes(entry_seed))
    entry = OracleMemoryLaneEntry(
        appended_at_utc=now_utc or advisory_utc_now(),
        lane_id=lane_id,
        sequence_number=sequence_number,
        entry_id=_sha256_bytes(_json_canonical_bytes({"lane_id": lane_id, "sequence_number": sequence_number, "entry_hash": entry_hash})),
        transition_id=manifest.transition_id,
        previous_entry_hash=previous_entry_hash,
        entry_hash=entry_hash,
        manifest_path=_normalize_path(manifest_path),
        manifest_sha256=_sha256_file(manifest_path),
        transition_classification=manifest.transition_classification,
        drift_score=manifest.drift_score,
        current_input_timestamp_utc=report.current_input_timestamp_utc,
        current_epistemic_status=report.current_epistemic_status,
        current_recommended_global_action=report.current_recommended_global_action,
        evidence_status=verification.status,
        summary_line=manifest.summary_line,
    )
    lane_path.parent.mkdir(parents=True, exist_ok=True)
    with lane_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry.model_dump(mode="json"), separators=(",", ":"), default=str) + "\n")
    return entry



def summarize_oracle_memory_lane(*, lane_path: Path, now_utc: Optional[datetime] = None) -> OracleMemoryLaneSummary:
    lane_path = lane_path.resolve()
    entries: list[OracleMemoryLaneEntry] = []
    if lane_path.exists():
        for raw in lane_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            entries.append(OracleMemoryLaneEntry.model_validate(json.loads(raw)))
    classification_counts: dict[str, int] = {}
    severe_drift_count = 0
    evidence_gap_count = 0
    for entry in entries:
        classification_counts[entry.transition_classification] = classification_counts.get(entry.transition_classification, 0) + 1
        if entry.transition_classification == "EVIDENCE_GAP":
            evidence_gap_count += 1
        if entry.drift_score >= 0.55:
            severe_drift_count += 1
    latest = entries[-1] if entries else None
    operator_actions = [
        "Treat oracle memory summaries as advisory-only research surfaces.",
        "Preserve the JSONL lane as append-only history; never rewrite prior entries.",
    ]
    if evidence_gap_count:
        operator_actions.append("Repair evidence gaps before leaning on multi-day transition trends.")
    if severe_drift_count:
        operator_actions.append("Review severe or material drift clusters before trusting stable-regime assumptions.")
    summary_line = (
        f"Oracle memory lane entries={len(entries)}; latest={latest.transition_classification if latest else 'none'}; "
        f"evidence_gaps={evidence_gap_count}; severe_drift_count={severe_drift_count}"
    )
    return OracleMemoryLaneSummary(
        generated_at_utc=now_utc or advisory_utc_now(),
        lane_id=lane_path.stem,
        entry_count=len(entries),
        first_input_timestamp_utc=entries[0].current_input_timestamp_utc if entries else None,
        last_input_timestamp_utc=latest.current_input_timestamp_utc if latest else None,
        latest_transition_classification=latest.transition_classification if latest else None,
        latest_global_action=latest.current_recommended_global_action if latest else None,
        latest_epistemic_status=latest.current_epistemic_status if latest else None,
        severe_drift_count=severe_drift_count,
        evidence_gap_count=evidence_gap_count,
        classification_counts=classification_counts,
        operator_actions=operator_actions,
        summary_line=summary_line,
    )



def review_oracle_memory_lane(*, lane_path: Path, repo_root: Optional[Path] = None, window_size: int = 7, now_utc: Optional[datetime] = None) -> OracleMemoryReviewReport:
    lane_path = lane_path.resolve()
    repo_root = (repo_root or Path.cwd()).resolve()
    summary = summarize_oracle_memory_lane(lane_path=lane_path, now_utc=now_utc)
    entries: list[OracleMemoryLaneEntry] = []
    if lane_path.exists():
        for raw in lane_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            entries.append(OracleMemoryLaneEntry.model_validate(json.loads(raw)))
    window_entries = entries[-max(window_size, 1):]
    triggers: list[str] = []
    observed_transition_ids: list[str] = []
    strategy_decay_counts: dict[str, int] = {}
    evidence_gap_count = 0
    epistemic_escalation_count = 0
    global_action_escalation_count = 0
    severe_or_material_drift_count = 0

    for entry in window_entries:
        observed_transition_ids.append(entry.transition_id)
        if entry.transition_classification == "EVIDENCE_GAP":
            evidence_gap_count += 1
        if entry.transition_classification == "EPISTEMIC_ESCALATION" or entry.current_epistemic_status == "UNKNOWN_UNKNOWNS":
            epistemic_escalation_count += 1
        if entry.transition_classification == "GLOBAL_ACTION_ESCALATION" or entry.current_recommended_global_action == "DEFENSIVE_POSTURE":
            global_action_escalation_count += 1
        if entry.drift_score >= 0.55:
            severe_or_material_drift_count += 1
        manifest_resolved = advisory_resolve_existing_path(entry.manifest_path, repo_root=repo_root, preferred_parent=lane_path.parent)
        if manifest_resolved is None:
            continue
        try:
            manifest = OracleTransitionEvidenceManifest.model_validate(json.loads(manifest_resolved.read_text(encoding="utf-8")))
            report = _load_transition_report(manifest=manifest, manifest_path=manifest_resolved, repo_root=repo_root)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            continue
        for transition in report.strategy_transitions:
            if transition.posterior_delta <= -0.10 and transition.current_action in {"CANARY", "HIBERNATE"}:
                strategy_decay_counts[transition.strategy_id] = strategy_decay_counts.get(transition.strategy_id, 0) + 1

    strategy_retrain_candidate_ids = sorted([sid for sid, count in strategy_decay_counts.items() if count >= 2])
    latest = window_entries[-1] if window_entries else None

    review_classification = "STABLE_RESEARCH_POSTURE"
    if evidence_gap_count >= 2 or (latest is not None and latest.transition_classification == "EVIDENCE_GAP"):
        review_classification = "REPAIR_FIRST"
        triggers.append("Repeated or latest evidence gaps make the memory window untrustworthy until repaired.")
    elif epistemic_escalation_count >= 2 or (latest is not None and latest.current_epistemic_status == "UNKNOWN_UNKNOWNS"):
        review_classification = "DEFENSIVE_RESEARCH_POSTURE"
        triggers.append("Epistemic escalation cluster indicates unstable world-state assumptions and demands defensive research posture.")
    elif strategy_retrain_candidate_ids:
        review_classification = "STRATEGY_RETRAIN_REVIEW"
        triggers.append("At least one strategy showed repeated posterior-confidence decay while already downgraded to CANARY/HIBERNATE.")
    elif severe_or_material_drift_count >= 2 or global_action_escalation_count >= 2:
        review_classification = "HEIGHTENED_RESEARCH_POSTURE"
        triggers.append("Material drift or repeated defensive action escalation suggests heightened research monitoring.")
    else:
        triggers.append("No repeated evidence, epistemic, or strategy-decay clusters breached the review thresholds.")

    operator_actions = [
        "Treat oracle memory review as advisory-only judgment built from append-only verified transition history.",
        "Preserve the lane and linked transition manifests together so the review remains replayable.",
    ]
    if review_classification == "REPAIR_FIRST":
        operator_actions.append("Repair missing or unverifiable transition evidence before relying on multi-day oracle conclusions.")
    elif review_classification == "DEFENSIVE_RESEARCH_POSTURE":
        operator_actions.append("Shift research posture defensive and delay confidence-heavy model interpretation until epistemic stress subsides.")
    elif review_classification == "STRATEGY_RETRAIN_REVIEW":
        operator_actions.append("Queue retrain or forensic review for the flagged strategies before restoring full confidence assumptions.")
    elif review_classification == "HEIGHTENED_RESEARCH_POSTURE":
        operator_actions.append("Increase review cadence and compare the latest oracle evidence against recent transition drivers.")
    else:
        operator_actions.append("Maintain routine monitoring cadence; no multi-day review trigger requires escalation.")

    summary_line = (
        f"Oracle memory review={review_classification}; window_entries={len(window_entries)}; "
        f"evidence_gaps={evidence_gap_count}; epistemic_escalations={epistemic_escalation_count}; "
        f"action_escalations={global_action_escalation_count}; retrain_candidates={','.join(strategy_retrain_candidate_ids) if strategy_retrain_candidate_ids else 'none'}"
    )
    return OracleMemoryReviewReport(
        generated_at_utc=now_utc or advisory_utc_now(),
        lane_id=summary.lane_id,
        window_entry_count=len(window_entries),
        window_start_sequence_number=window_entries[0].sequence_number if window_entries else None,
        window_end_sequence_number=window_entries[-1].sequence_number if window_entries else None,
        first_input_timestamp_utc=window_entries[0].current_input_timestamp_utc if window_entries else None,
        last_input_timestamp_utc=window_entries[-1].current_input_timestamp_utc if window_entries else None,
        latest_transition_classification=summary.latest_transition_classification,
        latest_global_action=summary.latest_global_action,
        latest_epistemic_status=summary.latest_epistemic_status,
        review_classification=review_classification,
        evidence_gap_count=evidence_gap_count,
        epistemic_escalation_count=epistemic_escalation_count,
        global_action_escalation_count=global_action_escalation_count,
        severe_or_material_drift_count=severe_or_material_drift_count,
        strategy_retrain_candidate_ids=strategy_retrain_candidate_ids,
        observed_transition_ids=observed_transition_ids,
        triggers=triggers,
        operator_actions=operator_actions,
        summary_line=summary_line,
    )





_ORACLE_MEMORY_REVIEW_PAYLOAD_TYPE = "application/vnd.strategy-validator.oracle-memory-review.v1+json"


def _find_memory_review_report_path(*, manifest: OracleMemoryReviewEvidenceManifest, manifest_path: Path, repo_root: Path) -> Path:
    for subject in manifest.subjects:
        if subject.name == "ORACLE_MEMORY_REVIEW_REPORT.json":
            resolved = advisory_resolve_existing_path(subject.path, repo_root=repo_root, preferred_parent=manifest_path.parent)
            if resolved is None:
                fallback = manifest_path.parent / Path(subject.path).name
                if fallback.exists():
                    return fallback.resolve()
                raise FileNotFoundError(f"oracle memory review report subject missing from evidence chain: {subject.path}")
            return resolved
    raise FileNotFoundError("oracle memory review evidence manifest does not include ORACLE_MEMORY_REVIEW_REPORT.json")



def _load_memory_review_report(*, manifest: OracleMemoryReviewEvidenceManifest, manifest_path: Path, repo_root: Path) -> OracleMemoryReviewReport:
    report_path = _find_memory_review_report_path(manifest=manifest, manifest_path=manifest_path, repo_root=repo_root)
    return OracleMemoryReviewReport.model_validate(json.loads(report_path.read_text(encoding="utf-8")))



def build_oracle_memory_review_evidence_bundle(
    *,
    source_memory_lane_path: Path,
    review_path: Path,
    markdown_path: Path,
    repo_root: Optional[Path] = None,
    signing_private_key_path: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> tuple[OracleMemoryReviewEvidenceManifest, DsseEnvelope | None]:
    repo_root = (repo_root or Path.cwd()).resolve()
    source_memory_lane_path = source_memory_lane_path.resolve()
    review_path = review_path.resolve()
    markdown_path = markdown_path.resolve()

    review = OracleMemoryReviewReport.model_validate(json.loads(review_path.read_text(encoding="utf-8")))
    assembly = assemble_evidence_subjects(
        artifact_paths=(source_memory_lane_path, review_path, markdown_path),
        repo_root=repo_root,
        artifact_descriptor=_artifact_descriptor,
        normalize_path=_normalize_path,
    )
    review_id = _sha256_bytes(
        _json_canonical_bytes(
            {
                "lane_id": review.lane_id,
                "review_classification": review.review_classification,
                "window_end_sequence_number": review.window_end_sequence_number,
                "observed_transition_ids": review.observed_transition_ids,
                "summary_line": review.summary_line,
            }
        )
    )
    manifest = OracleMemoryReviewEvidenceManifest(
        generated_at_utc=now_utc or advisory_utc_now(),
        review_id=review_id,
        lane_id=review.lane_id,
        execution_authority="ADVISORY_ONLY",
        source_memory_lane_path=_normalize_path(source_memory_lane_path),
        review_classification=review.review_classification,
        window_entry_count=review.window_entry_count,
        window_end_sequence_number=review.window_end_sequence_number,
        latest_global_action=review.latest_global_action,
        latest_epistemic_status=review.latest_epistemic_status,
        integrity_status=assembly.integrity_status,
        subjects=assembly.subjects,
        missing_artifact_paths=assembly.missing_artifact_paths,
        summary_line=review.summary_line,
    )
    envelope = sign_manifest_envelope(
        manifest=manifest,
        payload_type=_ORACLE_MEMORY_REVIEW_PAYLOAD_TYPE,
        signing_private_key_path=signing_private_key_path,
        json_canonical_bytes=_json_canonical_bytes,
        sign_dsse_payload=_sign_dsse_payload,
    )
    return manifest, envelope



def verify_oracle_memory_review_evidence_bundle(
    *,
    manifest_path: Path,
    repo_root: Optional[Path] = None,
    dsse_path: Optional[Path] = None,
    public_key_path: Optional[Path] = None,
) -> OracleMemoryReviewEvidenceVerification:
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest_path = manifest_path.resolve()
    manifest = OracleMemoryReviewEvidenceManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    return build_evidence_verification(
        manifest=manifest,
        manifest_path=manifest_path,
        repo_root=repo_root,
        resolver=advisory_resolve_existing_path,
        sha256_file=_sha256_file,
        dsse_path=dsse_path,
        public_key_path=public_key_path,
        payload_type=_ORACLE_MEMORY_REVIEW_PAYLOAD_TYPE,
        json_canonical_bytes=_json_canonical_bytes,
        dsse_model=DsseEnvelope,
        verify_dsse_envelope=_verify_dsse_envelope,
        verification_factory=OracleMemoryReviewEvidenceVerification,
        verified_at_utc=advisory_utc_now(),
        normalize_path=_normalize_path,
    )



def append_oracle_memory_review_to_lane(
    *,
    manifest_path: Path,
    verification: OracleMemoryReviewEvidenceVerification,
    lane_path: Path,
    repo_root: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> OracleReviewLaneEntry:
    manifest_path = manifest_path.resolve()
    lane_path = lane_path.resolve()
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest = OracleMemoryReviewEvidenceManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    if verification.status != "VERIFIED":
        raise ValueError("oracle review lane only accepts VERIFIED memory review evidence")
    review = _load_memory_review_report(manifest=manifest, manifest_path=manifest_path, repo_root=repo_root)

    entries: list[OracleReviewLaneEntry] = []
    if lane_path.exists():
        for raw in lane_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            entries.append(OracleReviewLaneEntry.model_validate(json.loads(raw)))
    sequence_number = len(entries)
    previous_entry_hash = entries[-1].entry_hash if entries else None
    lane_id = lane_path.stem
    entry_seed = {
        "lane_id": lane_id,
        "sequence_number": sequence_number,
        "review_id": manifest.review_id,
        "previous_entry_hash": previous_entry_hash or "GENESIS",
        "manifest_sha256": _sha256_file(manifest_path),
        "review_classification": manifest.review_classification,
        "window_end_sequence_number": manifest.window_end_sequence_number,
        "latest_global_action": manifest.latest_global_action,
        "latest_epistemic_status": manifest.latest_epistemic_status,
        "evidence_status": verification.status,
    }
    entry_hash = _sha256_bytes(_json_canonical_bytes(entry_seed))
    entry = OracleReviewLaneEntry(
        appended_at_utc=now_utc or advisory_utc_now(),
        lane_id=lane_id,
        sequence_number=sequence_number,
        entry_id=_sha256_bytes(_json_canonical_bytes({"lane_id": lane_id, "sequence_number": sequence_number, "entry_hash": entry_hash})),
        review_id=manifest.review_id,
        previous_entry_hash=previous_entry_hash,
        entry_hash=entry_hash,
        manifest_path=_normalize_path(manifest_path),
        manifest_sha256=_sha256_file(manifest_path),
        review_classification=manifest.review_classification,
        window_end_sequence_number=manifest.window_end_sequence_number,
        latest_global_action=manifest.latest_global_action,
        latest_epistemic_status=manifest.latest_epistemic_status,
        evidence_status=verification.status,
        summary_line=manifest.summary_line,
    )
    lane_path.parent.mkdir(parents=True, exist_ok=True)
    with lane_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry.model_dump(mode="json"), separators=(",", ":"), default=str) + "\n")
    return entry



def generate_oracle_weekly_digest(*, lane_path: Path, window_size: int = 7, repo_root: Optional[Path] = None, search_root: Optional[Path] = None, now_utc: Optional[datetime] = None) -> OracleWeeklyDigestReport:
    lane_path = lane_path.resolve()
    entries: list[OracleReviewLaneEntry] = []
    if lane_path.exists():
        for raw in lane_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            entries.append(OracleReviewLaneEntry.model_validate(json.loads(raw)))
    window_entries = entries[-max(window_size, 1):]
    classification_counts: dict[str, int] = {}
    observed_review_ids: list[str] = []
    recurring_patterns: list[str] = []
    for entry in window_entries:
        observed_review_ids.append(entry.review_id)
        classification_counts[entry.review_classification] = classification_counts.get(entry.review_classification, 0) + 1

    latest = window_entries[-1] if window_entries else None
    repair_count = classification_counts.get("REPAIR_FIRST", 0)
    defensive_count = classification_counts.get("DEFENSIVE_RESEARCH_POSTURE", 0)
    retrain_count = classification_counts.get("STRATEGY_RETRAIN_REVIEW", 0)
    heightened_count = classification_counts.get("HEIGHTENED_RESEARCH_POSTURE", 0)

    cadence_feedback = summarize_exact_cadence_feedback(repo_root=repo_root, search_root=search_root, window_size=max(window_size, 1))

    doctrine_posture = "STABLE_RESEARCH_POSTURE"
    if repair_count >= 2 or (latest is not None and latest.review_classification == "REPAIR_FIRST"):
        doctrine_posture = "REPAIR_FIRST"
        recurring_patterns.append("Repeated repair-first reviews indicate evidence or lane hygiene problems must be fixed before deeper interpretation.")
    elif defensive_count >= 2 or (latest is not None and latest.latest_epistemic_status == "UNKNOWN_UNKNOWNS"):
        doctrine_posture = "DEFENSIVE_RESEARCH_POSTURE"
        recurring_patterns.append("Defensive research posture persisted across the review window due to epistemic instability or repeated high-stress states.")
    elif retrain_count >= 1:
        doctrine_posture = "STRATEGY_RETRAIN_REVIEW"
        recurring_patterns.append("At least one review in the window repeatedly flagged strategy retrain conditions.")
    elif heightened_count >= 2:
        doctrine_posture = "HEIGHTENED_RESEARCH_POSTURE"
        recurring_patterns.append("Heightened monitoring persisted across multiple reviews and should be treated as an active doctrine, not a one-off signal.")
    elif window_entries:
        recurring_patterns.append("Recent review history stayed within stable research posture bounds.")
    else:
        recurring_patterns.append("No review history exists yet for a weekly doctrine digest.")

    if classification_counts.get("REPAIR_FIRST", 0) and classification_counts.get("DEFENSIVE_RESEARCH_POSTURE", 0):
        recurring_patterns.append("Both evidence repair pressure and defensive research posture appeared in the same window; prioritize evidence repair before over-interpreting macro stress.")
    if classification_counts.get("STRATEGY_RETRAIN_REVIEW", 0) and classification_counts.get("HEIGHTENED_RESEARCH_POSTURE", 0):
        recurring_patterns.append("Strategy decay surfaced during a heightened monitoring period, suggesting retrain review should be coupled with regime-context analysis.")
    if cadence_feedback.exact_feedback_confirmation_count >= 2:
        recurring_patterns.append("Repeated exact sealed execution confirmations are reinforcing doctrine pressure inside the weekly window; escalate cadence for the directly supported clauses before generalizing.")
    elif cadence_feedback.exact_feedback_relief_count >= 2 and cadence_feedback.exact_feedback_confirmation_count == 0:
        recurring_patterns.append("Repeated exact sealed relieving outcomes are tempering weekly doctrine pressure for a bounded clause subset; keep review active but allow local relaxation.")

    operator_actions = [
        "Treat the weekly digest as advisory doctrine built from signed review evidence and append-only review history.",
        "Preserve the review lane and linked manifests together so recurring patterns remain replayable.",
    ]
    if doctrine_posture == "REPAIR_FIRST":
        operator_actions.append("Repair review evidence or memory-lane integrity before leaning on weekly oracle narratives.")
    elif doctrine_posture == "DEFENSIVE_RESEARCH_POSTURE":
        operator_actions.append("Adopt a defensive research cadence and delay confidence-heavy model interpretation until uncertainty normalizes.")
    elif doctrine_posture == "STRATEGY_RETRAIN_REVIEW":
        operator_actions.append("Schedule retrain or forensic analysis for the affected strategies before restoring baseline confidence.")
    elif doctrine_posture == "HEIGHTENED_RESEARCH_POSTURE":
        operator_actions.append("Increase review cadence and compare the latest doctrine drivers against the last verified transition cluster.")
    else:
        operator_actions.append("Maintain routine review cadence; no weekly doctrine trigger requires escalation.")
    if cadence_feedback.exact_feedback_confirmation_count >= 2:
        operator_actions.append("Escalate weekly doctrine review cadence because repeated exact sealed confirmations are validating live clause pressure.")
    elif cadence_feedback.exact_feedback_relief_count >= 2 and cadence_feedback.exact_feedback_confirmation_count == 0:
        operator_actions.append("Keep weekly doctrine review active but allow the repeated exact sealed relieving outcomes to soften cadence for the directly supported clauses.")
    elif cadence_feedback.exact_evidence_support_score >= 0.85:
        operator_actions.append("Anchor weekly doctrine cadence to the exact sealed execution subjects and avoid generalizing beyond the directly supported scope.")

    summary_line = (
        f"Oracle weekly digest={doctrine_posture}; window_reviews={len(window_entries)}; "
        f"repair={repair_count}; defensive={defensive_count}; retrain={retrain_count}; heightened={heightened_count}; "
        f"exact_support={cadence_feedback.exact_evidence_support_score:.2f}; exact_confirm={cadence_feedback.exact_feedback_confirmation_count}; exact_relief={cadence_feedback.exact_feedback_relief_count}"
    )
    return OracleWeeklyDigestReport(
        generated_at_utc=now_utc or advisory_utc_now(),
        lane_id=lane_path.stem,
        exact_evidence_support_score=cadence_feedback.exact_evidence_support_score,
        exact_feedback_confirmation_count=cadence_feedback.exact_feedback_confirmation_count,
        exact_feedback_relief_count=cadence_feedback.exact_feedback_relief_count,
        window_review_count=len(window_entries),
        window_start_sequence_number=window_entries[0].sequence_number if window_entries else None,
        window_end_sequence_number=window_entries[-1].sequence_number if window_entries else None,
        latest_review_classification=latest.review_classification if latest else None,
        latest_global_action=latest.latest_global_action if latest else None,
        latest_epistemic_status=latest.latest_epistemic_status if latest else None,
        doctrine_posture=doctrine_posture,
        classification_counts=classification_counts,
        recurring_patterns=recurring_patterns,
        observed_review_ids=observed_review_ids,
        operator_actions=operator_actions,
        summary_line=summary_line,
    )





_ORACLE_WEEKLY_DIGEST_PAYLOAD_TYPE = "application/vnd.strategy-validator.oracle-weekly-digest.v1+json"


def _find_weekly_digest_report_path(*, manifest: OracleWeeklyDigestEvidenceManifest, manifest_path: Path, repo_root: Path) -> Path:
    for subject in manifest.subjects:
        if subject.name == "ORACLE_WEEKLY_DIGEST.json":
            resolved = advisory_resolve_existing_path(subject.path, repo_root=repo_root, preferred_parent=manifest_path.parent)
            if resolved is None:
                fallback = manifest_path.parent / Path(subject.path).name
                if fallback.exists():
                    return fallback.resolve()
                raise FileNotFoundError(f"oracle weekly digest report subject missing from evidence chain: {subject.path}")
            return resolved
    raise FileNotFoundError("oracle weekly digest evidence manifest does not include ORACLE_WEEKLY_DIGEST.json")


def _load_weekly_digest_report(*, manifest: OracleWeeklyDigestEvidenceManifest, manifest_path: Path, repo_root: Path) -> OracleWeeklyDigestReport:
    report_path = _find_weekly_digest_report_path(manifest=manifest, manifest_path=manifest_path, repo_root=repo_root)
    return OracleWeeklyDigestReport.model_validate(json.loads(report_path.read_text(encoding="utf-8")))


def _fallback_weekly_digest_report(*, manifest: OracleWeeklyDigestEvidenceManifest, now_utc: Optional[datetime] = None) -> OracleWeeklyDigestReport:
    return OracleWeeklyDigestReport(
        generated_at_utc=now_utc or advisory_utc_now(),
        lane_id=manifest.lane_id,
        window_review_count=manifest.window_review_count,
        window_end_sequence_number=manifest.window_end_sequence_number,
        latest_review_classification=manifest.latest_review_classification,
        latest_global_action=manifest.latest_global_action,
        latest_epistemic_status=manifest.latest_epistemic_status,
        doctrine_posture=manifest.doctrine_posture,
        classification_counts={manifest.doctrine_posture: 1} if manifest.window_review_count else {},
        recurring_patterns=["Digest report missing; fallback posture synthesized from weekly digest evidence manifest."],
        observed_review_ids=[],
        operator_actions=["Repair or regenerate the underlying weekly digest report before relying on week-over-week doctrine analysis."],
        summary_line=manifest.summary_line,
    )


def build_oracle_weekly_digest_evidence_bundle(
    *,
    source_review_lane_path: Path,
    digest_path: Path,
    markdown_path: Path,
    repo_root: Optional[Path] = None,
    signing_private_key_path: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> tuple[OracleWeeklyDigestEvidenceManifest, DsseEnvelope | None]:
    repo_root = (repo_root or Path.cwd()).resolve()
    source_review_lane_path = source_review_lane_path.resolve()
    digest_path = digest_path.resolve()
    markdown_path = markdown_path.resolve()

    digest = OracleWeeklyDigestReport.model_validate(json.loads(digest_path.read_text(encoding="utf-8")))
    digest_id = _sha256_bytes(
        _json_canonical_bytes(
            {
                "lane_id": digest.lane_id,
                "doctrine_posture": digest.doctrine_posture,
                "window_end_sequence_number": digest.window_end_sequence_number,
                "observed_review_ids": digest.observed_review_ids,
                "summary_line": digest.summary_line,
            }
        )
    )
    return build_signed_evidence_manifest(
        artifact_paths=(source_review_lane_path, digest_path, markdown_path),
        repo_root=repo_root,
        artifact_descriptor=_artifact_descriptor,
        normalize_path=_normalize_path,
        manifest_factory=lambda *, subjects, missing_artifact_paths, integrity_status: OracleWeeklyDigestEvidenceManifest(
            generated_at_utc=now_utc or advisory_utc_now(),
            digest_id=digest_id,
            lane_id=digest.lane_id,
            execution_authority="ADVISORY_ONLY",
            source_review_lane_path=_normalize_path(source_review_lane_path),
            doctrine_posture=digest.doctrine_posture,
            window_review_count=digest.window_review_count,
            window_end_sequence_number=digest.window_end_sequence_number,
            latest_review_classification=digest.latest_review_classification,
            latest_global_action=digest.latest_global_action,
            latest_epistemic_status=digest.latest_epistemic_status,
            integrity_status=integrity_status,
            subjects=subjects,
            missing_artifact_paths=missing_artifact_paths,
            summary_line=digest.summary_line,
        ),
        payload_type=_ORACLE_WEEKLY_DIGEST_PAYLOAD_TYPE,
        signing_private_key_path=signing_private_key_path,
        json_canonical_bytes=_json_canonical_bytes,
        sign_dsse_payload=_sign_dsse_payload,
    )


def verify_oracle_weekly_digest_evidence_bundle(
    *,
    manifest_path: Path,
    repo_root: Optional[Path] = None,
    dsse_path: Optional[Path] = None,
    public_key_path: Optional[Path] = None,
) -> OracleWeeklyDigestEvidenceVerification:
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest_path = manifest_path.resolve()
    manifest = OracleWeeklyDigestEvidenceManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    return build_evidence_verification(
        manifest=manifest,
        manifest_path=manifest_path,
        repo_root=repo_root,
        resolver=advisory_resolve_existing_path,
        sha256_file=_sha256_file,
        dsse_path=dsse_path,
        public_key_path=public_key_path,
        payload_type=_ORACLE_WEEKLY_DIGEST_PAYLOAD_TYPE,
        json_canonical_bytes=_json_canonical_bytes,
        dsse_model=DsseEnvelope,
        verify_dsse_envelope=_verify_dsse_envelope,
        verification_factory=OracleWeeklyDigestEvidenceVerification,
        verified_at_utc=advisory_utc_now(),
        normalize_path=_normalize_path,
    )
