from __future__ import annotations

import ast
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "strategy_validator" / "contracts"

ENTRY_MODULES = (
    "provider_capabilities_official",
    "provider_capabilities_market",
    "provider_capabilities_alternative",
    "provider_capabilities_execution",
)


def _class_names(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [node.name for node in tree.body if isinstance(node, ast.ClassDef)]


def _call_names(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            calls.append(node.func.id)
    return calls


def test_provider_capabilities_is_legacy_facade() -> None:
    facade_path = CONTRACTS / "provider_capabilities.py"

    assert len(facade_path.read_text(encoding="utf-8").splitlines()) <= 45
    assert _class_names(facade_path) == []
    assert "ProviderCapability" not in _call_names(facade_path)


def test_provider_schema_types_are_isolated_from_registry_entries() -> None:
    types_path = CONTRACTS / "provider_capabilities_types.py"
    classes = set(_class_names(types_path))

    assert {
        "ProviderCategory",
        "ProviderAccessType",
        "DefaultTrustLevel",
        "PitSuitability",
        "ProviderCapability",
    } <= classes
    assert "ProviderCapability" not in _call_names(types_path)


def test_provider_entry_subphases_own_expected_provider_groups() -> None:
    expected_ids = {
        "provider_capabilities_official": {
            "sec_edgar",
            "ecb",
            "eurostat",
            "world_bank_open_data",
            "oecd",
            "imf_data",
            "fred",
            "bls",
            "bls_registered_api",
        },
        "provider_capabilities_market": {
            "alpha_vantage",
            "eodhd",
            "finnhub",
            "financial_modeling_prep",
            "massive",
            "nasdaq_data_link",
            "polygon_io",
            "tiingo",
            "twelve_data",
        },
        "provider_capabilities_alternative": {
            "api_sports",
            "binance_public",
            "coingecko",
            "coinmarketcap",
            "football_data_org",
            "gdelt",
            "guardian_open_platform",
            "kraken_public",
            "mediastack",
            "newsapi",
            "sportmonks",
            "the_odds_api",
        },
        "provider_capabilities_execution": {"alpaca"},
    }

    for module_name, provider_ids in expected_ids.items():
        source = (CONTRACTS / f"{module_name}.py").read_text(encoding="utf-8")
        for provider_id in provider_ids:
            assert f'provider_id="{provider_id}"' in source


def test_provider_registry_aggregates_subphase_entries_in_legacy_order() -> None:
    facade = importlib.import_module("strategy_validator.contracts.provider_capabilities")
    registry = importlib.import_module("strategy_validator.contracts.provider_capabilities_registry")

    ids = [provider.provider_id for provider in facade.all_provider_capabilities()]
    assert ids[:4] == ["alpha_vantage", "alpaca", "api_sports", "binance_public"]
    assert ids[-3:] == ["tiingo", "twelve_data", "world_bank_open_data"]
    assert facade.all_provider_capabilities() == registry.all_provider_capabilities()

    subphase_count = 0
    for module_name in ENTRY_MODULES:
        module = importlib.import_module(f"strategy_validator.contracts.{module_name}")
        export_name = module.__all__[0]
        subphase_count += len(getattr(module, export_name))
    assert subphase_count == len(ids)


def test_legacy_provider_capabilities_import_surface_stays_available() -> None:
    facade = importlib.import_module("strategy_validator.contracts.provider_capabilities")

    assert facade.SCHEMA_VERSION == "provider_capabilities/v2"
    assert facade.ProviderCapability.__name__ == "ProviderCapability"
    assert facade.ProviderCategory.MACRO.value == "macro"
    assert facade.ProviderAccessType.PUBLIC_NO_SIGNUP.value == "PUBLIC_NO_SIGNUP"
    assert facade.PitSuitability.STRONG_PIT_SOURCE.value == "STRONG_PIT_SOURCE"
    assert callable(facade.all_provider_capabilities)
    assert callable(facade.export_provider_capabilities_payload)
    assert callable(facade.capability_by_provider_id)
