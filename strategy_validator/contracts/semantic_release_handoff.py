from __future__ import annotations

from pydantic import Field

from strategy_validator.contracts.semantic_core import NonEmptyString, SemanticBaseModel
from strategy_validator.contracts.semantic_release_capsule import (
    SemanticAdjudicationReleaseDecisionRecordSummary,
)

class SemanticAdjudicationReleaseDecisionLedgerEntry(SemanticBaseModel):
    """Append-only entry in the semantic release decision ledger."""

    entry_index: int = Field(ge=0)
    decision_id: NonEmptyString
    capsule_id: NonEmptyString
    index_id: NonEmptyString
    bundle_id: NonEmptyString
    experiment_id: NonEmptyString
    decision: NonEmptyString
    decision_allowed: bool
    decided_by: NonEmptyString
    decision_payload_checksum: NonEmptyString
    previous_entry_checksum: str | None = None
    entry_checksum: NonEmptyString


class SemanticAdjudicationReleaseDecisionLedger(SemanticBaseModel):
    """Portable append-only ledger for terminal semantic release decision records.

    This ledger is not the canonical validator ledger. It is an operator/CI
    handoff ledger that chains terminal semantic release decision records before
    the proposal enters the validator authority path.
    """

    schema_version: NonEmptyString = "semantic_adjudication_release_decision_ledger/v1"
    ledger_id: NonEmptyString
    experiment_id: NonEmptyString
    entry_count: int = Field(ge=0)
    accepted_decision_count: int = Field(ge=0)
    blocked_decision_count: int = Field(ge=0)
    terminal_recommended_action: NonEmptyString
    entries: list[SemanticAdjudicationReleaseDecisionLedgerEntry] = Field(default_factory=list)
    payload_checksum: NonEmptyString


class SemanticAdjudicationReleaseDecisionLedgerIssue(SemanticBaseModel):
    """Verification issue for a semantic release decision ledger."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"
    decision_id: str | None = None


class SemanticAdjudicationReleaseDecisionLedgerVerificationReport(SemanticBaseModel):
    """Verification report for the append-only semantic release decision ledger."""

    schema_version: NonEmptyString = "semantic_adjudication_release_decision_ledger_verification/v1"
    ledger_id: NonEmptyString
    experiment_id: NonEmptyString
    verified: bool
    expected_payload_checksum: NonEmptyString
    observed_payload_checksum: NonEmptyString
    entry_count: int = Field(ge=0)
    accepted_decision_count: int = Field(ge=0)
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[SemanticAdjudicationReleaseDecisionLedgerIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString


class SemanticAdjudicationReleaseDecisionLedgerSummary(SemanticBaseModel):
    """Compact operator/CI status summary for a semantic release decision ledger."""

    schema_version: NonEmptyString = "semantic_adjudication_release_decision_ledger_summary/v1"
    ledger_id: NonEmptyString
    experiment_id: NonEmptyString
    ledger_verified: bool
    entry_count: int = Field(ge=0)
    accepted_decision_count: int = Field(ge=0)
    blocked_decision_count: int = Field(ge=0)
    terminal_decision_id: str | None = None
    terminal_decision: str | None = None
    terminal_decision_allowed: bool = False
    terminal_recommended_action: NonEmptyString
    recommended_action: NonEmptyString
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    ledger_issue_codes: list[str] = Field(default_factory=list)
    payload_checksum: NonEmptyString
    issue_count: int = Field(ge=0)


class SemanticAdjudicationReleaseHandoffCertificate(SemanticBaseModel):
    """Terminal certificate for handing a semantic release decision ledger to validator adjudication.

    This is a compact, portable artifact intended for CI and operators. It does
    not mutate the canonical validator ledger; it seals the terminal release
    decision-ledger summary immediately before handoff.
    """

    schema_version: NonEmptyString = "semantic_adjudication_release_handoff_certificate/v1"
    certificate_id: NonEmptyString
    ledger_id: NonEmptyString
    experiment_id: NonEmptyString
    terminal_decision_id: str | None = None
    terminal_decision: str | None = None
    handoff_allowed: bool
    ledger_payload_checksum: NonEmptyString
    ledger_summary: SemanticAdjudicationReleaseDecisionLedgerSummary
    issued_by: NonEmptyString
    issue_reason: str | None = None
    payload_checksum: NonEmptyString


class SemanticAdjudicationReleaseHandoffCertificateIssue(SemanticBaseModel):
    """Verification issue for a terminal semantic handoff certificate."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"


class SemanticAdjudicationReleaseHandoffCertificateVerificationReport(SemanticBaseModel):
    """Verification report for a terminal semantic handoff certificate."""

    schema_version: NonEmptyString = "semantic_adjudication_release_handoff_certificate_verification/v1"
    certificate_id: NonEmptyString
    ledger_id: NonEmptyString
    experiment_id: NonEmptyString
    verified: bool
    handoff_allowed: bool
    expected_payload_checksum: NonEmptyString
    observed_payload_checksum: NonEmptyString
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[SemanticAdjudicationReleaseHandoffCertificateIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString


class SemanticAdjudicationReleaseHandoffCertificateSummary(SemanticBaseModel):
    """Smallest terminal status object for CI/operator handoff decisions."""

    schema_version: NonEmptyString = "semantic_adjudication_release_handoff_certificate_summary/v1"
    certificate_id: NonEmptyString
    ledger_id: NonEmptyString
    experiment_id: NonEmptyString
    certificate_verified: bool
    ledger_verified: bool
    handoff_allowed: bool
    terminal_decision_id: str | None = None
    terminal_decision: str | None = None
    recommended_action: NonEmptyString
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    certificate_issue_codes: list[str] = Field(default_factory=list)
    ledger_payload_checksum: NonEmptyString
    certificate_payload_checksum: NonEmptyString
    issue_count: int = Field(ge=0)


class SemanticReleaseHandoffCertificateEvidenceIssue(SemanticBaseModel):
    """Verification issue for validator-facing semantic handoff certificate evidence."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"


class SemanticReleaseHandoffCertificateEvidenceVerificationReport(SemanticBaseModel):
    """Verification report for Evidence wrapping a semantic release handoff certificate."""

    schema_version: NonEmptyString = "semantic_release_handoff_certificate_evidence_verification/v1"
    evidence_id: NonEmptyString
    experiment_id: NonEmptyString
    verified: bool
    handoff_allowed: bool
    expected_checksum: NonEmptyString
    observed_checksum: NonEmptyString
    certificate_id: str | None = None
    certificate_payload_checksum: str | None = None
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[SemanticReleaseHandoffCertificateEvidenceIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString


class SemanticReleaseHandoffCertificateEvidenceSummary(SemanticBaseModel):
    """Compact terminal status for validator-facing handoff certificate Evidence."""

    schema_version: NonEmptyString = "semantic_release_handoff_certificate_evidence_summary/v1"
    evidence_id: NonEmptyString
    experiment_id: NonEmptyString
    evidence_verified: bool
    handoff_allowed: bool
    certificate_id: str | None = None
    certificate_payload_checksum: str | None = None
    evidence_payload_checksum: NonEmptyString
    recommended_action: NonEmptyString
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    issue_codes: list[str] = Field(default_factory=list)
    issue_count: int = Field(ge=0)


