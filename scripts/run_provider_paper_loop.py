"""Host wrapper for `strategy-validator-provider-paper-loop` (fixture-first by default).

The provider loop imports optional numerical/plotting stacks.  Some hosts keep
non-critical finalizers alive after output is written; this wrapper exits after
flushing so operator demos and CI smoke commands do not hang at interpreter
shutdown.  The CLI entrypoint remains importable as ``strategy_validator.cli``.
"""
from __future__ import annotations

import os
import sys

from strategy_validator.cli.provider_paper_loop import main

if __name__ == "__main__":
    rc = int(main())
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(rc)
