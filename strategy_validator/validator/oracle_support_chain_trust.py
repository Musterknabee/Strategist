"""Advisory support-chain trust assessment (read-only; no ledger mutation)."""

from __future__ import annotations

from strategy_validator.contracts.oracle_types import (
    OracleArtifactCoverageStatus,
    OracleArtifactIntegrityStatus,
    OracleConstitutionalTrustStatus,
    OracleEvidenceStatus,
    OracleSupportVerificationStatus,
)


def assess_support_chain_trust(
    *,
    evidence_freshness_status: OracleEvidenceStatus,
    stale_artifact_count: int,
    evidence_integrity_status: OracleArtifactIntegrityStatus,
    unverified_artifact_count: int,
    evidence_coverage_status: OracleArtifactCoverageStatus,
    missing_expected_artifact_count: int,
    support_verification_status: OracleSupportVerificationStatus,
    formal_verification_required: bool,
) -> tuple[OracleConstitutionalTrustStatus, str, list[str]]:
    reasons: list[str] = []
    if formal_verification_required and support_verification_status != "VERIFIED":
        reasons.append("formal_support_verification_required_but_not_verified")
    if evidence_freshness_status == "STALE":
        reasons.append("stale_evidence")
    if stale_artifact_count > 0:
        reasons.append(f"stale_artifact_count={stale_artifact_count}")
    if unverified_artifact_count > 0:
        reasons.append(f"unverified_artifact_count={unverified_artifact_count}")
    if missing_expected_artifact_count > 0:
        reasons.append(f"missing_expected_artifact_count={missing_expected_artifact_count}")
    if evidence_integrity_status not in {"VERIFIED", "UNKNOWN"}:
        reasons.append(f"integrity={evidence_integrity_status}")
    if evidence_coverage_status in {"INCOMPLETE", "UNKNOWN"} and missing_expected_artifact_count > 0:
        reasons.append(f"coverage={evidence_coverage_status}")

    if reasons:
        return (
            "TRUST_RESTRICTED",
            "Support-chain trust is restricted: " + "; ".join(reasons),
            reasons,
        )
    return "TRUSTED", "Advisory support-chain checks are within nominal envelopes.", []
