from __future__ import annotations

from typing import Iterable

from strategy_validator.contracts.oracle_types import (
    OracleConstitutionalTrustStatus,
    OracleOperatorReadiness,
)
from strategy_validator.contracts.oracle_strategic_fusion import OracleStrategicPosture


def _unique(items: Iterable[str]) -> list[str]:
    out: list[str] = []
    for item in items:
        v = str(item).strip()
        if v and v not in out:
            out.append(v)
    return out


def assess_attestation_operator_readiness(*, epistemic_status: str, recommended_global_action: str, evidence_freshness_status: str, stale_artifact_count: int, evidence_integrity_status: str, unverified_artifact_count: int, evidence_coverage_status: str, missing_expected_artifact_count: int, support_verification_status: str = "ABSENT") -> tuple[OracleOperatorReadiness, str, list[str]]:
    reasons: list[str] = []
    readiness: OracleOperatorReadiness = "READY_FOR_REVIEW"
    if stale_artifact_count > 0 or evidence_freshness_status == "STALE":
        readiness = "HOLD_FOR_REFRESH"
        reasons.append("supporting strategist inputs are stale and should be refreshed before operator reliance")
    elif epistemic_status == "UNKNOWN_UNKNOWNS":
        readiness = "REVIEW_WITH_CAUTION"
        reasons.append("epistemic state is unknown-unknowns, so the attestation should drive escalation rather than confident interpretation")
    elif evidence_freshness_status in {"AGING", "UNKNOWN"}:
        readiness = "REVIEW_WITH_CAUTION"
        reasons.append("supporting strategist inputs are aging or incompletely timestamped")
    if unverified_artifact_count > 0 or evidence_integrity_status in {"MIXED", "UNVERIFIED"}:
        readiness = "REVIEW_WITH_CAUTION" if readiness == "READY_FOR_REVIEW" else readiness
        reasons.append("the attestation support chain includes incomplete or unverified artifacts")
    if missing_expected_artifact_count > 0 or evidence_coverage_status in {"PARTIAL", "MISSING"}:
        readiness = "REVIEW_WITH_CAUTION" if readiness == "READY_FOR_REVIEW" else readiness
        reasons.append("one or more expected supporting artifacts are missing from the attestation support chain")
    if support_verification_status == "UNVERIFIED":
        readiness = "REVIEW_WITH_CAUTION" if readiness == "READY_FOR_REVIEW" else readiness
        reasons.append("formal support verification is present but unverified for the attestation support chain")
    elif support_verification_status == "INCOMPLETE":
        readiness = "REVIEW_WITH_CAUTION" if readiness == "READY_FOR_REVIEW" else readiness
        reasons.append("formal support verification is incomplete for the attestation support chain")
    if recommended_global_action == "DEFENSIVE_POSTURE":
        readiness = "REVIEW_WITH_CAUTION" if readiness == "READY_FOR_REVIEW" else readiness
        reasons.append("the report already recommends a defensive posture")
    elif recommended_global_action == "CANARY_REVIEW":
        readiness = "REVIEW_WITH_CAUTION" if readiness == "READY_FOR_REVIEW" else readiness
        reasons.append("the report already recommends canary review rather than broad confidence")
    reasons = _unique(reasons)
    if readiness == "READY_FOR_REVIEW":
        reasons.append("fresh inputs and nominal epistemic conditions support routine operator review")
    summary = {
        "READY_FOR_REVIEW": "Operator readiness is routine: this attestation is fit for normal review within advisory-only boundaries.",
        "REVIEW_WITH_CAUTION": "Operator readiness is cautious: review the listed risk signals before leaning on this attestation.",
        "HOLD_FOR_REFRESH": "Operator readiness is blocked on freshness: refresh stale strategist inputs before relying on this attestation.",
    }[readiness]
    return readiness, summary, reasons



