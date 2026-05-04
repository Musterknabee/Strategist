"""Advisory support-chain remediation hints (read-only; no ledger mutation)."""

from __future__ import annotations

from strategy_validator.contracts.oracle_types import (
    OracleArtifactCoverageStatus,
    OracleArtifactIntegrityStatus,
    OracleEvidenceStatus,
    OracleSupportChainRemediationStatus,
    OracleSupportVerificationStatus,
)


def assess_support_chain_remediation(
    *,
    evidence_freshness_status: OracleEvidenceStatus,
    stale_artifact_count: int,
    evidence_integrity_status: OracleArtifactIntegrityStatus,
    unverified_artifact_count: int,
    evidence_coverage_status: OracleArtifactCoverageStatus,
    missing_expected_artifact_labels: list[str],
    support_verification_status: OracleSupportVerificationStatus,
    formal_verification_required: bool,
) -> tuple[OracleSupportChainRemediationStatus, str, list[str]]:
    actions: list[str] = []
    if formal_verification_required and support_verification_status != "VERIFIED":
        actions.append("Seal support verification manifests before relying on downstream automation.")
    if missing_expected_artifact_labels:
        actions.append("Restore expected artifacts: " + ", ".join(missing_expected_artifact_labels))
    if evidence_freshness_status == "STALE" or stale_artifact_count > 0:
        actions.append("Refresh stale oracle artifacts referenced by this attestation.")
    if unverified_artifact_count > 0:
        actions.append("Verify or replace unverified lineage artifacts.")
    if evidence_integrity_status not in {"VERIFIED", "UNKNOWN"}:
        actions.append("Re-seal or re-verify integrity for lineage artifacts.")
    if evidence_coverage_status == "INCOMPLETE" and missing_expected_artifact_labels:
        actions.append("Close evidence coverage gaps called out by the coverage summary.")

    if actions:
        return (
            "REMEDIATION_RECOMMENDED",
            "Support-chain remediation recommended before expanding reliance.",
            actions,
        )
    return "NO_REMEDIATION", "No support-chain remediation required for this advisory snapshot.", []
