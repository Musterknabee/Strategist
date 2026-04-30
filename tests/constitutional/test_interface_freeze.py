from __future__ import annotations

import pytest

from strategy_validator.contracts import interface_freeze


@pytest.mark.constitutional
def test_interface_freeze_marker_matches_package_version() -> None:
    import strategy_validator

    assert interface_freeze.PILOT_RC_INTERFACE_FREEZE == strategy_validator.__version__


@pytest.mark.constitutional
def test_frozen_import_surface_importable() -> None:
    interface_freeze.verify_frozen_import_surface()
