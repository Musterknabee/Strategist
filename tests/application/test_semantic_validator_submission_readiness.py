from pathlib import Path


def test_submission_readiness_surface_is_fail_closed() -> None:
    source = Path("strategy_validator/application/research_integrity.py").read_text()
    assert "build_semantic_validator_submission_readiness_report" in source
    assert "SEMANTIC_VALIDATOR_SUBMISSION_EVIDENCE_REQUIRED" in source
    assert "SEMANTIC_VALIDATOR_SUBMISSION_EVIDENCE_NOT_ATTACHED_TO_PROPOSAL" in source
    assert "SUBMIT_PROPOSAL_TO_VALIDATOR_ADJUDICATION" in source


def test_submission_readiness_uses_terminal_evidence_verifier() -> None:
    source = Path("strategy_validator/application/research_integrity.py").read_text()
    assert "verify_semantic_validator_submission_packet_evidence(evidence)" in source
    assert "_SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SOURCE" in source
