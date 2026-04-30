"""PIT, future-leakage, and phantom-edge gate evaluation."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.experiments import GateResult
from strategy_validator.core.enums import BANK_STATE_RANKING, PromotionState
from strategy_validator.validator.orchestrator.evidence_gates import (
    _evidence_indicates_future_leakage,
    _phantom_edge_detected,
    _pit_integrity_ok,
)


@dataclass(frozen=True)
class EvidenceIntegrityGateOutcome:
    """State and gate output for evidence-integrity evaluation."""

    state: PromotionState
    gates: tuple[GateResult, ...]


def evaluate_evidence_integrity_gates(
    evidence: Iterable[Evidence],
    *,
    state: PromotionState,
) -> EvidenceIntegrityGateOutcome:
    """Evaluate immutable evidence-integrity gates without mutating proposal state."""
    evidence_items = tuple(evidence)
    gates: list[GateResult] = []

    leakage = _evidence_indicates_future_leakage(evidence_items)
    pit_ok = _pit_integrity_ok(evidence_items)
    phantom_edge = _phantom_edge_detected(evidence_items)

    gates.append(GateResult(gate_name="FutureLeakage", passed=not leakage))
    gates.append(GateResult(gate_name="PointInTimeIntegrity", passed=pit_ok))
    gates.append(GateResult(gate_name="PhantomEdgeDetection", passed=not phantom_edge))

    if leakage:
        state = _reconcile_states(state, PromotionState.INVALID)
    if not pit_ok:
        state = _reconcile_states(state, PromotionState.REJECTED)
    if phantom_edge:
        state = _reconcile_states(state, PromotionState.REJECTED)

    return EvidenceIntegrityGateOutcome(state=state, gates=tuple(gates))


def _reconcile_states(current_state: PromotionState, new_restriction: PromotionState) -> PromotionState:
    if BANK_STATE_RANKING[new_restriction] > BANK_STATE_RANKING[current_state]:
        return new_restriction
    return current_state
