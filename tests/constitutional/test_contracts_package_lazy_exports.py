from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

from strategy_validator import contracts
from strategy_validator.contracts._exports import _EXPORT_MAP
from strategy_validator.contracts._exports_foundation import EXPORTS_FOUNDATION
from strategy_validator.contracts._exports_operational_runtime import EXPORTS_OPERATIONAL_RUNTIME
from strategy_validator.contracts._exports_operator_ui import EXPORTS_OPERATOR_UI
from strategy_validator.contracts._exports_research_strategy import EXPORTS_RESEARCH_STRATEGY

CONTRACTS_INIT = Path('strategy_validator/contracts/__init__.py')


def test_contracts_root_package_uses_lazy_exports() -> None:
    tree = ast.parse(CONTRACTS_INIT.read_text())
    eager = [
        node for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module not in {'__future__', 'importlib', 'strategy_validator.contracts._exports'}
    ]
    assert eager == []
    assert hasattr(contracts, '__getattr__')


def test_contracts_root_package_lazily_resolves_exports() -> None:
    sys.modules.pop('strategy_validator.contracts', None)
    sys.modules.pop('strategy_validator.contracts.decision_record', None)
    module = importlib.import_module('strategy_validator.contracts')
    assert 'strategy_validator.contracts.decision_record' not in sys.modules

    decision_record = module.DecisionRecord
    assert decision_record.__name__ == 'DecisionRecord'
    assert 'strategy_validator.contracts.decision_record' in sys.modules


def test_contracts_export_map_is_composed_from_grouped_registries() -> None:
    expected = {
        **EXPORTS_FOUNDATION,
        **EXPORTS_OPERATOR_UI,
        **EXPORTS_OPERATIONAL_RUNTIME,
        **EXPORTS_RESEARCH_STRATEGY,
    }
    assert _EXPORT_MAP == expected


def test_contracts_grouped_exports_keep_key_surfaces_in_expected_buckets() -> None:
    assert EXPORTS_FOUNDATION['DecisionRecord'] == 'strategy_validator.contracts.decision_record'
    assert EXPORTS_FOUNDATION['OracleMorningAttestation'] == 'strategy_validator.contracts.advisory'
    assert EXPORTS_OPERATOR_UI['UiWorkboardExportDocument'] == 'strategy_validator.contracts.ui_workboard_export'
    assert EXPORTS_OPERATOR_UI['OracleOperatorControlPlaneBundle'] == 'strategy_validator.contracts.operator_control_plane_bundle'
    assert EXPORTS_OPERATIONAL_RUNTIME['MutationSafetyStatus'] == 'strategy_validator.contracts.operational'
    assert EXPORTS_RESEARCH_STRATEGY['OracleScenarioLabReport'] == 'strategy_validator.contracts.strategic'
