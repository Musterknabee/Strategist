import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_ui_facade_snapshot_assets_and_generator_exist():
    snap=ROOT/"docs/api/ui-public-facade.snapshot.json"; script=ROOT/"scripts/ui_facade_contract_snapshot.py"
    assert snap.exists() and script.exists()
    payload=json.loads(snap.read_text())
    assert isinstance(payload,dict) and payload.get("schema_version")
    assert "/ui/facade" in script.read_text()
def test_ui_facade_snapshot_is_ci_checked_without_static_fallback():
    ci=(ROOT/".github/workflows/ci.yml").read_text()
    assert "ui_facade_contract_snapshot.py --check" in ci
    assert "--no-static-fallback" in ci
