#!/usr/bin/env python3
"""Compatibility wrapper for the packaged single-tenant API smoke CLI."""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from strategy_validator.cli.single_tenant_api_smoke import main


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
