from __future__ import annotations

import importlib
from pathlib import Path


def test_projections_root_package_avoids_eager_submodule_imports() -> None:
    source = Path('strategy_validator/projections/__init__.py').read_text()
    assert 'from strategy_validator.projections.operator_terminal_record_service import' not in source
    assert 'from strategy_validator.projections.operator_pack_service import' not in source
    assert '_EXPORT_MAP' in source
    assert '__getattr__' in source


def test_projections_lazy_exports_resolve_runtime_symbols() -> None:
    projections = importlib.import_module('strategy_validator.projections')
    query_builder = getattr(projections, 'build_operator_pack_query')
    checkpoint_emitter = getattr(projections, 'emit_oracle_event_checkpoint_projection_registry')
    assert callable(query_builder)
    assert callable(checkpoint_emitter)
