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
from strategy_validator.application.research_integrity_validator_submission_acceptance_ledger import (
    summarize_semantic_validator_ingress_acceptance_ledger,
)

def _semantic_validator_submission_packet_checksum_payload(
    packet: SemanticValidatorSubmissionPacket,
) -> dict[str, Any]:
    payload = packet.model_dump(mode="json")
    payload.pop("payload_checksum", None)
    return payload


def build_semantic_validator_submission_packet(
    acceptance_ledger: SemanticValidatorIngressAcceptanceLedger,
    *,
    submitted_by: str = "operator",
    submission_reason: str = "",
    records: list[SemanticValidatorIngressAcceptanceRecord] | None = None,
) -> SemanticValidatorSubmissionPacket:
    """Build the terminal packet an operator/CI hands to validator adjudication.

    The packet is intentionally evidence-only: it seals the accepted ingress
    ledger summary and terminal Evidence reference, but it does not write to the
    canonical validator ledger or grant authority.
    """
    summary = summarize_semantic_validator_ingress_acceptance_ledger(
        acceptance_ledger,
        records=records,
    )
    terminal_acceptance_id = summary.terminal_acceptance_id or "none"
    terminal_packet_id = summary.terminal_packet_id or "none"
    terminal_evidence_id = summary.terminal_evidence_id or "none"
    ready = summary.recommended_action == "SUBMIT_TERMINAL_ACCEPTED_PACKET_TO_VALIDATOR"
    base = SemanticValidatorSubmissionPacket(
        submission_packet_id=f"semantic-validator-submission-packet-{acceptance_ledger.experiment_id}-{acceptance_ledger.payload_checksum[:16]}",
        acceptance_ledger_id=acceptance_ledger.ledger_id,
        experiment_id=acceptance_ledger.experiment_id,
        terminal_acceptance_id=terminal_acceptance_id,
        terminal_packet_id=terminal_packet_id,
        terminal_evidence_id=terminal_evidence_id,
        acceptance_ledger_payload_checksum=acceptance_ledger.payload_checksum,
        acceptance_ledger_summary=summary,
        submitted_by=submitted_by,
        submission_reason=submission_reason,
        ready_for_validator_adjudication=ready,
        payload_checksum="pending",
    )
    return base.model_copy(
        update={"payload_checksum": _sha256_payload(_semantic_validator_submission_packet_checksum_payload(base))}
    )


