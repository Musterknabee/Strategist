"""Controlled rollout operations CLI dispatcher."""
from __future__ import annotations

from strategy_validator.cli.rollout_bootstrap import build_rollout_parser


def main(argv: list[str] | None = None) -> int:
    parser = build_rollout_parser()
    ns = parser.parse_args(argv)
    return int(ns._run(ns))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
