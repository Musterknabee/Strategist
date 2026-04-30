from __future__ import annotations

from strategy_validator.application.research_integrity import (
    build_semantic_validator_ingress_acceptance_record,
    summarize_semantic_validator_ingress_acceptance_record,
    verify_semantic_validator_ingress_acceptance_record,
)


def test_semantic_validator_ingress_acceptance_record_contract_is_exported() -> None:
    assert callable(build_semantic_validator_ingress_acceptance_record)
    assert callable(verify_semantic_validator_ingress_acceptance_record)
    assert callable(summarize_semantic_validator_ingress_acceptance_record)
