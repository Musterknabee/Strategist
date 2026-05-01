#!/usr/bin/env python3
"""Host entrypoint for Research OS runtime demo (delegates to installed CLI)."""
from __future__ import annotations

from strategy_validator.cli.research_os_runtime_demo import main

if __name__ == "__main__":
    raise SystemExit(main())