def verify_semantic_validator_submission_packet(
    submission_packet: SemanticValidatorSubmissionPacket,
    *,
    acceptance_ledger: SemanticValidatorIngressAcceptanceLedger | None = None,
    records: list[SemanticValidatorIngressAcceptanceRecord] | None = None,
) -> SemanticValidatorSubmissionPacketVerificationReport:
    """Verify a terminal semantic validator submission packet."""
    issues: list[SemanticValidatorSubmissionPacketIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(SemanticValidatorSubmissionPacketIssue(code=code, message=message, severity=severity))

    observed_checksum = submission_packet.payload_checksum
    expected_checksum = _sha256_payload(_semantic_validator_submission_packet_checksum_payload(submission_packet))
    if observed_checksum != expected_checksum:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_CHECKSUM_MISMATCH", "submission packet payload checksum does not match canonical payload")
    if submission_packet.schema_version != "semantic_validator_submission_packet/v1":
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_SCHEMA_VERSION_UNSUPPORTED", "unsupported semantic validator submission packet schema version")
    if not submission_packet.ready_for_validator_adjudication:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_NOT_READY", "submission packet is not ready for validator adjudication")
    if submission_packet.acceptance_ledger_summary.recommended_action != "SUBMIT_TERMINAL_ACCEPTED_PACKET_TO_VALIDATOR":
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_LEDGER_SUMMARY_NOT_HANDOFF_READY", "embedded acceptance-ledger summary is not terminal-handoff ready")
    if submission_packet.acceptance_ledger_summary.payload_checksum != submission_packet.acceptance_ledger_payload_checksum:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_LEDGER_CHECKSUM_DRIFT", "embedded acceptance-ledger summary checksum differs from packet ledger checksum")
    if submission_packet.acceptance_ledger_summary.terminal_acceptance_id != submission_packet.terminal_acceptance_id:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_ACCEPTANCE_ID_DRIFT", "terminal acceptance id differs from embedded ledger summary")
    if submission_packet.acceptance_ledger_summary.terminal_packet_id != submission_packet.terminal_packet_id:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_PACKET_ID_DRIFT", "terminal packet id differs from embedded ledger summary")
    if submission_packet.acceptance_ledger_summary.terminal_evidence_id != submission_packet.terminal_evidence_id:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_ID_DRIFT", "terminal evidence id differs from embedded ledger summary")

    if acceptance_ledger is not None:
        rebuilt = build_semantic_validator_submission_packet(
            acceptance_ledger,
            submitted_by=submission_packet.submitted_by,
            submission_reason=submission_packet.submission_reason,
            records=records,
        )
        if submission_packet.acceptance_ledger_id != acceptance_ledger.ledger_id:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_LEDGER_ID_MISMATCH", "packet ledger id differs from supplied acceptance ledger")
        if submission_packet.experiment_id != acceptance_ledger.experiment_id:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EXPERIMENT_MISMATCH", "packet experiment id differs from supplied acceptance ledger")
        if submission_packet.acceptance_ledger_payload_checksum != acceptance_ledger.payload_checksum:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_LEDGER_PAYLOAD_CHECKSUM_DRIFT", "packet ledger checksum differs from supplied acceptance ledger")
        if submission_packet.acceptance_ledger_summary != rebuilt.acceptance_ledger_summary:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_LEDGER_SUMMARY_DRIFT", "embedded acceptance-ledger summary differs from rebuilt summary")
        if submission_packet.payload_checksum != rebuilt.payload_checksum:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_REBUILT_CHECKSUM_DRIFT", "packet checksum differs from packet rebuilt from supplied ledger")

    verified = not any(item.severity == "BLOCKER" for item in issues)
    ready = bool(verified and submission_packet.ready_for_validator_adjudication)
    return SemanticValidatorSubmissionPacketVerificationReport(
        submission_packet_id=submission_packet.submission_packet_id,
        acceptance_ledger_id=submission_packet.acceptance_ledger_id,
        experiment_id=submission_packet.experiment_id,
        verified=verified,
        ready_for_validator_adjudication=ready,
        expected_payload_checksum=expected_checksum,
        observed_payload_checksum=observed_checksum,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="SUBMIT_SEMANTIC_VALIDATOR_PACKET_TO_ADJUDICATION" if ready else "REBUILD_OR_BLOCK_SEMANTIC_VALIDATOR_SUBMISSION_PACKET",
    )


def summarize_semantic_validator_submission_packet(
    submission_packet: SemanticValidatorSubmissionPacket,
    *,
    acceptance_ledger: SemanticValidatorIngressAcceptanceLedger | None = None,
    records: list[SemanticValidatorIngressAcceptanceRecord] | None = None,
) -> SemanticValidatorSubmissionPacketSummary:
    """Build a compact terminal status summary for validator submission."""
    report = verify_semantic_validator_submission_packet(
        submission_packet,
        acceptance_ledger=acceptance_ledger,
        records=records,
    )
    blocker_codes = [item.code for item in report.issues if item.severity == "BLOCKER"]
    warning_codes = [item.code for item in report.issues if item.severity != "BLOCKER"]
    return SemanticValidatorSubmissionPacketSummary(
        submission_packet_id=submission_packet.submission_packet_id,
        acceptance_ledger_id=submission_packet.acceptance_ledger_id,
        experiment_id=submission_packet.experiment_id,
        submission_verified=report.verified,
        ready_for_validator_adjudication=report.ready_for_validator_adjudication,
        terminal_acceptance_id=submission_packet.terminal_acceptance_id,
        terminal_packet_id=submission_packet.terminal_packet_id,
        terminal_evidence_id=submission_packet.terminal_evidence_id,
        acceptance_ledger_payload_checksum=submission_packet.acceptance_ledger_payload_checksum,
        submission_payload_checksum=submission_packet.payload_checksum,
        submitted_by=submission_packet.submitted_by,
        recommended_action=report.recommended_action,
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        issue_codes=report.issue_codes,
        issue_count=report.issue_count,
    )


_SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SCHEMA_VERSION = "semantic_validator_submission_packet_evidence/v1"
_SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SOURCE = "strategy_validator.application.research_integrity.semantic_validator_submission_packet_evidence"


__all__ = [
    "build_semantic_validator_submission_packet",
    "verify_semantic_validator_submission_packet",
    "summarize_semantic_validator_submission_packet",
]
