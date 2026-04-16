import pytest
from pydantic import ValidationError
from strategy_validator.tribunal.constraints import (
    GeneratorArtifact,
    SkepticArtifact,
    SpanCitation,
    TribunalVerdict
)
from strategy_validator.tribunal.agents.pipeline import TribunalPipeline
from strategy_validator.core.config import load_config

# Load global config for testing thresholds
CONFIG = load_config()

# 1. Test extra forbidden fields
def test_forbidden_extra_fields():
    with pytest.raises(ValidationError):
        GeneratorArtifact(
            novelty_score=0.5,
            polarity_score=0.0,
            source_spans=[],
            extra_field="not allowed"
        )

# 2. Test empty citation strings
def test_empty_citation_strings():
    with pytest.raises(ValidationError):
        SpanCitation(exact_quote="", context_rationale="valid")
    with pytest.raises(ValidationError):
        SpanCitation(exact_quote="valid", context_rationale=" ")

# 3. Test invalid score ranges
def test_invalid_score_ranges():
    with pytest.raises(ValidationError):
        GeneratorArtifact(novelty_score=1.1, polarity_score=0.0, source_spans=[])
    with pytest.raises(ValidationError):
        GeneratorArtifact(novelty_score=0.5, polarity_score=-1.5, source_spans=[])

# 4. Test contradiction_count mismatch
def test_contradiction_count_mismatch():
    with pytest.raises(ValidationError, match="Contradiction count"):
        SkepticArtifact(
            contradiction_count=2,
            rebuttal_spans=[
                SpanCitation(exact_quote="q1", context_rationale="r1")
            ]
        )

# 5. Test low-evidence forced abstain (using CONFIG thresholds)
def mock_low_evidence_adapter(prompt, content, model):
    if model == GeneratorArtifact:
        return GeneratorArtifact(novelty_score=0.5, polarity_score=0.0, source_spans=[])
    if model == SkepticArtifact:
        return SkepticArtifact(contradiction_count=0, rebuttal_spans=[])
    if model == TribunalVerdict:
        # Use a value just below the configured threshold
        density = CONFIG.tribunal_thresholds.min_evidence_density - 0.01
        return TribunalVerdict(
            final_belief_conflict_score=0.0, 
            final_evidence_density=density,
            abstain_flag=False
        )
    return None

def test_low_evidence_forced_abstain():
    pipeline = TribunalPipeline(
        generator_adapter=mock_low_evidence_adapter,
        skeptic_adapter=mock_low_evidence_adapter,
        judge_adapter=mock_low_evidence_adapter,
        thresholds=CONFIG.tribunal_thresholds
    )
    artifact = pipeline.execute("any text", "evt-1")
    assert artifact.abstain_flag is True

# 6. Test non-neutral claims without spans forced abstain
def mock_non_neutral_no_spans_adapter(prompt, content, model):
    if model == GeneratorArtifact:
        # Just above the neutrality tolerance from config
        val = CONFIG.tribunal_thresholds.neutral_novelty + CONFIG.tribunal_thresholds.neutral_tolerance + 0.01
        return GeneratorArtifact(
            novelty_score=val,
            polarity_score=CONFIG.tribunal_thresholds.neutral_polarity, 
            source_spans=[] 
        )
    if model == SkepticArtifact:
        return SkepticArtifact(contradiction_count=0, rebuttal_spans=[])
    if model == TribunalVerdict:
        return TribunalVerdict(
            final_belief_conflict_score=0.0, 
            final_evidence_density=0.5, 
            abstain_flag=False
        )
    return None

def test_non_neutral_no_spans_forced_abstain():
    pipeline = TribunalPipeline(
        generator_adapter=mock_non_neutral_no_spans_adapter,
        skeptic_adapter=mock_non_neutral_no_spans_adapter,
        judge_adapter=mock_non_neutral_no_spans_adapter,
        thresholds=CONFIG.tribunal_thresholds
    )
    artifact = pipeline.execute("any text", "evt-2")
    assert artifact.abstain_flag is True
