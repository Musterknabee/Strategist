"""Ensure selected CLIs can print --help without UnicodeEncodeError on narrow consoles."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "argv",
    [
        [sys.executable, "-m", "strategy_validator.cli.thesis_mutation_batch_loop", "--help"],
        [sys.executable, "-m", "strategy_validator.cli.research_os_runtime_demo", "--help"],
        [sys.executable, str(REPO_ROOT / "scripts" / "purge_repo_transients.py"), "--help"],
    ],
)
def test_cli_help_exits_zero(argv: list[str]) -> None:
    env = {**os.environ}
    # Narrow stdio encoding catches argparse help text that is not ASCII-safe on legacy Windows consoles.
    env["PYTHONIOENCODING"] = "cp1252"
    proc = subprocess.run(
        argv,
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert proc.returncode == 0, (argv, proc.stderr, proc.stdout)
