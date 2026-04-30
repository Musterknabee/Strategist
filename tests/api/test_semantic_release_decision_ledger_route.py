from pathlib import Path


def test_semantic_release_decision_ledger_routes_are_registered() -> None:
    source = Path('strategy_validator/api/routes/research_release.py').read_text(encoding='utf-8')
    assert '/semantic-adjudication-bundle/release-decision-ledger' in source
    assert '/semantic-adjudication-bundle/release-decision-ledger/verify' in source
    assert 'build_semantic_adjudication_release_decision_ledger' in source
    assert 'verify_semantic_adjudication_release_decision_ledger' in source
