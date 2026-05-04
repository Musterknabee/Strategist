from __future__ import annotations

from pathlib import Path


def test_semantic_validator_ingress_acceptance_record_routes_are_registered() -> None:
    source = Path('strategy_validator/api/routes/research_handoff.py').read_text(encoding='utf-8')
    assert '/validator-handoff-packet/ingress/acceptance-record' in source
    assert '/validator-handoff-packet/ingress/acceptance-record/verify' in source
    assert '/validator-handoff-packet/ingress/acceptance-record/summary' in source
