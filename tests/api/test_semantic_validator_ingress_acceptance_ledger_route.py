from pathlib import Path


def test_acceptance_ledger_routes_are_registered() -> None:
    source = Path("strategy_validator/api/routes/research_handoff.py").read_text(encoding="utf-8")
    assert "/validator-handoff-packet/ingress/acceptance-ledger" in source
    assert "/validator-handoff-packet/ingress/acceptance-ledger/verify" in source
    assert "/validator-handoff-packet/ingress/acceptance-ledger/summary" in source
    assert "build_semantic_validator_ingress_acceptance_ledger" in source
