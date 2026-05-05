from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_operator_doctor_console_script_registered() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'strategy-validator-operator-doctor = "strategy_validator.cli.operator_doctor:main"' in text


def test_operator_doctor_contains_required_disclaimers_and_schema() -> None:
    text = (ROOT / "strategy_validator/cli/operator_doctor.py").read_text(encoding="utf-8")
    assert "operator_doctor/v1" in text
    assert "Not production deployment approval." in text
    assert "Not operator signoff." in text
    assert "No live trading authorization." in text
    assert "No profitability claim." in text
