class StrategyValidatorError(Exception):
    """Base exception for the Strategy Validator platform."""
    pass

class ConstitutionalViolation(StrategyValidatorError):
    """Raised when an architectural boundary is crossed."""
    pass

class LeakageDetected(StrategyValidatorError):
    """Raised when future data leakage is detected in an experiment."""
    pass

class ImmutableViolation(StrategyValidatorError):
    """Raised when an attempt is made to mutate the immutable ledger."""
    pass

class AdjudicationError(StrategyValidatorError):
    """Raised when the validator orchestrator fails to process evidence."""
    pass


class LedgerAuthorizationError(ConstitutionalViolation):
    """Raised when a caller attempts to bypass the adjudication write authority."""
    pass


class IllegalPromotionStateTransition(ConstitutionalViolation):
    """Raised when an append-only ledger event attempts a forbidden state transition."""
    pass


class LedgerPayloadViolation(ConstitutionalViolation):
    """Raised when ledger payload invariants are violated at write time."""
    pass
