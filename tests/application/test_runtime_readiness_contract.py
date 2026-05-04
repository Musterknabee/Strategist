from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_application_readiness_facade_uses_canonical_validator_readiness():
    text=(ROOT/"strategy_validator/application/readiness.py").read_text()
    for item in ["perform_readiness_check","perform_deployment_readiness_check","get_current_readiness"]:
        assert item in text
