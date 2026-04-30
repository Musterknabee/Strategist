"""Startup self-check CLI (readiness, schema, connector wiring)."""
from __future__ import annotations

import argparse
import json
import sys

from strategy_validator.core.config import load_config
from strategy_validator.validator.operator_checks import (
    export_startup_json_bundle,
    run_startup_self_check,
    validate_alpaca_market_data_connector,
    validate_http_market_data_connector,
    validate_nvidia_nim_connector,
    validate_openbb_market_data_connector,
)
from strategy_validator.validator.readiness import perform_deployment_readiness_check, perform_readiness_check
from strategy_validator.application.readiness import summarize_deployment_readiness_payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Strategy Validator startup self-check")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON bundle (heartbeat, health, blockers, connector issues).",
    )
    parser.add_argument(
        "--deployment-json",
        action="store_true",
        help="Emit deployment readiness preflight JSON and exit non-zero unless READY.",
    )
    parser.add_argument(
        "--deployment-summary-json",
        action="store_true",
        help="Emit compact operator deployment readiness summary JSON and exit non-zero unless READY.",
    )
    parser.add_argument(
        "--repo-root",
        default="",
        help="Repository root to scan for deployment readiness private-key hygiene.",
    )
    ns = parser.parse_args(argv)

    if ns.deployment_summary_json:
        payload = summarize_deployment_readiness_payload(repo_root=ns.repo_root or None)
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        sys.stdout.flush()
        return 0 if payload["ok"] else 1

    if ns.deployment_json:
        report = perform_deployment_readiness_check(repo_root=ns.repo_root or None)
        sys.stdout.write(json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n")
        sys.stdout.flush()
        return 0 if report.status == "READY" else 1

    if ns.json:
        sys.stdout.write(export_startup_json_bundle())
        sys.stdout.flush()
        readiness = perform_readiness_check()
        cfg = load_config()
        http_issues = validate_http_market_data_connector(cfg)
        alpaca_issues = validate_alpaca_market_data_connector(cfg)
        openbb_issues = validate_openbb_market_data_connector(cfg)
        nim_issues = validate_nvidia_nim_connector(cfg)
        return 0 if readiness.status == "READY" and not http_issues and not alpaca_issues and not openbb_issues and not nim_issues else 1

    code, text = run_startup_self_check()
    sys.stdout.write(text)
    sys.stdout.flush()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
