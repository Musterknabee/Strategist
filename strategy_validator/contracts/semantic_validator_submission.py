from __future__ import annotations

from pydantic import Field

from strategy_validator.contracts.semantic_core import NonEmptyString, SemanticBaseModel
from strategy_validator.contracts.semantic_validator_handoff import (
    SemanticValidatorHandoffPacketIngressCertificateSummary,
)

class SemanticValidatorIngressAcceptanceRecord(SemanticBaseModel):
    """Terminal operator/CI record accepting a certified semantic packet for validator adjudication."""

    schema_version: NonEmptyString = "semantic_validator_ingress_acceptance_record/v1"
    acceptance_id: NonEmptyString
    certificate_id: NonEmptyString
    packet_id: NonEmptyString
    experiment_id: NonEmptyString
    evidence_id: NonEmptyString
    ready_for_validator_ingress: bool
    accepted_for_validator_adjudication: bool
    certificate_payload_checksum: NonEmptyString
    packet_payload_checksum: NonEmptyString
    evidence_payload_checksum: NonEmptyString
    certificate_summary: SemanticValidatorHandoffPacketIngressCertificateSummary
    accepted_by: NonEmptyString = "operator"
    acceptance_reason: str = ""
    payload_checksum: NonEmptyString

class SemanticValidatorIngressAcceptanceRecordIssue(SemanticBaseModel):
    """Verification issue for a terminal validator-ingress acceptance record."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"

class SemanticValidatorIngressAcceptanceRecordVerificationReport(SemanticBaseModel):
    """Verification report for a terminal validator-ingress acceptance record."""

    schema_version: NonEmptyString = "semantic_validator_ingress_acceptance_record_verification/v1"
    acceptance_id: NonEmptyString
    certificate_id: NonEmptyString
    packet_id: NonEmptyString
    experiment_id: NonEmptyString
    verified: bool
    accepted_for_validator_adjudication: bool
    ready_for_validator_ingress: bool
    expected_payload_checksum: NonEmptyString
    observed_payload_checksum: NonEmptyString
    certificate_payload_checksum: NonEmptyString
    packet_payload_checksum: NonEmptyString
    evidence_payload_checksum: NonEmptyString
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[SemanticValidatorIngressAcceptanceRecordIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString

class SemanticValidatorIngressAcceptanceRecordSummary(SemanticBaseModel):
    """Smallest operator/CI summary for terminal validator-ingress acceptance."""

    schema_version: NonEmptyString = "semantic_validator_ingress_acceptance_record_summary/v1"
    acceptance_id: NonEmptyString
    certificate_id: NonEmptyString
    packet_id: NonEmptyString
    experiment_id: NonEmptyString
    verified: bool
    accepted_for_validator_adjudication: bool
    ready_for_validator_ingress: bool
    evidence_id: NonEmptyString
    certificate_payload_checksum: NonEmptyString
    packet_payload_checksum: NonEmptyString
    evidence_payload_checksum: NonEmptyString
    recommended_action: NonEmptyString
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    issue_codes: list[str] = Field(default_factory=list)
    issue_count: int = Field(ge=0)

class SemanticValidatorIngressAcceptanceLedgerEntry(SemanticBaseModel):
    """Append-only entry in the terminal semantic validator-ingress acceptance ledger."""

    entry_index: int = Field(ge=0)
    acceptance_id: NonEmptyString
    certificate_id: NonEmptyString
    packet_id: NonEmptyString
    experiment_id: NonEmptyString
    evidence_id: NonEmptyString
    accepted_for_validator_adjudication: bool
    ready_for_validator_ingress: bool
    accepted_by: NonEmptyString
    acceptance_payload_checksum: NonEmptyString
    previous_entry_checksum: str | None = None
    entry_checksum: NonEmptyString

class SemanticValidatorIngressAcceptanceLedger(SemanticBaseModel):
    """Portable append-only ledger of terminal validator-ingress acceptance records.

    This ledger is separate from the canonical validator ledger. It provides a
    compact operator/CI receipt chain proving which semantic handoff acceptance
    record was terminal before validator adjudication was invoked.
    """

    schema_version: NonEmptyString = "semantic_validator_ingress_acceptance_ledger/v1"
    ledger_id: NonEmptyString
    experiment_id: NonEmptyString
    entry_count: int = Field(ge=0)
    accepted_entry_count: int = Field(ge=0)
    rejected_entry_count: int = Field(ge=0)
    terminal_recommended_action: NonEmptyString
    entries: list[SemanticValidatorIngressAcceptanceLedgerEntry] = Field(default_factory=list)
    payload_checksum: NonEmptyString

class SemanticValidatorIngressAcceptanceLedgerIssue(SemanticBaseModel):
    """Verification issue for the terminal validator-ingress acceptance ledger."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"
    acceptance_id: str | None = None