def assess_fusion_operator_readiness(*, epistemic_status: str, strategic_posture: OracleStrategicPosture, evidence_freshness_status: str, stale_artifact_count: int, evidence_integrity_status: str, unverified_artifact_count: int, evidence_coverage_status: str, missing_expected_artifact_count: int, support_verification_status: str = "ABSENT") -> tuple[OracleOperatorReadiness, str, list[str]]:
    reasons: list[str] = []
    readiness: OracleOperatorReadiness = "READY_FOR_REVIEW"
    if stale_artifact_count > 0 or evidence_freshness_status == "STALE":
        readiness = "HOLD_FOR_REFRESH"
        reasons.append("one or more fused strategist artifacts are stale")
    elif epistemic_status == "UNKNOWN_UNKNOWNS":
        readiness = "REVIEW_WITH_CAUTION"
        reasons.append("epistemic stress is too high for routine interpretation")
    elif evidence_freshness_status in {"AGING", "UNKNOWN"}:
        readiness = "REVIEW_WITH_CAUTION"
        reasons.append("the fused evidence chain is aging or incompletely timestamped")
    if unverified_artifact_count > 0 or evidence_integrity_status in {"MIXED", "UNVERIFIED"}:
        readiness = "REVIEW_WITH_CAUTION" if readiness == "READY_FOR_REVIEW" else readiness
        reasons.append("the fused evidence chain includes incomplete or unverified artifacts")
    if missing_expected_artifact_count > 0 or evidence_coverage_status in {"PARTIAL", "MISSING"}:
        readiness = "REVIEW_WITH_CAUTION" if readiness == "READY_FOR_REVIEW" else readiness
        reasons.append("the fused strategist view is missing one or more expected supporting artifacts")
    if support_verification_status == "UNVERIFIED":
        readiness = "REVIEW_WITH_CAUTION" if readiness == "READY_FOR_REVIEW" else readiness
        reasons.append("formal support verification is present but unverified for the fused support chain")
    elif support_verification_status == "INCOMPLETE":
        readiness = "REVIEW_WITH_CAUTION" if readiness == "READY_FOR_REVIEW" else readiness
        reasons.append("formal support verification is incomplete for the fused support chain")
    elif support_verification_status == "ABSENT" and evidence_coverage_status == "COMPLETE":
        readiness = "REVIEW_WITH_CAUTION" if readiness == "READY_FOR_REVIEW" else readiness
        reasons.append("formal support verification has not yet been produced for the otherwise complete fused support chain")
    if strategic_posture in {"DEFENSIVE_RESEARCH", "RESEARCH_FREEZE", "CAUTION_BIASED"}:
        readiness = "REVIEW_WITH_CAUTION" if readiness == "READY_FOR_REVIEW" else readiness
        reasons.append(f"strategic posture is {strategic_posture}")
    reasons = _unique(reasons)
    if readiness == "READY_FOR_REVIEW":
        reasons.append("fused evidence is fresh enough for routine operator interpretation")
    summary = {
        "READY_FOR_REVIEW": "Operator readiness is routine: the fused strategist view is fit for normal review within advisory-only boundaries.",
        "REVIEW_WITH_CAUTION": "Operator readiness is cautious: treat the fused strategist view as reviewable but not frictionless.",
        "HOLD_FOR_REFRESH": "Operator readiness is blocked on freshness: refresh stale fused evidence before relying on this strategist view.",
    }[readiness]
    return readiness, summary, reasons



def assess_briefing_operator_readiness(*, trust_status: OracleConstitutionalTrustStatus, evidence_freshness_status: str, stale_artifact_count: int, evidence_integrity_status: str, unverified_artifact_count: int, evidence_coverage_status: str, missing_expected_artifact_count: int, support_verification_status: str = "ABSENT") -> tuple[OracleOperatorReadiness, str, list[str]]:
    reasons: list[str] = []
    readiness: OracleOperatorReadiness = "READY_FOR_REVIEW"
    if trust_status == "UNTRUSTED":
        readiness = "HOLD_FOR_REFRESH"
        reasons.append("the canonical briefing pack is untrusted")
    elif stale_artifact_count > 0 or evidence_freshness_status == "STALE":
        readiness = "HOLD_FOR_REFRESH"
        reasons.append("the canonical briefing pack contains stale supporting artifacts that should be refreshed before operator reliance")
    elif trust_status == "TRUST_RESTRICTED":
        readiness = "REVIEW_WITH_CAUTION"
        reasons.append("the canonical briefing pack is trust-restricted")
    elif evidence_freshness_status in {"AGING", "UNKNOWN"}:
        readiness = "REVIEW_WITH_CAUTION"
        reasons.append("the canonical briefing pack includes aging or incompletely timestamped evidence")
    if unverified_artifact_count > 0 or evidence_integrity_status in {"MIXED", "UNVERIFIED"}:
        readiness = "REVIEW_WITH_CAUTION" if readiness == "READY_FOR_REVIEW" else readiness
        reasons.append("the canonical briefing pack includes incomplete or unverified supporting artifacts")
    if missing_expected_artifact_count > 0 or evidence_coverage_status in {"PARTIAL", "MISSING"}:
        readiness = "REVIEW_WITH_CAUTION" if readiness == "READY_FOR_REVIEW" else readiness
        reasons.append("the canonical briefing pack is missing one or more expected supporting artifacts")
    if support_verification_status == "UNVERIFIED":
        readiness = "REVIEW_WITH_CAUTION" if readiness == "READY_FOR_REVIEW" else readiness
        reasons.append("formal support verification is present but unverified for the canonical support chain")
    elif support_verification_status == "INCOMPLETE":
        readiness = "REVIEW_WITH_CAUTION" if readiness == "READY_FOR_REVIEW" else readiness
        reasons.append("formal support verification is incomplete for the canonical support chain")
    elif support_verification_status == "ABSENT" and evidence_coverage_status == "COMPLETE":
        readiness = "REVIEW_WITH_CAUTION" if readiness == "READY_FOR_REVIEW" else readiness
        reasons.append("formal support verification has not yet been produced for the otherwise complete canonical support chain")
    reasons = _unique(reasons)
    if readiness == "READY_FOR_REVIEW":
        reasons.append("the canonical briefing pack is trusted and sufficiently fresh for routine operator review")
    summary = {
        "READY_FOR_REVIEW": "Operator readiness is routine: the canonical briefing pack is fit for normal operator review.",
        "REVIEW_WITH_CAUTION": "Operator readiness is cautious: use the canonical briefing pack, but preserve review friction and provenance discipline.",
        "HOLD_FOR_REFRESH": "Operator readiness is blocked: repair trust or freshness gaps before treating this briefing pack as canonical.",
    }[readiness]
    return readiness, summary, reasons
