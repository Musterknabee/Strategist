"""Host wrapper for `strategy-validator-provider-paper-loop` (fixture-first by default)."""
from __future__ import annotations

import sys

from strategy_validator.cli.provider_paper_loop import main

if __name__ == "__main__":
    raise SystemExit(main())
