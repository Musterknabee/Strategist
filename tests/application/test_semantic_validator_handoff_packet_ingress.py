from __future__ import annotations

from strategy_validator.application.research_integrity import (
    build_semantic_validator_handoff_packet_ingress_report,
    summarize_semantic_validator_handoff_packet_ingress,
)


def test_validator_handoff_packet_ingress_symbols_are_exported() -> None:
    assert callable(build_semantic_validator_handoff_packet_ingress_report)
    assert callable(summarize_semantic_validator_handoff_packet_ingress)
