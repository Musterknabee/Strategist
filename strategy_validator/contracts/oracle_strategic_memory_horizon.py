from __future__ import annotations

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field

from strategy_validator.contracts.oracle_types import AdvisoryRegime
from strategy_validator.contracts.oracle_strategic_memory_common import OracleStrategicPosture


class OracleStrategicMemoryPoint(BaseModel):
    point_id: str
    generated_at_utc: datetime
    oracle_run_id: str
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    strategic_posture: OracleStrategicPosture
    conviction_state: Literal["HIGH_CONVICTION", "GUARDED_CONVICTION", "FRAGILE_CONVICTION", "BROKEN_CONVICTION"]
    conviction_score: float = Field(ge=0.0, le=1.0)
    fragility_score: float = Field(ge=0.0, le=1.0)
    top_driver_kind: Literal["REGIME_DRIVER", "STRATEGY_DRIVER", "DOCTRINE_DRIVER", "SCENARIO_DRIVER", "CONTRADICTION_DRIVER", "INVESTIGATION_DRIVER"] | None = None
    top_driver_title: str | None = None
    top_driver_rank_score: float = Field(default=0.0, ge=0.0, le=1.0)
    summary_line: str

    model_config = {"extra": "forbid"}

class OracleStrategicDriverDriftItem(BaseModel):
    driver_kind: Literal["REGIME_DRIVER", "STRATEGY_DRIVER", "DOCTRINE_DRIVER", "SCENARIO_DRIVER", "CONTRADICTION_DRIVER", "INVESTIGATION_DRIVER"]
    baseline_rank_score: float = Field(ge=0.0, le=1.0)
    current_rank_score: float = Field(ge=0.0, le=1.0)
    drift_delta: float = Field(ge=-1.0, le=1.0)
    drift_direction: Literal["RISING", "FALLING", "STABLE"]
    summary_line: str

    model_config = {"extra": "forbid"}

class OracleStrategicMemoryHorizonReport(BaseModel):
    schema_version: Literal["oracle_strategic_memory_horizon_report/v1"] = "oracle_strategic_memory_horizon_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    horizon_observation_count: int = Field(ge=1)
    sealed_history_observation_count: int = Field(default=0, ge=0)
    unsealed_history_excluded_count: int = Field(default=0, ge=0)
    history_integrity_status: Literal["CURRENT_ONLY", "SEALED_HISTORY", "MIXED_HISTORY"] = "CURRENT_ONLY"
    source_stack_manifest_paths: List[str] = Field(default_factory=list)
    current_conviction_state: Literal["HIGH_CONVICTION", "GUARDED_CONVICTION", "FRAGILE_CONVICTION", "BROKEN_CONVICTION"]
    current_conviction_score: float = Field(ge=0.0, le=1.0)
    conviction_score_delta: float = Field(ge=-1.0, le=1.0)
    fragility_score_delta: float = Field(ge=-1.0, le=1.0)
    drift_state: Literal["FIRST_OBSERVATION", "STRENGTHENING", "SOFTENING", "REVERSING", "VOLATILE", "STABLE"]
    summary_line: str
    strongest_rising_driver_kind: Literal["REGIME_DRIVER", "STRATEGY_DRIVER", "DOCTRINE_DRIVER", "SCENARIO_DRIVER", "CONTRADICTION_DRIVER", "INVESTIGATION_DRIVER"] | None = None
    strongest_falling_driver_kind: Literal["REGIME_DRIVER", "STRATEGY_DRIVER", "DOCTRINE_DRIVER", "SCENARIO_DRIVER", "INVESTIGATION_DRIVER", "CONTRADICTION_DRIVER"] | None = None
    points: List[OracleStrategicMemoryPoint] = Field(default_factory=list)
    driver_drifts: List[OracleStrategicDriverDriftItem] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


__all__ = ['OracleStrategicMemoryPoint', 'OracleStrategicDriverDriftItem', 'OracleStrategicMemoryHorizonReport']
