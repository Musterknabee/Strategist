"""Validator-submission research routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from strategy_validator.application.research_integrity import (
    build_semantic_validator_submission_packet,
    verify_semantic_validator_submission_packet,
    summarize_semantic_validator_submission_packet,
    build_semantic_validator_submission_packet_evidence,
    verify_semantic_validator_submission_packet_evidence,
    summarize_semantic_validator_submission_packet_evidence,
    build_semantic_validator_submission_readiness_report,
    summarize_semantic_validator_submission_readiness,
)
from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.semantic import (
    SemanticValidatorIngressAcceptanceLedger,
    SemanticValidatorIngressAcceptanceRecord,
    SemanticValidatorSubmissionPacket,
)

router = APIRouter()

class SemanticValidatorSubmissionPacketRequest(BaseModel):
    acceptance_ledger: dict[str, Any]
    acceptance_records: list[dict[str, Any]] | None = None
    submitted_by: str = "operator"
    submission_reason: str = ""


class SemanticValidatorSubmissionPacketVerificationRequest(BaseModel):
    submission_packet: dict[str, Any]
    acceptance_ledger: dict[str, Any] | None = None
    acceptance_records: list[dict[str, Any]] | None = None


@router.post("/semantic-adjudication-bundle/validator-submission-packet")
def semantic_validator_submission_packet(
    request: SemanticValidatorSubmissionPacketRequest,
) -> dict[str, object]:
    ledger = SemanticValidatorIngressAcceptanceLedger.model_validate(request.acceptance_ledger)
    records = (
        [SemanticValidatorIngressAcceptanceRecord.model_validate(item) for item in request.acceptance_records]
        if request.acceptance_records is not None
        else None
    )
    packet = build_semantic_validator_submission_packet(
        ledger,
        submitted_by=request.submitted_by,
        submission_reason=request.submission_reason,
        records=records,
    )
    return packet.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/validator-submission-packet/verify")
def semantic_validator_submission_packet_verify(
    request: SemanticValidatorSubmissionPacketVerificationRequest,
) -> dict[str, object]:
    packet = SemanticValidatorSubmissionPacket.model_validate(request.submission_packet)
    ledger = SemanticValidatorIngressAcceptanceLedger.model_validate(request.acceptance_ledger) if request.acceptance_ledger is not None else None
    records = (
        [SemanticValidatorIngressAcceptanceRecord.model_validate(item) for item in request.acceptance_records]
        if request.acceptance_records is not None
        else None
    )
    report = verify_semantic_validator_submission_packet(packet, acceptance_ledger=ledger, records=records)
    return report.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/validator-submission-packet/summary")
def semantic_validator_submission_packet_summary(
    request: SemanticValidatorSubmissionPacketVerificationRequest,
) -> dict[str, object]:
    packet = SemanticValidatorSubmissionPacket.model_validate(request.submission_packet)
    ledger = SemanticValidatorIngressAcceptanceLedger.model_validate(request.acceptance_ledger) if request.acceptance_ledger is not None else None
    records = (
        [SemanticValidatorIngressAcceptanceRecord.model_validate(item) for item in request.acceptance_records]
        if request.acceptance_records is not None
        else None
    )
    summary = summarize_semantic_validator_submission_packet(packet, acceptance_ledger=ledger, records=records)
    return summary.model_dump(mode="json")


class SemanticValidatorSubmissionPacketEvidenceRequest(BaseModel):
    submission_packet: dict[str, Any]


class SemanticValidatorSubmissionPacketEvidenceVerificationRequest(BaseModel):
    evidence: dict[str, Any]
    submission_packet: dict[str, Any] | None = None


@router.post("/semantic-adjudication-bundle/validator-submission-packet/evidence")
def semantic_validator_submission_packet_evidence(
    request: SemanticValidatorSubmissionPacketEvidenceRequest,
) -> dict[str, object]:
    packet = SemanticValidatorSubmissionPacket.model_validate(request.submission_packet)
    evidence = build_semantic_validator_submission_packet_evidence(packet)
    return evidence.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/validator-submission-packet/evidence/verify")
def semantic_validator_submission_packet_evidence_verify(
    request: SemanticValidatorSubmissionPacketEvidenceVerificationRequest,
) -> dict[str, object]:
    evidence = Evidence.model_validate(request.evidence)
    packet = SemanticValidatorSubmissionPacket.model_validate(request.submission_packet) if request.submission_packet is not None else None
    report = verify_semantic_validator_submission_packet_evidence(evidence, submission_packet=packet)
    return report.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/validator-submission-packet/evidence/summary")
def semantic_validator_submission_packet_evidence_summary(
    request: SemanticValidatorSubmissionPacketEvidenceVerificationRequest,
) -> dict[str, object]:
    evidence = Evidence.model_validate(request.evidence)
    packet = SemanticValidatorSubmissionPacket.model_validate(request.submission_packet) if request.submission_packet is not None else None
    summary = summarize_semantic_validator_submission_packet_evidence(evidence, submission_packet=packet)
    return summary.model_dump(mode="json")


class SemanticValidatorSubmissionReadinessRequest(BaseModel):
    proposal: dict[str, Any]
    submission_packet_evidence: dict[str, Any] | None = None
    require_submission_packet_evidence: bool = True


@router.post("/semantic-adjudication-bundle/validator-submission/readiness")
def semantic_validator_submission_readiness(
    request: SemanticValidatorSubmissionReadinessRequest,
) -> dict[str, object]:
    proposal = ExperimentManifest.model_validate(request.proposal)
    evidence = Evidence.model_validate(request.submission_packet_evidence) if request.submission_packet_evidence is not None else None
    report = build_semantic_validator_submission_readiness_report(
        proposal,
        submission_packet_evidence=evidence,
        require_submission_packet_evidence=request.require_submission_packet_evidence,
    )
    return report.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/validator-submission/readiness/summary")
def semantic_validator_submission_readiness_summary(
    request: SemanticValidatorSubmissionReadinessRequest,
) -> dict[str, object]:
    proposal = ExperimentManifest.model_validate(request.proposal)
    evidence = Evidence.model_validate(request.submission_packet_evidence) if request.submission_packet_evidence is not None else None
    summary = summarize_semantic_validator_submission_readiness(
        proposal,
        submission_packet_evidence=evidence,
        require_submission_packet_evidence=request.require_submission_packet_evidence,
    )
    return summary.model_dump(mode="json")