class SemanticValidatorIngressAcceptanceLedgerVerificationReport(SemanticBaseModel):
    """Verification report for a terminal validator-ingress acceptance ledger."""

    schema_version: NonEmptyString = "semantic_validator_ingress_acceptance_ledger_verification/v1"
    ledger_id: NonEmptyString
    experiment_id: NonEmptyString
    verified: bool
    expected_payload_checksum: NonEmptyString
    observed_payload_checksum: NonEmptyString
    entry_count: int = Field(ge=0)
    accepted_entry_count: int = Field(ge=0)
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[SemanticValidatorIngressAcceptanceLedgerIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString

class SemanticValidatorIngressAcceptanceLedgerSummary(SemanticBaseModel):
    """Compact operator/CI summary for terminal validator-ingress acceptance ledger state."""

    schema_version: NonEmptyString = "semantic_validator_ingress_acceptance_ledger_summary/v1"
    ledger_id: NonEmptyString
    experiment_id: NonEmptyString
    ledger_verified: bool
    entry_count: int = Field(ge=0)
    accepted_entry_count: int = Field(ge=0)
    rejected_entry_count: int = Field(ge=0)
    terminal_acceptance_id: str | None = None
    terminal_packet_id: str | None = None
    terminal_evidence_id: str | None = None
    terminal_accepted_for_validator_adjudication: bool = False
    terminal_ready_for_validator_ingress: bool = False
    terminal_recommended_action: NonEmptyString
    recommended_action: NonEmptyString
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    ledger_issue_codes: list[str] = Field(default_factory=list)
    payload_checksum: NonEmptyString
    issue_count: int = Field(ge=0)

class SemanticValidatorSubmissionPacket(SemanticBaseModel):
    """Terminal packet submitted to the validator after semantic ingress acceptance.

    This remains an operator/release artifact. It carries the acceptance-ledger
    summary and the terminal validator-facing evidence reference, but does not
    grant ledger write authority or bypass orchestrator gates.
    """

    schema_version: NonEmptyString = "semantic_validator_submission_packet/v1"
    submission_packet_id: NonEmptyString
    acceptance_ledger_id: NonEmptyString
    experiment_id: NonEmptyString
    terminal_acceptance_id: NonEmptyString
    terminal_packet_id: NonEmptyString
    terminal_evidence_id: NonEmptyString
    acceptance_ledger_payload_checksum: NonEmptyString
    acceptance_ledger_summary: SemanticValidatorIngressAcceptanceLedgerSummary
    submitted_by: NonEmptyString
    submission_reason: str = ""
    ready_for_validator_adjudication: bool
    payload_checksum: NonEmptyString

class SemanticValidatorSubmissionPacketIssue(SemanticBaseModel):
    """Verification issue for a terminal semantic validator submission packet."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"

class SemanticValidatorSubmissionPacketVerificationReport(SemanticBaseModel):
    """Verification report for a terminal semantic validator submission packet."""

    schema_version: NonEmptyString = "semantic_validator_submission_packet_verification/v1"
    submission_packet_id: NonEmptyString
    acceptance_ledger_id: NonEmptyString
    experiment_id: NonEmptyString
    verified: bool
    ready_for_validator_adjudication: bool
    expected_payload_checksum: NonEmptyString
    observed_payload_checksum: NonEmptyString
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[SemanticValidatorSubmissionPacketIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString

class SemanticValidatorSubmissionPacketSummary(SemanticBaseModel):
    """Compact operator/CI summary for terminal semantic validator submission."""

    schema_version: NonEmptyString = "semantic_validator_submission_packet_summary/v1"
    submission_packet_id: NonEmptyString
    acceptance_ledger_id: NonEmptyString
    experiment_id: NonEmptyString
    submission_verified: bool
    ready_for_validator_adjudication: bool
    terminal_acceptance_id: NonEmptyString
    terminal_packet_id: NonEmptyString
    terminal_evidence_id: NonEmptyString
    acceptance_ledger_payload_checksum: NonEmptyString
    submission_payload_checksum: NonEmptyString
    submitted_by: NonEmptyString
    recommended_action: NonEmptyString
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    issue_codes: list[str] = Field(default_factory=list)
    issue_count: int = Field(ge=0)

class SemanticValidatorSubmissionPacketEvidenceIssue(SemanticBaseModel):
    """Verification issue for validator submission-packet Evidence."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"

class SemanticValidatorSubmissionPacketEvidenceVerificationReport(SemanticBaseModel):
    """Verification report for Evidence wrapping the terminal validator submission packet."""

    schema_version: NonEmptyString = "semantic_validator_submission_packet_evidence_verification/v1"
    evidence_id: NonEmptyString
    experiment_id: NonEmptyString
    verified: bool
    ready_for_validator_adjudication: bool
    submission_packet_id: str | None = None
    submission_packet_payload_checksum: str | None = None
    expected_checksum: NonEmptyString
    observed_checksum: NonEmptyString
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[SemanticValidatorSubmissionPacketEvidenceIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString

class SemanticValidatorSubmissionPacketEvidenceSummary(SemanticBaseModel):
    """Compact operator/CI summary for terminal submission-packet Evidence."""

    schema_version: NonEmptyString = "semantic_validator_submission_packet_evidence_summary/v1"
    evidence_id: NonEmptyString
    experiment_id: NonEmptyString
    evidence_verified: bool
    ready_for_validator_adjudication: bool
    submission_packet_id: str | None = None
    submission_packet_payload_checksum: str | None = None
    evidence_payload_checksum: NonEmptyString
    recommended_action: NonEmptyString
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    issue_codes: list[str] = Field(default_factory=list)
    issue_count: int = Field(ge=0)

class SemanticValidatorSubmissionReadinessIssue(SemanticBaseModel):
    """Issue emitted by the final proposal-level semantic validator submission readiness check."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"

class SemanticValidatorSubmissionReadinessReport(SemanticBaseModel):
    """End-to-end readiness report for handing a semantic proposal to validator adjudication."""

    schema_version: NonEmptyString = "semantic_validator_submission_readiness/v1"
    experiment_id: NonEmptyString
    ready_for_validator_adjudication: bool
    submission_evidence_present: bool
    submission_evidence_id: str | None = None
    submission_evidence_checksum: str | None = None
    submission_packet_id: str | None = None
    submission_packet_payload_checksum: str | None = None
    evidence_attached_to_proposal: bool
    require_submission_packet_evidence: bool
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[SemanticValidatorSubmissionReadinessIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString

class SemanticValidatorSubmissionReadinessSummary(SemanticBaseModel):
    """Compact operator/CI summary for final semantic validator submission readiness."""

    schema_version: NonEmptyString = "semantic_validator_submission_readiness_summary/v1"
    experiment_id: NonEmptyString
    ready_for_validator_adjudication: bool
    submission_evidence_present: bool
    evidence_attached_to_proposal: bool
    submission_evidence_id: str | None = None
    submission_packet_id: str | None = None
    recommended_action: NonEmptyString
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    issue_codes: list[str] = Field(default_factory=list)
    issue_count: int = Field(ge=0)

__all__ = ['SemanticValidatorIngressAcceptanceRecord', 'SemanticValidatorIngressAcceptanceRecordIssue', 'SemanticValidatorIngressAcceptanceRecordVerificationReport', 'SemanticValidatorIngressAcceptanceRecordSummary', 'SemanticValidatorIngressAcceptanceLedgerEntry', 'SemanticValidatorIngressAcceptanceLedger', 'SemanticValidatorIngressAcceptanceLedgerIssue', 'SemanticValidatorIngressAcceptanceLedgerVerificationReport', 'SemanticValidatorIngressAcceptanceLedgerSummary', 'SemanticValidatorSubmissionPacket', 'SemanticValidatorSubmissionPacketIssue', 'SemanticValidatorSubmissionPacketVerificationReport', 'SemanticValidatorSubmissionPacketSummary', 'SemanticValidatorSubmissionPacketEvidenceIssue', 'SemanticValidatorSubmissionPacketEvidenceVerificationReport', 'SemanticValidatorSubmissionPacketEvidenceSummary', 'SemanticValidatorSubmissionReadinessIssue', 'SemanticValidatorSubmissionReadinessReport', 'SemanticValidatorSubmissionReadinessSummary']
