from enum import Enum, auto

class PromotionState(Enum):
    INVALID = "INVALID"
    REJECTED = "REJECTED"
    QUARANTINED = "QUARANTINED"
    CONDITIONAL = "CONDITIONAL"
    CANARY_ONLY = "CANARY_ONLY"
    PROMOTABLE = "PROMOTABLE"

# Authoritative severity ordering (Higher index = More restrictive)
BANK_STATE_RANKING = {
    PromotionState.PROMOTABLE: 0,
    PromotionState.CANARY_ONLY: 1,
    PromotionState.CONDITIONAL: 2,
    PromotionState.QUARANTINED: 3,
    PromotionState.REJECTED: 4,
    PromotionState.INVALID: 5,
}

class MetricSourceMode(Enum):
    PROVIDED = "PROVIDED"
    RECOMPUTED = "RECOMPUTED"
    VERIFIED = "VERIFIED"

class EvidenceType(Enum):
    BACKTEST_LOG = auto()
    MONTE_CARLO_RESULTS = auto()
    OUT_OF_SAMPLE_AUDIT = auto()
    COST_SUMMARY = auto()
    TRIBUNAL_OPINION = auto()
    EXECUTION_LOG = auto()

class RuntimeMode(Enum):
    DEV = "DEV"
    TEST = "TEST"
    PRODUCTION = "PRODUCTION"
