from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from strategy_validator.contracts.interface_freeze import PILOT_RC_INTERFACE_FREEZE
from strategy_validator.contracts.operational import (
    ClosureReleaseAttestation,
    ClosureSnapshotManifest,
    ClosureSnapshotVerification,
    ControlledRolloutRules,
    DsseEnvelope,
    GovernedExceptionMemo,
    GovernedExceptionVerification,
    RuntimeEvidenceReview,
)
from strategy_validator.core.config import load_config
from strategy_validator.validator.operator_checks import export_startup_json_bundle
from strategy_validator.validator.readiness import perform_readiness_check


from strategy_validator.validator.rollout_ops_evidence import (
    _DEFAULT_RULES_PATH,
    _artifact_descriptor,
    _json_canonical_bytes,
    _load_json,
    _normalize_path,
    _resolve_existing_path,
    _sha256_bytes,
    _sha256_file,
    _sha256_text,
    _sign_dsse_payload,
    _utc_now,
    _verify_dsse_envelope,
    build_closure_snapshot,
    build_daily_checklist,
    build_rollout_bundle,
    generate_host_fingerprint,
    generate_snapshot_signing_keypair,
    parse_analyze_summary,
    review_runtime_evidence,
    verify_closure_snapshot,
)


_GOVERNED_EXCEPTION_PAYLOAD_TYPE = "application/vnd.strategy-validator.governed-exception.v1+json"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _policy_sha256(policy_path: Path) -> str:
    return _sha256_text(policy_path.read_text(encoding="utf-8"))


def load_controlled_rollout_rules(path: Optional[Path] = None) -> ControlledRolloutRules:
    target = path or _DEFAULT_RULES_PATH
    return ControlledRolloutRules.model_validate(json.loads(target.read_text(encoding="utf-8")))


def _git_output(args: list[str]) -> Optional[str]:
    try:
        out = subprocess.check_output(args, text=True).strip()
        return out or None
    except Exception:
        return None


def _first_matching_tag_for_head() -> Optional[str]:
    try:
        out = subprocess.check_output(["git", "tag", "--points-at", "HEAD"], text=True).splitlines()
        return out[0].strip() if out else None
    except Exception:
        return None


def _resolve_classification_from_snapshot(*, manifest: ClosureSnapshotManifest, review: RuntimeEvidenceReview, verification: ClosureSnapshotVerification) -> tuple[str, list[str], bool, list[str], str, str, list[str], list[str]]:
    primary = getattr(review, "primary_classification", "WITHIN_BOUNDS")
    secondary = list(getattr(review, "secondary_classifications", []) or [])
    governed_codes = list(getattr(review, "governed_exception_codes", []) or [])
    reasons = list(review.reasons)
    actions: list[str] = []
    signoff_status = getattr(review, "signoff_status", "WITHHELD")
    final_release_stance = "SIGNOFF_WITHHELD"

    if verification.status != "VERIFIED" or manifest.integrity_status != "VERIFIED":
        primary = "EVIDENCE_INTEGRITY_FAILURE"
        secondary = [item for item in secondary if item != primary]
        governed_codes = []
        signoff_status = "WITHHELD"
        final_release_stance = "SIGNOFF_WITHHELD"
        reasons = [
            "Canonical closure evidence is not fully verified; release conclusions cannot be promoted from narrative evidence.",
        ]
        if manifest.missing_artifact_paths:
            reasons.append("Closure snapshot is incomplete because referenced rollout artifacts are missing.")
        if verification.digest_mismatches:
            reasons.append("Closure snapshot verification found artifact digest mismatches.")
        actions.extend([
            "Repair the canonical evidence chain and regenerate the closure snapshot.",
            "Re-run closure snapshot verification before updating signoff documents.",
        ])
        return primary, secondary, False, governed_codes, signoff_status, final_release_stance, reasons, actions

    if review.decision == "ROLLBACK_RECOMMENDED":
        primary = "RUNTIME_FAILURE"
        signoff_status = "WITHHELD"
        final_release_stance = "ROLLBACK_RECOMMENDED"
        actions.append("Rollback or remediate the active release before further rollout expansion.")
    elif review.decision == "BLOCK_AND_INVESTIGATE":
        primary = "RUNTIME_FAILURE"
        signoff_status = "WITHHELD"
        final_release_stance = "SIGNOFF_WITHHELD"
        actions.append("Investigate and remediate must-fix runtime blockers before signoff.")
    elif review.decision == "CANDIDATE_RC2":
        signoff_status = "WITHHELD"
        final_release_stance = "SIGNOFF_WITHHELD"
        if primary == "ENVIRONMENTAL_NONCONFORMANCE":
            if "POLICY_MISMATCH" not in secondary:
                secondary.append("POLICY_MISMATCH")
            actions.extend([
                "Either approve a time-bounded governed exception for the current environment or promote an RC2 policy adjustment.",
                "Do not reinterpret environmental nonconformance as clean release closure without written approval.",
            ])
        else:
            if primary not in {"DATA_QUALITY_DEGRADATION", "POLICY_MISMATCH"}:
                primary = "POLICY_MISMATCH"
            actions.append("Review rollout thresholds and determine whether RC2 policy adjustments are required.")
    else:
        signoff_status = "APPROVED"
        final_release_stance = "KEEP_CURRENT_BASELINE"
        actions.append("Archive the verified closure package as the canonical release evidence chain.")

    governed_exception_eligible = primary == "ENVIRONMENTAL_NONCONFORMANCE" and bool(governed_codes)
    if primary == "ENVIRONMENTAL_NONCONFORMANCE":
        final_release_stance = "SIGNOFF_WITHHELD"
    return primary, [x for i, x in enumerate(secondary) if x != primary and x not in secondary[:i]], governed_exception_eligible, governed_codes, signoff_status, final_release_stance, reasons, actions


