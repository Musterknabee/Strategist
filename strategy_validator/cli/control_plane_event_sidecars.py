from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from strategy_validator.projections.control_plane_event_index import (
    build_control_plane_event_projection_index,
    write_control_plane_event_projection_index,
)
from strategy_validator.projections.control_plane_event_sidecars import (
    build_control_plane_event_reconciliation_report,
    write_control_plane_event_reconciliation_report,
    build_control_plane_event_sidecar_replay_report,
    write_control_plane_event_sidecar_replay_report,
)


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _cmd_replay(args: argparse.Namespace) -> int:
    if args.output_path:
        report = write_control_plane_event_sidecar_replay_report(
            event_root=args.event_root,
            output_path=args.output_path,
        )
    else:
        report = build_control_plane_event_sidecar_replay_report(args.event_root)
    payload = report.to_payload()
    if args.json:
        _print_json(payload)
    if args.fail_on_rejected and report.rejected_count:
        return 2
    return 0


def _cmd_reconcile(args: argparse.Namespace) -> int:
    if args.output_path:
        report = write_control_plane_event_reconciliation_report(
            event_root=args.event_root,
            output_path=args.output_path,
        )
    else:
        report = build_control_plane_event_reconciliation_report(args.event_root)
    payload = report.to_payload()
    payload["operator_journal_chain_verified"] = bool(args.verify_operator_chain)
    if args.json:
        _print_json(payload)
    if args.verify_operator_chain and not report.operator_journal_chain_ok:
        return 3
    if args.fail_on_drift and not report.ok:
        return 2
    return 0


def _cmd_index(args: argparse.Namespace) -> int:
    if args.output_path:
        index = write_control_plane_event_projection_index(
            event_root=args.event_root,
            output_path=args.output_path,
        )
    else:
        index = build_control_plane_event_projection_index(args.event_root)
    payload = index.to_payload()
    if args.json:
        _print_json(payload)
    if args.fail_on_drift and not index.ok:
        return 2
    return 0




def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="strategy-validator-control-plane-event-sidecars",
        description="Replay and reconcile control-plane *.event.json sidecars.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    replay = subparsers.add_parser("replay", help="Verify control-plane event sidecars on disk.")
    replay.add_argument("--event-root", type=Path, required=True)
    replay.add_argument("--output-path", type=Path)
    replay.add_argument("--fail-on-rejected", action="store_true")
    replay.add_argument("--json", action="store_true")
    replay.set_defaults(func=_cmd_replay)

    reconcile = subparsers.add_parser(
        "reconcile",
        help="Compare sidecar events with journaled control-plane-event operator actions.",
    )
    reconcile.add_argument("--event-root", type=Path, required=True)
    reconcile.add_argument("--output-path", type=Path)
    reconcile.add_argument("--fail-on-drift", action="store_true")
    reconcile.add_argument(
        "--verify-operator-chain",
        action="store_true",
        help="Fail separately when the operator_action_events hash chain is not clean.",
    )
    reconcile.add_argument("--json", action="store_true")
    reconcile.set_defaults(func=_cmd_reconcile)

    index = subparsers.add_parser(
        "index",
        help="Build a compact projection index over sidecar and journaled control-plane events.",
    )
    index.add_argument("--event-root", type=Path, required=True)
    index.add_argument("--output-path", type=Path)
    index.add_argument("--fail-on-drift", action="store_true")
    index.add_argument("--json", action="store_true")
    index.set_defaults(func=_cmd_index)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
