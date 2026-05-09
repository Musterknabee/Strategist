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
from strategy_validator.application.research_integrity_validator_submission_packet import (
    summarize_semantic_validator_submission_packet,
    verify_semantic_validator_submission_packet,
)

_SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SCHEMA_VERSION = "semantic_validator_submission_packet_evidence/v1"
_SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SOURCE = "strategy_validator.application.research_integrity.semantic_validator_submission_packet_evidence"


def build_semantic_validator_submission_packet_evidence(
    submission_packet: SemanticValidatorSubmissionPacket,
) -> Evidence:
    """Wrap the terminal validator submission packet as ordinary validator Evidence.

    This is the final bridge into the normal adjudication evidence stream. It
    carries no write authority; the orchestrator still validates it as evidence
    before any ledger mutation path is reached.
    """
    summary = summarize_semantic_validator_submission_packet(submission_packet)
    payload: dict[str, Any] = {
        "schema_version": _SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SCHEMA_VERSION,
        "submission_packet": submission_packet.model_dump(mode="json"),
        "submission_packet_summary": summary.model_dump(mode="json"),
        "submission_packet_id": submission_packet.submission_packet_id,
        "submission_packet_payload_checksum": submission_packet.payload_checksum,
        "ready_for_validator_adjudication": summary.ready_for_validator_adjudication,
    }
    checksum = _sha256_payload(payload)
    return Evidence(
        evidence_id=f"semantic-validator-submission-packet-evidence-{submission_packet.experiment_id}-{checksum[:16]}",
        experiment_id=submission_packet.experiment_id,
        evidence_type=EvidenceType.TRIBUNAL_OPINION,
        payload=payload,
        source_module=_SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SOURCE,
        checksum=checksum,
    )


def verify_semantic_validator_submission_packet_evidence(
    evidence: Evidence,
    *,
    submission_packet: SemanticValidatorSubmissionPacket | None = None,
) -> SemanticValidatorSubmissionPacketEvidenceVerificationReport:
    """Verify Evidence wrapping a terminal semantic validator submission packet."""
    issues: list[SemanticValidatorSubmissionPacketEvidenceIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(SemanticValidatorSubmissionPacketEvidenceIssue(code=code, message=message, severity=severity))

    expected_checksum = _sha256_payload(evidence.payload)
    observed_checksum = evidence.checksum
    if observed_checksum != expected_checksum:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_CHECKSUM_MISMATCH", "Evidence checksum does not match canonical payload")
    if evidence.payload.get("schema_version") != _SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SCHEMA_VERSION:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SCHEMA_UNSUPPORTED", "unsupported submission-packet Evidence schema")
    if evidence.source_module != _SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SOURCE:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SOURCE_MISMATCH", "Evidence source_module is not the canonical submission-packet evidence builder")

    packet_id: str | None = None
    packet_checksum: str | None = None
    packet_ready = False
    try:
        embedded_packet = SemanticValidatorSubmissionPacket.model_validate(evidence.payload.get("submission_packet"))
        embedded_summary = SemanticValidatorSubmissionPacketSummary.model_validate(evidence.payload.get("submission_packet_summary"))
    except Exception:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_PAYLOAD_INVALID", "Evidence payload does not contain a valid embedded submission packet/summary")
        embedded_packet = None
        embedded_summary = None

    if embedded_packet is not None and embedded_summary is not None:
        packet_id = embedded_packet.submission_packet_id
        packet_checksum = embedded_packet.payload_checksum
        packet_report = verify_semantic_validator_submission_packet(embedded_packet)
        rebuilt_summary = summarize_semantic_validator_submission_packet(embedded_packet)
        packet_ready = bool(packet_report.ready_for_validator_adjudication)
        if evidence.experiment_id != embedded_packet.experiment_id:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_EXPERIMENT_MISMATCH", "Evidence experiment_id differs from embedded submission packet")
        if evidence.payload.get("submission_packet_id") != embedded_packet.submission_packet_id:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_PACKET_ID_DRIFT", "payload submission_packet_id differs from embedded packet")
        if evidence.payload.get("submission_packet_payload_checksum") != embedded_packet.payload_checksum:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_PACKET_CHECKSUM_DRIFT", "payload submission packet checksum differs from embedded packet")
        if evidence.payload.get("ready_for_validator_adjudication") is not packet_ready:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_READY_FLAG_DRIFT", "payload readiness flag differs from verified submission packet")
        if embedded_summary != rebuilt_summary:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SUMMARY_DRIFT", "embedded submission-packet summary differs from rebuilt summary")
        if not packet_report.verified:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_PACKET_INVALID", "embedded semantic validator submission packet failed verification")
        if not packet_ready:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_PACKET_NOT_READY", "embedded semantic validator submission packet is not ready for adjudication")
        if submission_packet is not None and submission_packet.model_dump(mode="json") != embedded_packet.model_dump(mode="json"):
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SOURCE_PACKET_DRIFT", "supplied source submission packet differs from embedded packet")

    verified = not any(item.severity == "BLOCKER" for item in issues)
    ready = bool(verified and packet_ready)
    return SemanticValidatorSubmissionPacketEvidenceVerificationReport(
        evidence_id=evidence.evidence_id,
        experiment_id=evidence.experiment_id,
        verified=verified,
        ready_for_validator_adjudication=ready,
        submission_packet_id=packet_id,
        submission_packet_payload_checksum=packet_checksum,
        expected_checksum=expected_checksum,
        observed_checksum=observed_checksum,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="ALLOW_SEMANTIC_VALIDATOR_SUBMISSION_EVIDENCE" if ready else "REBUILD_OR_BLOCK_SEMANTIC_VALIDATOR_SUBMISSION_EVIDENCE",
    )


def summarize_semantic_validator_submission_packet_evidence(
    evidence: Evidence,
    *,
    submission_packet: SemanticValidatorSubmissionPacket | None = None,
) -> SemanticValidatorSubmissionPacketEvidenceSummary:
    """Return a compact operator/CI view of validator submission-packet Evidence."""
    report = verify_semantic_validator_submission_packet_evidence(evidence, submission_packet=submission_packet)
    blocker_codes = [item.code for item in report.issues if item.severity == "BLOCKER"]
    warning_codes = [item.code for item in report.issues if item.severity != "BLOCKER"]
    return SemanticValidatorSubmissionPacketEvidenceSummary(
        evidence_id=report.evidence_id,
        experiment_id=report.experiment_id,
        evidence_verified=report.verified,
        ready_for_validator_adjudication=report.ready_for_validator_adjudication,
        submission_packet_id=report.submission_packet_id,
        submission_packet_payload_checksum=report.submission_packet_payload_checksum,
        evidence_payload_checksum=report.observed_checksum,
        recommended_action="HAND_OFF_SUBMISSION_PACKET_EVIDENCE_TO_VALIDATOR" if report.ready_for_validator_adjudication else "REBUILD_OR_BLOCK_SEMANTIC_VALIDATOR_SUBMISSION_EVIDENCE",
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        issue_codes=report.issue_codes,
        issue_count=report.issue_count,
    )


__all__ = [
    "build_semantic_validator_submission_packet_evidence",
    "verify_semantic_validator_submission_packet_evidence",
    "summarize_semantic_validator_submission_packet_evidence",
]
