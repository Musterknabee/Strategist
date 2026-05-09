"""Semantic adjudication release handoff certificate and evidence routes."""

from __future__ import annotations

from fastapi import APIRouter

from strategy_validator.api.routes.research_release_common import *  # noqa: F403

router = APIRouter()

class SemanticAdjudicationReleaseHandoffCertificateRequest(BaseModel):
    decision_ledger: dict[str, Any]
    decision_records: list[dict[str, Any]] | None = None
    issued_by: str = "operator"
    issue_reason: str | None = None


class SemanticAdjudicationReleaseHandoffCertificateVerificationRequest(BaseModel):
    certificate: dict[str, Any]
    decision_ledger: dict[str, Any] | None = None
    decision_records: list[dict[str, Any]] | None = None


@router.post("/semantic-adjudication-bundle/release-handoff-certificate")
def semantic_adjudication_release_handoff_certificate(
    request: SemanticAdjudicationReleaseHandoffCertificateRequest,
) -> dict[str, object]:
    ledger = SemanticAdjudicationReleaseDecisionLedger.model_validate(request.decision_ledger)
    records = (
        [SemanticAdjudicationReleaseDecisionRecord.model_validate(item) for item in request.decision_records]
        if request.decision_records is not None
        else None
    )
    certificate = build_semantic_adjudication_release_handoff_certificate(
        ledger,
        records=records,
        issued_by=request.issued_by,
        issue_reason=request.issue_reason,
    )
    return certificate.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/release-handoff-certificate/verify")
def semantic_adjudication_release_handoff_certificate_verify(
    request: SemanticAdjudicationReleaseHandoffCertificateVerificationRequest,
) -> dict[str, object]:
    certificate = SemanticAdjudicationReleaseHandoffCertificate.model_validate(request.certificate)
    ledger = (
        SemanticAdjudicationReleaseDecisionLedger.model_validate(request.decision_ledger)
        if request.decision_ledger is not None
        else None
    )
    records = (
        [SemanticAdjudicationReleaseDecisionRecord.model_validate(item) for item in request.decision_records]
        if request.decision_records is not None
        else None
    )
    report = verify_semantic_adjudication_release_handoff_certificate(
        certificate,
        ledger=ledger,
        records=records,
    )
    return report.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/release-handoff-certificate/summary")
def semantic_adjudication_release_handoff_certificate_summary(
    request: SemanticAdjudicationReleaseHandoffCertificateVerificationRequest,
) -> dict[str, object]:
    certificate = SemanticAdjudicationReleaseHandoffCertificate.model_validate(request.certificate)
    ledger = (
        SemanticAdjudicationReleaseDecisionLedger.model_validate(request.decision_ledger)
        if request.decision_ledger is not None
        else None
    )
    records = (
        [SemanticAdjudicationReleaseDecisionRecord.model_validate(item) for item in request.decision_records]
        if request.decision_records is not None
        else None
    )
    summary = summarize_semantic_adjudication_release_handoff_certificate(
        certificate,
        ledger=ledger,
        records=records,
    )
    return summary.model_dump(mode="json")


class SemanticReleaseHandoffCertificateEvidenceRequest(BaseModel):
    certificate: dict[str, Any]


class SemanticReleaseHandoffCertificateEvidenceVerificationRequest(BaseModel):
    evidence: dict[str, Any]


@router.post("/semantic-adjudication-bundle/release-handoff-certificate/evidence")
def semantic_adjudication_release_handoff_certificate_evidence(
    request: SemanticReleaseHandoffCertificateEvidenceRequest,
) -> dict[str, object]:
    certificate = SemanticAdjudicationReleaseHandoffCertificate.model_validate(request.certificate)
    evidence = build_semantic_release_handoff_certificate_evidence(certificate)
    return evidence.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/release-handoff-certificate/evidence/verify")
def semantic_adjudication_release_handoff_certificate_evidence_verify(
    request: SemanticReleaseHandoffCertificateEvidenceVerificationRequest,
) -> dict[str, object]:
    evidence = Evidence.model_validate(request.evidence)
    report = verify_semantic_release_handoff_certificate_evidence(evidence)
    return report.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/release-handoff-certificate/evidence/summary")
def semantic_adjudication_release_handoff_certificate_evidence_summary(
    request: SemanticReleaseHandoffCertificateEvidenceVerificationRequest,
) -> dict[str, object]:
    evidence = Evidence.model_validate(request.evidence)
    summary = summarize_semantic_release_handoff_certificate_evidence(evidence)
    return summary.model_dump(mode="json")
