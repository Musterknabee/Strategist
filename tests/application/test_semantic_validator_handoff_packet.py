from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_validator_handoff_packet_contract_and_application_surface_exist() -> None:
    contract = (ROOT / "strategy_validator/contracts/semantic.py").read_text(encoding="utf-8")
    app = (ROOT / "strategy_validator/application/research_integrity.py").read_text(encoding="utf-8")

    assert "class SemanticValidatorHandoffPacket" in contract
    assert "class SemanticValidatorHandoffPacketVerificationReport" in contract
    assert "class SemanticValidatorHandoffPacketSummary" in contract
    assert "def build_semantic_validator_handoff_packet" in app
    assert "def verify_semantic_validator_handoff_packet" in app
    assert "def summarize_semantic_validator_handoff_packet" in app


def test_validator_handoff_packet_verifier_is_fail_closed() -> None:
    app = (ROOT / "strategy_validator/application/research_integrity.py").read_text(encoding="utf-8")

    assert "SEMANTIC_VALIDATOR_HANDOFF_PACKET_CHECKSUM_MISMATCH" in app
    assert "SEMANTIC_VALIDATOR_HANDOFF_PACKET_EVIDENCE_INVALID" in app
    assert "SEMANTIC_VALIDATOR_HANDOFF_PACKET_HANDOFF_NOT_ALLOWED" in app
    assert "SEMANTIC_VALIDATOR_HANDOFF_PACKET_SOURCE_EVIDENCE_DRIFT" in app
    assert "HAND_OFF_PACKET_TO_VALIDATOR" in app
    assert "REBUILD_OR_BLOCK_SEMANTIC_VALIDATOR_HANDOFF_PACKET" in app
