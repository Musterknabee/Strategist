from __future__ import annotations

import ast
from pathlib import Path

from strategy_validator import contracts


def test_contracts_root_package_uses_lazy_exports() -> None:
    module_path = Path('strategy_validator/contracts/__init__.py')
    tree = ast.parse(module_path.read_text())
    eager = [
        node for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module not in {'__future__', 'importlib'}
    ]
    assert eager == []
    assert hasattr(contracts, '__getattr__')


def test_contracts_root_export_map_points_to_bounded_modules() -> None:
    assert contracts._EXPORT_MAP['DecisionRecord'] == 'strategy_validator.contracts.decision_record'
    assert contracts._EXPORT_MAP['OracleMorningAttestation'] == 'strategy_validator.contracts.advisory'
    assert contracts.DecisionRecord.__name__ == 'DecisionRecord'
    assert contracts.OracleMorningAttestation.__name__ == 'OracleMorningAttestation'
