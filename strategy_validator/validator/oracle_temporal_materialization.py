from __future__ import annotations

from datetime import date, datetime, time, timezone

from strategy_validator.contracts.oracle_strategic_fusion import (
    OracleSensorIngestionInput,
    OracleSensorRawMacroInput,
    OracleSensorRawMicrostructureInput,
)
from strategy_validator.contracts.oracle_core import StrategyHealthSnapshot
from strategy_validator.contracts.oracle_temporal_semantics import TemporalSemanticBatchManifest


def _normalize_date_key(value: date | datetime | str) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value))


def materialize_temporal_semantic_sensor_inputs(
    manifest: TemporalSemanticBatchManifest,
    *,
    universe_label: str,
    macro_by_date: dict[date | datetime | str, OracleSensorRawMacroInput],
    microstructure_by_date: dict[date | datetime | str, OracleSensorRawMicrostructureInput],
    generated_for_by_date: dict[date | datetime | str, datetime] | None = None,
    strategies_by_date: dict[date | datetime | str, list[StrategyHealthSnapshot]] | None = None,
) -> tuple[OracleSensorIngestionInput, ...]:
    macro_map = {_normalize_date_key(k): v for k, v in macro_by_date.items()}
    micro_map = {_normalize_date_key(k): v for k, v in microstructure_by_date.items()}
    generated_map = {_normalize_date_key(k): v for k, v in (generated_for_by_date or {}).items()}
    strategy_map = {_normalize_date_key(k): v for k, v in (strategies_by_date or {}).items()}

    payloads: list[OracleSensorIngestionInput] = []
    for day in manifest.days:
        pt_date = day.point_in_time_date
        macro = macro_map.get(pt_date)
        micro = micro_map.get(pt_date)
        if macro is None:
            raise ValueError(f"missing macro_raw for {pt_date.isoformat()}")
        if micro is None:
            raise ValueError(f"missing microstructure_raw for {pt_date.isoformat()}")
        generated_for = generated_map.get(pt_date)
        if generated_for is None:
            generated_for = datetime.combine(pt_date, time(hour=12), tzinfo=timezone.utc)
        payloads.append(
            OracleSensorIngestionInput(
                generated_for_utc=generated_for,
                universe_label=universe_label,
                macro_raw=macro,
                semantic_raw=day.semantic_raw,
                microstructure_raw=micro,
                strategies=strategy_map.get(pt_date, []),
            )
        )
    return tuple(payloads)
