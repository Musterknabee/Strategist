"""Research OS closure verification and operator attestation operations.

This module verifies digest-linked Research OS closure evidence and writes
operator attestation artifacts. It is deliberately evidence/read-plane only:
no live trading, no broker orders, no ledger writes, and no network access.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_paths import artifact_root_directory
from strategy_validator.contracts.research_os_attestation import (
    ResearchOsClosureDigestCheck,
    ResearchOsClosureVerificationResult,
    ResearchOsClosureVerificationStatus,
    ResearchOsOperatorAttestation,
    ResearchOsOperatorDecision,
)
from strategy_validator.contracts.research_os_closure import ResearchOsClosureManifest, ResearchOsTrustBanner
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

_SCHEMA = "ui_research_os_attestation/v1"

_SECRET_MARKERS = (
    "STRATEGY_VALIDATOR_API_TOKEN",
    "ALPACA_API_SECRET",
    "ALPACA_SECRET_KEY",
    "POLYGON_API_KEY",
    "TIINGO_API_KEY",
    "TWELVE_DATA_API_KEY",
    "SECRET_KEY",
    "PRIVATE_KEY",
    "BEARER ",
)


def _artifact_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    if artifact_root is not None:
        return artifact_root.expanduser().resolve()
    return artifact_root_directory(repo_root)


def research_os_attestation_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (_artifact_root(repo_root, artifact_root) / "research_os_attestation").resolve()


def research_os_verification_latest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (research_os_attestation_root(repo_root, artifact_root) / "latest" / "closure_verification_result.json").resolve()


def research_os_operator_attestation_latest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (research_os_attestation_root(repo_root, artifact_root) / "latest" / "operator_attestation.json").resolve()




def research_os_closure_latest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (_artifact_root(repo_root, artifact_root) / "research_os_closure" / "latest" / "research_os_closure_manifest.json").resolve()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _manifest_sha(raw: dict[str, Any]) -> str:
    body = {k: v for k, v in raw.items() if k != "manifest_sha256"}
    return canonical_json_sha256(body)


def _result_with_digest(result: ResearchOsClosureVerificationResult) -> ResearchOsClosureVerificationResult:
    body = result.model_dump(mode="json", exclude={"result_sha256"})
    return result.model_copy(update={"result_sha256": canonical_json_sha256(body)})


def _attestation_with_digest(attestation: ResearchOsOperatorAttestation) -> ResearchOsOperatorAttestation:
    body = attestation.model_dump(mode="json", exclude={"attestation_sha256"})
    return attestation.model_copy(update={"attestation_sha256": canonical_json_sha256(body)})


def _artifact_check(raw_ref: dict[str, Any]) -> ResearchOsClosureDigestCheck:
    kind = str(raw_ref.get("artifact_kind") or "unknown")
    path = Path(str(raw_ref.get("artifact_path") or ""))
    expected = raw_ref.get("file_sha256") if isinstance(raw_ref.get("file_sha256"), str) else None
    exists_now = path.is_file()
    readable_now = False
    observed: str | None = None
    warnings: list[str] = []
    blockers: list[str] = []
    match: bool | None = None
    if not exists_now:
        if expected:
            blockers.append("ARTIFACT_MISSING_AFTER_CLOSURE")
        else:
            warnings.append("ARTIFACT_STILL_MISSING")
        match = None if not expected else False
    else:
        try:
            observed = _sha256_file(path)
        except OSError:
            blockers.append("ARTIFACT_UNREADABLE_AFTER_CLOSURE")
        raw = _read_json(path)
        readable_now = raw is not None
        if raw is None:
            blockers.append("ARTIFACT_JSON_UNREADABLE_AFTER_CLOSURE")
        else:
            body = json.dumps(raw, sort_keys=True)
            for marker in _SECRET_MARKERS:
                if marker in body:
                    blockers.append(f"SECRET_MARKER_PRESENT:{marker}")
        if expected and observed:
            match = expected == observed
            if not match:
                blockers.append("ARTIFACT_DIGEST_MISMATCH_AFTER_CLOSURE")
        elif observed and not expected:
            warnings.append("ARTIFACT_NOW_PRESENT_BUT_WAS_NOT_DIGESTED")
            match = None
    return ResearchOsClosureDigestCheck(
        artifact_kind=kind,
        artifact_path=str(path),
        expected_sha256=expected,
        observed_sha256=observed,
        exists_now=exists_now,
        readable_now=readable_now,
        match=match,
        warnings=warnings,
        blockers=blockers,
    )


def verify_research_os_closure_manifest(
    *,
    verification_id: str = "research-os-closure-verification",
    manifest_path: Path | None = None,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
) -> ResearchOsClosureVerificationResult:
    """Verify latest or provided Research OS closure manifest against current files."""
    path = (manifest_path.expanduser().resolve() if manifest_path is not None else research_os_closure_latest_path(repo_root, artifact_root))
    raw = _read_json(path)
    if raw is None:
        result = ResearchOsClosureVerificationResult(
            verification_id=verification_id,
            manifest_path=str(path),
            status=ResearchOsClosureVerificationStatus.MISSING,
            trust_banner=ResearchOsTrustBanner.UNTRUSTED,
            warnings=[],
            blockers=["NO_READABLE_RESEARCH_OS_CLOSURE_MANIFEST"],
        )
        return _result_with_digest(result)

    warnings: list[str] = []
    blockers: list[str] = []
    checks: list[ResearchOsClosureDigestCheck] = []
    digest_mismatches: list[str] = []
    missing_artifacts: list[str] = []
    unreadable_artifacts: list[str] = []

    try:
        manifest = ResearchOsClosureManifest.model_validate(raw)
    except Exception as exc:
        result = ResearchOsClosureVerificationResult(
            verification_id=verification_id,
            manifest_path=str(path),
            status=ResearchOsClosureVerificationStatus.BLOCKED,
            trust_banner=ResearchOsTrustBanner.UNTRUSTED,
            warnings=[],
            blockers=[f"INVALID_CLOSURE_MANIFEST:{type(exc).__name__}"],
        )
        return _result_with_digest(result)

    expected_manifest_sha = raw.get("manifest_sha256") if isinstance(raw.get("manifest_sha256"), str) else None
    observed_manifest_sha = _manifest_sha(raw)
    if expected_manifest_sha != observed_manifest_sha:
        blockers.append("CLOSURE_MANIFEST_DIGEST_MISMATCH")

    body = json.dumps(raw, sort_keys=True)
    for marker in _SECRET_MARKERS:
        if marker in body:
            blockers.append(f"SECRET_MARKER_PRESENT_IN_CLOSURE:{marker}")

    for ref in raw.get("artifacts") or []:
        if not isinstance(ref, dict):
            blockers.append("INVALID_ARTIFACT_REF")
            continue
        check = _artifact_check(ref)
        checks.append(check)
        if check.expected_sha256 and check.match is False:
            digest_mismatches.append(check.artifact_kind)
        if check.expected_sha256 and not check.exists_now:
            missing_artifacts.append(check.artifact_kind)
        if check.exists_now and not check.readable_now:
            unreadable_artifacts.append(check.artifact_kind)
        warnings.extend(f"{check.artifact_kind}:{w}" for w in check.warnings)
        blockers.extend(f"{check.artifact_kind}:{b}" for b in check.blockers)

    if digest_mismatches:
        blockers.append("ARTIFACT_DIGEST_MISMATCHES_PRESENT")
    if missing_artifacts:
        blockers.append("DIGESTED_ARTIFACTS_MISSING_AFTER_CLOSURE")
    if unreadable_artifacts:
        blockers.append("ARTIFACTS_UNREADABLE_AFTER_CLOSURE")

    if blockers:
        status = ResearchOsClosureVerificationStatus.TAMPERED if digest_mismatches or "CLOSURE_MANIFEST_DIGEST_MISMATCH" in blockers else ResearchOsClosureVerificationStatus.BLOCKED
        banner = ResearchOsTrustBanner.UNTRUSTED
    else:
        status = ResearchOsClosureVerificationStatus.VERIFIED
        banner = manifest.trust_banner

    result = ResearchOsClosureVerificationResult(
        verification_id=verification_id,
        closure_id=manifest.closure_id,
        manifest_path=str(path),
        artifact_root=manifest.artifact_root,
        status=status,
        trust_banner=banner,
        manifest_sha256_expected=expected_manifest_sha,
        manifest_sha256_observed=observed_manifest_sha,
        evidence_spine_sha256_expected=manifest.digests.get("evidence_spine_sha256"),
        artifact_checks=checks,
        digest_mismatches=sorted(set(digest_mismatches)),
        missing_artifacts=sorted(set(missing_artifacts)),
        unreadable_artifacts=sorted(set(unreadable_artifacts)),
        warnings=sorted(set(warnings)),
        blockers=sorted(set(blockers)),
        no_live_trading=manifest.no_live_trading,
        no_broker_orders=manifest.no_broker_orders,
        no_profitability_claim=manifest.no_profitability_claim,
        deployment_approval_unchanged=manifest.deployment_approval_unchanged,
    )
    return _result_with_digest(result)


def write_research_os_closure_verification(
    result: ResearchOsClosureVerificationResult,
    *,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    overwrite: bool = False,
) -> Path:
    root = research_os_attestation_root(repo_root, artifact_root)
    vid = result.verification_id
    vdir = root / "verifications" / vid
    if vdir.exists():
        if not overwrite:
            raise FileExistsError(f"RESEARCH_OS_VERIFICATION_EXISTS:{vid}")
        shutil.rmtree(vdir)
    path = vdir / "closure_verification_result.json"
    _write_json(path, result.model_dump(mode="json"))
    latest = root / "latest"
    _write_json(latest / "closure_verification_result.json", result.model_dump(mode="json"))
    return path.resolve()


def build_operator_attestation(
    *,
    attestation_id: str,
    operator_id: str,
    decision: ResearchOsOperatorDecision | str,
    rationale: str = "",
    constraints: list[str] | None = None,
    verification: ResearchOsClosureVerificationResult | None = None,
    manifest_path: Path | None = None,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
) -> ResearchOsOperatorAttestation:
    verification = verification or verify_research_os_closure_manifest(
        verification_id=f"{attestation_id}-verification",
        manifest_path=manifest_path,
        repo_root=repo_root,
        artifact_root=artifact_root,
    )
    decision_enum = decision if isinstance(decision, ResearchOsOperatorDecision) else ResearchOsOperatorDecision(str(decision))
    blockers = list(verification.blockers)
    warnings = list(verification.warnings)
    if verification.status != ResearchOsClosureVerificationStatus.VERIFIED:
        blockers.append(f"ATTESTATION_BLOCKED_BY_VERIFICATION_STATUS:{verification.status.value}")
        decision_enum = ResearchOsOperatorDecision.BLOCKED
    if verification.trust_banner != ResearchOsTrustBanner.TRUSTED and decision_enum == ResearchOsOperatorDecision.ACKNOWLEDGED:
        warnings.append("ACKNOWLEDGED_RESTRICTED_OR_UNTRUSTED_CLOSURE")
    att = ResearchOsOperatorAttestation(
        attestation_id=attestation_id,
        closure_id=verification.closure_id or "UNKNOWN_CLOSURE",
        operator_id=operator_id,
        decision=decision_enum,
        rationale=rationale,
        constraints=list(constraints or []),
        verification_status=verification.status,
        closure_trust_banner=verification.trust_banner,
        closure_manifest_sha256=verification.manifest_sha256_expected,
        verification_result_sha256=verification.result_sha256,
        warnings=sorted(set(warnings)),
        blockers=sorted(set(blockers)),
        no_live_trading=verification.no_live_trading,
        no_broker_orders=verification.no_broker_orders,
        no_profitability_claim=verification.no_profitability_claim,
        deployment_approval_unchanged=verification.deployment_approval_unchanged,
    )
    return _attestation_with_digest(att)


def write_operator_attestation(
    attestation: ResearchOsOperatorAttestation,
    *,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    overwrite: bool = False,
) -> Path:
    root = research_os_attestation_root(repo_root, artifact_root)
    adir = root / "attestations" / attestation.attestation_id
    if adir.exists():
        if not overwrite:
            raise FileExistsError(f"RESEARCH_OS_ATTESTATION_EXISTS:{attestation.attestation_id}")
        shutil.rmtree(adir)
    path = adir / "operator_attestation.json"
    _write_json(path, attestation.model_dump(mode="json"))
    latest = root / "latest"
    _write_json(latest / "operator_attestation.json", attestation.model_dump(mode="json"))
    return path.resolve()


def load_latest_verification(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> ResearchOsClosureVerificationResult | None:
    raw = _read_json(research_os_verification_latest_path(repo_root, artifact_root))
    if raw is None:
        return None
    return ResearchOsClosureVerificationResult.model_validate(raw)


def load_latest_attestation(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> ResearchOsOperatorAttestation | None:
    raw = _read_json(research_os_operator_attestation_latest_path(repo_root, artifact_root))
    if raw is None:
        return None
    return ResearchOsOperatorAttestation.model_validate(raw)


def build_ui_research_os_attestation_latest_payload(*, repo_root: Path | None = None) -> dict[str, Any]:
    verification = load_latest_verification(repo_root=repo_root)
    attestation = load_latest_attestation(repo_root=repo_root)
    degraded: list[str] = []
    if verification is None:
        degraded.append("NO_CLOSURE_VERIFICATION_RESULT")
    elif verification.status != ResearchOsClosureVerificationStatus.VERIFIED:
        degraded.append(f"VERIFICATION_{verification.status.value}")
    if attestation is None:
        degraded.append("NO_OPERATOR_ATTESTATION")
    elif attestation.decision in {ResearchOsOperatorDecision.REJECTED, ResearchOsOperatorDecision.BLOCKED}:
        degraded.append(f"ATTESTATION_{attestation.decision.value}")
    return {
        "schema_version": _SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_plane_only": True,
        "no_live_trading": True,
        "no_broker_orders": True,
        "no_order_controls": True,
        "status": "PRESENT" if verification or attestation else "NOT_PRESENT",
        "verification_artifact_path": str(research_os_verification_latest_path(repo_root)),
        "attestation_artifact_path": str(research_os_operator_attestation_latest_path(repo_root)),
        "latest_verification": verification.model_dump(mode="json") if verification else None,
        "latest_attestation": attestation.model_dump(mode="json") if attestation else None,
        "degraded": sorted(set(degraded)),
    }


__all__ = [
    "build_operator_attestation",
    "build_ui_research_os_attestation_latest_payload",
    "load_latest_attestation",
    "load_latest_verification",
    "research_os_attestation_root",
    "research_os_operator_attestation_latest_path",
    "research_os_verification_latest_path",
    "verify_research_os_closure_manifest",
    "write_operator_attestation",
    "write_research_os_closure_verification",
]
