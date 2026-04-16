from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

CONTROL_PLANE_INIT = Path('strategy_validator/control_plane/__init__.py')


def test_control_plane_root_package_avoids_eager_submodule_imports() -> None:
    tree = ast.parse(CONTROL_PLANE_INIT.read_text(encoding='utf-8'))
    eager_from_imports = [
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module
        and node.module.startswith('strategy_validator.control_plane.')
    ]
    assert eager_from_imports == []


def test_control_plane_root_package_lazily_resolves_exports() -> None:
    sys.modules.pop('strategy_validator.control_plane', None)
    sys.modules.pop('strategy_validator.control_plane.operator_queue_service', None)
    module = importlib.import_module('strategy_validator.control_plane')
    assert 'strategy_validator.control_plane.operator_queue_service' not in sys.modules

    request_type = module.OracleGovernanceWorkQueueRequest
    assert request_type.__name__ == 'OracleGovernanceWorkQueueRequest'
    assert 'strategy_validator.control_plane.operator_queue_service' in sys.modules
