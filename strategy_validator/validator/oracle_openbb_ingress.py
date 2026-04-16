from __future__ import annotations

from datetime import date, datetime
from typing import Iterable

from strategy_validator.contracts.oracle import OracleSensorRawMacroInput, OracleSensorRawMicrostructureInput
from strategy_validator.contracts.oracle_temporal import OpenBBTemporalSensorIngressBatchResult, OpenBBTemporalSensorIngressDayResult
from strategy_validator.validator.providers.openbb_provider import OpenBBMarketDataProvider


def _coerce_date(value: date | datetime | str) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value))


def fetch_openbb_temporal_sensor_inputs(
    dates: Iterable[date | datetime | str],
    *,
    provider: OpenBBMarketDataProvider,
    universe_label: str,
) -> tuple[dict[date, OracleSensorRawMacroInput], dict[date, OracleSensorRawMicrostructureInput], OpenBBTemporalSensorIngressBatchResult]:
    normalized_dates = tuple(sorted({_coerce_date(item) for item in dates}))
    macro_by_date: dict[date, OracleSensorRawMacroInput] = {}
    micro_by_date: dict[date, OracleSensorRawMicrostructureInput] = {}
    results: list[OpenBBTemporalSensorIngressDayResult] = []
    hydrated_dates: list[date] = []
    missing_macro_dates: list[date] = []
    missing_micro_dates: list[date] = []

    for pt_date in normalized_dates:
        notes: list[str] = []
        macro = provider.provide_oracle_macro_input(universe_label=universe_label, point_in_time_date=pt_date.isoformat())
        micro = provider.provide_oracle_microstructure_input(universe_label=universe_label, point_in_time_date=pt_date.isoformat())
        if macro is not None:
            macro_by_date[pt_date] = macro
        else:
            missing_macro_dates.append(pt_date)
            notes.append('macro_raw missing from OpenBB ingress')
        if micro is not None:
            micro_by_date[pt_date] = micro
        else:
            missing_micro_dates.append(pt_date)
            notes.append('microstructure_raw missing from OpenBB ingress')
        if macro is not None and micro is not None:
            hydrated_dates.append(pt_date)
        results.append(
            OpenBBTemporalSensorIngressDayResult(
                point_in_time_date=pt_date,
                macro_available=macro is not None,
                microstructure_available=micro is not None,
                notes=notes,
            )
        )

    report = OpenBBTemporalSensorIngressBatchResult(
        provider_id=provider.provider_id,
        universe_label=universe_label,
        requested_dates=list(normalized_dates),
        hydrated_dates=hydrated_dates,
        missing_macro_dates=missing_macro_dates,
        missing_microstructure_dates=missing_micro_dates,
        results=results,
        summary_line=(
            f"Fetched OpenBB temporal sensor ingress for {len(normalized_dates)} requested days in {universe_label}; "
            f"hydrated={len(hydrated_dates)} missing_macro={len(missing_macro_dates)} missing_micro={len(missing_micro_dates)}."
        ),
    )
    return macro_by_date, micro_by_date, report
