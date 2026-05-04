from __future__ import annotations
from pathlib import Path


def test_validator_handoff_packet_ingress_certificate_routes_are_registered() -> None:
    text = Path('strategy_validator/api/routes/research_handoff.py').read_text(encoding='utf-8')
    assert '/semantic-adjudication-bundle/validator-handoff-packet/ingress/certificate' in text
    assert '/semantic-adjudication-bundle/validator-handoff-packet/ingress/certificate/verify' in text
    assert '/semantic-adjudication-bundle/validator-handoff-packet/ingress/certificate/summary' in text
    assert 'build_semantic_validator_handoff_packet_ingress_certificate' in text
    assert 'verify_semantic_validator_handoff_packet_ingress_certificate' in text
    assert 'summarize_semantic_validator_handoff_packet_ingress_certificate' in text
