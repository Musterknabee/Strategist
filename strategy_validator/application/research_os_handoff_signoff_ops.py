"""Research OS handoff verification and reviewer signoff operations.

This module is intentionally offline/read-plane-only. It verifies local handoff
evidence, records reviewer signoff artifacts, and never performs network calls,
broker calls, ledger writes, deployment approval, or profitability certification.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_handoff_ops import research_os_handoff_latest_path
from strategy_validator.application.research_os_paths import artifact_root_directory
from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner
from strategy_validator.contracts.research_os_handoff_signoff import (
    ResearchOsHandoffDigestCheckStatus,
    ResearchOsHandoffReviewerDecision,
    ResearchOsHandoffReviewerSignoff,
    ResearchOsHandoffSourceDigestCheck,
    ResearchOsHandoffVerificationResult,
    ResearchOsHandoffVerificationStatus,
)

_SCHEMA = "ui_research_os_handoff_signoff/v1"

_SECRET_MARKERS = (
    "STRATEGY_VALIDATOR_API_TOKEN",
    "ALPACA_API_SECRET",
    "ALPACA_SECRET_KEY",
    "POLYGON_API_KEY",
    "TIINGO_API_KEY",
    "TWELVE_DATA_API_KEY",
    "PRIVATE_KEY",
    "BEARER ",
)


def _artifact_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    if artifact_root is not None:
        return artifact_root.expanduser().resolve()
    return artifact_root_directory(repo_root)


def research_os_handoff_signoff_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (_artifact_root(repo_root, artifact_root) / "research_os_handoff_signoff").resolve()


def research_os_handoff_verification_latest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (research_os_handoff_signoff_root(repo_root, artifact_root) / "latest" / "research_os_handoff_verification_result.json").resolve()


def research_os_handoff_reviewer_signoff_latest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (research_os_handoff_signoff_root(repo_root, artifact_root) / "latest" / "research_os_handoff_reviewer_signoff.json").resolve()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _contains_secret_marker(path: Path) -> bool:
    try:
        if not path.is_file() or path.stat().st_size > 5_000_000:
            return False
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    upper = text.upper()
    return any(marker.upper() in upper for marker in _SECRET_MARKERS)


def _list(raw: dict[str, Any] | None, key: str, limit: int = 80) -> list[str]:
    value = raw.get(key) if isinstance(raw, dict) else []
    if not isinstance(value, list):
        return []
    rows = [str(x) for x in value if x is not None]
    if len(rows) > limit:
        return rows[:limit] + [f"{key.upper()}_TRUNCATED:{len(rows)}"]
    return rows


def _observed_handoff_spine(raw: dict[str, Any]) -> str:
    spine = {
        "handoff_id": raw.get("handoff_id"),
        "status": raw.get("status"),
        "decision": raw.get("decision"),
        "source_release_readiness_decision": raw.get("source_release_readiness_decision"),
        "source_policy_gate_decision": raw.get("source_policy_gate_decision"),
        "source_exception_status": raw.get("source_exception_status"),
        "checklist": [
            {
                "item_id": c.get("item_id"),
                "status": c.get("status"),
                "blockers": c.get("blockers", []),
                "warnings": c.get("warnings", []),
            }
            for c in raw.get("checklist", [])
            if isinstance(c, dict)
        ],
        "source_refs": [
            {
                "label": r.get("label"),
                "present": r.get("present"),
                "manifest_sha256": r.get("manifest_sha256"),
                "status_hint": r.get("status_hint"),
                "decision_hint": r.get("decision_hint"),
            }
            for r in raw.get("source_refs", [])
            if isinstance(r, dict)
        ],
    }
    return _canonical_sha256(spine)


def _observed_manifest_sha(raw: dict[str, Any]) -> str:
    payload = dict(raw)
    payload.pop("manifest_sha256", None)
    return _canonical_sha256(payload)


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


def _with_signoff_digest(signoff: ResearchOsHandoffReviewerSignoff) -> ResearchOsHandoffReviewerSignoff:
    payload = signoff.model_dump(mode="json", exclude={"signoff_spine_sha256", "manifest_sha256"})
    spine = {
        "signoff_id": payload.get("signoff_id"),
        "reviewer_id": payload.get("reviewer_id"),
        "decision": payload.get("decision"),
        "source_verification_id": payload.get("source_verification_id"),
        "source_verification_status": payload.get("source_verification_status"),
        "source_handoff_id": payload.get("source_handoff_id"),
        "source_handoff_decision": payload.get("source_handoff_decision"),
        "constraints": payload.get("constraints", []),
        "required_followups": payload.get("required_followups", []),
        "blockers": payload.get("blockers", []),
    }
    payload["signoff_spine_sha256"] = _canonical_sha256(spine)
    payload["manifest_sha256"] = _canonical_sha256(payload)
    return ResearchOsHandoffReviewerSignoff.model_validate(payload)


def build_research_os_handoff_reviewer_signoff(
    *,
    signoff_id: str = "research-os-handoff-reviewer-signoff",
    reviewer_id: str = "local-reviewer",
    decision: ResearchOsHandoffReviewerDecision = ResearchOsHandoffReviewerDecision.ACCEPTED_WITH_RESTRICTIONS,
    rationale: str = "Single-tenant handoff evidence reviewed; not deployment approval.",
    constraints: list[str] | None = None,
    artifact_root: Path | None = None,
    repo_root: Path | None = None,
) -> ResearchOsHandoffReviewerSignoff:
    root = _artifact_root(repo_root, artifact_root)
    verification = load_latest_research_os_handoff_verification_result(repo_root=repo_root, artifact_root=root)
    warnings: list[str] = []
    blockers: list[str] = []
    required_followups: list[str] = []
    constraints_out = list(constraints or [])

    if verification is None:
        final_decision = ResearchOsHandoffReviewerDecision.BLOCKED
        trust = ResearchOsTrustBanner.UNTRUSTED
        blockers.append("NO_HANDOFF_VERIFICATION_RESULT")
        source_status = None
        source_handoff_id = None
        source_handoff_decision = None
        source_verification_id = None
    else:
        source_status = verification.status.value
        source_handoff_id = verification.source_handoff_id
        source_handoff_decision = verification.source_handoff_decision
        source_verification_id = verification.verification_id
        warnings.extend(verification.warnings)
        blockers.extend(verification.blockers)
        if verification.status in {ResearchOsHandoffVerificationStatus.TAMPERED, ResearchOsHandoffVerificationStatus.MISSING, ResearchOsHandoffVerificationStatus.BLOCKED}:
            final_decision = ResearchOsHandoffReviewerDecision.BLOCKED
            trust = ResearchOsTrustBanner.UNTRUSTED
            blockers.append(f"HANDOFF_VERIFICATION_{verification.status.value}")
        elif decision == ResearchOsHandoffReviewerDecision.REJECTED:
            final_decision = ResearchOsHandoffReviewerDecision.REJECTED
            trust = ResearchOsTrustBanner.TRUST_RESTRICTED
            required_followups.append("Reviewer rejected handoff; rebuild evidence and review rationale.")
        elif verification.status == ResearchOsHandoffVerificationStatus.STALE:
            final_decision = ResearchOsHandoffReviewerDecision.ACCEPTED_WITH_RESTRICTIONS
            trust = ResearchOsTrustBanner.TRUST_RESTRICTED
            constraints_out.append("Handoff verification is STALE/RESTRICTED; use for review only and refresh before deployment evidence.")
        elif source_handoff_decision == "SINGLE_TENANT_HANDOFF_READY" and decision == ResearchOsHandoffReviewerDecision.ACKNOWLEDGED:
            final_decision = ResearchOsHandoffReviewerDecision.ACKNOWLEDGED
            trust = ResearchOsTrustBanner.TRUSTED
        else:
            final_decision = ResearchOsHandoffReviewerDecision.ACCEPTED_WITH_RESTRICTIONS
            trust = ResearchOsTrustBanner.TRUST_RESTRICTED
            constraints_out.append("Reviewer signoff is restricted to single-tenant release review; it is not deployment approval.")

    constraints_out.extend([
        "No live trading.",
        "No broker orders.",
        "No browser order controls.",
        "DEPLOYMENT_APPROVED remains false and unchanged.",
    ])
    if blockers:
        required_followups.append("Resolve handoff verification blockers before handoff signoff can be used for review.")
    elif warnings:
        required_followups.append("Resolve or explicitly carry remaining handoff verification warnings before deployment evidence review.")

    signoff = ResearchOsHandoffReviewerSignoff(
        signoff_id=signoff_id,
        signed_at_utc=datetime.now(timezone.utc),
        artifact_root=str(root),
        reviewer_id=reviewer_id,
        decision=final_decision,
        trust_banner=trust,
        source_verification_id=source_verification_id,
        source_verification_status=source_status,
        source_handoff_id=source_handoff_id,
        source_handoff_decision=source_handoff_decision,
        rationale=rationale,
        constraints=sorted(set(str(x) for x in constraints_out if x))[:80],
        required_followups=sorted(set(str(x) for x in required_followups if x))[:80],
        warnings=sorted(set(str(x) for x in warnings if x))[:120],
        blockers=sorted(set(str(x) for x in blockers if x))[:120],
    )
    return _with_signoff_digest(signoff)


def write_research_os_handoff_reviewer_signoff(
    signoff: ResearchOsHandoffReviewerSignoff,
    *,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    overwrite: bool = False,
) -> Path:
    root = research_os_handoff_signoff_root(repo_root, artifact_root)
    path = root / "signoffs" / signoff.signoff_id / "research_os_handoff_reviewer_signoff.json"
    if path.exists() and not overwrite:
        raise FileExistsError(f"handoff reviewer signoff already exists: {path}")
    payload = signoff.model_dump(mode="json")
    _write_json(path, payload)
    latest = root / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    _write_json(latest / "research_os_handoff_reviewer_signoff.json", payload)
    _write_json(latest / "latest_signoff_ref.json", {"signoff_id": signoff.signoff_id, "signoff_path": str(path), "manifest_sha256": signoff.manifest_sha256})
    return path


def build_and_write_research_os_handoff_reviewer_signoff(
    *,
    signoff_id: str = "research-os-handoff-reviewer-signoff",
    reviewer_id: str = "local-reviewer",
    decision: ResearchOsHandoffReviewerDecision = ResearchOsHandoffReviewerDecision.ACCEPTED_WITH_RESTRICTIONS,
    rationale: str = "Single-tenant handoff evidence reviewed; not deployment approval.",
    constraints: list[str] | None = None,
    artifact_root: Path | None = None,
    repo_root: Path | None = None,
    overwrite: bool = False,
) -> tuple[ResearchOsHandoffReviewerSignoff, Path]:
    signoff = build_research_os_handoff_reviewer_signoff(
        signoff_id=signoff_id,
        reviewer_id=reviewer_id,
        decision=decision,
        rationale=rationale,
        constraints=constraints,
        artifact_root=artifact_root,
        repo_root=repo_root,
    )
    path = write_research_os_handoff_reviewer_signoff(signoff, repo_root=repo_root, artifact_root=artifact_root, overwrite=overwrite)
    return signoff, path


def load_latest_research_os_handoff_reviewer_signoff(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> ResearchOsHandoffReviewerSignoff | None:
    raw = _read_json(research_os_handoff_reviewer_signoff_latest_path(repo_root, artifact_root))
    if raw is None:
        return None
    try:
        return ResearchOsHandoffReviewerSignoff.model_validate(raw)
    except Exception:
        return None


def build_ui_research_os_handoff_signoff_latest_payload(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> dict[str, Any]:
    verification_path = research_os_handoff_verification_latest_path(repo_root, artifact_root)
    signoff_path = research_os_handoff_reviewer_signoff_latest_path(repo_root, artifact_root)
    verification = load_latest_research_os_handoff_verification_result(repo_root=repo_root, artifact_root=artifact_root)
    signoff = load_latest_research_os_handoff_reviewer_signoff(repo_root=repo_root, artifact_root=artifact_root)
    degraded: list[str] = []
    if verification is None:
        degraded.append("NO_RESEARCH_OS_HANDOFF_VERIFICATION_RESULT")
    elif verification.status != ResearchOsHandoffVerificationStatus.VERIFIED:
        degraded.append(f"HANDOFF_VERIFICATION_{verification.status.value}")
    if signoff is None:
        degraded.append("NO_RESEARCH_OS_HANDOFF_REVIEWER_SIGNOFF")
    elif signoff.decision in {ResearchOsHandoffReviewerDecision.BLOCKED, ResearchOsHandoffReviewerDecision.REJECTED}:
        degraded.append(f"HANDOFF_SIGNOFF_{signoff.decision.value}")
    return {
        "schema_version": _SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PRESENT" if verification is not None or signoff is not None else "MISSING",
        "degraded": degraded,
        "verification_path": str(verification_path),
        "signoff_path": str(signoff_path),
        "latest_verification": verification.model_dump(mode="json") if verification is not None else None,
        "latest_signoff": signoff.model_dump(mode="json") if signoff is not None else None,
        "read_plane_only": True,
        "no_live_trading": True,
        "no_broker_orders": True,
        "no_order_controls": True,
    }


__all__ = [
    "build_and_write_research_os_handoff_reviewer_signoff",
    "build_and_write_research_os_handoff_verification_result",
    "build_research_os_handoff_reviewer_signoff",
    "build_research_os_handoff_verification_result",
    "build_ui_research_os_handoff_signoff_latest_payload",
    "load_latest_research_os_handoff_reviewer_signoff",
    "load_latest_research_os_handoff_verification_result",
    "research_os_handoff_reviewer_signoff_latest_path",
    "research_os_handoff_signoff_root",
    "research_os_handoff_verification_latest_path",
    "write_research_os_handoff_reviewer_signoff",
    "write_research_os_handoff_verification_result",
]
