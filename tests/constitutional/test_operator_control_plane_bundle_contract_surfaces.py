from __future__ import annotations

import inspect
from pathlib import Path

from strategy_validator.contracts import (
    OracleOperatorControlPlaneBundle,
    OracleOperatorControlPlaneBundleRequest,
)


def test_control_plane_bundle_contracts_resolve_from_bounded_contract_module() -> None:
    contract_module = "strategy_validator.contracts.operator_control_plane_bundle"
    for symbol in (
        OracleOperatorControlPlaneBundle,
        OracleOperatorControlPlaneBundleRequest,
    ):
        assert inspect.getmodule(symbol).__name__ == contract_module


def test_control_plane_bundle_contract_module_is_not_defined_inline_in_control_plane() -> None:
    source = Path("strategy_validator/control_plane/operator_control_plane_bundle_contracts.py").read_text(encoding="utf-8")
    for class_name in (
        "class OracleOperatorControlPlaneBundle",
        "class OracleOperatorControlPlaneBundleRequest",
    ):
        assert class_name not in source
