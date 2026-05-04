"""Semantic gate evaluation for the adjudication orchestrator."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.experiments import ExperimentManifest, GateResult
from strategy_validator.core.enums import BANK_STATE_RANKING, PromotionState
from strategy_validator.validator.orchestrator.evidence_gates import (
    _evaluate_semantic_research_integrity,
    _evaluate_semantic_release_handoff_certificate_evidence,
    _evaluate_semantic_validator_submission_packet_evidence,
    _semantic_artifacts_missing_spans,
)


@dataclass(frozen=True)
class SemanticGateOutcome:
    """State, gates, and note output from semantic gate evaluation."""

    state: PromotionState
    gates: tuple[GateResult, ...]
    summary_notes: tuple[str, ...]


def evaluate_semantic_gates(
    experiment: ExperimentManifest,
    evidence: Iterable[Evidence],
    *,
    state: PromotionState,
) -> SemanticGateOutcome:
    """Evaluate semantic integrity gates without committing state."""
    gates: list[GateResult] = []
    summary_notes: list[str] = []

    semantic_missing = _semantic_artifacts_missing_spans(experiment.evidence_bundle.semantic_artifacts)
    gates.append(GateResult(gate_name="SemanticEvidenceSufficiency", passed=not semantic_missing))
    if semantic_missing:
        state = _reconcile_states(state, PromotionState.QUARANTINED)

    semantic_research_gate = _evaluate_semantic_research_integrity(experiment)
    gates.append(semantic_research_gate)
    if not semantic_research_gate.passed:
        state = _reconcile_states(state, PromotionState.QUARANTINED)
        summary_notes.append(
            "SEMANTIC_RESEARCH_INTEGRITY_BLOCKED: "
            f"{semantic_research_gate.reason or 'semantic evidence integrity failed'}"
        )

    semantic_handoff_gate = _evaluate_semantic_release_handoff_certificate_evidence(evidence)
    gates.append(semantic_handoff_gate)
    if not semantic_handoff_gate.passed:
        state = _reconcile_states(state, PromotionState.QUARANTINED)
        summary_notes.append(
            "SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_BLOCKED: "
            f"{semantic_handoff_gate.reason or 'semantic release handoff certificate evidence failed'}"
        )

    semantic_submission_gate = _evaluate_semantic_validator_submission_packet_evidence(evidence)
    gates.append(semantic_submission_gate)
    if not semantic_submission_gate.passed:
        state = _reconcile_states(state, PromotionState.QUARANTINED)
        summary_notes.append(
            "SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_BLOCKED: "
            f"{semantic_submission_gate.reason or 'semantic validator submission-packet evidence failed'}"
        )

    return SemanticGateOutcome(
        state=state,
        gates=tuple(gates),
        summary_notes=tuple(summary_notes),
    )


def _reconcile_states(current_state: PromotionState, new_restriction: PromotionState) -> PromotionState:
    if BANK_STATE_RANKING[new_restriction] > BANK_STATE_RANKING[current_state]:
        return new_restriction
    return current_state
