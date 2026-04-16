from __future__ import annotations

from typing import Iterable

from strategy_validator.contracts.oracle import OracleSupportChainRemediationStatus, OracleSupportVerificationStatus


def _unique(items: Iterable[str]) -> list[str]:
    out: list[str] = []
    for item in items:
        value = str(item).strip()
        if value and value not in out:
            out.append(value)
    return out


def assess_support_chain_remediation(
    *,
    evidence_freshness_status: str,
    stale_artifact_count: int,
    evidence_integrity_status: str,
    unverified_artifact_count: int,
    evidence_coverage_status: str,
    missing_expected_artifact_labels: list[str] | None = None,
    support_verification_status: OracleSupportVerificationStatus = "ABSENT",
    formal_verification_required: bool = False,
) -> tuple[OracleSupportChainRemediationStatus, str, list[str]]:
    actions: list[str] = []
    status: OracleSupportChainRemediationStatus = "NO_REMEDIATION"
    missing_expected_artifact_labels = list(missing_expected_artifact_labels or [])

    def recommend(action: str) -> None:
        nonlocal status
        if status == "NO_REMEDIATION":
            status = "REMEDIATION_RECOMMENDED"
        actions.append(action)

    def require(action: str) -> None:
        nonlocal status
        status = "REMEDIATION_REQUIRED"
        actions.append(action)

    if stale_artifact_count > 0 or evidence_freshness_status == "STALE":
        require("Refresh stale supporting artifacts before relying on this strategist surface.")
    elif evidence_freshness_status in {"AGING", "UNKNOWN"}:
        recommend("Refresh or timestamp aging support-chain artifacts to preserve operator trust.")

    if unverified_artifact_count > 0 or evidence_integrity_status == "UNVERIFIED":
        require("Repair or regenerate unverified support-chain artifacts before treating this surface as grounded.")
    elif evidence_integrity_status == "MIXED":
        recommend("Investigate incomplete support-chain artifacts and promote them to verified state where possible.")

    if evidence_coverage_status == "MISSING" or missing_expected_artifact_labels:
        labels = ", ".join(missing_expected_artifact_labels) if missing_expected_artifact_labels else "expected support artifacts"
        require(f"Regenerate the missing support-chain artifacts: {labels}.")
    elif evidence_coverage_status == "PARTIAL":
        recommend("Backfill partially covered support-chain artifacts before increasing reliance on this surface.")

    if support_verification_status == "UNVERIFIED":
        require("Investigate failed formal support verification and repair the verification artifact before relying on this surface.")
    elif support_verification_status == "INCOMPLETE":
        recommend("Complete formal support verification for the current support chain.")
    elif support_verification_status == "ABSENT" and formal_verification_required and evidence_coverage_status == "COMPLETE":
        recommend("Produce formal support verification artifacts for the complete support chain.")

    actions = _unique(actions)
    if status == "NO_REMEDIATION":
        actions.append("No support-chain remediation is currently required; preserve normal provenance discipline.")
    summary = {
        "NO_REMEDIATION": "Support-chain remediation is clear: no immediate repair steps are required.",
        "REMEDIATION_RECOMMENDED": "Support-chain remediation is recommended: improve provenance quality before leaning harder on this strategist surface.",
        "REMEDIATION_REQUIRED": "Support-chain remediation is required: repair support-chain gaps before relying on this strategist surface.",
    }[status]
    return status, summary, actions
