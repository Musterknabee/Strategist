from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from strategy_validator.application.research_integrity import (
    build_semantic_adjudication_readiness_report,
    build_semantic_research_gate_artifact,
)
from strategy_validator.application.research_preflight import run_semantic_research_preflight
from strategy_validator.contracts.semantic import FeatureFactoryArtifact
from strategy_validator.core.enums import PromotionState
from strategy_validator.ledger.reader import HashChainVerificationReport, verify_hash_chain
from strategy_validator.proposers.experiments.generator import build_strategy_proposal
from strategy_validator.tribunal.agents.pipeline import TribunalPipeline
from strategy_validator.tribunal.constraints import GeneratorArtifact, SkepticArtifact, SpanCitation, TribunalVerdict
from strategy_validator.validator.orchestrator import adjudicate


@dataclass(frozen=True)
class StrategyValidationVerticalResult:
    schema_version: str
    experiment_id: str
    feature_event_id: str
    readiness_ready: bool
    preflight_recommended_action: str
    final_state: PromotionState
    ledger_verification: HashChainVerificationReport
    evidence_count: int

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'experiment_id': self.experiment_id,
            'feature_event_id': self.feature_event_id,
            'readiness_ready': self.readiness_ready,
            'preflight_recommended_action': self.preflight_recommended_action,
            'final_state': self.final_state.value,
            'ledger_verification': (
                self.ledger_verification.model_dump(mode='json')
                if hasattr(self.ledger_verification, 'model_dump')
                else self.ledger_verification.dict()
            ),
            'evidence_count': self.evidence_count,
        }


def _deterministic_stage_adapter(_: str, prompt: str, response_model: type[Any]) -> Any:
    if response_model is GeneratorArtifact:
        return GeneratorArtifact(
            novelty_score=0.72,
            polarity_score=-0.15,
            source_spans=[SpanCitation(exact_quote='margin pressure widened', context_rationale='explicit deterioration')],
        )
    if response_model is SkepticArtifact:
        return SkepticArtifact(
            contradiction_count=1,
            rebuttal_spans=[SpanCitation(exact_quote='cash buffer remains intact', context_rationale='mitigating context')],
        )
    if response_model is TribunalVerdict:
        return TribunalVerdict(
            final_belief_conflict_score=0.31,
            final_evidence_density=0.91,
            abstain_flag=False,
        )
    raise AssertionError(f'unexpected response model: {response_model!r}')


def build_deterministic_semantic_artifact(*, event_id: str) -> FeatureFactoryArtifact:
    return TribunalPipeline(
        generator_adapter=_deterministic_stage_adapter,
        skeptic_adapter=_deterministic_stage_adapter,
        judge_adapter=_deterministic_stage_adapter,
    ).execute(
        'Company update: margin pressure widened, but cash buffer remains intact.',
        event_id=event_id,
    )


def run_deterministic_strategy_validation_vertical(
    *,
    experiment_id: str = 'EXP-SEMANTIC-VERTICAL-001',
    strategy_name: str = 'SemanticVerticalAlpha',
    feature_event_id: str = 'event-semantic-vertical-001',
    evaluation_time_utc: datetime | None = None,
    market_data_subject_id: str = 'AAPL',
) -> StrategyValidationVerticalResult:
    evaluation_time = evaluation_time_utc or datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    artifact = build_deterministic_semantic_artifact(event_id=feature_event_id)
    proposal = build_strategy_proposal(
        experiment_id=experiment_id,
        strategy_name=strategy_name,
        evaluation_time_utc=evaluation_time,
        market_data_subject_id=market_data_subject_id,
    )
    preflight = run_semantic_research_preflight(
        proposal,
        artifact,
        published_at='2026-04-28T11:40:00Z',
        available_at='2026-04-28T11:50:00Z',
    )
    gate_artifact = build_semantic_research_gate_artifact(proposal)
    readiness = build_semantic_adjudication_readiness_report(
        proposal,
        gate_artifact=gate_artifact,
        require_gate_artifact=True,
    )
    if not readiness.ready_for_adjudication:
        raise ValueError('semantic readiness report blocked adjudication vertical')
    final_state = adjudicate(proposal, [])
    ledger_verification = verify_hash_chain(proposal.experiment_id)
    return StrategyValidationVerticalResult(
        schema_version='strategy_validation_vertical_result/v1',
        experiment_id=proposal.experiment_id,
        feature_event_id=feature_event_id,
        readiness_ready=readiness.ready_for_adjudication,
        preflight_recommended_action=preflight.recommended_action,
        final_state=final_state,
        ledger_verification=ledger_verification,
        evidence_count=len(proposal.evidence_bundle.evidence_items),
    )


__all__ = [
    'StrategyValidationVerticalResult',
    'build_deterministic_semantic_artifact',
    'run_deterministic_strategy_validation_vertical',
]
