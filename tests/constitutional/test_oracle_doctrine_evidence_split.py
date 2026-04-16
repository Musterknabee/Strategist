from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ENGINE_PATH = REPO_ROOT / "strategy_validator" / "validator" / "oracle_doctrine_engine.py"
EVIDENCE_PATH = REPO_ROOT / "strategy_validator" / "validator" / "oracle_doctrine_evidence.py"


def test_oracle_doctrine_engine_imports_evidence_functions_from_bounded_module() -> None:
    source = ENGINE_PATH.read_text(encoding="utf-8")
    assert "from strategy_validator.validator.oracle_doctrine_evidence import (" in source
    for name in [
        "build_oracle_doctrine_drift_evidence_bundle",
        "verify_oracle_doctrine_drift_evidence_bundle",
        "append_oracle_doctrine_drift_to_lane",
        "build_oracle_monthly_digest_evidence_bundle",
        "build_oracle_quarterly_review_evidence_bundle",
        "build_oracle_semiannual_audit_evidence_bundle",
        "build_oracle_annual_review_evidence_bundle",
    ]:
        assert name in source


def test_oracle_doctrine_evidence_module_owns_moved_definitions() -> None:
    source = EVIDENCE_PATH.read_text(encoding="utf-8")
    for name in [
        "build_oracle_doctrine_drift_evidence_bundle",
        "verify_oracle_doctrine_drift_evidence_bundle",
        "append_oracle_doctrine_drift_to_lane",
        "build_oracle_monthly_digest_evidence_bundle",
        "verify_oracle_monthly_digest_evidence_bundle",
        "append_oracle_monthly_digest_to_lane",
        "build_oracle_quarterly_review_evidence_bundle",
        "verify_oracle_quarterly_review_evidence_bundle",
        "append_oracle_quarterly_review_to_lane",
        "build_oracle_semiannual_audit_evidence_bundle",
        "verify_oracle_semiannual_audit_evidence_bundle",
        "append_oracle_semiannual_audit_to_lane",
        "build_oracle_annual_review_evidence_bundle",
        "verify_oracle_annual_review_evidence_bundle",
        "append_oracle_annual_review_to_lane",
    ]:
        assert f"def {name}(" in source
