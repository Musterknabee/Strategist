from __future__ import annotations

from typing import Iterable

from strategy_validator.contracts.oracle import OracleConstitutionalTrustStatus, OracleSupportVerificationStatus


def _unique(items: Iterable[str]) -> list[str]:
    out: list[str] = []
    for item in items:
        value = str(item).strip()
        if value and value not in out:
            out.append(value)
    return out


def assess_support_chain_trust(
    *,
    evidence_freshness_status: str,
    stale_artifact_count: int,
    evidence_integrity_status: str,
    unverified_artifact_count: int,
    evidence_coverage_status: str,
    missing_expected_artifact_count: int,
    support_verification_status: OracleSupportVerificationStatus = "ABSENT",
    formal_verification_required: bool = False,
) -> tuple[OracleConstitutionalTrustStatus, str, list[str]]:
    reasons: list[str] = []
    status: OracleConstitutionalTrustStatus = "TRUSTED"

    if stale_artifact_count > 0 or evidence_freshness_status == "STALE":
        status = "UNTRUSTED"
        reasons.append("support chain contains stale artifacts")
    elif evidence_freshness_status in {"AGING", "UNKNOWN"}:
        status = "TRUST_RESTRICTED"
        reasons.append("support chain is aging or incompletely timestamped")

    if unverified_artifact_count > 0 or evidence_integrity_status == "UNVERIFIED":
        status = "UNTRUSTED"
        reasons.append("support chain includes unverified artifacts")
    elif evidence_integrity_status == "MIXED":
        status = "TRUST_RESTRICTED" if status == "TRUSTED" else status
        reasons.append("support chain mixes verified and incomplete artifacts")

    if missing_expected_artifact_count > 0 or evidence_coverage_status == "MISSING":
        status = "UNTRUSTED"
        reasons.append("support chain is missing expected artifacts")
    elif evidence_coverage_status == "PARTIAL":
        status = "TRUST_RESTRICTED" if status == "TRUSTED" else status
        reasons.append("support chain is only partially covered by expected artifacts")

    if support_verification_status == "UNVERIFIED":
        status = "UNTRUSTED"
        reasons.append("formal support verification is present but unverified")
    elif support_verification_status == "INCOMPLETE":
        status = "TRUST_RESTRICTED" if status == "TRUSTED" else status
        reasons.append("formal support verification is incomplete")
    elif support_verification_status == "ABSENT" and formal_verification_required and evidence_coverage_status == "COMPLETE":
        status = "TRUST_RESTRICTED" if status == "TRUSTED" else status
        reasons.append("formal support verification has not yet been produced")

    reasons = _unique(reasons)
    if status == "TRUSTED":
        reasons.append("support chain is fresh, complete, and sufficiently verified for routine trust")
    summary = {
        "TRUSTED": "Support-chain trust is trusted: the supporting artifact chain is fit for routine operator reliance.",
        "TRUST_RESTRICTED": "Support-chain trust is restricted: the supporting artifact chain is usable, but only with explicit caution.",
        "UNTRUSTED": "Support-chain trust is untrusted: repair support-chain gaps before relying on this strategist surface.",
    }[status]
    return status, summary, reasons
