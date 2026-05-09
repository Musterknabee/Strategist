"""CLI: Alpaca paper broker evidence (optional keys; no browser orders)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from strategy_validator.cli_support import paper_broker_runtime as _runtime
from strategy_validator.cli_support.paper_broker_parser import build_paper_broker_parser

_RUNTIME_EXPORTS = frozenset(_runtime.__all__)


def __getattr__(name: str) -> Any:
    """Delegate the legacy paper-broker monkeypatch surface to the runtime registry."""

    if name in _RUNTIME_EXPORTS:
        return getattr(_runtime, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Expose delegated runtime symbols to interactive/operator introspection."""

    return sorted({*globals(), *_RUNTIME_EXPORTS})


def _paper_broker_artifact_root() -> Path:
    return (Path.cwd() / "artifacts" / "paper_broker").resolve()


def _merge_env(env_file: Path | None) -> dict[str, str]:
    base = {k: str(v) for k, v in os.environ.items()}
    if env_file is None:
        return base
    vals, _ = _runtime.parse_env_file(env_file)
    return {**base, **vals}


def main(argv: list[str] | None = None) -> int:
    p = build_paper_broker_parser()
    ns = p.parse_args(argv)
    raw_ef = str(getattr(ns, "env_file", "") or "").strip()
    env = _merge_env(Path(raw_ef) if raw_ef else None)

    from strategy_validator.cli_support import (
        paper_broker_custody_commands,
        paper_broker_evidence_bundle_commands,
        paper_broker_order_commands,
        paper_broker_retention_commands,
    )

    for command_family in (
        paper_broker_order_commands,
        paper_broker_evidence_bundle_commands,
        paper_broker_retention_commands,
        paper_broker_custody_commands,
    ):
        result = command_family.handle(ns, env)
        if result is not None:
            return result

    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
