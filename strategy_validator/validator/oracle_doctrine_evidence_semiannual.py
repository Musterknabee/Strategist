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


OracleSemiannualAuditReport.model_rebuild(force=True)
OracleSemiannualAuditEvidenceManifest.model_rebuild(force=True)
OracleSemiannualAuditEvidenceVerification.model_rebuild(force=True)
OracleSemiannualLaneEntry.model_rebuild(force=True)
OracleQuarterlyLaneEntry.model_rebuild(force=True)

__all__ = [name for name in globals() if not name.startswith("__")]
