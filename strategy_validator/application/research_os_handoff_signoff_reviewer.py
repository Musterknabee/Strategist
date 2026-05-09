"""Reviewer signoff operations for verified Research OS handoff packs."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.research_os_handoff_signoff_common import (
    _artifact_root,
    _canonical_sha256,
    _read_json,
    _write_json,
    research_os_handoff_reviewer_signoff_latest_path,
    research_os_handoff_signoff_root,
)
from strategy_validator.application.research_os_handoff_signoff_verification import load_latest_research_os_handoff_verification_result
from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner
from strategy_validator.contracts.research_os_handoff_signoff import (
    ResearchOsHandoffReviewerDecision,
    ResearchOsHandoffReviewerSignoff,
    ResearchOsHandoffVerificationStatus,
)


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

__all__ = [
    "_with_signoff_digest",
    "build_and_write_research_os_handoff_reviewer_signoff",
    "build_research_os_handoff_reviewer_signoff",
    "load_latest_research_os_handoff_reviewer_signoff",
    "write_research_os_handoff_reviewer_signoff",
]
