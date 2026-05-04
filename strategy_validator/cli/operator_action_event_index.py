from __future__ import annotations

import sys

from strategy_validator.cli.ledger_ops import main as _ledger_ops_main


def main(argv: list[str] | None = None) -> int:
    """Compatibility shim for the operator action projection index CLI.

    The canonical operator-safe command surface is now::

        strategy-validator-ledger-ops index-operator-actions

    Keep this module executable for older automation that still calls
    ``python -m strategy_validator.cli.operator_action_event_index`` while
    delegating all behavior to ``ledger_ops`` so there is only one
    implementation path.
    """

    args = list(sys.argv[1:] if argv is None else argv)
    return _ledger_ops_main(["index-operator-actions", *args])


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
