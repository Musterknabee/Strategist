from __future__ import annotations

from pydantic import Field

from strategy_validator.contracts.semantic_core import NonEmptyString, SemanticBaseModel
from strategy_validator.contracts.semantic_bundle_release_index import (
    SemanticAdjudicationBundleReleaseIndexVerificationReport,
)

class SemanticAdjudicationReleaseCapsule(SemanticBaseModel):
    """Final portable capsule for operator/CI semantic adjudication release handoff.

    The capsule wraps the release index and the verification decision made
    against the current bundle/manifest/proposal context. It is deliberately
    small and checksummed so it can be archived as the final semantic-lane
    release handoff receipt.
    """

    schema_version: NonEmptyString = "semantic_adjudication_release_capsule/v1"
    capsule_id: NonEmptyString
    index_id: NonEmptyString
    bundle_id: NonEmptyString
    experiment_id: NonEmptyString
    proposal_digest: NonEmptyString
    index_payload_checksum: NonEmptyString
    release_preflight_recommended_action: NonEmptyString
    ready_for_adjudication: bool
    index_verification: SemanticAdjudicationBundleReleaseIndexVerificationReport
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    payload_checksum: NonEmptyString


class SemanticAdjudicationReleaseCapsuleIssue(SemanticBaseModel):
    """Verification issue for the semantic adjudication release capsule."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"


class SemanticAdjudicationReleaseCapsuleVerificationReport(SemanticBaseModel):
    """Verification report for the final semantic release capsule."""

    schema_version: NonEmptyString = "semantic_adjudication_release_capsule_verification/v1"
    capsule_id: NonEmptyString
    index_id: NonEmptyString
    bundle_id: NonEmptyString
    experiment_id: NonEmptyString
    verified: bool
    expected_payload_checksum: NonEmptyString
    observed_payload_checksum: NonEmptyString
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[SemanticAdjudicationReleaseCapsuleIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString


class SemanticAdjudicationReleaseCapsuleSummary(SemanticBaseModel):
    """Compact operator/CI status summary for the final semantic release capsule."""

    schema_version: NonEmptyString = "semantic_adjudication_release_capsule_summary/v1"
    capsule_id: NonEmptyString
    index_id: NonEmptyString
    bundle_id: NonEmptyString
    experiment_id: NonEmptyString
    capsule_verified: bool
    embedded_index_verified: bool
    ready_for_adjudication: bool
    release_preflight_recommended_action: NonEmptyString
    recommended_action: NonEmptyString
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    capsule_issue_codes: list[str] = Field(default_factory=list)
    index_issue_codes: list[str] = Field(default_factory=list)
    index_payload_checksum: NonEmptyString
    capsule_payload_checksum: NonEmptyString
    issue_count: int = Field(ge=0)


class SemanticAdjudicationReleaseDecisionRecord(SemanticBaseModel):
    """Operator decision record over a verified semantic release capsule.

    This is the terminal human/CI handoff receipt. It does not adjudicate or
    mutate the ledger; it records whether the sealed semantic capsule is being
    accepted for validator handoff or blocked for rebuild.
    """

    schema_version: NonEmptyString = "semantic_adjudication_release_decision_record/v1"
    decision_id: NonEmptyString
    capsule_id: NonEmptyString
    index_id: NonEmptyString
    bundle_id: NonEmptyString
    experiment_id: NonEmptyString
    proposal_digest: NonEmptyString
    capsule_payload_checksum: NonEmptyString
    capsule_summary: SemanticAdjudicationReleaseCapsuleSummary
    decision: NonEmptyString
    decision_allowed: bool
    decided_by: NonEmptyString = "operator"
    decision_reason: str | None = None
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    payload_checksum: NonEmptyString


class SemanticAdjudicationReleaseDecisionRecordIssue(SemanticBaseModel):
    """Verification issue for a semantic release decision record."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"


class SemanticAdjudicationReleaseDecisionRecordVerificationReport(SemanticBaseModel):
    """Verification report for the terminal semantic release decision record."""

    schema_version: NonEmptyString = "semantic_adjudication_release_decision_record_verification/v1"
    decision_id: NonEmptyString
    capsule_id: NonEmptyString
    experiment_id: NonEmptyString
    verified: bool
    expected_payload_checksum: NonEmptyString
    observed_payload_checksum: NonEmptyString
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[SemanticAdjudicationReleaseDecisionRecordIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString


class SemanticAdjudicationReleaseDecisionRecordSummary(SemanticBaseModel):
    """Compact terminal operator/CI status summary for a release decision record."""

    schema_version: NonEmptyString = "semantic_adjudication_release_decision_record_summary/v1"
    decision_id: NonEmptyString
    capsule_id: NonEmptyString
    index_id: NonEmptyString
    bundle_id: NonEmptyString
    experiment_id: NonEmptyString
    decision: NonEmptyString
    decision_allowed: bool
    record_verified: bool
    capsule_ready_for_adjudication: bool
    capsule_summary_recommended_action: NonEmptyString
    recommended_action: NonEmptyString
    decided_by: NonEmptyString
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    record_issue_codes: list[str] = Field(default_factory=list)
    capsule_payload_checksum: NonEmptyString
    decision_payload_checksum: NonEmptyString
    issue_count: int = Field(ge=0)


