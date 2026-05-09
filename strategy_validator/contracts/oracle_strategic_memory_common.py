from __future__ import annotations

from typing import Literal


OracleStrategicPosture = Literal[
    "OPPORTUNITY_BIASED",
    "BALANCED_OBSERVATION",
    "CAUTION_BIASED",
    "DEFENSIVE_RESEARCH",
    "RESEARCH_FREEZE",
]

OracleStrategicTransitionClassification = Literal[
    "STABLE_REGIME",
    "DRIFTING",
    "TRANSITIONING",
    "HIGH_UNCERTAINTY",
    "STRUCTURAL_BREAK_CANDIDATE",
]

OracleThesisCurrentState = Literal["SUPPORTIVE", "CAUTIONARY", "AT_RISK", "BROKEN", "NEUTRAL"]
OracleThesisEvolutionState = Literal["EMERGING", "STRENGTHENING", "WEAKENING", "REVERSING", "STABLE"]
OracleResearchPriorityKind = Literal[
    "REGIME_INVESTIGATION",
    "STRATEGY_VALIDATION",
    "DOCTRINE_REVIEW",
    "THESIS_REVIEW",
    "SCENARIO_PROBE",
]


__all__ = [
    "OracleStrategicPosture",
    "OracleStrategicTransitionClassification",
    "OracleThesisCurrentState",
    "OracleThesisEvolutionState",
    "OracleResearchPriorityKind",
]
