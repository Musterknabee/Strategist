"""Load and validate strategy batch specs from JSON/YAML (no code execution)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from strategy_validator.contracts.strategy_batch import StrategyBatchSpec, StrategyTypeId

_ALLOWED_TYPES: frozenset[str] = frozenset({"momentum", "mean_reversion", "volatility_breakout"})


def load_strategy_batch_spec(path: str | Path) -> StrategyBatchSpec:
    """Parse *path* as JSON or YAML and return a validated :class:`StrategyBatchSpec`."""

    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(f"batch spec not found: {target}")

    text = target.read_text(encoding="utf-8")
    suffix = target.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        raw: Any = yaml.safe_load(text)
    else:
        raw = json.loads(text)

    if not isinstance(raw, dict):
        raise ValueError("batch spec root must be an object")

    spec = StrategyBatchSpec.model_validate(raw)
    for s in spec.strategies:
        if s.strategy_type not in _ALLOWED_TYPES:  # pragma: no cover - pydantic already constrains
            raise ValueError(f"unsupported strategy_type: {s.strategy_type}")
    return spec


__all__ = ["load_strategy_batch_spec"]
