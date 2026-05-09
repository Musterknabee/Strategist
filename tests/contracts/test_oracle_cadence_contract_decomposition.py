from __future__ import annotations

import ast
import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "strategy_validator" / "contracts"

SUBPHASE_MODULES = (
    "oracle_cadence_memory",
    "oracle_cadence_weekly",
    "oracle_cadence_doctrine_drift",
    "oracle_cadence_monthly",
    "oracle_cadence_quarterly",
    "oracle_cadence_semiannual",
    "oracle_cadence_annual",
    "oracle_cadence_constitutional",
)


def _class_names(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [node.name for node in tree.body if isinstance(node, ast.ClassDef)]


def test_oracle_cadence_reviews_is_legacy_facade() -> None:
    facade_path = CONTRACTS / "oracle_cadence_reviews.py"

    assert len(facade_path.read_text(encoding="utf-8").splitlines()) <= 50
    assert _class_names(facade_path) == []


def test_oracle_cadence_subphases_own_expected_contract_families() -> None:
    expected_classes = {
        "oracle_cadence_memory": {
            "OracleMemoryLaneEntry",
            "OracleMemoryLaneSummary",
            "OracleMemoryReviewReport",
            "OracleReviewLaneEntry",
        },
        "oracle_cadence_weekly": {
            "OracleWeeklyDigestReport",
            "OracleWeeklyDigestEvidenceManifest",
            "OracleWeeklyDigestEvidenceVerification",
        },
        "oracle_cadence_doctrine_drift": {
            "OracleDoctrineDriftReport",
            "OracleDoctrineDriftEvidenceManifest",
            "OracleDoctrineLaneEntry",
        },
        "oracle_cadence_monthly": {
            "OracleMonthlyDigestReport",
            "OracleMonthlyDigestEvidenceManifest",
            "OracleMonthlyLaneEntry",
        },
        "oracle_cadence_quarterly": {
            "OracleQuarterlyReviewReport",
            "OracleQuarterlyReviewEvidenceManifest",
            "OracleQuarterlyLaneEntry",
        },
        "oracle_cadence_semiannual": {
            "OracleSemiannualAuditReport",
            "OracleSemiannualAuditEvidenceManifest",
            "OracleSemiannualLaneEntry",
        },
        "oracle_cadence_annual": {
            "OracleAnnualReviewReport",
            "OracleAnnualReviewEvidenceManifest",
            "OracleAnnualLaneEntry",
        },
        "oracle_cadence_constitutional": {
            "OracleConstitutionalDigestReport",
            "OracleDoctrineLineageIndex",
            "OracleDoctrineLineageVerification",
            "OracleConstitutionalGateReport",
        },
    }

    for module_name, class_names in expected_classes.items():
        owned = set(_class_names(CONTRACTS / f"{module_name}.py"))
        assert class_names <= owned


def test_oracle_cadence_facade_exports_match_subphases() -> None:
    facade = importlib.import_module("strategy_validator.contracts.oracle_cadence_reviews")
    expected_exports: list[str] = []
    for subphase_name in SUBPHASE_MODULES:
        subphase = importlib.import_module(f"strategy_validator.contracts.{subphase_name}")
        expected_exports.extend(subphase.__all__)

    assert list(facade.__all__) == expected_exports


def test_legacy_oracle_cadence_import_surface_stays_available() -> None:
    facade = importlib.import_module("strategy_validator.contracts.oracle_cadence_reviews")

    assert facade.OracleMemoryReviewReport.__name__ == "OracleMemoryReviewReport"
    assert facade.OracleDoctrineDriftReport.__name__ == "OracleDoctrineDriftReport"
    assert facade.OracleMonthlyDigestReport.__name__ == "OracleMonthlyDigestReport"
    assert facade.OracleConstitutionalGateReport.__name__ == "OracleConstitutionalGateReport"
