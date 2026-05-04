from __future__ import annotations

from strategy_validator.application.research_integrity import (
    build_semantic_validator_handoff_packet_ingress_certificate,
    verify_semantic_validator_handoff_packet_ingress_certificate,
    summarize_semantic_validator_handoff_packet_ingress_certificate,
)


def test_validator_handoff_packet_ingress_certificate_symbols_are_exported() -> None:
    assert callable(build_semantic_validator_handoff_packet_ingress_certificate)
    assert callable(verify_semantic_validator_handoff_packet_ingress_certificate)
    assert callable(summarize_semantic_validator_handoff_packet_ingress_certificate)
