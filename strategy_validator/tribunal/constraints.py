from __future__ import annotations

from typing import List, Annotated
from pydantic import BaseModel, Field, ConfigDict, StringConstraints, model_validator

from strategy_validator.contracts.semantic import NonEmptyString, FeatureFactoryArtifact

class TribunalBaseModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

class SpanCitation(TribunalBaseModel):
    """Verbatim proof extracted from source text."""
    exact_quote: NonEmptyString = Field(description="The verbatim string from the source text.")
    context_rationale: NonEmptyString = Field(description="Internal reasoning for why this quote was selected.")

class GeneratorArtifact(TribunalBaseModel):
    """The initial forensic extraction case."""
    novelty_score: float = Field(ge=0.0, le=1.0)
    polarity_score: float = Field(ge=-1.0, le=1.0)
    source_spans: List[SpanCitation]

class SkepticArtifact(TribunalBaseModel):
    """The hostile critique of the Generator's claims."""
    contradiction_count: int = Field(ge=0)
    rebuttal_spans: List[SpanCitation]

    @model_validator(mode="after")
    def validate_contradiction_counts(self) -> SkepticArtifact:
        if self.contradiction_count != len(self.rebuttal_spans):
            raise ValueError(
                f"Contradiction count ({self.contradiction_count}) must match "
                f"rebuttal spans length ({len(self.rebuttal_spans)})"
            )
        return self

class TribunalVerdict(TribunalBaseModel):
    """The final adjudicated state of belief."""
    final_belief_conflict_score: float = Field(ge=0.0, le=1.0)
    final_evidence_density: float = Field(ge=0.0, le=1.0)
    abstain_flag: bool = Field(default=False)


