from pathlib import Path


def test_release_decision_ledger_summary_route_is_registered() -> None:
    source = Path("strategy_validator/api/routes/research_release.py").read_text(encoding="utf-8")
    assert '/semantic-adjudication-bundle/release-decision-ledger/summary' in source
    assert "summarize_semantic_adjudication_release_decision_ledger" in source
