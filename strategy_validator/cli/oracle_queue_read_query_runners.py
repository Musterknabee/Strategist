from __future__ import annotations

from strategy_validator.cli.oracle_queue_runner_common import *
from strategy_validator.cli.oracle_queue_runner_common import _build_queue_kwargs, _emit_payload


def cmd_oracle_operator_queue_query(ns: argparse.Namespace) -> int:
    payload = build_queue_query_payload(**_build_queue_kwargs(ns))
    return _emit_payload(payload, ns.output)


def cmd_oracle_operator_workboard_query(ns: argparse.Namespace) -> int:
    payload = build_workboard_payload(board_label=ns.board_label, **_build_queue_kwargs(ns))
    return _emit_payload(payload, ns.output)
