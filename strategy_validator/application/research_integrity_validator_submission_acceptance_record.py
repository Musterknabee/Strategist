from __future__ import annotations

from typing import Any

from strategy_validator.application.research_integrity_common import _sha256_payload
from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.core.enums import EvidenceType
from strategy_validator.contracts.semantic import (
    SemanticValidatorHandoffPacket,
    SemanticValidatorHandoffPacketIngressCertificate,
    SemanticValidatorIngressAcceptanceRecord,
    SemanticValidatorIngressAcceptanceRecordIssue,
    SemanticValidatorIngressAcceptanceRecordVerificationReport,
    SemanticValidatorIngressAcceptanceRecordSummary,
    SemanticValidatorIngressAcceptanceLedger,
    SemanticValidatorIngressAcceptanceLedgerEntry,
    SemanticValidatorIngressAcceptanceLedgerIssue,
    SemanticValidatorIngressAcceptanceLedgerVerificationReport,
    SemanticValidatorIngressAcceptanceLedgerSummary,
    SemanticValidatorSubmissionPacket,
    SemanticValidatorSubmissionPacketIssue,
    SemanticValidatorSubmissionPacketVerificationReport,
    SemanticValidatorSubmissionPacketSummary,
    SemanticValidatorSubmissionPacketEvidenceIssue,
    SemanticValidatorSubmissionPacketEvidenceVerificationReport,
    SemanticValidatorSubmissionPacketEvidenceSummary,
    SemanticValidatorSubmissionReadinessIssue,
    SemanticValidatorSubmissionReadinessReport,
    SemanticValidatorSubmissionReadinessSummary,
)
from strategy_validator.application.research_integrity_validator_handoff import (
    summarize_semantic_validator_handoff_packet_ingress_certificate,
)

def _semantic_validator_ingress_acceptance_record_payload_checksum(
    record: SemanticValidatorIngressAcceptanceRecord,
) -> str:
    payload = record.model_dump(mode="json")
    payload.pop("payload_checksum", None)
    return _sha256_payload(payload)


def build_semantic_validator_ingress_acceptance_record(
    certificate: SemanticValidatorHandoffPacketIngressCertificate,
    *,
    packet: SemanticValidatorHandoffPacket | None = None,
    proposal: ExperimentManifest | None = None,
    require_packet_evidence_on_proposal: bool = True,
    accepted_by: str = "operator",
    acceptance_reason: str = "",
) -> SemanticValidatorIngressAcceptanceRecord:
    """Seal the final operator/CI acceptance of a certified semantic packet for validator adjudication."""
    summary = summarize_semantic_validator_handoff_packet_ingress_certificate(
        certificate,
        packet=packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=require_packet_evidence_on_proposal,
    )
    accepted = summary.recommended_action == "HAND_OFF_CERTIFIED_PACKET_EVIDENCE_TO_VALIDATOR" and summary.ready_for_validator_ingress
    acceptance_id = "semantic-validator-ingress-accept-" + _sha256_payload(
        {
            "certificate_id": certificate.certificate_id,
            "packet_id": certificate.packet_id,
            "experiment_id": certificate.experiment_id,
            "certificate_payload_checksum": certificate.payload_checksum,
            "summary": summary.model_dump(mode="json"),
            "accepted_by": accepted_by,
            "acceptance_reason": acceptance_reason,
        }
    )[:24]
    record = SemanticValidatorIngressAcceptanceRecord(
        acceptance_id=acceptance_id,
        certificate_id=certificate.certificate_id,
        packet_id=certificate.packet_id,
        experiment_id=certificate.experiment_id,
        evidence_id=certificate.evidence_id,
        ready_for_validator_ingress=summary.ready_for_validator_ingress,
        accepted_for_validator_adjudication=accepted,
        certificate_payload_checksum=certificate.payload_checksum,
        packet_payload_checksum=certificate.packet_payload_checksum,
        evidence_payload_checksum=certificate.evidence_payload_checksum,
        certificate_summary=summary,
        accepted_by=accepted_by or "operator",
        acceptance_reason=acceptance_reason or "",
        payload_checksum="pending",
    )
    return record.model_copy(update={"payload_checksum": _semantic_validator_ingress_acceptance_record_payload_checksum(record)})


