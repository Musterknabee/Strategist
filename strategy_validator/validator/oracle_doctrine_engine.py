from __future__ import annotations

# Shared contracts, evidence helpers, and low-level oracle transition utilities.
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


from strategy_validator.validator.oracle_review_engine import (
    _fallback_weekly_digest_report,
    _load_weekly_digest_report,
    verify_oracle_weekly_digest_evidence_bundle,
)

from strategy_validator.validator.oracle_cadence_feedback import summarize_exact_cadence_feedback

from strategy_validator.validator.oracle_doctrine_evidence_monthly_quarterly import (
    _find_monthly_digest_report_path,
    _find_quarterly_review_report_path,
    _load_monthly_digest_report,
    _load_quarterly_review_report,
    append_oracle_monthly_digest_to_lane,
    append_oracle_quarterly_review_to_lane,
    build_oracle_monthly_digest_evidence_bundle,
    build_oracle_quarterly_review_evidence_bundle,
    generate_oracle_monthly_digest,
    generate_oracle_quarterly_review,
    verify_oracle_monthly_digest_evidence_bundle,
    verify_oracle_quarterly_review_evidence_bundle,
)
from strategy_validator.validator.oracle_doctrine_evidence_semiannual import (
    _find_semiannual_audit_report_path,
    _load_semiannual_audit_report,
    append_oracle_semiannual_audit_to_lane,
    build_oracle_semiannual_audit_evidence_bundle,
    generate_oracle_semiannual_audit,
    verify_oracle_semiannual_audit_evidence_bundle,
)
from strategy_validator.validator.oracle_doctrine_evidence_annual import (
    _find_annual_review_report_path,
    _load_annual_review_report,
    append_oracle_annual_review_to_lane,
    build_oracle_annual_review_evidence_bundle,
    generate_oracle_annual_review,
    verify_oracle_annual_review_evidence_bundle,
)
from strategy_validator.validator.oracle_doctrine_evidence_foundations import (
    _find_doctrine_drift_report_path,
    _load_doctrine_drift_report,
    append_oracle_doctrine_drift_to_lane,
    build_oracle_doctrine_drift_evidence_bundle,
    verify_oracle_doctrine_drift_evidence_bundle,
)

from strategy_validator.validator.oracle_doctrine_rendering import (
    render_oracle_annual_review_markdown,
    render_oracle_constitutional_digest_markdown,
    render_oracle_doctrine_drift_markdown,
    render_oracle_monthly_digest_markdown,
    render_oracle_quarterly_review_markdown,
    render_oracle_semiannual_audit_markdown,
)

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


