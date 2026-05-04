"""CLI for optional GPU capability probing."""
from __future__ import annotations

import argparse
import json
import sys

from strategy_validator.research_compute.gpu_probe import probe_gpu_capability


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe optional torch/CUDA capability for advisory research compute.")
    parser.add_argument("--json", action="store_true", help="Pretty-print JSON output.")
    ns = parser.parse_args(argv)
    payload = probe_gpu_capability()
    indent = 2 if ns.json else None
    sys.stdout.write(json.dumps(payload, indent=indent, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
