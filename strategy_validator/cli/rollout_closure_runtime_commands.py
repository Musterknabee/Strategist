"""Bounded runtime/rollout closure command registration and handlers."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategy_validator.cli.application_rollout_surfaces import (
    build_daily_checklist_payload,
    build_rollout_bundle_payload,
    default_startup_json_bundle_payload,
    generate_host_fingerprint_payload,
    load_controlled_rollout_rules_payload,
    parse_analyze_summary_payload,
    review_runtime_evidence_payload,
)
from strategy_validator.cli.oracle_cli_common import write_json
from strategy_validator.contracts.operational import DailyOperationsChecklist
from strategy_validator.contracts.operational import RolloutScope


def cmd_fingerprint(ns: argparse.Namespace) -> int:
    fp = generate_host_fingerprint_payload(
        host_kind=ns.host_kind,
        host_label=ns.host_label or None,
        policy_path=Path(ns.policy_path),
    )
    payload = fp.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    return 0


def cmd_bundle(ns: argparse.Namespace) -> int:
    scope = RolloutScope(
        environment=ns.environment,
        provider=ns.provider,
        symbols=[s.strip().upper() for s in ns.symbols.split(",") if s.strip()],
        allowed_actions=[a.strip() for a in ns.allowed_actions.split(",") if a.strip()],
        operator_signoff_required=True,
    )
    bundle = build_rollout_bundle_payload(
        policy_path=Path(ns.policy_path),
        keyed_host_fingerprint_path=Path(ns.fingerprint),
        burnin_artifact_paths=[Path(p) for p in ns.artifacts],
        scope=scope,
    )
    payload = bundle.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    return 0


def cmd_checklist(ns: argparse.Namespace) -> int:
    summaries = [parse_analyze_summary_payload(Path(p)) for p in ns.analyze]
    startup = default_startup_json_bundle_payload() if ns.use_live_startup else None
    rules = load_controlled_rollout_rules_payload(path=Path(ns.rules_path) if ns.rules_path else None)
    checklist = build_daily_checklist_payload(
        analyze_summaries=summaries,
        startup_json=startup,
        telemetry_sink_healthy=not ns.telemetry_unhealthy,
        rules=rules,
    )
    payload = checklist.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    return 0


def cmd_review(ns: argparse.Namespace) -> int:
    raw = json.loads(Path(ns.checklist).read_text(encoding="utf-8"))
    checklist = DailyOperationsChecklist.model_validate(raw)
    rules = load_controlled_rollout_rules_payload(path=Path(ns.rules_path) if ns.rules_path else None)
    decision = review_runtime_evidence_payload(checklist=checklist, rules=rules)
    payload = decision.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    return 0


def register_rollout_closure_runtime_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    fp = sub.add_parser("fingerprint", help="Generate secret-safe keyed-host fingerprint")
    fp.add_argument("--host-kind", choices=["AGENT_HOST", "KEYED_OPERATOR_HOST"], required=True)
    fp.add_argument("--host-label", default="", help="Optional operator label for host/session.")
    fp.add_argument("--policy-path", default="strategy_validator/promotion_gates.yaml")
    fp.add_argument("--output", default="", help="Write JSON artifact path.")
    fp.set_defaults(_run=cmd_fingerprint)

    bd = sub.add_parser("bundle", help="Build controlled rollout bundle manifest")
    bd.add_argument("--policy-path", default="strategy_validator/promotion_gates.yaml")
    bd.add_argument("--fingerprint", required=True, help="Fingerprint JSON file path.")
    bd.add_argument("--artifacts", nargs="+", required=True, help="Burn-in artifact file paths.")
    bd.add_argument("--environment", choices=["staging", "paper", "production_shadow", "unknown"], default="paper")
    bd.add_argument("--provider", default="alpaca_data_v2")
    bd.add_argument("--symbols", default="SPY,QQQ")
    bd.add_argument("--allowed-actions", default="observe,archive,recommend")
    bd.add_argument("--output", default="", help="Write JSON artifact path.")
    bd.set_defaults(_run=cmd_bundle)

    dc = sub.add_parser("daily-checklist", help="Generate daily controlled-rollout checklist")
    dc.add_argument("--analyze", nargs="+", required=True, help="pilot *_analyze.txt files")
    dc.add_argument("--use-live-startup", action="store_true", help="Embed live startup bundle result")
    dc.add_argument("--telemetry-unhealthy", action="store_true", help="Mark telemetry sink as unhealthy")
    dc.add_argument("--rules-path", default="", help="Optional rollout rules JSON path.")
    dc.add_argument("--output", default="", help="Write JSON artifact path.")
    dc.set_defaults(_run=cmd_checklist)

    rv = sub.add_parser("review", help="Compute auditable release decision from checklist JSON")
    rv.add_argument("checklist", help="Checklist JSON path.")
    rv.add_argument("--rules-path", default="", help="Optional rollout rules JSON path.")
    rv.add_argument("--output", default="", help="Write JSON artifact path.")
    rv.set_defaults(_run=cmd_review)
