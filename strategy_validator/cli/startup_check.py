"""Startup self-check CLI (readiness, schema, connector wiring)."""
from __future__ import annotations

import argparse
import sys

from strategy_validator.core.config import load_config
from strategy_validator.validator.operator_checks import (
    export_startup_json_bundle,
    run_startup_self_check,
    validate_alpaca_market_data_connector,
    validate_http_market_data_connector,
)
from strategy_validator.validator.readiness import perform_readiness_check


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Strategy Validator startup self-check")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON bundle (heartbeat, health, blockers, connector issues).",
    )
    ns = parser.parse_args(argv)

    if ns.json:
        sys.stdout.write(export_startup_json_bundle())
        sys.stdout.flush()
        readiness = perform_readiness_check()
        cfg = load_config()
        http_issues = validate_http_market_data_connector(cfg)
        alpaca_issues = validate_alpaca_market_data_connector(cfg)
        return 0 if readiness.status == "READY" and not http_issues and not alpaca_issues else 1

    code, text = run_startup_self_check()
    sys.stdout.write(text)
    sys.stdout.flush()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
