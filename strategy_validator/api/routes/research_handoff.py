"""Validator-handoff and ingress-acceptance research routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from strategy_validator.application.research_integrity import (
    build_semantic_validator_handoff_packet,
    verify_semantic_validator_handoff_packet,
    summarize_semantic_validator_handoff_packet,
    build_semantic_validator_handoff_packet_ingress_report,
    summarize_semantic_validator_handoff_packet_ingress,
    build_semantic_validator_handoff_packet_ingress_certificate,
    verify_semantic_validator_handoff_packet_ingress_certificate,
    summarize_semantic_validator_handoff_packet_ingress_certificate,
    build_semantic_validator_ingress_acceptance_record,
    verify_semantic_validator_ingress_acceptance_record,
    summarize_semantic_validator_ingress_acceptance_record,
    build_semantic_validator_ingress_acceptance_ledger,
    verify_semantic_validator_ingress_acceptance_ledger,
    summarize_semantic_validator_ingress_acceptance_ledger,
)
from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.semantic import (
    SemanticValidatorHandoffPacket,
    SemanticValidatorHandoffPacketIngressCertificate,
    SemanticValidatorIngressAcceptanceRecord,
    SemanticValidatorIngressAcceptanceLedger,
)

router = APIRouter()

class SemanticValidatorHandoffPacketRequest(BaseModel):
    evidence: dict[str, Any]


class SemanticValidatorHandoffPacketVerificationRequest(BaseModel):
    packet: dict[str, Any]
    evidence: dict[str, Any] | None = None


@router.post("/semantic-adjudication-bundle/validator-handoff-packet")
def semantic_validator_handoff_packet(
    request: SemanticValidatorHandoffPacketRequest,
) -> dict[str, object]:
    evidence = Evidence.model_validate(request.evidence)
    packet = build_semantic_validator_handoff_packet(evidence)
    return packet.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/validator-handoff-packet/verify")
def semantic_validator_handoff_packet_verify(
    request: SemanticValidatorHandoffPacketVerificationRequest,
) -> dict[str, object]:
    packet = SemanticValidatorHandoffPacket.model_validate(request.packet)
    evidence = Evidence.model_validate(request.evidence) if request.evidence is not None else None
    report = verify_semantic_validator_handoff_packet(packet, evidence=evidence)
    return report.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/validator-handoff-packet/summary")
def semantic_validator_handoff_packet_summary(
    request: SemanticValidatorHandoffPacketVerificationRequest,
) -> dict[str, object]:
    packet = SemanticValidatorHandoffPacket.model_validate(request.packet)
    evidence = Evidence.model_validate(request.evidence) if request.evidence is not None else None
    summary = summarize_semantic_validator_handoff_packet(packet, evidence=evidence)
    return summary.model_dump(mode="json")


class SemanticValidatorHandoffPacketIngressRequest(BaseModel):
    packet: dict[str, Any]
    proposal: dict[str, Any] | None = None
    require_packet_evidence_on_proposal: bool = True


@router.post("/semantic-adjudication-bundle/validator-handoff-packet/ingress")
def semantic_validator_handoff_packet_ingress(
    request: SemanticValidatorHandoffPacketIngressRequest,
) -> dict[str, object]:
    packet = SemanticValidatorHandoffPacket.model_validate(request.packet)
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    report = build_semantic_validator_handoff_packet_ingress_report(
        packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=request.require_packet_evidence_on_proposal,
    )
    return report.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/validator-handoff-packet/ingress/summary")
def semantic_validator_handoff_packet_ingress_summary(
    request: SemanticValidatorHandoffPacketIngressRequest,
) -> dict[str, object]:
    packet = SemanticValidatorHandoffPacket.model_validate(request.packet)
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    summary = summarize_semantic_validator_handoff_packet_ingress(
        packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=request.require_packet_evidence_on_proposal,
    )
    return summary.model_dump(mode="json")


class SemanticValidatorHandoffPacketIngressCertificateRequest(BaseModel):
    packet: dict[str, Any]
    proposal: dict[str, Any] | None = None
    require_packet_evidence_on_proposal: bool = True
    issued_by: str = "operator"
    issue_reason: str = ""


class SemanticValidatorHandoffPacketIngressCertificateVerificationRequest(BaseModel):
    certificate: dict[str, Any]
    packet: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None
    require_packet_evidence_on_proposal: bool = True


@router.post("/semantic-adjudication-bundle/validator-handoff-packet/ingress/certificate")
def semantic_validator_handoff_packet_ingress_certificate(
    request: SemanticValidatorHandoffPacketIngressCertificateRequest,
) -> dict[str, object]:
    packet = SemanticValidatorHandoffPacket.model_validate(request.packet)
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    certificate = build_semantic_validator_handoff_packet_ingress_certificate(
        packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=request.require_packet_evidence_on_proposal,
        issued_by=request.issued_by,
        issue_reason=request.issue_reason,
    )
    return certificate.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/validator-handoff-packet/ingress/certificate/verify")
def semantic_validator_handoff_packet_ingress_certificate_verify(
    request: SemanticValidatorHandoffPacketIngressCertificateVerificationRequest,
) -> dict[str, object]:
    certificate = SemanticValidatorHandoffPacketIngressCertificate.model_validate(request.certificate)
    packet = SemanticValidatorHandoffPacket.model_validate(request.packet) if request.packet is not None else None
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    report = verify_semantic_validator_handoff_packet_ingress_certificate(
        certificate,
        packet=packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=request.require_packet_evidence_on_proposal,
    )
    return report.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/validator-handoff-packet/ingress/certificate/summary")
def semantic_validator_handoff_packet_ingress_certificate_summary(
    request: SemanticValidatorHandoffPacketIngressCertificateVerificationRequest,
) -> dict[str, object]:
    certificate = SemanticValidatorHandoffPacketIngressCertificate.model_validate(request.certificate)
    packet = SemanticValidatorHandoffPacket.model_validate(request.packet) if request.packet is not None else None
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    summary = summarize_semantic_validator_handoff_packet_ingress_certificate(
        certificate,
        packet=packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=request.require_packet_evidence_on_proposal,
    )
    return summary.model_dump(mode="json")


class SemanticValidatorIngressAcceptanceRecordRequest(BaseModel):
    certificate: dict[str, Any]
    packet: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None
    require_packet_evidence_on_proposal: bool = True
    accepted_by: str = "operator"
    acceptance_reason: str = ""


class SemanticValidatorIngressAcceptanceRecordVerificationRequest(BaseModel):
    record: dict[str, Any]
    certificate: dict[str, Any] | None = None
    packet: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None
    require_packet_evidence_on_proposal: bool = True


@router.post("/semantic-adjudication-bundle/validator-handoff-packet/ingress/acceptance-record")
def semantic_validator_ingress_acceptance_record(
    request: SemanticValidatorIngressAcceptanceRecordRequest,
) -> dict[str, object]:
    certificate = SemanticValidatorHandoffPacketIngressCertificate.model_validate(request.certificate)
    packet = SemanticValidatorHandoffPacket.model_validate(request.packet) if request.packet is not None else None
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    record = build_semantic_validator_ingress_acceptance_record(
        certificate,
        packet=packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=request.require_packet_evidence_on_proposal,
        accepted_by=request.accepted_by,
        acceptance_reason=request.acceptance_reason,
    )
    return record.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/validator-handoff-packet/ingress/acceptance-record/verify")
def semantic_validator_ingress_acceptance_record_verify(
    request: SemanticValidatorIngressAcceptanceRecordVerificationRequest,
) -> dict[str, object]:
    record = SemanticValidatorIngressAcceptanceRecord.model_validate(request.record)
    certificate = SemanticValidatorHandoffPacketIngressCertificate.model_validate(request.certificate) if request.certificate is not None else None
    packet = SemanticValidatorHandoffPacket.model_validate(request.packet) if request.packet is not None else None
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    report = verify_semantic_validator_ingress_acceptance_record(
        record,
        certificate=certificate,
        packet=packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=request.require_packet_evidence_on_proposal,
    )
    return report.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/validator-handoff-packet/ingress/acceptance-record/summary")
def semantic_validator_ingress_acceptance_record_summary(
    request: SemanticValidatorIngressAcceptanceRecordVerificationRequest,
) -> dict[str, object]:
    record = SemanticValidatorIngressAcceptanceRecord.model_validate(request.record)
    certificate = SemanticValidatorHandoffPacketIngressCertificate.model_validate(request.certificate) if request.certificate is not None else None
    packet = SemanticValidatorHandoffPacket.model_validate(request.packet) if request.packet is not None else None
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    summary = summarize_semantic_validator_ingress_acceptance_record(
        record,
        certificate=certificate,
        packet=packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=request.require_packet_evidence_on_proposal,
    )
    return summary.model_dump(mode="json")


class SemanticValidatorIngressAcceptanceLedgerRequest(BaseModel):
    acceptance_records: list[dict[str, Any]]


class SemanticValidatorIngressAcceptanceLedgerVerificationRequest(BaseModel):
    acceptance_ledger: dict[str, Any]
    acceptance_records: list[dict[str, Any]] | None = None


@router.post("/semantic-adjudication-bundle/validator-handoff-packet/ingress/acceptance-ledger")
def semantic_validator_ingress_acceptance_ledger(
    request: SemanticValidatorIngressAcceptanceLedgerRequest,
) -> dict[str, object]:
    records = [SemanticValidatorIngressAcceptanceRecord.model_validate(item) for item in request.acceptance_records]
    ledger = build_semantic_validator_ingress_acceptance_ledger(records)
    return ledger.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/validator-handoff-packet/ingress/acceptance-ledger/verify")
def semantic_validator_ingress_acceptance_ledger_verify(
    request: SemanticValidatorIngressAcceptanceLedgerVerificationRequest,
) -> dict[str, object]:
    ledger = SemanticValidatorIngressAcceptanceLedger.model_validate(request.acceptance_ledger)
    records = (
        [SemanticValidatorIngressAcceptanceRecord.model_validate(item) for item in request.acceptance_records]
        if request.acceptance_records is not None
        else None
    )
    report = verify_semantic_validator_ingress_acceptance_ledger(ledger, records=records)
    return report.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/validator-handoff-packet/ingress/acceptance-ledger/summary")
def semantic_validator_ingress_acceptance_ledger_summary(
    request: SemanticValidatorIngressAcceptanceLedgerVerificationRequest,
) -> dict[str, object]:
    ledger = SemanticValidatorIngressAcceptanceLedger.model_validate(request.acceptance_ledger)
    records = (
        [SemanticValidatorIngressAcceptanceRecord.model_validate(item) for item in request.acceptance_records]
        if request.acceptance_records is not None
        else None
    )
    summary = summarize_semantic_validator_ingress_acceptance_ledger(ledger, records=records)
    return summary.model_dump(mode="json")
