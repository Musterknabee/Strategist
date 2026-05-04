from __future__ import annotations

from strategy_validator.contracts import oracle_temporal_results as temporal_results_contracts
from strategy_validator.contracts import oracle_temporal_semantics as temporal_semantics_contracts

ORACLE_TEMPORAL_SCHEMA_MODULES: tuple[object, ...] = (
    temporal_semantics_contracts,
    temporal_results_contracts,
)

__all__ = ["ORACLE_TEMPORAL_SCHEMA_MODULES"]
