from __future__ import annotations

import logging
from typing import Any, Callable, TypeVar

from strategy_validator.tribunal.constraints import (
    GeneratorArtifact,
    SkepticArtifact,
    TribunalVerdict,
    SpanCitation,
    FeatureFactoryArtifact,
)
from strategy_validator.tribunal.prompts import (
    GENERATOR_SYSTEM_PROMPT,
    SKEPTIC_SYSTEM_PROMPT,
    JUDGE_SYSTEM_PROMPT,
)
from strategy_validator.core.config import TribunalThresholds

logger = logging.getLogger(__name__)

T = TypeVar("T")

class HallucinationError(ValueError):
    """Raised when an LLM cites text that does not exist in the source."""
    pass

StageAdapter = Callable[[str, str, type[T]], T]

def verify_citation_integrity(text: str, citations: list[SpanCitation]) -> None:
    """Ensure every citation is a verbatim substring of the source text."""
    for citation in citations:
        if citation.exact_quote not in text:
            raise HallucinationError(
                f"HALLUCINATION DETECTED: Quote '{citation.exact_quote}' not found in source text."
            )

class TribunalPipeline:
    def __init__(
        self,
        generator_adapter: StageAdapter[GeneratorArtifact],
        skeptic_adapter: StageAdapter[SkepticArtifact],
        judge_adapter: StageAdapter[TribunalVerdict],
        thresholds: TribunalThresholds | None = None,
    ):
        self.generator = generator_adapter
        self.skeptic = skeptic_adapter
        self.judge = judge_adapter
        self.thresholds = thresholds or TribunalThresholds()

    def execute(self, raw_text: str, event_id: str) -> FeatureFactoryArtifact:
        """
        Adversarial forensic pipeline: Generator -> Skeptic -> Judge.
        """
        # 1. Generator Stage
        generator_output = self.generator(GENERATOR_SYSTEM_PROMPT, raw_text, GeneratorArtifact)
        verify_citation_integrity(raw_text, generator_output.source_spans)

        # 2. Skeptic Stage
        skeptic_input = f"SOURCE TEXT: {raw_text}\n\nGENERATOR CLAIMS: {generator_output.model_dump_json()}"
        skeptic_output = self.skeptic(SKEPTIC_SYSTEM_PROMPT, skeptic_input, SkepticArtifact)
        verify_citation_integrity(raw_text, skeptic_output.rebuttal_spans)

        # 3. Judge Stage
        judge_input = (
            f"RAW SOURCE TEXT: {raw_text}\n\n"
            f"GENERATOR CASE: {generator_output.model_dump_json()}\n\n"
            f"SKEPTIC REBUTTAL: {skeptic_output.model_dump_json()}"
        )
        verdict = self.judge(JUDGE_SYSTEM_PROMPT, judge_input, TribunalVerdict)

        # 4. Deterministic Pipeline-Side Abstain Guards using injected thresholds
        final_abstain = verdict.abstain_flag

        # A. Force abstain on low evidence density
        if verdict.final_evidence_density < self.thresholds.min_evidence_density:
            final_abstain = True

        # B. Force abstain when non-neutral claims lack evidence
        is_novel = abs(generator_output.novelty_score - self.thresholds.neutral_novelty) > self.thresholds.neutral_tolerance
        is_polarized = abs(generator_output.polarity_score - self.thresholds.neutral_polarity) > self.thresholds.neutral_tolerance
        if (is_novel or is_polarized) and not generator_output.source_spans:
            final_abstain = True

        return FeatureFactoryArtifact(
            event_id=event_id,
            forensic_status="adjudicated",
            novelty_score=generator_output.novelty_score,
            polarity_score=generator_output.polarity_score,
            belief_conflict=verdict.final_belief_conflict_score,
            evidence_density=verdict.final_evidence_density,
            abstain_flag=final_abstain,
            metadata={
                "generator_quotes": [s.exact_quote for s in generator_output.source_spans],
                "skeptic_rebuttals": [s.exact_quote for s in skeptic_output.rebuttal_spans],
                "contradiction_count": skeptic_output.contradiction_count,
            },
        )
