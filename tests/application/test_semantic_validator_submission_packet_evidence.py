from strategy_validator.application.research_integrity import (
    build_semantic_validator_submission_packet_evidence,
    summarize_semantic_validator_submission_packet_evidence,
    verify_semantic_validator_submission_packet_evidence,
)


def test_submission_packet_evidence_functions_are_exported() -> None:
    assert callable(build_semantic_validator_submission_packet_evidence)
    assert callable(verify_semantic_validator_submission_packet_evidence)
    assert callable(summarize_semantic_validator_submission_packet_evidence)
