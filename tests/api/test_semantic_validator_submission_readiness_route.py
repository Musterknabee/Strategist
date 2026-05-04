from pathlib import Path


def test_submission_readiness_routes_are_registered() -> None:
    source = Path("strategy_validator/api/routes/research_submission.py").read_text()
    assert '/semantic-adjudication-bundle/validator-submission/readiness"' in source
    assert '/semantic-adjudication-bundle/validator-submission/readiness/summary"' in source
    assert "build_semantic_validator_submission_readiness_report" in source
    assert "summarize_semantic_validator_submission_readiness" in source
