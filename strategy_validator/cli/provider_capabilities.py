"""Emit the optional provider capability registry as JSON."""
from __future__ import annotations

import argparse
import json
import sys

from strategy_validator.contracts.provider_capabilities import export_provider_capabilities_payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export the optional research/data provider capability registry (JSON).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Pretty-print JSON (default output is JSON regardless).",
    )
    ns = parser.parse_args(argv)
    payload = export_provider_capabilities_payload()
    indent = 2 if ns.json else None
    sys.stdout.write(json.dumps(payload, indent=indent, sort_keys=True) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
