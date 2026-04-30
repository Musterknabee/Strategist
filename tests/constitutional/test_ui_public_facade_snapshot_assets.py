from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_ui_public_facade_snapshot_is_machine_readable_and_committed():
    assert (ROOT/"docs/api/ui-public-facade.snapshot.json").exists()
    assert (ROOT/"scripts/ui_facade_contract_snapshot.py").exists()
def test_ui_public_facade_snapshot_contract_is_listed_in_source_health():
    text=(ROOT/"scripts/source_health.py").read_text()
    assert "tests/api/test_ui_public_facade_snapshot_contract.py" in text
    assert "tests/constitutional/test_ui_public_facade_snapshot_assets.py" in text
