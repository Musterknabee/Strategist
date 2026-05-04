from __future__ import annotations

from pydantic import Field

from strategy_validator.contracts.semantic_core import NonEmptyString, SemanticBaseModel

class SemanticResearchIntegrityIssue(SemanticBaseModel):
    """Issue emitted by proposal-level semantic research integrity verification."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"
    evidence_id: str | None = None

class SemanticResearchIntegrityReport(SemanticBaseModel):
    """Proposal-level verification report for attached semantic research evidence."""

    schema_version: NonEmptyString = "semantic_research_integrity/v1"
    experiment_id: NonEmptyString
    verified: bool
    semantic_evidence_count: int = Field(ge=0)
    data_spine_seal_present: bool
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[SemanticResearchIntegrityIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString

class SemanticResearchAdjudicationGateSummary(SemanticBaseModel):
    """Compact operator summary for the semantic research adjudication gate."""

    schema_version: NonEmptyString = "semantic_research_adjudication_gate_summary/v1"
    experiment_id: NonEmptyString
    gate_name: NonEmptyString = "SemanticResearchIntegrity"
    gate_passed: bool
    gate_reason: str | None = None
    recommended_action: NonEmptyString
    semantic_lane_present: bool
    semantic_artifact_count: int = Field(ge=0)
    semantic_evidence_count: int = Field(ge=0)
    data_spine_seal_present: bool
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    issue_count: int = Field(ge=0)

class SemanticResearchGateArtifact(SemanticBaseModel):
    """Machine-readable artifact sealing the semantic adjudication gate summary."""

    schema_version: NonEmptyString = "semantic_research_gate_artifact/v1"
    artifact_id: NonEmptyString
    experiment_id: NonEmptyString
    proposal_digest: NonEmptyString
    summary: SemanticResearchAdjudicationGateSummary
    semantic_evidence_checksums: list[str] = Field(default_factory=list)
    data_spine_fingerprint: str | None = None
    payload_checksum: NonEmptyString

class SemanticResearchGateArtifactIssue(SemanticBaseModel):
    """Verification issue for a semantic adjudication gate artifact."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"

class SemanticResearchGateArtifactVerificationReport(SemanticBaseModel):
    """Verification report for a semantic adjudication gate artifact."""

    schema_version: NonEmptyString = "semantic_research_gate_artifact_verification/v1"
    artifact_id: NonEmptyString
    experiment_id: NonEmptyString
    verified: bool
    expected_payload_checksum: NonEmptyString
    observed_payload_checksum: NonEmptyString
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[SemanticResearchGateArtifactIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString

class SemanticAdjudicationReadinessIssue(SemanticBaseModel):
    """Issue emitted by the final semantic lane readiness preflight before adjudication."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"

class SemanticAdjudicationReadinessReport(SemanticBaseModel):
    """Operator-facing readiness report for handing a proposal to adjudication."""

    schema_version: NonEmptyString = "semantic_adjudication_readiness/v1"
    experiment_id: NonEmptyString
    ready_for_adjudication: bool
    semantic_lane_present: bool
    gate_passed: bool
    gate_artifact_required: bool
    gate_artifact_present: bool
    gate_artifact_verified: bool | None = None
    gate_artifact_id: str | None = None
    gate_artifact_checksum: str | None = None
    semantic_summary: SemanticResearchAdjudicationGateSummary
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    issue_count: int = Field(ge=0)
    issues: list[SemanticAdjudicationReadinessIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString

