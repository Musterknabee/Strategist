from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_ledger_writer_rejects_non_orchestrator_authority():
    text=(ROOT/"strategy_validator/ledger/writer/__init__.py").read_text()
    assert "Only strategy_validator.validator.orchestrator may acquire ledger write authority." in text
    assert "Ledger writes require the orchestrator authority token." in text
