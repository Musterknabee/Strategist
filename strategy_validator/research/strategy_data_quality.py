"""Local bar data quality evaluation (deterministic; research)."""
from __future__ import annotations

import math
from datetime import datetime, timezone
from strategy_validator.contracts.strategy_data_quality import (
    DataQualityGateStatus,
    DataQualityIssue,
    DataQualityResult,
)
from strategy_validator.contracts.strategy_data_snapshot import StrategyBar, StrategyDataSnapshot
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

_OUTLIER_ABS_RET = 0.50


def evaluate_local_bars_data_quality(
    *,
    strategy_id: str,
    batch_id: str,
    run_id: str,
    bars: list[StrategyBar],
    as_of_utc: datetime,
    synthetic_demo: bool,
    snapshot: StrategyDataSnapshot | None,
    load_warnings: list[str],
) -> DataQualityResult:
    if synthetic_demo:
        body = DataQualityResult(
            strategy_id=strategy_id,
            batch_id=batch_id,
            run_id=run_id,
            row_count=len(bars),
            symbol_count=len({b.symbol for b in bars}) if bars else 0,
            gate_status=DataQualityGateStatus.NOT_APPLICABLE,
            blockers=[],
            warnings=["SYNTHETIC_DEMO_NOT_DATA_QUALITY_PROOF"],
            issues=[
                DataQualityIssue(
                    code="SYNTHETIC_DEMO",
                    severity="WARNING",
                    detail="Synthetic prices do not prove production bar hygiene.",
                )
            ],
        )
        plain = body.model_dump(mode="json")
        return body.model_copy(
            update={"data_quality_evidence_sha256": canonical_json_sha256(plain)}
        )

    blockers: list[str] = []
    warnings: list[str] = []
    issues: list[DataQualityIssue] = []

    row_count = len(bars)
    syms = {b.symbol for b in bars}
    symbol_count = len(syms)

    ts_min = min((b.timestamp_utc for b in bars), default=None)
    ts_max = max((b.timestamp_utc for b in bars), default=None)

    seen: set[tuple[str, str]] = set()
    duplicate_timestamp_count = 0
    future_row_count = 0
    bad_ohlc_count = 0
    zero_or_negative_price_count = 0
    zero_volume_count = 0
    as_of = as_of_utc.astimezone(timezone.utc)

    naive_ts = False
    for b in bars:
        key = (b.symbol, b.timestamp_utc.isoformat())
        if key in seen:
            duplicate_timestamp_count += 1
        seen.add(key)
        if b.timestamp_utc.tzinfo is None:
            naive_ts = True
        if b.timestamp_utc > as_of:
            future_row_count += 1
        if b.close <= 0:
            zero_or_negative_price_count += 1
        if b.volume == 0:
            zero_volume_count += 1
        o, h, l, c = b.open, b.high, b.low, b.close
        hi_need = max(o, c, l)
        lo_need = min(o, c, h)
        if h + 1e-12 < hi_need or l - 1e-12 > lo_need:
            bad_ohlc_count += 1

    missing_volume_signal = row_count > 0 and zero_volume_count == row_count

    outlier_return_count = 0
    by_sym: dict[str, list[StrategyBar]] = {}
    for b in bars:
        by_sym.setdefault(b.symbol, []).append(b)
    for sym, seq in by_sym.items():
        seq.sort(key=lambda x: x.timestamp_utc)
        prev_close: float | None = None
        for bar in seq:
            if prev_close is not None and prev_close > 0:
                lr = math.log(max(bar.close, 1e-12) / prev_close)
                if abs(lr) > _OUTLIER_ABS_RET:
                    outlier_return_count += 1
            prev_close = bar.close

    if naive_ts:
        blockers.append("TIMESTAMP_NOT_TIMEZONE_AWARE")
        issues.append(
            DataQualityIssue(
                code="NAIVE_TIMESTAMP",
                severity="BLOCKER",
                detail="One or more bars lack timezone-aware timestamps.",
            )
        )
    if duplicate_timestamp_count:
        blockers.append("DUPLICATE_SYMBOL_TIMESTAMP_ROWS")
        issues.append(
            DataQualityIssue(
                code="DUPLICATE_TIMESTAMP",
                severity="BLOCKER",
                detail=f"duplicate_timestamp_count={duplicate_timestamp_count}",
            )
        )
    if future_row_count:
        blockers.append("FUTURE_ROWS_RELATIVE_TO_AS_OF")
    if bad_ohlc_count:
        blockers.append("BAD_OHLC_RELATIONS")
    if zero_or_negative_price_count:
        blockers.append("NON_POSITIVE_CLOSE")

    if missing_volume_signal:
        warnings.append("MISSING_OR_ALL_ZERO_VOLUME")
        issues.append(
            DataQualityIssue(
                code="VOLUME_METADATA",
                severity="WARNING",
                detail="All bar volumes are zero; volume-based realism checks degraded.",
            )
        )

    if snapshot is not None and snapshot.published_at_utc is None:
        warnings.append("MISSING_PUBLISHED_AT_METADATA")
        issues.append(
            DataQualityIssue(
                code="PIT_PUBLISH_TIME",
                severity="WARNING",
                detail="published_at_utc missing on snapshot; PIT downgrade may apply.",
            )
        )

    if outlier_return_count > 0:
        warnings.append(f"OUTLIER_RETURNS:{outlier_return_count}")

    gate = DataQualityGateStatus.PROVEN
    if blockers:
        gate = DataQualityGateStatus.BLOCKED
    elif warnings:
        gate = DataQualityGateStatus.WARNING

    body = DataQualityResult(
        strategy_id=strategy_id,
        batch_id=batch_id,
        run_id=run_id,
        row_count=row_count,
        symbol_count=symbol_count,
        timestamp_min_utc=ts_min,
        timestamp_max_utc=ts_max,
        missing_close_count=0,
        missing_volume_count=1 if missing_volume_signal else 0,
        duplicate_timestamp_count=duplicate_timestamp_count,
        future_row_count=future_row_count,
        bad_ohlc_count=bad_ohlc_count,
        zero_or_negative_price_count=zero_or_negative_price_count,
        zero_volume_count=zero_volume_count,
        outlier_return_count=outlier_return_count,
        timezone_status="UTC_NORMALIZED",
        gate_status=gate,
        blockers=blockers,
        warnings=warnings,
        issues=issues,
    )
    plain = body.model_dump(mode="json")
    return body.model_copy(
        update={"data_quality_evidence_sha256": canonical_json_sha256(plain)}
    )


__all__ = ["evaluate_local_bars_data_quality"]
