from pathlib import Path


def test_decoy_survival_battery_is_implemented() -> None:
    path = Path(__file__).resolve().parents[1] / "decoys" / "test_decoy_placeholder.py"
    text = path.read_text(encoding="utf-8")
    assert "pytest.mark.xfail" not in text
    assert "decoy_battery_results" in text
