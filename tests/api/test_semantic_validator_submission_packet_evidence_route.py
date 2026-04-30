from pathlib import Path

ROUTE = Path("strategy_validator/api/routes/research_submission.py")


def test_submission_packet_evidence_routes_are_registered() -> None:
    source = ROUTE.read_text(encoding="utf-8")
    assert "/semantic-adjudication-bundle/validator-submission-packet/evidence" in source
    assert "/semantic-adjudication-bundle/validator-submission-packet/evidence/verify" in source
    assert "/semantic-adjudication-bundle/validator-submission-packet/evidence/summary" in source
