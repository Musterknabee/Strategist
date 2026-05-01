from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import os
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from strategy_validator.contracts.interface_freeze import PILOT_RC_INTERFACE_FREEZE
from strategy_validator.contracts.operational import (
    ClosureSnapshotInvariantSet,
    ClosureSnapshotManifest,
    ClosureSnapshotOperationalSummary,
    ClosureSnapshotVerification,
    ControlledRolloutBundle,
    ControlledRolloutRules,
    DailyOperationsChecklist,
    DsseEnvelope,
    DsseSignature,
    EvidenceResourceDescriptor,
    KeyedHostFingerprint,
    RolloutHostKind,
    RolloutScope,
    RuntimeEvidenceReview,
)
from strategy_validator.core.config import load_config
from strategy_validator.validator.readiness import perform_readiness_check

_SECRET_ENV_KEYS: tuple[str, ...] = (
    "APCA_API_KEY_ID",
    "APCA_API_SECRET_KEY",
    "STRATEGY_VALIDATOR_ALPACA_API_KEY_ID_ENV",
    "STRATEGY_VALIDATOR_ALPACA_API_SECRET_KEY_ENV",
)
_DEFAULT_RULES_PATH = Path(__file__).resolve().parents[1] / "policies" / "controlled_rollout_rules.json"
_CLOSURE_SNAPSHOT_PAYLOAD_TYPE = "application/vnd.strategy-validator.closure-snapshot.v1+json"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _normalize_path(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def _json_canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


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

def _load_json(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _resolve_existing_path(raw_path: str | Path, *, repo_root: Path, preferred_parent: Optional[Path] = None) -> Optional[Path]:
    p = Path(raw_path)
    candidates: list[Path] = []
    if p.is_absolute():
        candidates.append(p)
    else:
        if preferred_parent is not None:
            candidates.append(preferred_parent / p)
        candidates.append(repo_root / p)
        candidates.append(Path.cwd() / p)
    seen: set[str] = set()
    for candidate in candidates:
        key = _normalize_path(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists():
            return candidate.resolve()
    return None


def _artifact_descriptor(path: Path, *, repo_root: Path) -> EvidenceResourceDescriptor:
    try:
        stored_path = _normalize_path(path.resolve().relative_to(repo_root.resolve()))
    except Exception:
        stored_path = _normalize_path(path.resolve())
    media_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    return EvidenceResourceDescriptor(
        name=path.name,
        path=stored_path,
        digest={"sha256": _sha256_file(path)},
        size_bytes=path.stat().st_size,
        media_type=media_type,
    )


def _public_key_id(public_key: Ed25519PublicKey) -> str:
    der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return _sha256_bytes(der)


def _dsse_pae(payload_type: str, payload: bytes) -> bytes:
    pt = payload_type.encode("utf-8")
    return b"DSSEv1 " + str(len(pt)).encode("ascii") + b" " + pt + b" " + str(len(payload)).encode("ascii") + b" " + payload


def generate_snapshot_signing_keypair(*, private_key_path: Path, public_key_path: Path) -> tuple[Path, Path]:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    private_key_path.parent.mkdir(parents=True, exist_ok=True)
    public_key_path.parent.mkdir(parents=True, exist_ok=True)
    private_key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_key_path.write_bytes(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return private_key_path, public_key_path


def _load_private_key(path: Path) -> Ed25519PrivateKey:
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("closure snapshot signing requires an Ed25519 private key")
    return key


def _load_public_key(path: Path) -> Ed25519PublicKey:
    key = serialization.load_pem_public_key(path.read_bytes())
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("closure snapshot verification requires an Ed25519 public key")
    return key


def _sign_dsse_payload(*, payload_type: str, payload: bytes, signing_private_key_path: Path) -> DsseEnvelope:
    private_key = _load_private_key(signing_private_key_path)
    public_key = private_key.public_key()
    signature = private_key.sign(_dsse_pae(payload_type, payload))
    return DsseEnvelope(
        payloadType=payload_type,
        payload=base64.b64encode(payload).decode("ascii"),
        signatures=[
            DsseSignature(
                keyid=_public_key_id(public_key),
                sig=base64.b64encode(signature).decode("ascii"),
            )
        ],
    )


def _verify_dsse_envelope(*, envelope: DsseEnvelope, expected_payload: bytes, public_key_path: Path, expected_payload_type: str) -> None:
    public_key = _load_public_key(public_key_path)
    if envelope.payloadType != expected_payload_type:
        raise ValueError(f"unexpected DSSE payload type: {envelope.payloadType}")
    actual_payload = base64.b64decode(envelope.payload.encode("ascii"))
    if actual_payload != expected_payload:
        raise ValueError("DSSE payload does not match closure snapshot manifest bytes")
    if not envelope.signatures:
        raise ValueError("DSSE envelope contains no signatures")
    expected_keyid = _public_key_id(public_key)
    verification_error: Optional[Exception] = None
    for signature in envelope.signatures:
        if signature.keyid != expected_keyid:
            continue
        try:
            public_key.verify(base64.b64decode(signature.sig.encode("ascii")), _dsse_pae(envelope.payloadType, actual_payload))
            return
        except Exception as exc:  # pragma: no cover - exercised by failure tests via outer path
            verification_error = exc
            break
    if verification_error is not None:
        raise ValueError("DSSE signature verification failed") from verification_error
    raise ValueError("no DSSE signature matched the supplied public key")


def generate_host_fingerprint(
    *,
    host_kind: RolloutHostKind,
    host_label: Optional[str] = None,
    policy_path: Path,
    env_keys: Iterable[str] = _SECRET_ENV_KEYS,
    now_utc: Optional[datetime] = None,
) -> KeyedHostFingerprint:
    cfg = load_config()
    readiness = perform_readiness_check()
    now = now_utc or _utc_now()
    env_presence: dict[str, bool] = {}
    env_hashes: dict[str, str] = {}
    for key in env_keys:
        val = os.environ.get(key)
        env_presence[key] = val is not None and val != ""
        if val:
            env_hashes[key] = _sha256_text(val)
    return KeyedHostFingerprint(
        generated_at_utc=now,
        host_kind=host_kind,
        host_label=host_label or socket.gethostname(),
        interface_freeze_id=PILOT_RC_INTERFACE_FREEZE,
        runtime_mode=cfg.mode,
        config_fingerprint=readiness.config_fingerprint,
        policy_sha256=_policy_sha256(policy_path),
        git_commit=_git_output(["git", "rev-parse", "HEAD"]),
        git_tag=_first_matching_tag_for_head(),
        env_presence=env_presence,
        env_value_sha256=env_hashes,
    )


def parse_analyze_summary(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    split = text.split("\n\n", 1)
    head = split[0].strip()
    return dict(json.loads(head))


def build_rollout_bundle(
    *,
    policy_path: Path,
    keyed_host_fingerprint_path: Path,
    burnin_artifact_paths: list[Path],
    scope: RolloutScope,
    now_utc: Optional[datetime] = None,
) -> ControlledRolloutBundle:
    if not keyed_host_fingerprint_path.exists():
        raise FileNotFoundError(f"keyed host fingerprint artifact does not exist: {keyed_host_fingerprint_path}")
    missing_burnin = [str(p) for p in burnin_artifact_paths if not p.exists()]
    if missing_burnin:
        raise FileNotFoundError(
            "controlled rollout bundle cannot reference missing burn-in artifacts: " + ", ".join(missing_burnin)
        )
    cfg = load_config()
    readiness = perform_readiness_check()
    policy = cfg.runtime_policy
    provider_summary = (
        f"allow_provisional={policy.allow_provisional_market_data}; "
        f"allow_snapshot={policy.allow_snapshot_market_data}; "
        f"allow_fallback={policy.allow_market_data_fallback}; "
        f"strict_mode={policy.strict_production_mode}"
    )
    return ControlledRolloutBundle(
        generated_at_utc=now_utc or _utc_now(),
        runtime_mode=cfg.mode,
        config_fingerprint=readiness.config_fingerprint,
        policy_sha256=_policy_sha256(policy_path),
        interface_freeze_id=PILOT_RC_INTERFACE_FREEZE,
        release_commit=_git_output(["git", "rev-parse", "HEAD"]),
        release_tag=_first_matching_tag_for_head(),
        provider_source_policy_summary=provider_summary,
        keyed_host_fingerprint_path=_normalize_path(keyed_host_fingerprint_path),
        burnin_artifact_paths=[_normalize_path(p) for p in burnin_artifact_paths],
        scope=scope,
    )


def build_daily_checklist(
    *,
    analyze_summaries: list[dict[str, Any]],
    startup_json: Optional[dict[str, Any]] = None,
    telemetry_sink_healthy: bool = True,
    rules: Optional[ControlledRolloutRules] = None,
    now_utc: Optional[datetime] = None,
) -> DailyOperationsChecklist:
    rules = rules or load_controlled_rollout_rules()
    readiness = perform_readiness_check()
    total_rounds = sum(int(s.get("rounds") or 0) for s in analyze_summaries)
    provider_success = sum(int((s.get("provider_status_counts") or {}).get("SUCCESS", 0)) for s in analyze_summaries)
    stale = sum(int((s.get("effective_freshness_counts") or {}).get("STALE", 0)) for s in analyze_summaries)
    fallback = sum(int(s.get("fallback_applied_rounds") or 0) for s in analyze_summaries)
    circuit = sum(int((s.get("provider_status_counts") or {}).get("CIRCUIT_OPEN", 0)) for s in analyze_summaries)
    auth = sum(int((s.get("failure_domain_counts") or {}).get("AUTH", 0)) for s in analyze_summaries)
    rl = sum(int(s.get("rate_limit_proxy_rounds") or 0) for s in analyze_summaries)
    timeout = sum(int(s.get("timeout_signal_rounds") or 0) for s in analyze_summaries)
    retry = 0
    startup_ok = True
    checklist_readiness_status = readiness.status
    if startup_json is not None:
        snapshot_readiness_status = (
            startup_json.get("readiness", {}).get("status")
            or startup_json.get("heartbeat", {}).get("readiness_status")
            or startup_json.get("readiness_status")
            or "BLOCKED"
        )
        startup_ok = (
            snapshot_readiness_status == "READY"
            and not startup_json.get("http_market_data_connector_issues")
            and not startup_json.get("alpaca_market_data_connector_issues")
        )
        checklist_readiness_status = snapshot_readiness_status

    policy_change_reasons: list[str] = []
    if stale >= max(rules.policy_change_stale_floor, total_rounds // rules.policy_change_stale_fraction_denominator if total_rounds else rules.policy_change_stale_floor):
        policy_change_reasons.append("freshness_anomaly_threshold_crossed")
    if timeout >= max(rules.policy_change_timeout_floor, total_rounds // rules.policy_change_timeout_fraction_denominator if total_rounds else rules.policy_change_timeout_floor):
        policy_change_reasons.append("timeout_threshold_crossed")
    if circuit >= max(rules.policy_change_circuit_floor, total_rounds // rules.policy_change_circuit_fraction_denominator if total_rounds else rules.policy_change_circuit_floor):
        policy_change_reasons.append("circuit_open_threshold_crossed")
    if auth + rl >= max(rules.policy_change_auth_rate_limit_floor, total_rounds // rules.policy_change_auth_rate_limit_fraction_denominator if total_rounds else rules.policy_change_auth_rate_limit_floor):
        policy_change_reasons.append("auth_or_rate_limit_threshold_crossed")

    provider_availability_ok = provider_success > 0 and circuit < total_rounds
    return DailyOperationsChecklist(
        generated_at_utc=now_utc or _utc_now(),
        startup_check_passed=startup_ok,
        readiness_status=checklist_readiness_status,
        provider_availability_ok=provider_availability_ok,
        freshness_anomaly_count=stale,
        fallback_count=fallback,
        circuit_open_count=circuit,
        auth_rate_limit_count=auth + rl,
        timeout_count=timeout,
        retry_count=retry,
        telemetry_sink_healthy=telemetry_sink_healthy,
        policy_change_justified=bool(policy_change_reasons),
        policy_change_reasons=policy_change_reasons,
    )


def review_runtime_evidence(
    *,
    checklist: DailyOperationsChecklist | dict[str, object],
    rules: Optional[ControlledRolloutRules] = None,
    now_utc: Optional[datetime] = None,
) -> RuntimeEvidenceReview:
    if isinstance(checklist, dict):
        try:
            checklist = DailyOperationsChecklist.model_validate(checklist)
        except Exception as exc:
            raise ValueError(f"invalid runtime evidence checklist payload: {exc}") from exc
    rules = rules or load_controlled_rollout_rules()
    reasons: list[str] = []
    observe_only: list[str] = []
    must_fix: list[str] = []
    governed_exception_codes: list[str] = []
    secondary_classifications: list[str] = []
    decision = "KEEP_CURRENT_RELEASE"
    primary_classification = "WITHIN_BOUNDS"
    signoff_status = "APPROVED"

    if checklist.freshness_anomaly_count > 0:
        secondary_classifications.append("DATA_QUALITY_DEGRADATION")
    if checklist.policy_change_justified:
        secondary_classifications.append("POLICY_MISMATCH")

    if checklist.readiness_status == "BLOCKED" or not checklist.startup_check_passed:
        decision = "BLOCK_AND_INVESTIGATE"
        primary_classification = "RUNTIME_FAILURE"
        signoff_status = "WITHHELD"
        must_fix.append("startup_or_readiness_blocked")
        reasons.append("Readiness/startup checks are not passing.")

    if checklist.auth_rate_limit_count >= rules.decision_auth_rate_limit_block_floor:
        decision = "BLOCK_AND_INVESTIGATE"
        primary_classification = "RUNTIME_FAILURE"
        signoff_status = "WITHHELD"
        must_fix.append("auth_or_rate_limit_instability")
        reasons.append("Repeated auth/rate-limit failures in controlled rollout.")

    if checklist.circuit_open_count >= rules.decision_circuit_block_floor and checklist.fallback_count == 0:
        decision = "ROLLBACK_RECOMMENDED" if decision == "BLOCK_AND_INVESTIGATE" else "BLOCK_AND_INVESTIGATE"
        primary_classification = "RUNTIME_FAILURE"
        signoff_status = "WITHHELD"
        must_fix.append("persistent_circuit_open_without_recovery")
        reasons.append("Circuit remains open without recovery/fallback.")

    freshness_only_nonconformance = (
        checklist.policy_change_justified
        and checklist.freshness_anomaly_count > 0
        and checklist.timeout_count == 0
        and checklist.auth_rate_limit_count == 0
        and checklist.circuit_open_count == 0
        and checklist.startup_check_passed
        and checklist.readiness_status == "READY"
        and not must_fix
    )

    if checklist.policy_change_justified and decision == "KEEP_CURRENT_RELEASE":
        decision = "CANDIDATE_RC2"
        signoff_status = "WITHHELD"
        if freshness_only_nonconformance:
            primary_classification = "ENVIRONMENTAL_NONCONFORMANCE"
            governed_exception_codes.append("freshness_nonconformance_without_runtime_failure")
            reasons.append("Freshness thresholds were crossed without functional/runtime failure; evidence indicates environmental nonconformance.")
        elif checklist.timeout_count > 0 or checklist.auth_rate_limit_count > 0:
            primary_classification = "DATA_QUALITY_DEGRADATION"
            reasons.append("Observed thresholds crossed; evidence supports policy adjustment discussion.")
        else:
            primary_classification = "POLICY_MISMATCH"
            reasons.append("Observed thresholds crossed; evidence supports policy adjustment discussion.")

    if checklist.fallback_count > 0 and checklist.policy_change_justified is False:
        observe_only.append("fallback_events_observed_below_change_threshold")

    if decision == "KEEP_CURRENT_RELEASE" and checklist.freshness_anomaly_count == 0 and checklist.fallback_count == 0:
        secondary_classifications = []

    if not reasons:
        reasons.append("Controlled rollout evidence remains within keep-current-release bounds.")

    secondary_unique = [
        item for idx, item in enumerate(secondary_classifications)
        if item != primary_classification and item not in secondary_classifications[:idx]
    ]
    governed_exception_eligible = bool(governed_exception_codes)

    return RuntimeEvidenceReview(
        generated_at_utc=now_utc or _utc_now(),
        decision=decision,
        primary_classification=primary_classification,
        secondary_classifications=secondary_unique,
        signoff_status=signoff_status,
        governed_exception_eligible=governed_exception_eligible,
        governed_exception_codes=governed_exception_codes,
        reasons=reasons,
        observe_only_flags=observe_only,
        must_fix_flags=must_fix,
    )


def _build_snapshot_invariants(*, fingerprint: KeyedHostFingerprint, bundle: ControlledRolloutBundle) -> ClosureSnapshotInvariantSet:
    mismatches: list[str] = []
    if fingerprint.interface_freeze_id != bundle.interface_freeze_id:
        mismatches.append("interface_freeze_id")
    if fingerprint.policy_sha256 != bundle.policy_sha256:
        mismatches.append("policy_sha256")
    if fingerprint.config_fingerprint != bundle.config_fingerprint:
        mismatches.append("config_fingerprint")
    if fingerprint.runtime_mode != bundle.runtime_mode:
        mismatches.append("runtime_mode")
    if bundle.release_commit and fingerprint.git_commit and bundle.release_commit != fingerprint.git_commit:
        mismatches.append("release_commit")
    if bundle.release_tag and fingerprint.git_tag and bundle.release_tag != fingerprint.git_tag:
        mismatches.append("release_tag")
    if mismatches:
        raise ValueError(
            "canonical closure invariants disagree across fingerprint and bundle: " + ", ".join(sorted(mismatches))
        )
    return ClosureSnapshotInvariantSet(
        interface_freeze_id=bundle.interface_freeze_id,
        policy_sha256=bundle.policy_sha256,
        config_fingerprint=bundle.config_fingerprint,
        runtime_mode=bundle.runtime_mode,
        release_commit=bundle.release_commit or fingerprint.git_commit,
        release_tag=bundle.release_tag or fingerprint.git_tag,
        host_kind=fingerprint.host_kind,
    )


def build_closure_snapshot(
    *,
    closure_dir: Path,
    repo_root: Optional[Path] = None,
    fingerprint_path: Optional[Path] = None,
    bundle_path: Optional[Path] = None,
    checklist_path: Optional[Path] = None,
    review_path: Optional[Path] = None,
    allow_incomplete: bool = False,
    signing_private_key_path: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> tuple[ClosureSnapshotManifest, Optional[DsseEnvelope]]:
    repo_root = (repo_root or Path.cwd()).resolve()
    closure_dir = closure_dir.resolve()
    fingerprint_file = (fingerprint_path or closure_dir / "KEYED_HOST_FINGERPRINT.json").resolve()
    bundle_file = (bundle_path or closure_dir / "ROLLOUT_BUNDLE.json").resolve()
    checklist_file = (checklist_path or closure_dir / "DAILY_CHECKLIST.json").resolve()
    review_file = (review_path or closure_dir / "RUNTIME_REVIEW.json").resolve()

    required_files = [fingerprint_file, bundle_file, checklist_file, review_file]
    missing_required = [str(p) for p in required_files if not p.exists()]
    if missing_required:
        raise FileNotFoundError("closure snapshot requires canonical artifacts: " + ", ".join(missing_required))

    fingerprint = KeyedHostFingerprint.model_validate(_load_json(fingerprint_file))
    bundle = ControlledRolloutBundle.model_validate(_load_json(bundle_file))
    checklist = DailyOperationsChecklist.model_validate(_load_json(checklist_file))
    review = RuntimeEvidenceReview.model_validate(_load_json(review_file))

    invariants = _build_snapshot_invariants(fingerprint=fingerprint, bundle=bundle)

    referenced_fingerprint = _resolve_existing_path(
        bundle.keyed_host_fingerprint_path,
        repo_root=repo_root,
        preferred_parent=bundle_file.parent,
    )
    if referenced_fingerprint is None:
        raise FileNotFoundError(
            f"rollout bundle references a keyed fingerprint artifact that does not exist: {bundle.keyed_host_fingerprint_path}"
        )
    if referenced_fingerprint.resolve() != fingerprint_file.resolve():
        raise ValueError("rollout bundle keyed_host_fingerprint_path does not match the canonical fingerprint artifact")

    subjects = [
        _artifact_descriptor(fingerprint_file, repo_root=repo_root),
        _artifact_descriptor(bundle_file, repo_root=repo_root),
        _artifact_descriptor(checklist_file, repo_root=repo_root),
        _artifact_descriptor(review_file, repo_root=repo_root),
    ]
    missing_artifact_paths: list[str] = []
    for raw_path in bundle.burnin_artifact_paths:
        resolved = _resolve_existing_path(raw_path, repo_root=repo_root, preferred_parent=bundle_file.parent)
        if resolved is None:
            missing_artifact_paths.append(_normalize_path(raw_path))
            continue
        subjects.append(_artifact_descriptor(resolved, repo_root=repo_root))

    integrity_status = "VERIFIED" if not missing_artifact_paths else "INCOMPLETE"
    if missing_artifact_paths and not allow_incomplete:
        raise FileNotFoundError(
            "closure snapshot cannot be finalized with missing burn-in artifacts: " + ", ".join(missing_artifact_paths)
        )

    manifest = ClosureSnapshotManifest(
        generated_at_utc=now_utc or _utc_now(),
        closure_id=closure_dir.name,
        closure_dir=_normalize_path(closure_dir.relative_to(repo_root) if closure_dir.is_relative_to(repo_root) else closure_dir),
        integrity_status=integrity_status,
        subjects=subjects,
        missing_artifact_paths=missing_artifact_paths,
        invariants=invariants,
        scope=bundle.scope,
        operational_summary=ClosureSnapshotOperationalSummary(
            startup_check_passed=checklist.startup_check_passed,
            readiness_status=checklist.readiness_status,
            provider_availability_ok=checklist.provider_availability_ok,
            freshness_anomaly_count=checklist.freshness_anomaly_count,
            fallback_count=checklist.fallback_count,
            circuit_open_count=checklist.circuit_open_count,
            auth_rate_limit_count=checklist.auth_rate_limit_count,
            timeout_count=checklist.timeout_count,
            policy_change_justified=checklist.policy_change_justified,
            release_decision=review.decision,
            observe_only_flags=review.observe_only_flags,
            must_fix_flags=review.must_fix_flags,
        ),
    )
    envelope = None
    if signing_private_key_path is not None:
        manifest_bytes = _json_canonical_bytes(manifest.model_dump(mode="json"))
        envelope = _sign_dsse_payload(
            payload_type=_CLOSURE_SNAPSHOT_PAYLOAD_TYPE,
            payload=manifest_bytes,
            signing_private_key_path=signing_private_key_path,
        )
    return manifest, envelope


def verify_closure_snapshot(
    *,
    snapshot_path: Path,
    repo_root: Optional[Path] = None,
    dsse_path: Optional[Path] = None,
    public_key_path: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> ClosureSnapshotVerification:
    repo_root = (repo_root or Path.cwd()).resolve()
    snapshot_path = snapshot_path.resolve()
    manifest = ClosureSnapshotManifest.model_validate(_load_json(snapshot_path))

    digest_mismatches: list[str] = []
    missing_artifact_paths: list[str] = []
    verified_subject_count = 0

    for subject in manifest.subjects:
        resolved = _resolve_existing_path(subject.path, repo_root=repo_root, preferred_parent=snapshot_path.parent)
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
            envelope = DsseEnvelope.model_validate(_load_json(dsse_path.resolve()))
            _verify_dsse_envelope(envelope=envelope, expected_payload=manifest_bytes, public_key_path=public_key_path.resolve(), expected_payload_type=_CLOSURE_SNAPSHOT_PAYLOAD_TYPE)
            signature_verified = True
    else:
        notes.append("closure snapshot is unsigned or signature verification was skipped")

    status = "VERIFIED"
    if manifest.integrity_status == "INCOMPLETE" or missing_artifact_paths:
        status = "INCOMPLETE"
    elif not artifact_digests_verified or (dsse_path is not None and not signature_verified):
        status = "UNVERIFIED"
    elif dsse_path is None:
        status = "UNVERIFIED"

    return ClosureSnapshotVerification(
        verified_at_utc=now_utc or _utc_now(),
        manifest_path=_normalize_path(snapshot_path.relative_to(repo_root) if snapshot_path.is_relative_to(repo_root) else snapshot_path),
        status=status,
        verified_subject_count=verified_subject_count,
        artifact_digests_verified=artifact_digests_verified,
        signature_verified=signature_verified,
        digest_mismatches=digest_mismatches,
        missing_artifact_paths=missing_artifact_paths,
        notes=notes,
    )

