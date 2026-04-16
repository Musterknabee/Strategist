from pathlib import Path


def test_oracle_advisory_imports_evidence_surface() -> None:
    advisory = Path("strategy_validator/validator/oracle_advisory.py").read_text(encoding="utf-8")
    assert "from strategy_validator.validator.oracle_advisory_evidence import (" in advisory
    assert "build_oracle_evidence_bundle," in advisory
    assert "verify_oracle_evidence_bundle," in advisory
    assert "def build_oracle_evidence_bundle(" not in advisory
    assert "def verify_oracle_evidence_bundle(" not in advisory


def test_oracle_advisory_evidence_module_owns_split_functions() -> None:
    evidence = Path("strategy_validator/validator/oracle_advisory_evidence.py").read_text(encoding="utf-8")
    assert "def load_oracle_input(" in evidence
    assert "def build_oracle_evidence_bundle(" in evidence
    assert "def verify_oracle_evidence_bundle(" in evidence
