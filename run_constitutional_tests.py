"""Run constitutional test package (delegates to pytest for collection).

Includes anti-regression invariant tests — the fastest constitutional gate.
"""
import subprocess
import sys


if __name__ == "__main__":
    raise SystemExit(
        subprocess.call(
            [sys.executable, "-m", "pytest", "tests/constitutional", "-v"],
            cwd=__import__("pathlib").Path(__file__).resolve().parent,
        )
    )
