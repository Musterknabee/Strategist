from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_validator_handoff_packet_routes_are_registered() -> None:
    source = (ROOT / "strategy_validator/api/routes/research_handoff.py").read_text(encoding="utf-8")

    assert '"/semantic-adjudication-bundle/validator-handoff-packet"' in source
    assert '"/semantic-adjudication-bundle/validator-handoff-packet/verify"' in source
    assert '"/semantic-adjudication-bundle/validator-handoff-packet/summary"' in source
    assert "build_semantic_validator_handoff_packet" in source
    assert "verify_semantic_validator_handoff_packet" in source
    assert "summarize_semantic_validator_handoff_packet" in source
