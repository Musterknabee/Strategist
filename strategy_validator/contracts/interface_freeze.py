"""
Pilot / RC interface freeze markers.

These are **documentation and import-surface guards**, not runtime enforcement of
immutability across the whole codebase. Operators and CI pin behavior to the
listed modules and ``PILOT_RC_INTERFACE_FREEZE`` for a release candidate.
"""
from __future__ import annotations

import importlib
from typing import Final, Tuple

# Bumped in lockstep with package __version__ for each RC / pilot freeze.
PILOT_RC_INTERFACE_FREEZE: Final[str] = "0.1.0rc1"

# Public JSON / Pydantic contracts and operator-facing policy seams (import-only check).
FROZEN_IMPORT_SURFACE: Final[Tuple[str, ...]] = (
    "strategy_validator.contracts.market_data",
    "strategy_validator.contracts.execution",
    "strategy_validator.contracts.vendor_runtime",
    "strategy_validator.contracts.calibration",
    "strategy_validator.contracts.operational",
    "strategy_validator.core.config",
)


def verify_frozen_import_surface() -> None:
    """Import each frozen module; raises ImportError if the RC surface is broken."""
    for name in FROZEN_IMPORT_SURFACE:
        importlib.import_module(name)
