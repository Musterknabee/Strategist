from pathlib import Path


def test_validator_submission_packet_routes_are_registered() -> None:
    source = Path("strategy_validator/api/routes/research_submission.py").read_text(encoding="utf-8")
    assert "/validator-submission-packet" in source
    assert "/validator-submission-packet/verify" in source
    assert "/validator-submission-packet/summary" in source
    assert "build_semantic_validator_submission_packet" in source
