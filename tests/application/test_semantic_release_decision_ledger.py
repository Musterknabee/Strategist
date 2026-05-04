from pathlib import Path


def test_semantic_release_decision_ledger_contracts_are_declared() -> None:
    source = Path('strategy_validator/contracts/semantic.py').read_text(encoding='utf-8')
    assert 'class SemanticAdjudicationReleaseDecisionLedgerEntry' in source
    assert 'class SemanticAdjudicationReleaseDecisionLedger' in source
    assert 'class SemanticAdjudicationReleaseDecisionLedgerVerificationReport' in source


def test_semantic_release_decision_ledger_builder_verifier_are_declared() -> None:
    source = Path('strategy_validator/application/research_integrity.py').read_text(encoding='utf-8')
    assert 'def build_semantic_adjudication_release_decision_ledger(' in source
    assert 'def verify_semantic_adjudication_release_decision_ledger(' in source
    assert 'SEMANTIC_RELEASE_DECISION_LEDGER_PREVIOUS_HASH_MISMATCH' in source
    assert 'SEMANTIC_RELEASE_DECISION_LEDGER_MULTIPLE_ACCEPTS' in source
