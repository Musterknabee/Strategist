"""Order/account parser registration for the paper broker CLI."""
from __future__ import annotations

import argparse
from pathlib import Path


def register_order_parsers(sub: argparse._SubParsersAction) -> None:
    s_status = sub.add_parser("status", help="Account snapshot (paper endpoint only).")
    s_status.add_argument("--env-file", default="", type=Path)
    s_status.add_argument("--output-root", default="", type=Path, help="Write paper_broker/latest/paper_broker_status.json")
    s_status.add_argument(
        "--allow-network",
        action="store_true",
        help="Query Alpaca account endpoint when policy is PAPER_READY (default: policy only).",
    )
    s_status.add_argument("--json", action="store_true")

    s_pos = sub.add_parser("positions", help="List paper positions.")
    s_pos.add_argument("--env-file", default="", type=Path)

    s_snap = sub.add_parser(
        "snapshot-account-positions",
        help="Persist a secret-free paper account/position snapshot artifact for reconciliation.",
    )
    s_snap.add_argument("--env-file", default="", type=Path)
    s_snap.add_argument(
        "--allow-network",
        action="store_true",
        help="Query Alpaca paper account and positions. Without this flag, writes policy/account hints only.",
    )
    s_snap.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Write snapshot evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_select = sub.add_parser("select-intent", help="Persist a paper-only execution intent selection artifact.")
    s_select.add_argument("--tracking-id", required=True)
    s_select.add_argument("--symbol", default="SPY")
    s_select.add_argument("--qty", type=float, default=1.0)
    s_select.add_argument("--side", default="buy", choices=["buy", "sell"])
    s_select.add_argument("--strategy-id", default="")
    s_select.add_argument("--selected-by", default="operator")
    s_select.add_argument("--reason", default="manual paper dry-run preparation")
    s_select.add_argument("--source-artifact", default="")
    s_select.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Write selected intent under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_dry = sub.add_parser("dry-run-order", help="Validate intent without submitting.")
    s_dry.add_argument("--tracking-id", required=True)
    s_dry.add_argument("--symbol", default="SPY")
    s_dry.add_argument("--qty", type=float, default=1.0)
    s_dry.add_argument("--side", default="buy", choices=["buy", "sell"])
    s_dry.add_argument("--env-file", default="", type=Path)
    s_dry.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Write dry-run evidence under this paper_broker root (default: artifacts/paper_broker).",
    )
    s_dry.add_argument(
        "--no-artifact",
        action="store_true",
        help="Print validation result only; do not write paper_order_dry_run.json evidence.",
    )

    s_replay = sub.add_parser(
        "dry-run-selected-intent",
        help="Replay the selected paper intent artifact through dry-run validation and persist linked evidence.",
    )
    s_replay.add_argument("--tracking-id", default="", help="Tracking id whose latest selected intent should be replayed.")
    s_replay.add_argument(
        "--selection-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_intent_selection.json path to replay. Overrides --tracking-id.",
    )
    s_replay.add_argument("--env-file", default="", type=Path)
    s_replay.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_sub = sub.add_parser("submit-paper-order", help="Submit order to paper API (CLI only).")
    s_sub.add_argument("--tracking-id", required=True)
    s_sub.add_argument("--symbol", default="SPY")
    s_sub.add_argument("--qty", type=float, default=1.0)
    s_sub.add_argument("--side", default="buy", choices=["buy", "sell"])
    s_sub.add_argument("--confirm-paper", action="store_true", required=True)
    s_sub.add_argument("--env-file", default="", type=Path)
    s_sub.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write guarded submission evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_order_status = sub.add_parser(
        "refresh-order-status",
        help="Persist a read-only paper broker order-status refresh artifact for a guarded submission.",
    )
    s_order_status.add_argument("--tracking-id", default="", help="Tracking id whose latest submission should be refreshed.")
    s_order_status.add_argument("--broker-order-id", default="", help="Explicit broker order id. Defaults to latest submission receipt order id.")
    s_order_status.add_argument("--submission-artifact", default="", type=Path, help="Explicit guarded submission artifact path.")
    s_order_status.add_argument("--env-file", default="", type=Path)
    s_order_status.add_argument(
        "--allow-network",
        action="store_true",
        help="Query Alpaca paper order status. Without this flag, writes a blocked status-refresh artifact.",
    )
    s_order_status.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write paper execution evidence under this paper_broker root (default: artifacts/paper_broker).",
    )