def compare_oracle_weekly_digests(
    *,
    previous_manifest_path: Path,
    current_manifest_path: Path,
    repo_root: Optional[Path] = None,
    previous_dsse_path: Optional[Path] = None,
    current_dsse_path: Optional[Path] = None,
    previous_public_key_path: Optional[Path] = None,
    current_public_key_path: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> OracleDoctrineDriftReport:
    repo_root = (repo_root or Path.cwd()).resolve()
    previous_manifest_path = previous_manifest_path.resolve()
    current_manifest_path = current_manifest_path.resolve()

    previous_verification = verify_oracle_weekly_digest_evidence_bundle(
        manifest_path=previous_manifest_path,
        repo_root=repo_root,
        dsse_path=previous_dsse_path,
        public_key_path=previous_public_key_path,
    )
    current_verification = verify_oracle_weekly_digest_evidence_bundle(
        manifest_path=current_manifest_path,
        repo_root=repo_root,
        dsse_path=current_dsse_path,
        public_key_path=current_public_key_path,
    )

    previous_manifest = OracleWeeklyDigestEvidenceManifest.model_validate(json.loads(previous_manifest_path.read_text(encoding="utf-8")))
    current_manifest = OracleWeeklyDigestEvidenceManifest.model_validate(json.loads(current_manifest_path.read_text(encoding="utf-8")))

    comparison_status = "VERIFIED"
    if previous_verification.status != "VERIFIED" or current_verification.status != "VERIFIED":
        comparison_status = "INCOMPLETE" if (previous_verification.status == "INCOMPLETE" or current_verification.status == "INCOMPLETE") else "UNVERIFIED"

    try:
        previous_digest = _load_weekly_digest_report(manifest=previous_manifest, manifest_path=previous_manifest_path, repo_root=repo_root)
    except FileNotFoundError:
        previous_digest = _fallback_weekly_digest_report(manifest=previous_manifest)
    try:
        current_digest = _load_weekly_digest_report(manifest=current_manifest, manifest_path=current_manifest_path, repo_root=repo_root)
    except FileNotFoundError:
        current_digest = _fallback_weekly_digest_report(manifest=current_manifest)

    previous_patterns = set(previous_digest.recurring_patterns)
    current_patterns = set(current_digest.recurring_patterns)
    overlap_count = len(previous_patterns & current_patterns)
    shift_count = len((previous_patterns | current_patterns) - (previous_patterns & current_patterns))

    classification = "DOCTRINE_STABLE"
    drift_score = 0.0
    if comparison_status != "VERIFIED":
        classification = "DOCTRINE_EVIDENCE_GAP"
        drift_score = 1.0 if comparison_status == "INCOMPLETE" else 0.7
    elif previous_digest.doctrine_posture == current_digest.doctrine_posture == "REPAIR_FIRST":
        classification = "RECURRING_REPAIR"
        drift_score = 1.0
    elif previous_digest.doctrine_posture == current_digest.doctrine_posture == "STRATEGY_RETRAIN_REVIEW":
        classification = "RECURRING_RETRAIN"
        drift_score = 0.8
    else:
        prev_rank = _doctrine_rank(previous_digest.doctrine_posture)
        curr_rank = _doctrine_rank(current_digest.doctrine_posture)
        delta = curr_rank - prev_rank
        if delta > 0:
            classification = "DOCTRINE_ESCALATION"
            drift_score = min(1.0, 0.35 + 0.2 * delta + (0.1 if current_digest.latest_epistemic_status == "UNKNOWN_UNKNOWNS" else 0.0))
        elif delta < 0:
            classification = "DOCTRINE_RELIEF"
            drift_score = min(1.0, 0.25 + 0.15 * abs(delta))
        else:
            classification = "DOCTRINE_STABLE"
            drift_score = 0.1 if shift_count else 0.0

    drift_level = _drift_level_from_score(drift_score)
    operator_actions = [
        "Treat doctrine drift as advisory governance memory derived from signed weekly digest evidence.",
        "Preserve both weekly digest manifests and their linked review lanes together so doctrine comparisons remain replayable.",
    ]
    if classification == "DOCTRINE_EVIDENCE_GAP":
        operator_actions.append("Repair or regenerate incomplete weekly digest evidence before relying on doctrine drift conclusions.")
    elif classification == "RECURRING_REPAIR":
        operator_actions.append("Escalate lane or evidence hygiene work; recurring repair posture indicates doctrine cannot safely stabilize yet.")
    elif classification == "RECURRING_RETRAIN":
        operator_actions.append("Keep retrain review active across weeks and compare the affected strategies against the latest verified transition clusters.")
    elif classification == "DOCTRINE_ESCALATION":
        operator_actions.append("Increase doctrine review cadence and compare the new posture against the prior week before restoring confidence-heavy interpretation.")
    elif classification == "DOCTRINE_RELIEF":
        operator_actions.append("Do not immediately relax discipline; confirm the relief posture persists in the next verified weekly digest.")
    else:
        operator_actions.append("Maintain normal doctrine review cadence; no week-over-week doctrine escalation is present.")

    summary_line = (
        f"Oracle doctrine drift={classification}; previous={previous_digest.doctrine_posture}; "
        f"current={current_digest.doctrine_posture}; comparison_status={comparison_status}; "
        f"pattern_overlap={overlap_count}; pattern_shift={shift_count}"
    )
    return OracleDoctrineDriftReport(
        generated_at_utc=now_utc or advisory_utc_now(),
        previous_digest_id=previous_manifest.digest_id,
        current_digest_id=current_manifest.digest_id,
        lane_id=current_digest.lane_id,
        execution_authority="ADVISORY_ONLY",
        previous_verification_status=previous_verification.status,
        current_verification_status=current_verification.status,
        comparison_status=comparison_status,
        previous_doctrine_posture=previous_digest.doctrine_posture,
        current_doctrine_posture=current_digest.doctrine_posture,
        previous_latest_review_classification=previous_digest.latest_review_classification,
        current_latest_review_classification=current_digest.latest_review_classification,
        previous_latest_global_action=previous_digest.latest_global_action,
        current_latest_global_action=current_digest.latest_global_action,
        previous_latest_epistemic_status=previous_digest.latest_epistemic_status,
        current_latest_epistemic_status=current_digest.latest_epistemic_status,
        recurring_pattern_overlap_count=overlap_count,
        recurring_pattern_shift_count=shift_count,
        drift_classification=classification,
        drift_level=drift_level,
        operator_actions=operator_actions,
        summary_line=summary_line,
    )





















def generate_oracle_constitutional_digest(*, lane_path: Path, window_size: int = 3, repo_root: Optional[Path] = None, search_root: Optional[Path] = None, now_utc: Optional[datetime] = None) -> OracleConstitutionalDigestReport:
    lane_path = lane_path.resolve()
    entries: list[OracleAnnualLaneEntry] = []
    if lane_path.exists():
        for raw in lane_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            entries.append(OracleAnnualLaneEntry.model_validate(json.loads(raw)))
    window_entries = entries[-max(window_size, 1):]
    annual_classification_counts: dict[str, int] = {}
    observed_annual_review_ids: list[str] = []
    recurring_patterns: list[str] = []
    for entry in window_entries:
        observed_annual_review_ids.append(entry.annual_review_id)
        annual_classification_counts[entry.annual_review_classification] = annual_classification_counts.get(entry.annual_review_classification, 0) + 1

    latest = window_entries[-1] if window_entries else None
    exact_evidence_support_score = max((float(getattr(entry, "exact_evidence_support_score", 0.0) or 0.0) for entry in window_entries), default=0.0)
    exact_feedback_confirmation_count = sum(int(getattr(entry, "exact_feedback_confirmation_count", 0) or 0) for entry in window_entries)
    exact_feedback_relief_count = sum(int(getattr(entry, "exact_feedback_relief_count", 0) or 0) for entry in window_entries)
    strategic_search_root = _default_constitutional_search_root(lane_path=lane_path, repo_root=repo_root, search_root=search_root)
    strategic_stack_evidence_count = _count_valid_strategic_stack_manifests(search_root=strategic_search_root)
    strategic_stack_requirement_met = strategic_stack_evidence_count > 0
    strategic_backing_classification = "SEALED_STRATEGIC_STACK_BACKED" if strategic_stack_requirement_met else ("DOCTRINE_ONLY_LADDER_BACKED" if window_entries else "NO_STRATEGIC_STACK_HISTORY")
    evidence_gap_count = annual_classification_counts.get("ANNUAL_EVIDENCE_GAP", 0)
    repair_count = annual_classification_counts.get("ANNUAL_REPAIR_STRUCTURAL", 0)
    retrain_count = annual_classification_counts.get("ANNUAL_RETRAIN_STRUCTURAL", 0)
    defensive_count = annual_classification_counts.get("ANNUAL_DEFENSIVE_STRUCTURAL", 0)
    heightened_count = annual_classification_counts.get("ANNUAL_HEIGHTENED_WATCH", 0)

    digest_classification: OracleConstitutionalDigestClassification = "CONSTITUTIONAL_STABLE_BASELINE"
    if evidence_gap_count >= 1 or (latest is not None and latest.evidence_status != "VERIFIED"):
        digest_classification = "CONSTITUTIONAL_EVIDENCE_GAP"
        recurring_patterns.append("At least one annual review lost verification integrity; repair annual evidence before trusting the constitutional digest.")
    elif repair_count >= 2 or (latest is not None and latest.annual_review_classification == "ANNUAL_REPAIR_STRUCTURAL"):
        digest_classification = "CONSTITUTIONAL_REPAIR_CHRONIC"
        recurring_patterns.append("Repair-structural annual review repeated across the constitutional window, indicating chronic evidence and governance instability.")
    elif retrain_count >= 2 or (latest is not None and latest.annual_review_classification == "ANNUAL_RETRAIN_STRUCTURAL"):
        digest_classification = "CONSTITUTIONAL_RETRAIN_CHRONIC"
        recurring_patterns.append("Retrain-structural annual review repeated across the constitutional window and should be treated as chronic model-health pressure.")
    elif defensive_count >= 2 or (latest is not None and latest.annual_review_classification == "ANNUAL_DEFENSIVE_STRUCTURAL"):
        digest_classification = "CONSTITUTIONAL_DEFENSIVE_CHRONIC"
        recurring_patterns.append("Defensive annual doctrine persisted across the constitutional window; stress appears chronic rather than cyclical.")
    elif heightened_count >= 2 or (latest is not None and latest.annual_review_classification == "ANNUAL_HEIGHTENED_WATCH"):
        digest_classification = "CONSTITUTIONAL_HEIGHTENED_WATCH"
        recurring_patterns.append("Heightened-watch annual doctrine remained active across the constitutional window and warrants continued scrutiny before confidence restoration.")
    elif window_entries:
        recurring_patterns.append("Constitutional oracle digest remained within stable baseline bounds.")
    else:
        recurring_patterns.append("No annual doctrine history exists yet for a constitutional oracle digest.")

    if repair_count and retrain_count:
        recurring_patterns.append("Repair-structural and retrain-structural annual outcomes overlapped; do not over-ascribe chronic model decay when evidence hygiene remains unstable.")
    if defensive_count and heightened_count:
        recurring_patterns.append("Heightened-watch and defensive annual outcomes both appeared within the constitutional window; preserve the annual lane so durable stress remains auditable.")
    if strategic_stack_requirement_met:
        recurring_patterns.append("Constitutional digest is backed by at least one sealed strategic stack evidence bundle, so long-horizon doctrine remains tied to replayable strategist epochs.")
    elif window_entries:
        recurring_patterns.append("Constitutional digest is currently backed only by doctrine ladder artifacts; seal strategic stack history before treating chronic doctrine as strategist-grounded.")
    else:
        recurring_patterns.append("No indexed strategic stack history was found while building the constitutional digest.")
    if exact_feedback_confirmation_count > 0:
        recurring_patterns.append(f"Constitutional cadence is being driven by repeated exact sealed confirmations ({exact_feedback_confirmation_count}), not only ambient doctrine pressure.")
    elif exact_feedback_relief_count > 0:
        recurring_patterns.append(f"Constitutional cadence includes repeated exact sealed relief signals ({exact_feedback_relief_count}); keep de-escalation bounded until broader strategist backing remains stable.")

    operator_actions = [
        "Treat the constitutional oracle digest as advisory governance memory derived from signed annual review evidence and an append-only annual lane.",
        "Preserve the annual lane, annual review evidence manifests, and linked semiannual lane together so the constitutional digest remains replayable.",
    ]
    if digest_classification == "CONSTITUTIONAL_EVIDENCE_GAP":
        operator_actions.append("Repair or regenerate missing annual evidence before relying on constitutional doctrine summaries.")
    elif digest_classification == "CONSTITUTIONAL_REPAIR_CHRONIC":
        operator_actions.append("Escalate governance and evidence remediation as a chronic constitutional concern.")
    elif digest_classification == "CONSTITUTIONAL_RETRAIN_CHRONIC":
        operator_actions.append("Escalate strategy forensic and retrain review as a chronic constitutional concern rather than a temporary fluctuation.")
    elif digest_classification == "CONSTITUTIONAL_DEFENSIVE_CHRONIC":
        operator_actions.append("Maintain defensive research doctrine and avoid confidence-heavy interpretation until constitutional stress materially recedes.")
    elif digest_classification == "CONSTITUTIONAL_HEIGHTENED_WATCH":
        operator_actions.append("Increase constitutional doctrine review cadence and compare the next annual review against the latest structural drivers.")
    else:
        operator_actions.append("Maintain baseline constitutional digest cadence; no chronic trigger currently requires escalation.")
    if strategic_stack_requirement_met:
        operator_actions.append("Treat chronic constitutional classifications as strategist-grounded only because sealed strategic stack history is present alongside the doctrine ladder.")
    elif window_entries:
        operator_actions.append("Do not treat chronic constitutional classifications as strategist-grounded yet; this digest is doctrine-only until sealed strategic stack history is indexed.")
    else:
        operator_actions.append("Index and seal strategic stack evidence before relying on constitutional digest summaries for long-horizon strategist claims.")
    if exact_feedback_confirmation_count > 0:
        operator_actions.append("Account for repeated exact sealed confirmations when setting constitutional doctrine cadence; do not dismiss them as generic ambient pressure.")
    elif exact_feedback_relief_count > 0:
        operator_actions.append("Repeated exact sealed relief is present; de-escalate constitutional cadence only in a bounded way while preserving long-horizon replayability checks.")

    summary_line = (
        f"Oracle constitutional digest={digest_classification}; backing={strategic_backing_classification}; "
        f"window_entries={len(window_entries)}; strategic_stack={strategic_stack_evidence_count}; "
        f"evidence_gap={evidence_gap_count}; repair={repair_count}; retrain={retrain_count}; "
        f"defensive={defensive_count}; heightened={heightened_count}; "
        f"exact_support={exact_evidence_support_score:.2f}; exact_confirm={exact_feedback_confirmation_count}; exact_relief={exact_feedback_relief_count}"
    )
    return OracleConstitutionalDigestReport(
        generated_at_utc=now_utc or advisory_utc_now(),
        lane_id=lane_path.stem,
        exact_evidence_support_score=exact_evidence_support_score,
        exact_feedback_confirmation_count=exact_feedback_confirmation_count,
        exact_feedback_relief_count=exact_feedback_relief_count,
        window_entry_count=len(window_entries),
        window_start_sequence_number=window_entries[0].sequence_number if window_entries else None,
        window_end_sequence_number=window_entries[-1].sequence_number if window_entries else None,
        latest_annual_review_id=latest.annual_review_id if latest else None,
        latest_annual_review_classification=latest.annual_review_classification if latest else None,
        constitutional_digest_classification=digest_classification,
        strategic_backing_classification=strategic_backing_classification,
        strategic_stack_evidence_count=strategic_stack_evidence_count,
        strategic_stack_requirement_met=strategic_stack_requirement_met,
        annual_classification_counts=annual_classification_counts,
        observed_annual_review_ids=observed_annual_review_ids,
        recurring_patterns=recurring_patterns,
        operator_actions=operator_actions,
        summary_line=summary_line,
    )


