from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.contracts.oracle_temporal import TemporalLaneStatus


def write_temporal_lane_status(path: Path, status: TemporalLaneStatus) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_temporal_lane_status(path: Path) -> TemporalLaneStatus:
    return TemporalLaneStatus.model_validate(json.loads(path.read_text(encoding="utf-8")))


__all__ = ["write_temporal_lane_status", "load_temporal_lane_status"]
