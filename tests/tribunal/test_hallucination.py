import pytest
from typing import Any, TypeVar
from strategy_validator.tribunal.agents.pipeline import TribunalPipeline, HallucinationError
from strategy_validator.tribunal.constraints import (
    GeneratorArtifact, 
    SpanCitation, 
    SkepticArtifact, 
    TribunalVerdict,
    FeatureFactoryArtifact
)

T = TypeVar("T")

def mock_hallucinating_adapter(prompt: str, content: str, model: type[T]) -> T:
    if model == GeneratorArtifact:
        return GeneratorArtifact(
            novelty_score=0.8,
            polarity_score=0.5,
            source_spans=[
                SpanCitation(
                    exact_quote="This quote does not exist in the source.",
                    context_rationale="Hallucinating for test purposes."
                )
            ]
        )
    if model == SkepticArtifact:
        return SkepticArtifact(contradiction_count=0, rebuttal_spans=[])
    if model == TribunalVerdict:
        return TribunalVerdict(final_belief_conflict_score=0.0, final_evidence_density=1.0)
    raise ValueError(f"Unknown model: {model}")

def test_pipeline_catches_hallucination_with_custom_exception():
    source_text = "The market is showing extreme stability."
    
    # Inject the hallucinating adapter for all stages
    pipeline = TribunalPipeline(
        generator_adapter=mock_hallucinating_adapter,
        skeptic_adapter=mock_hallucinating_adapter,
        judge_adapter=mock_hallucinating_adapter
    )
    
    with pytest.raises(HallucinationError, match="HALLUCINATION DETECTED"):
        pipeline.execute(source_text, "evt-123")

def mock_valid_adapter(prompt: str, content: str, model: type[T]) -> T:
    if model == GeneratorArtifact:
        return GeneratorArtifact(
            novelty_score=0.1,
            polarity_score=0.1,
            source_spans=[
                SpanCitation(
                    exact_quote="extreme stability",
                    context_rationale="Found verbatim."
                )
            ]
        )
    if model == SkepticArtifact:
        return SkepticArtifact(contradiction_count=0, rebuttal_spans=[])
    if model == TribunalVerdict:
        return TribunalVerdict(final_belief_conflict_score=0.0, final_evidence_density=1.0)
    raise ValueError(f"Unknown model: {model}")

def test_pipeline_successful_execution():
    source_text = "The market is showing extreme stability."
    pipeline = TribunalPipeline(
        generator_adapter=mock_valid_adapter,
        skeptic_adapter=mock_valid_adapter,
        judge_adapter=mock_valid_adapter
    )
    
    artifact = pipeline.execute(source_text, "evt-123")
    assert isinstance(artifact, FeatureFactoryArtifact)
    assert artifact.event_id == "evt-123"
    assert artifact.metadata["generator_quotes"] == ["extreme stability"]

if __name__ == "__main__":
    # Internal runner
    pytest.main([__file__])
