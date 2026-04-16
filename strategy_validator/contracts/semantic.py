from __future__ import annotations
from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict, StringConstraints

# Strict types with non-empty constraints
NonEmptyString = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]

class SemanticBaseModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

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
