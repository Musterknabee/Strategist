from __future__ import annotations

from pydantic import Field

from strategy_validator.contracts.semantic_core import NonEmptyString, SemanticBaseModel
from strategy_validator.contracts.semantic_release_handoff import (
    SemanticReleaseHandoffCertificateEvidenceSummary,
)

class SemanticValidatorHandoffPacket(SemanticBaseModel):
    """Portable packet containing the exact Evidence object intended for validator ingress."""

    schema_version: NonEmptyString = "semantic_validator_handoff_packet/v1"
    packet_id: NonEmptyString
    experiment_id: NonEmptyString
    evidence_id: NonEmptyString
    evidence_payload_checksum: NonEmptyString
    certificate_id: str | None = None
    certificate_payload_checksum: str | None = None
    handoff_allowed: bool
    evidence: dict
    evidence_summary: SemanticReleaseHandoffCertificateEvidenceSummary
    payload_checksum: NonEmptyString


class SemanticValidatorHandoffPacketIssue(SemanticBaseModel):
    """Verification issue for a validator handoff packet."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"


class SemanticValidatorHandoffPacketVerificationReport(SemanticBaseModel):
    """Verification report for the validator handoff packet."""

    schema_version: NonEmptyString = "semantic_validator_handoff_packet_verification/v1"
    packet_id: NonEmptyString
    experiment_id: NonEmptyString
    verified: bool
    handoff_allowed: bool
    evidence_id: NonEmptyString
    expected_payload_checksum: NonEmptyString
    observed_payload_checksum: NonEmptyString
    evidence_payload_checksum: NonEmptyString
    certificate_id: str | None = None
    certificate_payload_checksum: str | None = None
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[SemanticValidatorHandoffPacketIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString


class SemanticValidatorHandoffPacketSummary(SemanticBaseModel):
    """Smallest CI/operator status for the validator handoff packet."""

    schema_version: NonEmptyString = "semantic_validator_handoff_packet_summary/v1"
    packet_id: NonEmptyString
    experiment_id: NonEmptyString
    packet_verified: bool
    evidence_verified: bool
    handoff_allowed: bool
    evidence_id: NonEmptyString
    certificate_id: str | None = None
    packet_payload_checksum: NonEmptyString
    evidence_payload_checksum: NonEmptyString
    recommended_action: NonEmptyString
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    issue_codes: list[str] = Field(default_factory=list)
    issue_count: int = Field(ge=0)


class SemanticValidatorHandoffPacketIngressIssue(SemanticBaseModel):
    """Pre-adjudication validator-ingress issue for a semantic handoff packet."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"


class SemanticValidatorHandoffPacketIngressReport(SemanticBaseModel):
    """Pre-adjudication report proving a validator handoff packet is safe to ingest."""

    schema_version: NonEmptyString = "semantic_validator_handoff_packet_ingress_report/v1"
    packet_id: NonEmptyString
    experiment_id: NonEmptyString
    proposal_experiment_id: str | None = None
    packet_verified: bool
    evidence_verified: bool
    handoff_allowed: bool
    evidence_present_on_proposal: bool
    ready_for_validator_ingress: bool
    evidence_id: NonEmptyString
    evidence_payload_checksum: NonEmptyString
    packet_payload_checksum: NonEmptyString
    certificate_id: str | None = None
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[SemanticValidatorHandoffPacketIngressIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString


class SemanticValidatorHandoffPacketIngressSummary(SemanticBaseModel):
    """Smallest operator/CI summary for validator-ingress packet readiness."""

    schema_version: NonEmptyString = "semantic_validator_handoff_packet_ingress_summary/v1"
    packet_id: NonEmptyString
    experiment_id: NonEmptyString
    ready_for_validator_ingress: bool
    packet_verified: bool
    evidence_verified: bool
    handoff_allowed: bool
    evidence_present_on_proposal: bool
    evidence_id: NonEmptyString
    certificate_id: str | None = None
    packet_payload_checksum: NonEmptyString
    evidence_payload_checksum: NonEmptyString
    recommended_action: NonEmptyString
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    issue_codes: list[str] = Field(default_factory=list)
    issue_count: int = Field(ge=0)


class SemanticValidatorHandoffPacketIngressCertificate(SemanticBaseModel):
    """Portable certificate sealing validator-ingress packet readiness."""

    schema_version: NonEmptyString = "semantic_validator_handoff_packet_ingress_certificate/v1"
    certificate_id: NonEmptyString
    packet_id: NonEmptyString
    experiment_id: NonEmptyString
    ready_for_validator_ingress: bool
    evidence_id: NonEmptyString
    packet_payload_checksum: NonEmptyString
    evidence_payload_checksum: NonEmptyString
    ingress_report: SemanticValidatorHandoffPacketIngressReport
    issued_by: NonEmptyString = "operator"
    issue_reason: str = ""
    payload_checksum: NonEmptyString


class SemanticValidatorHandoffPacketIngressCertificateIssue(SemanticBaseModel):
    """Verification issue for a validator-ingress packet certificate."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"


class SemanticValidatorHandoffPacketIngressCertificateVerificationReport(SemanticBaseModel):
    """Verification report for a validator-ingress packet certificate."""

    schema_version: NonEmptyString = "semantic_validator_handoff_packet_ingress_certificate_verification/v1"
    certificate_id: NonEmptyString
    packet_id: NonEmptyString
    experiment_id: NonEmptyString
    verified: bool
    ready_for_validator_ingress: bool
    expected_payload_checksum: NonEmptyString
    observed_payload_checksum: NonEmptyString
    packet_payload_checksum: NonEmptyString
    evidence_payload_checksum: NonEmptyString
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[SemanticValidatorHandoffPacketIngressCertificateIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString


class SemanticValidatorHandoffPacketIngressCertificateSummary(SemanticBaseModel):
    """Smallest operator/CI summary for the validator-ingress certificate."""

    schema_version: NonEmptyString = "semantic_validator_handoff_packet_ingress_certificate_summary/v1"
    certificate_id: NonEmptyString
    packet_id: NonEmptyString
    experiment_id: NonEmptyString
    certificate_verified: bool
    ready_for_validator_ingress: bool
    packet_payload_checksum: NonEmptyString
    evidence_payload_checksum: NonEmptyString
    recommended_action: NonEmptyString
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    issue_codes: list[str] = Field(default_factory=list)
    issue_count: int = Field(ge=0)


__all__ = [
    "SemanticValidatorHandoffPacket",
    "SemanticValidatorHandoffPacketIssue",
    "SemanticValidatorHandoffPacketVerificationReport",
    "SemanticValidatorHandoffPacketSummary",
    "SemanticValidatorHandoffPacketIngressIssue",
    "SemanticValidatorHandoffPacketIngressReport",
    "SemanticValidatorHandoffPacketIngressSummary",
    "SemanticValidatorHandoffPacketIngressCertificate",
    "SemanticValidatorHandoffPacketIngressCertificateIssue",
    "SemanticValidatorHandoffPacketIngressCertificateVerificationReport",
    "SemanticValidatorHandoffPacketIngressCertificateSummary",
]
