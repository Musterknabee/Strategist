"""Verification result operations for Research OS handoff signoff."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_handoff_ops import research_os_handoff_latest_path
from strategy_validator.application.research_os_handoff_signoff_common import (
    _artifact_root,
    _canonical_sha256,
    _contains_secret_marker,
    _observed_handoff_spine,
    _observed_manifest_sha,
    _read_json,
    _sha256_file,
    _write_json,
    research_os_handoff_signoff_root,
    research_os_handoff_verification_latest_path,
)
from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner
from strategy_validator.contracts.research_os_handoff_signoff import (
    ResearchOsHandoffDigestCheckStatus,
    ResearchOsHandoffSourceDigestCheck,
    ResearchOsHandoffVerificationResult,
    ResearchOsHandoffVerificationStatus,
)


def _source_check(ref: dict[str, Any], *, artifact_root: Path) -> ResearchOsHandoffSourceDigestCheck:
    label = str(ref.get("label") or "unknown")
    raw_path = str(ref.get("artifact_path") or "")
    expected = str(ref.get("manifest_sha256")) if ref.get("manifest_sha256") is not None else None
    warnings: list[str] = []
    blockers: list[str] = []

    if not raw_path:
        warnings.append("NO_ARTIFACT_PATH_IN_SOURCE_REF")
        return ResearchOsHandoffSourceDigestCheck(
            label=label,
            artifact_path="",
            present=False,
            status=ResearchOsHandoffDigestCheckStatus.NOT_APPLICABLE,
            expected_manifest_sha256=expected,
            warnings=warnings,
        )

    path = Path(raw_path)
    if not path.is_absolute():
        path = (artifact_root / path).resolve()
    if not path.exists():
        blockers.append("SOURCE_ARTIFACT_MISSING")
        return ResearchOsHandoffSourceDigestCheck(
            label=label,
            artifact_path=str(path),
            present=False,
            status=ResearchOsHandoffDigestCheckStatus.MISSING,
            expected_manifest_sha256=expected,
            blockers=blockers,
        )

    file_sha = _sha256_file(path)
    if _contains_secret_marker(path):
        blockers.append("SECRET_MARKER_PRESENT")

    raw = _read_json(path)
    if raw is None:
        blockers.append("SOURCE_ARTIFACT_UNREADABLE_JSON")
        return ResearchOsHandoffSourceDigestCheck(
            label=label,
            artifact_path=str(path),
            present=True,
            status=ResearchOsHandoffDigestCheckStatus.UNREADABLE,
            expected_manifest_sha256=expected,
            observed_file_sha256=file_sha,
            blockers=blockers,
        )

    observed = str(raw.get("manifest_sha256")) if raw.get("manifest_sha256") is not None else None
    if expected is None:
        warnings.append("NO_EXPECTED_SOURCE_MANIFEST_SHA256")
        status = ResearchOsHandoffDigestCheckStatus.NO_EXPECTED_DIGEST
    elif observed != expected:
        blockers.append("SOURCE_MANIFEST_SHA256_MISMATCH")
        status = ResearchOsHandoffDigestCheckStatus.MISMATCH
    else:
        status = ResearchOsHandoffDigestCheckStatus.MATCH

    return ResearchOsHandoffSourceDigestCheck(
        label=label,
        artifact_path=str(path),
        present=True,
        status=status,
        expected_manifest_sha256=expected,
        observed_manifest_sha256=observed,
        observed_file_sha256=file_sha,
        warnings=warnings,
        blockers=blockers,
        metadata={
            "schema_version_observed": raw.get("schema_version"),
            "status_hint": raw.get("status"),
            "decision_hint": raw.get("decision"),
        },
    )

def _with_verification_digest(result: ResearchOsHandoffVerificationResult) -> ResearchOsHandoffVerificationResult:
    payload = result.model_dump(mode="json", exclude={"verification_spine_sha256", "result_sha256"})
    spine = {
        "verification_id": payload.get("verification_id"),
        "status": payload.get("status"),
        "source_handoff_id": payload.get("source_handoff_id"),
        "source_handoff_decision": payload.get("source_handoff_decision"),
        "expected_handoff_manifest_sha256": payload.get("expected_handoff_manifest_sha256"),
        "observed_handoff_manifest_sha256": payload.get("observed_handoff_manifest_sha256"),
        "expected_handoff_spine_sha256": payload.get("expected_handoff_spine_sha256"),
        "observed_handoff_spine_sha256": payload.get("observed_handoff_spine_sha256"),
        "source_digest_checks": [
            {
                "label": c.get("label"),
                "status": c.get("status"),
                "expected_manifest_sha256": c.get("expected_manifest_sha256"),
                "observed_manifest_sha256": c.get("observed_manifest_sha256"),
            }
            for c in payload.get("source_digest_checks", [])
        ],
    }
    payload["verification_spine_sha256"] = _canonical_sha256(spine)
    payload["result_sha256"] = _canonical_sha256(payload)
    return ResearchOsHandoffVerificationResult.model_validate(payload)

def build_research_os_handoff_verification_result(
    *,
    verification_id: str = "research-os-handoff-verification",
    artifact_root: Path | None = None,
    repo_root: Path | None = None,
) -> ResearchOsHandoffVerificationResult:
    root = _artifact_root(repo_root, artifact_root)
    handoff_path = research_os_handoff_latest_path(repo_root=repo_root, artifact_root=root)
    raw = _read_json(handoff_path)
    warnings: list[str] = []
    blockers: list[str] = []
    checks: list[ResearchOsHandoffSourceDigestCheck] = []

    if raw is None:
        result = ResearchOsHandoffVerificationResult(
            verification_id=verification_id,
            artifact_root=str(root),
            status=ResearchOsHandoffVerificationStatus.MISSING,
            trust_banner=ResearchOsTrustBanner.UNTRUSTED,
            handoff_manifest_path=str(handoff_path),
            warnings=["NO_RESEARCH_OS_HANDOFF_PACK"],
            blockers=["NO_RESEARCH_OS_HANDOFF_PACK"],
        )
        return _with_verification_digest(result)

    if _contains_secret_marker(handoff_path):
        blockers.append("HANDOFF_PACK_SECRET_MARKER_PRESENT")

    expected_manifest = str(raw.get("manifest_sha256")) if raw.get("manifest_sha256") is not None else None
    observed_manifest = _observed_manifest_sha(raw)
    if expected_manifest is None:
        blockers.append("HANDOFF_PACK_MISSING_MANIFEST_SHA256")
    elif observed_manifest != expected_manifest:
        blockers.append("HANDOFF_PACK_MANIFEST_SHA256_MISMATCH")

    expected_spine = str(raw.get("handoff_spine_sha256")) if raw.get("handoff_spine_sha256") is not None else None
    observed_spine = _observed_handoff_spine(raw)
    if expected_spine is None:
        warnings.append("HANDOFF_PACK_MISSING_SPINE_SHA256")
    elif observed_spine != expected_spine:
        blockers.append("HANDOFF_PACK_SPINE_SHA256_MISMATCH")

    refs = raw.get("source_refs") if isinstance(raw.get("source_refs"), list) else []
    for ref in refs:
        if isinstance(ref, dict):
            checks.append(_source_check(ref, artifact_root=root))

    for check in checks:
        warnings.extend(f"{check.label}:{w}" for w in check.warnings)
        blockers.extend(f"{check.label}:{b}" for b in check.blockers)

    for flag in ("read_plane_only", "no_live_trading", "no_broker_orders", "no_order_controls", "no_profitability_claim", "deployment_approval_unchanged"):
        if raw.get(flag) is False:
            blockers.append(f"HANDOFF_PACK_{flag}=false")
    if raw.get("deployment_approved") is True:
        blockers.append("HANDOFF_PACK_deployment_approved=true")

    match_count = sum(1 for c in checks if c.status == ResearchOsHandoffDigestCheckStatus.MATCH)
    mismatch_count = sum(1 for c in checks if c.status == ResearchOsHandoffDigestCheckStatus.MISMATCH)
    missing_count = sum(1 for c in checks if c.status in {ResearchOsHandoffDigestCheckStatus.MISSING, ResearchOsHandoffDigestCheckStatus.UNREADABLE})
    unchecked_count = sum(1 for c in checks if c.status in {ResearchOsHandoffDigestCheckStatus.NO_EXPECTED_DIGEST, ResearchOsHandoffDigestCheckStatus.NOT_APPLICABLE})

    source_decision = str(raw.get("decision")) if raw.get("decision") is not None else None
    source_status = str(raw.get("status")) if raw.get("status") is not None else None
    if blockers:
        if any("MISMATCH" in b or "SECRET" in b or "false" in b or "deployment_approved" in b for b in blockers):
            status = ResearchOsHandoffVerificationStatus.TAMPERED
        else:
            status = ResearchOsHandoffVerificationStatus.BLOCKED
        trust = ResearchOsTrustBanner.UNTRUSTED
        verified = False
    elif warnings or source_status in {"RESTRICTED", "NOT_READY"} or source_decision == "HANDOFF_WITH_RESTRICTIONS":
        status = ResearchOsHandoffVerificationStatus.STALE if warnings else ResearchOsHandoffVerificationStatus.VERIFIED
        trust = ResearchOsTrustBanner.TRUST_RESTRICTED
        verified = status == ResearchOsHandoffVerificationStatus.VERIFIED
    else:
        status = ResearchOsHandoffVerificationStatus.VERIFIED
        trust = ResearchOsTrustBanner.TRUSTED
        verified = True

    result = ResearchOsHandoffVerificationResult(
        verification_id=verification_id,
        verified_at_utc=datetime.now(timezone.utc),
        artifact_root=str(root),
        status=status,
        trust_banner=trust,
        handoff_verified=verified,
        source_handoff_id=str(raw.get("handoff_id")) if raw.get("handoff_id") is not None else None,
        source_handoff_status=source_status,
        source_handoff_decision=source_decision,
        handoff_manifest_path=str(handoff_path),
        expected_handoff_manifest_sha256=expected_manifest,
        observed_handoff_manifest_sha256=observed_manifest,
        expected_handoff_spine_sha256=expected_spine,
        observed_handoff_spine_sha256=observed_spine,
        source_digest_checks=checks,
        match_count=match_count,
        mismatch_count=mismatch_count,
        missing_count=missing_count,
        unchecked_count=unchecked_count,
        warnings=sorted(set(warnings))[:120],
        blockers=sorted(set(blockers))[:120],
    )
    return _with_verification_digest(result)

def write_research_os_handoff_verification_result(
    result: ResearchOsHandoffVerificationResult,
    *,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    overwrite: bool = False,
) -> Path:
    root = research_os_handoff_signoff_root(repo_root, artifact_root)
    path = root / "verifications" / result.verification_id / "research_os_handoff_verification_result.json"
    if path.exists() and not overwrite:
        raise FileExistsError(f"handoff verification already exists: {path}")
    payload = result.model_dump(mode="json")
    _write_json(path, payload)
    latest = root / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    _write_json(latest / "research_os_handoff_verification_result.json", payload)
    _write_json(latest / "latest_verification_ref.json", {"verification_id": result.verification_id, "result_path": str(path), "result_sha256": result.result_sha256})
    return path

def build_and_write_research_os_handoff_verification_result(
    *,
    verification_id: str = "research-os-handoff-verification",
    artifact_root: Path | None = None,
    repo_root: Path | None = None,
    overwrite: bool = False,
) -> tuple[ResearchOsHandoffVerificationResult, Path]:
    result = build_research_os_handoff_verification_result(verification_id=verification_id, artifact_root=artifact_root, repo_root=repo_root)
    path = write_research_os_handoff_verification_result(result, repo_root=repo_root, artifact_root=artifact_root, overwrite=overwrite)
    return result, path

def load_latest_research_os_handoff_verification_result(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> ResearchOsHandoffVerificationResult | None:
    raw = _read_json(research_os_handoff_verification_latest_path(repo_root, artifact_root))
    if raw is None:
        return None
    try:
        return ResearchOsHandoffVerificationResult.model_validate(raw)
    except Exception:
        return None

__all__ = [
    "_source_check",
    "_with_verification_digest",
    "build_and_write_research_os_handoff_verification_result",
    "build_research_os_handoff_verification_result",
    "load_latest_research_os_handoff_verification_result",
    "write_research_os_handoff_verification_result",
]