def verify_semantic_validator_ingress_acceptance_record(
    record: SemanticValidatorIngressAcceptanceRecord,
    *,
    certificate: SemanticValidatorHandoffPacketIngressCertificate | None = None,
    packet: SemanticValidatorHandoffPacket | None = None,
    proposal: ExperimentManifest | None = None,
    require_packet_evidence_on_proposal: bool = True,
) -> SemanticValidatorIngressAcceptanceRecordVerificationReport:
    """Verify the sealed final semantic validator-ingress acceptance record."""
    issues: list[SemanticValidatorIngressAcceptanceRecordIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(SemanticValidatorIngressAcceptanceRecordIssue(code=code, message=message, severity=severity))

    observed = record.payload_checksum
    expected = _semantic_validator_ingress_acceptance_record_payload_checksum(record)
    if observed != expected:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_CHECKSUM_MISMATCH", "acceptance record payload checksum does not match canonical payload")
    if record.schema_version != "semantic_validator_ingress_acceptance_record/v1":
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_SCHEMA_UNSUPPORTED", "unsupported validator-ingress acceptance record schema version")
    if record.certificate_id != record.certificate_summary.certificate_id:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_CERTIFICATE_ID_MISMATCH", "record certificate id differs from embedded certificate summary")
    if record.packet_id != record.certificate_summary.packet_id:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_PACKET_ID_MISMATCH", "record packet id differs from embedded certificate summary")
    if record.experiment_id != record.certificate_summary.experiment_id:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_EXPERIMENT_MISMATCH", "record experiment id differs from embedded certificate summary")
    if record.packet_payload_checksum != record.certificate_summary.packet_payload_checksum:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_PACKET_CHECKSUM_MISMATCH", "record packet checksum differs from embedded certificate summary")
    if record.evidence_payload_checksum != record.certificate_summary.evidence_payload_checksum:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_EVIDENCE_CHECKSUM_MISMATCH", "record evidence checksum differs from embedded certificate summary")
    if record.ready_for_validator_ingress != record.certificate_summary.ready_for_validator_ingress:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_READY_FLAG_DRIFT", "record ready flag differs from embedded certificate summary")
    if record.accepted_for_validator_adjudication and record.certificate_summary.recommended_action != "HAND_OFF_CERTIFIED_PACKET_EVIDENCE_TO_VALIDATOR":
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_ACCEPTED_WITH_NON_HANDOFF_SUMMARY", "record accepts adjudication but embedded certificate summary does not recommend handoff")
    if record.accepted_for_validator_adjudication and not record.ready_for_validator_ingress:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_ACCEPTED_UNREADY_CERTIFICATE", "record accepts adjudication but the certified packet is not ready for validator ingress")

    if certificate is not None:
        if certificate.certificate_id != record.certificate_id:
            issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_SOURCE_CERTIFICATE_ID_MISMATCH", "source certificate id differs from acceptance record")
        if certificate.payload_checksum != record.certificate_payload_checksum:
            issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_SOURCE_CERTIFICATE_CHECKSUM_DRIFT", "source certificate checksum differs from acceptance record")
        rebuilt_summary = summarize_semantic_validator_handoff_packet_ingress_certificate(
            certificate,
            packet=packet,
            proposal=proposal,
            require_packet_evidence_on_proposal=require_packet_evidence_on_proposal,
        )
        if rebuilt_summary.model_dump(mode="json") != record.certificate_summary.model_dump(mode="json"):
            issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_SUMMARY_DRIFT", "rebuilt certificate summary differs from embedded acceptance summary")

    verified = not any(item.severity == "BLOCKER" for item in issues)
    accepted = bool(record.accepted_for_validator_adjudication and record.ready_for_validator_ingress and verified)
    return SemanticValidatorIngressAcceptanceRecordVerificationReport(
        acceptance_id=record.acceptance_id,
        certificate_id=record.certificate_id,
        packet_id=record.packet_id,
        experiment_id=record.experiment_id,
        verified=verified,
        accepted_for_validator_adjudication=accepted,
        ready_for_validator_ingress=bool(record.ready_for_validator_ingress and verified),
        expected_payload_checksum=expected,
        observed_payload_checksum=observed,
        certificate_payload_checksum=record.certificate_payload_checksum,
        packet_payload_checksum=record.packet_payload_checksum,
        evidence_payload_checksum=record.evidence_payload_checksum,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="SUBMIT_ACCEPTED_SEMANTIC_PACKET_TO_VALIDATOR" if accepted else "REBUILD_OR_BLOCK_SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE",
    )


def summarize_semantic_validator_ingress_acceptance_record(
    record: SemanticValidatorIngressAcceptanceRecord,
    *,
    certificate: SemanticValidatorHandoffPacketIngressCertificate | None = None,
    packet: SemanticValidatorHandoffPacket | None = None,
    proposal: ExperimentManifest | None = None,
    require_packet_evidence_on_proposal: bool = True,
) -> SemanticValidatorIngressAcceptanceRecordSummary:
    """Return a compact operator/CI summary for the terminal validator-ingress acceptance record."""
    report = verify_semantic_validator_ingress_acceptance_record(
        record,
        certificate=certificate,
        packet=packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=require_packet_evidence_on_proposal,
    )
    blocker_codes = [item.code for item in report.issues if item.severity == "BLOCKER"]
    warning_codes = [item.code for item in report.issues if item.severity != "BLOCKER"]
    return SemanticValidatorIngressAcceptanceRecordSummary(
        acceptance_id=record.acceptance_id,
        certificate_id=record.certificate_id,
        packet_id=record.packet_id,
        experiment_id=record.experiment_id,
        verified=report.verified,
        accepted_for_validator_adjudication=report.accepted_for_validator_adjudication,
        ready_for_validator_ingress=report.ready_for_validator_ingress,
        evidence_id=record.evidence_id,
        certificate_payload_checksum=record.certificate_payload_checksum,
        packet_payload_checksum=record.packet_payload_checksum,
        evidence_payload_checksum=record.evidence_payload_checksum,
        recommended_action=report.recommended_action,
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        issue_codes=report.issue_codes,
        issue_count=report.issue_count,
    )


__all__ = [
    "build_semantic_validator_ingress_acceptance_record",
    "verify_semantic_validator_ingress_acceptance_record",
    "summarize_semantic_validator_ingress_acceptance_record",
]
