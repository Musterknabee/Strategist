"""Canonical rollout operations facade.

This module intentionally re-exports the typed rollout evidence primitives from
`rollout_ops_evidence` so legacy imports keep working without placeholder
`SimpleReport` shims.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.contracts.operational import (
    ClosureReleaseAttestation,
    ClosureSnapshotManifest,
    ClosureSnapshotVerification,
    GovernedExceptionMemo,
    GovernedExceptionVerification,
)
from strategy_validator.validator.rollout_ops_evidence import (
    _artifact_descriptor,
    _json_canonical_bytes,
    _normalize_path,
    _resolve_existing_path,
    _sha256_bytes,
    _sha256_file,
    _sign_dsse_payload,
    _verify_dsse_envelope,
    build_closure_snapshot,
    build_daily_checklist,
    build_rollout_bundle,
    generate_host_fingerprint,
    generate_snapshot_signing_keypair,
    load_controlled_rollout_rules,
    parse_analyze_summary,
    review_runtime_evidence,
    verify_closure_snapshot,
)
from strategy_validator.validator.rollout_ops_rendering import (
    render_decision_reconciliation_markdown,
    render_final_release_signoff_markdown,
    render_governed_exception_markdown,
)


def default_startup_json_bundle(*, readiness_status: str = "READY") -> dict[str, object]:
    return {
        "readiness": {"status": readiness_status},
        "http_market_data_connector_issues": [],
        "alpaca_market_data_connector_issues": [],
    }


def build_closure_release_attestation(*args, **kwargs):
    if args:
        raise TypeError("build_closure_release_attestation requires keyword arguments.")
    snapshot_path = Path(kwargs["snapshot_path"])
    verification = kwargs["verification"]
    verification_path = kwargs.get("verification_path")
    now_utc = kwargs.get("now_utc") or datetime.now(timezone.utc)
    governed_exception_memo = kwargs.get("governed_exception_memo")
    governed_exception_verification = kwargs.get("governed_exception_verification")
    manifest = ClosureSnapshotManifest.model_validate(json.loads(snapshot_path.read_text(encoding="utf-8")))
    verification = ClosureSnapshotVerification.model_validate(verification)
    review_path = snapshot_path.parent / "RUNTIME_REVIEW.json"
    review_payload = json.loads(review_path.read_text(encoding="utf-8")) if review_path.exists() else {}
    primary = str(review_payload.get("primary_classification") or "WITHIN_BOUNDS")
    secondary = list(review_payload.get("secondary_classifications") or [])
    governed_codes = list(review_payload.get("governed_exception_codes") or [])
    reasons = list(review_payload.get("reasons") or [])
    required_actions = list(review_payload.get("must_fix_flags") or [])
    signoff_status = "WITHHELD"
    final_stance = "SIGNOFF_WITHHELD"
    applied_id = None
    applied_code = None
    applied_by = None
    applied_until = None
    governed_verification = (
        GovernedExceptionVerification.model_validate(governed_exception_verification)
        if governed_exception_verification is not None
        else None
    )
    if (
        governed_exception_memo is not None
        and governed_verification is not None
        and governed_verification.status == "VERIFIED"
    ):
        memo = GovernedExceptionMemo.model_validate(governed_exception_memo)
        signoff_status = "APPROVED"
        final_stance = "KEEP_CURRENT_BASELINE_WITH_GOVERNED_EXCEPTION"
        applied_id = memo.exception_id
        applied_code = memo.governed_exception_code
        applied_by = memo.approved_by
        applied_until = memo.valid_until_utc
    elif verification.status == "VERIFIED" and primary == "WITHIN_BOUNDS":
        signoff_status = "APPROVED"
        final_stance = "KEEP_CURRENT_BASELINE"
    elif governed_verification is not None and governed_verification.status == "EXPIRED":
        reasons.append("Governed exception is expired and cannot approve signoff.")
    attestation = ClosureReleaseAttestation(
        generated_at_utc=now_utc,
        closure_id=manifest.closure_id,
        snapshot_path=str(snapshot_path),
        verification_path=str(verification_path) if verification_path is not None else verification.manifest_path,
        evidence_integrity_status="VERIFIED" if verification.status == "VERIFIED" else "INCOMPLETE",
        machine_decision=str(review_payload.get("decision") or ("CANDIDATE_RC2" if verification.status == "VERIFIED" else "BLOCK_AND_INVESTIGATE")),
        signoff_status=signoff_status,
        final_release_stance=final_stance,
        primary_classification=primary,
        secondary_classifications=secondary,
        governed_exception_eligible=bool(governed_codes),
        governed_exception_codes=governed_codes,
        applied_governed_exception_id=applied_id,
        applied_governed_exception_code=applied_code,
        applied_governed_exception_approved_by=applied_by,
        applied_governed_exception_valid_until_utc=applied_until,
        reasons=reasons,
        required_operator_actions=required_actions,
        summary_line="Closure release attestation generated from verification and runtime review evidence.",
    )
    return attestation, verification


def build_governed_exception_memo(*args, **kwargs):
    if args:
        raise TypeError("build_governed_exception_memo requires keyword arguments.")
    snapshot_path = Path(kwargs["snapshot_path"])
    verification_path = Path(kwargs["verification_path"])
    now_utc = kwargs.get("now_utc") or datetime.now(timezone.utc)
    exception_code = str(kwargs["exception_code"])
    requested_by = str(kwargs["requested_by"])
    approved_by = str(kwargs["approved_by"])
    valid_until_utc = kwargs["valid_until_utc"]
    rationale = str(kwargs["rationale"])
    constraints = list(kwargs.get("constraints") or [])
    private_key_path = kwargs.get("signing_private_key_path")
    manifest = ClosureSnapshotManifest.model_validate(json.loads(snapshot_path.read_text(encoding="utf-8")))
    verification = ClosureSnapshotVerification.model_validate(json.loads(verification_path.read_text(encoding="utf-8")))
    review_path = snapshot_path.parent / "RUNTIME_REVIEW.json"
    review_payload = json.loads(review_path.read_text(encoding="utf-8")) if review_path.exists() else {}
    base_attestation = build_closure_release_attestation(
        snapshot_path=snapshot_path,
        repo_root=kwargs.get("repo_root"),
        verification=verification,
        verification_path=verification_path,
        now_utc=now_utc,
    )[0]
    base_attestation_sha256 = hashlib.sha256(_json_canonical_bytes(base_attestation.model_dump(mode="json"))).hexdigest()
    memo = GovernedExceptionMemo(
        generated_at_utc=now_utc,
        exception_id=f"governed-exception-{manifest.closure_id}",
        closure_id=manifest.closure_id,
        snapshot_path=str(snapshot_path),
        verification_path=str(verification_path),
        machine_decision=base_attestation.machine_decision,
        primary_classification=base_attestation.primary_classification,
        governed_exception_code=exception_code,
        base_attestation_sha256=base_attestation_sha256,
        scope=manifest.scope,
        requested_by=requested_by,
        approved_by=approved_by,
        approved_at_utc=now_utc,
        valid_until_utc=valid_until_utc,
        rationale=rationale,
        constraints=constraints,
        subjects=manifest.subjects,
    )
    envelope = (
        _sign_dsse_payload(
            payload_type="application/vnd.strategy-validator.governed-exception-memo+json",
            payload=_json_canonical_bytes(memo.model_dump(mode="json")),
            signing_private_key_path=Path(private_key_path),
        )
        if private_key_path
        else None
    )
    return memo, envelope


def verify_governed_exception_memo(*args, **kwargs):
    if args:
        raise TypeError("verify_governed_exception_memo requires keyword arguments.")
    now_utc = kwargs.get("now_utc") or datetime.now(timezone.utc)
    memo_path = Path(kwargs["memo_path"])
    dsse_path = kwargs.get("dsse_path")
    public_key_path = kwargs.get("public_key_path")
    memo = GovernedExceptionMemo.model_validate(json.loads(memo_path.read_text(encoding="utf-8")))
    expired = now_utc > memo.valid_until_utc
    signature_verified = False
    notes: list[str] = []
    if dsse_path and public_key_path:
        try:
            envelope = json.loads(Path(dsse_path).read_text(encoding="utf-8"))
            from strategy_validator.contracts.operational import DsseEnvelope

            _verify_dsse_envelope(
                envelope=DsseEnvelope.model_validate(envelope),
                expected_payload=_json_canonical_bytes(memo.model_dump(mode="json")),
                public_key_path=Path(public_key_path),
                expected_payload_type="application/vnd.strategy-validator.governed-exception-memo+json",
            )
            signature_verified = True
        except Exception as exc:
            notes.append(f"signature verification failed: {exc}")
    base_attestation_match = bool(memo.base_attestation_sha256)
    status = "EXPIRED" if expired else ("VERIFIED" if signature_verified and base_attestation_match else "UNVERIFIED")
    return GovernedExceptionVerification(
        verified_at_utc=now_utc,
        memo_path=str(memo_path),
        status=status,
        artifact_digests_verified=signature_verified,
        signature_verified=signature_verified,
        base_attestation_match=base_attestation_match,
        notes=notes,
    )

__all__ = [
    "build_closure_release_attestation",
    "build_closure_snapshot",
    "build_daily_checklist",
    "build_governed_exception_memo",
    "build_rollout_bundle",
    "default_startup_json_bundle",
    "generate_host_fingerprint",
    "generate_snapshot_signing_keypair",
    "load_controlled_rollout_rules",
    "parse_analyze_summary",
    "render_decision_reconciliation_markdown",
    "render_final_release_signoff_markdown",
    "render_governed_exception_markdown",
    "review_runtime_evidence",
    "verify_closure_snapshot",
    "verify_governed_exception_memo",
    "_artifact_descriptor",
    "_json_canonical_bytes",
    "_normalize_path",
    "_resolve_existing_path",
    "_sha256_bytes",
    "_sha256_file",
    "_sign_dsse_payload",
    "_verify_dsse_envelope",
]
