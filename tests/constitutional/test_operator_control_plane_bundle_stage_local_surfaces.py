from pathlib import Path


def test_bundle_stage_modules_use_local_surface_modules() -> None:
    expectations = {
        "strategy_validator/control_plane/operator_control_plane_bundle_stage_core.py": (
            "operator_control_plane_bundle_stage_core_surfaces",
            "from strategy_validator.control_plane.operator_action_outcome_ledger import",
        ),
        "strategy_validator/control_plane/operator_control_plane_bundle_stage_reentry.py": (
            "operator_control_plane_bundle_stage_reentry_surfaces",
            "from strategy_validator.control_plane.operator_reentry_queue_state import",
        ),
        "strategy_validator/control_plane/operator_control_plane_bundle_stage_recurrence.py": (
            "operator_control_plane_bundle_stage_recurrence_surfaces",
            "from strategy_validator.control_plane.operator_chronic_instability_packet import",
        ),
    }
    for path, (surface_module, direct_import) in expectations.items():
        source = Path(path).read_text(encoding="utf-8")
        assert surface_module in source
        assert direct_import not in source


def test_bundle_stage_surface_modules_exist_and_are_bounded() -> None:
    for path in (
        "strategy_validator/control_plane/operator_control_plane_bundle_stage_core_surfaces.py",
        "strategy_validator/control_plane/operator_control_plane_bundle_stage_reentry_surfaces.py",
        "strategy_validator/control_plane/operator_control_plane_bundle_stage_recurrence_surfaces.py",
    ):
        source = Path(path).read_text(encoding="utf-8")
        assert "Bounded local imports for control-plane bundle" in source