def _attestation_sha256(attestation: ClosureReleaseAttestation) -> str:
    payload = attestation.model_dump(mode="json")
    payload.pop("generated_at_utc", None)
    return _sha256_bytes(_json_canonical_bytes(payload))


def _unique_in_order(items: list[str]) -> list[str]:
    return [item for idx, item in enumerate(items) if item not in items[:idx]]


def build_governed_exception_memo(
    *,
    snapshot_path: Path,
    verification_path: Path,
    exception_code: str,
    requested_by: str,
    approved_by: str,
    valid_until_utc: datetime,
    rationale: str,
    constraints: Optional[list[str]] = None,
    repo_root: Optional[Path] = None,
    review_path: Optional[Path] = None,
    signing_private_key_path: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> tuple[GovernedExceptionMemo, Optional[DsseEnvelope]]:
    repo_root = (repo_root or Path.cwd()).resolve()
    snapshot_path = snapshot_path.resolve()
    verification_path = verification_path.resolve()
    now = now_utc or _utc_now()
    if valid_until_utc <= now:
        raise ValueError("governed exception validity must extend into the future")

    verification = ClosureSnapshotVerification.model_validate(_load_json(verification_path))
    if verification.status != "VERIFIED":
        raise ValueError("governed exception memo requires a VERIFIED closure snapshot verification artifact")

    base_attestation, _ = build_closure_release_attestation(
        snapshot_path=snapshot_path,
        repo_root=repo_root,
        verification=verification,
        verification_path=verification_path,
        review_path=review_path,
        now_utc=now,
    )
    if not base_attestation.governed_exception_eligible:
        raise ValueError("governed exception memo requires a governed-exception-eligible closure attestation")
    if base_attestation.primary_classification != "ENVIRONMENTAL_NONCONFORMANCE":
        raise ValueError("governed exception memo applies only to environmental nonconformance classifications")
    if exception_code not in base_attestation.governed_exception_codes:
        raise ValueError(f"governed exception code not present in attestation: {exception_code}")

    manifest = ClosureSnapshotManifest.model_validate(_load_json(snapshot_path))
    memo_constraints = [
        "Applies only to the scoped controlled-rollout environment.",
        "Does not waive runtime failures, evidence-integrity failures, or production validation.",
        f"Expires automatically at {valid_until_utc.isoformat()}.",
    ]
    if constraints:
        memo_constraints.extend([item.strip() for item in constraints if item.strip()])
    memo_constraints = _unique_in_order(memo_constraints)

    exception_id = _sha256_text(
        "|".join([
            manifest.closure_id,
            exception_code,
            approved_by,
            now.isoformat(),
            valid_until_utc.isoformat(),
            _attestation_sha256(base_attestation),
        ])
    )[:24]

    memo = GovernedExceptionMemo(
        generated_at_utc=now,
        exception_id=exception_id,
        closure_id=manifest.closure_id,
        snapshot_path=_normalize_path(snapshot_path.relative_to(repo_root) if snapshot_path.is_relative_to(repo_root) else snapshot_path),
        verification_path=_normalize_path(verification_path.relative_to(repo_root) if verification_path.is_relative_to(repo_root) else verification_path),
        machine_decision=base_attestation.machine_decision,
        primary_classification=base_attestation.primary_classification,
        governed_exception_code=exception_code,
        base_attestation_sha256=_attestation_sha256(base_attestation),
        scope=manifest.scope,
        requested_by=requested_by,
        approved_by=approved_by,
        approved_at_utc=now,
        valid_until_utc=valid_until_utc,
        rationale=rationale,
        constraints=memo_constraints,
        subjects=[
            _artifact_descriptor(snapshot_path, repo_root=repo_root),
            _artifact_descriptor(verification_path, repo_root=repo_root),
        ],
    )
    envelope = None
    if signing_private_key_path is not None:
        payload = _json_canonical_bytes(memo.model_dump(mode="json"))
        envelope = _sign_dsse_payload(
            payload_type=_GOVERNED_EXCEPTION_PAYLOAD_TYPE,
            payload=payload,
            signing_private_key_path=signing_private_key_path,
        )
    return memo, envelope


def verify_governed_exception_memo(
    *,
    memo_path: Path,
    repo_root: Optional[Path] = None,
    dsse_path: Optional[Path] = None,
    public_key_path: Optional[Path] = None,
    review_path: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> GovernedExceptionVerification:
    repo_root = (repo_root or Path.cwd()).resolve()
    memo_path = memo_path.resolve()
    now = now_utc or _utc_now()
    memo = GovernedExceptionMemo.model_validate(_load_json(memo_path))

    digest_mismatches: list[str] = []
    notes: list[str] = []
    verified_subjects: dict[str, Path] = {}
    for subject in memo.subjects:
        resolved = _resolve_existing_path(subject.path, repo_root=repo_root, preferred_parent=memo_path.parent)
        if resolved is None:
            digest_mismatches.append(f"missing subject: {subject.path}")
            continue
        actual_sha = _sha256_file(resolved)
        expected_sha = subject.digest.get("sha256")
        if actual_sha != expected_sha:
            digest_mismatches.append(f"{subject.path}: expected {expected_sha}, got {actual_sha}")
            continue
        verified_subjects[subject.path] = resolved

    artifact_digests_verified = len(verified_subjects) == len(memo.subjects) and not digest_mismatches

    snapshot_resolved = _resolve_existing_path(memo.snapshot_path, repo_root=repo_root, preferred_parent=memo_path.parent)
    verification_resolved = _resolve_existing_path(memo.verification_path, repo_root=repo_root, preferred_parent=memo_path.parent)
    base_attestation_match = False
    if snapshot_resolved is None or verification_resolved is None:
        notes.append("governed exception could not resolve the canonical snapshot or verification artifact")
    else:
        verification = ClosureSnapshotVerification.model_validate(_load_json(verification_resolved))
        if verification.status != "VERIFIED":
            notes.append("governed exception references a closure verification artifact that is not VERIFIED")
        else:
            base_attestation, _ = build_closure_release_attestation(
                snapshot_path=snapshot_resolved,
                repo_root=repo_root,
                verification=verification,
                verification_path=verification_resolved,
                review_path=review_path,
                now_utc=now,
            )
            base_attestation_match = _attestation_sha256(base_attestation) == memo.base_attestation_sha256
            if not base_attestation_match:
                notes.append("current machine-derived attestation no longer matches the attestation digest approved by the memo")

    signature_verified = False
    payload = _json_canonical_bytes(memo.model_dump(mode="json"))
    if dsse_path is not None:
        if public_key_path is None:
            notes.append("governed exception DSSE envelope supplied without public key; signature was not verified")
        else:
            envelope = DsseEnvelope.model_validate(_load_json(dsse_path.resolve()))
            if envelope.payloadType != _GOVERNED_EXCEPTION_PAYLOAD_TYPE:
                raise ValueError(f"unexpected governed exception DSSE payload type: {envelope.payloadType}")
            _verify_dsse_envelope(envelope=envelope, expected_payload=payload, public_key_path=public_key_path.resolve(), expected_payload_type=_GOVERNED_EXCEPTION_PAYLOAD_TYPE)
            signature_verified = True
    else:
        notes.append("governed exception memo is unsigned or signature verification was skipped")

    if now > memo.valid_until_utc:
        status = "EXPIRED"
    elif artifact_digests_verified and base_attestation_match and signature_verified:
        status = "VERIFIED"
    else:
        status = "UNVERIFIED"

    return GovernedExceptionVerification(
        verified_at_utc=now,
        memo_path=_normalize_path(memo_path.relative_to(repo_root) if memo_path.is_relative_to(repo_root) else memo_path),
        status=status,
        artifact_digests_verified=artifact_digests_verified,
        signature_verified=signature_verified,
        base_attestation_match=base_attestation_match,
        digest_mismatches=digest_mismatches,
        notes=notes,
    )


def build_closure_release_attestation(
    *,
    snapshot_path: Path,
    repo_root: Optional[Path] = None,
    verification: Optional[ClosureSnapshotVerification] = None,
    verification_path: Optional[Path] = None,
    dsse_path: Optional[Path] = None,
    public_key_path: Optional[Path] = None,
    review_path: Optional[Path] = None,
    governed_exception_memo: Optional[GovernedExceptionMemo] = None,
    governed_exception_verification: Optional[GovernedExceptionVerification] = None,
    now_utc: Optional[datetime] = None,
) -> tuple[ClosureReleaseAttestation, ClosureSnapshotVerification]:
    repo_root = (repo_root or Path.cwd()).resolve()
    snapshot_path = snapshot_path.resolve()
    manifest = ClosureSnapshotManifest.model_validate(_load_json(snapshot_path))
    closure_dir = snapshot_path.parent
    review_file = (review_path or closure_dir / "RUNTIME_REVIEW.json").resolve()
    if not review_file.exists():
        raise FileNotFoundError(f"closure attestation requires runtime review artifact: {review_file}")
    review = RuntimeEvidenceReview.model_validate(_load_json(review_file))
    verification_obj = verification or verify_closure_snapshot(
        snapshot_path=snapshot_path,
        repo_root=repo_root,
        dsse_path=dsse_path,
        public_key_path=public_key_path,
        now_utc=now_utc,
    )
    verification_ref = verification_path.resolve() if verification_path is not None else None
    (
        primary,
        secondary,
        governed_exception_eligible,
        governed_codes,
        signoff_status,
        final_release_stance,
        reasons,
        actions,
    ) = _resolve_classification_from_snapshot(manifest=manifest, review=review, verification=verification_obj)

    if final_release_stance == "ROLLBACK_RECOMMENDED":
        summary_line = "Verified closure evidence recommends rollback or hard remediation before further rollout."
    elif governed_exception_eligible:
        summary_line = "Verified closure evidence shows environmental nonconformance only; signoff remains withheld unless a governed exception is approved."
    elif signoff_status == "APPROVED":
        summary_line = "Verified closure evidence remains within keep-current-release bounds."
    else:
        summary_line = "Verified closure evidence withholds signoff until runtime blockers or policy mismatches are resolved."

    attestation = ClosureReleaseAttestation(
        generated_at_utc=now_utc or _utc_now(),
        closure_id=manifest.closure_id,
        snapshot_path=_normalize_path(snapshot_path.relative_to(repo_root) if snapshot_path.is_relative_to(repo_root) else snapshot_path),
        verification_path=_normalize_path(verification_ref.relative_to(repo_root) if verification_ref and verification_ref.is_relative_to(repo_root) else verification_ref) if verification_ref is not None else None,
        evidence_integrity_status=verification_obj.status,
        machine_decision=review.decision,
        signoff_status=signoff_status,
        final_release_stance=final_release_stance,
        primary_classification=primary,
        secondary_classifications=secondary,
        governed_exception_eligible=governed_exception_eligible,
        governed_exception_codes=governed_codes,
        reasons=reasons,
        required_operator_actions=actions,
        summary_line=summary_line,
    )

    if governed_exception_memo is not None and governed_exception_verification is not None:
        if governed_exception_verification.status == "VERIFIED":
            if governed_exception_memo.closure_id != attestation.closure_id:
                raise ValueError("governed exception memo closure_id does not match the attested closure")
            if governed_exception_memo.governed_exception_code not in attestation.governed_exception_codes:
                raise ValueError("governed exception memo code is not permitted by the machine attestation")
            attestation.signoff_status = "APPROVED"
            attestation.final_release_stance = "KEEP_CURRENT_BASELINE_WITH_GOVERNED_EXCEPTION"
            attestation.applied_governed_exception_id = governed_exception_memo.exception_id
            attestation.applied_governed_exception_code = governed_exception_memo.governed_exception_code
            attestation.applied_governed_exception_approved_by = governed_exception_memo.approved_by
            attestation.applied_governed_exception_valid_until_utc = governed_exception_memo.valid_until_utc
            attestation.reasons = _unique_in_order(attestation.reasons + [
                f"Approved governed exception '{governed_exception_memo.governed_exception_code}' preserves the current baseline until {governed_exception_memo.valid_until_utc.isoformat()}.",
            ])
            attestation.required_operator_actions = _unique_in_order(attestation.required_operator_actions + [
                "Re-evaluate the closure snapshot before the governed exception expires.",
                "Do not renew the exception without re-verifying the snapshot and runtime review.",
            ])
            attestation.summary_line = "Verified closure evidence remains environmentally nonconformant, but an approved governed exception preserves the current baseline within the scoped environment."
        else:
            status_word = governed_exception_verification.status.lower()
            attestation.reasons = _unique_in_order(attestation.reasons + [
                f"A governed exception memo was supplied but is {status_word}; signoff remains withheld.",
            ])
            attestation.required_operator_actions = _unique_in_order(attestation.required_operator_actions + [
                "Repair, renew, or remove the invalid governed exception memo before treating it as authoritative.",
            ])

    return attestation, verification_obj

from strategy_validator.validator.rollout_ops_rendering import (
    render_decision_reconciliation_markdown,
    render_final_release_signoff_markdown,
    render_governed_exception_markdown,
)

def default_startup_json_bundle() -> dict[str, Any]:
    return dict(json.loads(export_startup_json_bundle()))
