from __future__ import annotations

from pydantic import Field

from strategy_validator.contracts.data_spine import PITJoinProvenance
from strategy_validator.contracts.semantic_core import NonEmptyString, SemanticBaseModel

class FeatureFactoryArtifact(SemanticBaseModel):
    """Final typed contract for FeatureFactory ingestion. Neutral and shared."""
    event_id: NonEmptyString
    forensic_status: NonEmptyString
    novelty_score: float = Field(ge=0.0, le=1.0)
    polarity_score: float = Field(ge=-1.0, le=1.0)
    belief_conflict: float = Field(ge=0.0, le=1.0)
    evidence_density: float = Field(ge=0.0, le=1.0)
    abstain_flag: bool = Field(default=False)
    metadata: dict = Field(default_factory=dict)

class SemanticFeatureRow(SemanticBaseModel):
    """Point-in-time feature row emitted by the semantic feature factory.

    Abstained tribunal artifacts preserve row lineage while setting score
    features to NaN so downstream joins can distinguish lawful missingness
    from zero-valued signal.
    """

    event_id: NonEmptyString
    asset_id: NonEmptyString
    published_at: object
    available_at: object
    novelty_score: float
    polarity_score: float
    belief_conflict_score: float
    abstain_flag: bool = Field(default=False)
    missingness_reason: str | None = None

class SemanticResearchFeatureMaterialization(SemanticBaseModel):
    """Bounded materialization of one semantic tribunal feature into PIT-ready evidence."""

    experiment_id: NonEmptyString
    asset_id: NonEmptyString
    feature_event_id: NonEmptyString
    joined_row_count: int = Field(ge=0)
    feature_row: SemanticFeatureRow
    pit_provenance: PITJoinProvenance

class SemanticMaterializationEvidenceIssue(SemanticBaseModel):
    """Verification issue for semantic materialization adjudication evidence."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"

class SemanticMaterializationEvidenceVerificationReport(SemanticBaseModel):
    """Deterministic pre-adjudication verification report for semantic evidence."""

    evidence_id: NonEmptyString
    experiment_id: NonEmptyString
    verified: bool
    checksum: NonEmptyString
    expected_checksum: NonEmptyString
    schema_version: str
    issue_count: int = Field(ge=0)
    issues: list[SemanticMaterializationEvidenceIssue] = Field(default_factory=list)

class SemanticResearchPreflightReport(SemanticBaseModel):
    """Operator-facing report for one semantic research intake preflight."""

    schema_version: NonEmptyString = "semantic_research_preflight/v1"
    experiment_id: NonEmptyString
    strategy_name: NonEmptyString
    asset_id: NonEmptyString
    feature_event_id: NonEmptyString
    evidence_id: NonEmptyString
    evidence_checksum: NonEmptyString
    evidence_verified: bool
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    joined_row_count: int = Field(ge=0)
    pit_dataset_id: NonEmptyString
    pit_row_count_after: int = Field(ge=0)
    data_spine_fingerprint: str | None = None
    attached_evidence_count: int = Field(ge=0)
    recommended_action: NonEmptyString

