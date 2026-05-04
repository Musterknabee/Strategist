from __future__ import annotations

from strategy_validator.contracts import oracle_cadence_reviews as oracle_cadence_reviews_contracts
from strategy_validator.contracts import oracle_core as oracle_core_contracts
from strategy_validator.contracts import oracle_evidence_events as oracle_evidence_events_contracts
from strategy_validator.contracts import oracle_operator_reports as oracle_operator_reports_contracts
from strategy_validator.contracts import oracle_strategic_fusion as oracle_strategic_fusion_contracts
from strategy_validator.contracts import oracle_strategic_memory as oracle_strategic_memory_contracts
from strategy_validator.contracts import oracle_strategic_programs as oracle_strategic_programs_contracts

ORACLE_SCHEMA_MODULES: tuple[object, ...] = (
    oracle_core_contracts,
    oracle_evidence_events_contracts,
    oracle_cadence_reviews_contracts,
    oracle_operator_reports_contracts,
    oracle_strategic_fusion_contracts,
    oracle_strategic_programs_contracts,
    oracle_strategic_memory_contracts,
)

__all__ = ["ORACLE_SCHEMA_MODULES"]
