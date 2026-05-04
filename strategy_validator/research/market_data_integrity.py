"""Market-data integrity checks for local/provider bar snapshots."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from math import isfinite
from typing import Any

from strategy_validator.contracts.market_data_integrity import (
    CorporateActionWarning,
    MarketDataIntegrityGateStatus,
    MarketDataIntegrityResult,
    PriceDiscontinuityCheck,
    SurvivorshipWarning,
    SymbolContinuityCheck,
    TradingCalendarCoverage,
)
from strategy_validator.contracts.strategy_data_snapshot import StrategyBar, StrategyDataSnapshot
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

_SPLIT_LIKE_RETURN = 0.45
_BLOCK_MISSING_RATIO = 0.25
_WARN_MISSING_RATIO = 0.10
_STALE_DAILY_HOURS = 96.0


def _business_day_count(start: datetime, end: datetime) -> int:
    if end < start:
        return 0
    d = start.date()
    stop = end.date()
    n = 0
    from datetime import timedelta

    while d <= stop:
        if d.weekday() < 5:
            n += 1
        d += timedelta(days=1)
    return n


def _finalize(res: MarketDataIntegrityResult) -> MarketDataIntegrityResult:
    body = res.model_dump(mode="json", exclude={"evidence_sha256"})
    return res.model_copy(update={"evidence_sha256": canonical_json_sha256(body)})


def evaluate_market_data_integrity(
    *,
    strategy_id: str,
    batch_id: str,
    run_id: str,
    bars: list[StrategyBar],
    as_of_utc: datetime,
    snapshot: StrategyDataSnapshot | None,
    provider_id: str = "unknown",
    license_scope: str = "unknown",
    trust_level: str = "unknown",
    adjusted_status: str = "UNKNOWN",
) -> MarketDataIntegrityResult:
    as_of = as_of_utc.astimezone(timezone.utc)
    if not bars:
        return _finalize(
            MarketDataIntegrityResult(
                strategy_id=strategy_id,
                batch_id=batch_id,
                run_id=run_id,
                provider_id=provider_id,
                license_scope=license_scope,
                trust_level=trust_level,
                adjusted_status="UNKNOWN",
                as_of_utc=as_of,
                gate_status=MarketDataIntegrityGateStatus.NOT_APPLICABLE,
                warnings=["NO_BARS_FOR_MARKET_DATA_INTEGRITY"],
            )
        )

    warnings: list[str] = []
    blockers: list[str] = []
    by_symbol: dict[str, list[StrategyBar]] = defaultdict(list)
    for b in bars:
        by_symbol[b.symbol.upper()].append(b)

    min_ts = min(b.timestamp_utc for b in bars).astimezone(timezone.utc)
    max_ts = max(b.timestamp_utc for b in bars).astimezone(timezone.utc)
    expected = _business_day_count(min_ts, max_ts)
    observed_days = {b.timestamp_utc.astimezone(timezone.utc).date() for b in bars if b.timestamp_utc.weekday() < 5}
    missing = max(0, expected - len(observed_days))
    ratio = 0.0 if expected == 0 else missing / expected
    cal_status = MarketDataIntegrityGateStatus.PROVEN
    if ratio > _BLOCK_MISSING_RATIO:
        cal_status = MarketDataIntegrityGateStatus.BLOCKED
        blockers.append(f"MISSING_TRADING_DAYS_RATIO:{ratio:.3f}")
    elif ratio > _WARN_MISSING_RATIO:
        cal_status = MarketDataIntegrityGateStatus.WARNING
        warnings.append(f"MISSING_TRADING_DAYS_RATIO:{ratio:.3f}")
    coverage = TradingCalendarCoverage(
        expected_trading_days=expected,
        observed_trading_days=len(observed_days),
        missing_trading_days=missing,
        missing_date_ratio=ratio,
        calendar_status=cal_status,
    )

    duplicate_count = 0
    seen: set[tuple[str, str]] = set()
    tz_warnings: list[str] = []
    for b in bars:
        key = (b.symbol.upper(), b.timestamp_utc.isoformat())
        if key in seen:
            duplicate_count += 1
        seen.add(key)
        if b.timestamp_utc.tzinfo is None:
            tz_warnings.append("NAIVE_TIMESTAMP")
    if duplicate_count:
        blockers.append("DUPLICATE_VENDOR_RECORDS")
    if tz_warnings:
        blockers.append("TIMEZONE_SESSION_INCONSISTENCY")

    last_hours = max(0.0, (as_of - max_ts).total_seconds() / 3600.0)
    if last_hours > _STALE_DAILY_HOURS:
        blockers.append(f"STALE_LAST_BAR_HOURS:{last_hours:.1f}")

    cont: list[SymbolContinuityCheck] = []
    disc: list[PriceDiscontinuityCheck] = []
    corp: list[CorporateActionWarning] = []
    surv: list[SurvivorshipWarning] = []
    for sym, seq in sorted(by_symbol.items()):
        seq = sorted(seq, key=lambda x: x.timestamp_utc)
        sym_days = {b.timestamp_utc.date() for b in seq if b.timestamp_utc.weekday() < 5}
        sym_expected = _business_day_count(seq[0].timestamp_utc, seq[-1].timestamp_utc)
        sym_missing = max(0, sym_expected - len(sym_days))
        status = MarketDataIntegrityGateStatus.PROVEN
        if sym_expected and sym_missing / sym_expected > _BLOCK_MISSING_RATIO:
            status = MarketDataIntegrityGateStatus.BLOCKED
        elif sym_expected and sym_missing / sym_expected > _WARN_MISSING_RATIO:
            status = MarketDataIntegrityGateStatus.WARNING
        cont.append(
            SymbolContinuityCheck(
                symbol=sym,
                first_seen_utc=seq[0].timestamp_utc,
                last_seen_utc=seq[-1].timestamp_utc,
                observed_days=len(sym_days),
                missing_days=sym_missing,
                status=status,
            )
        )
        if seq[0].timestamp_utc > min_ts or seq[-1].timestamp_utc < max_ts:
            surv.append(
                SurvivorshipWarning(
                    symbol=sym,
                    warning_code="SYMBOL_NOT_PRESENT_FULL_LOOKBACK",
                    detail="Symbol is not continuously present for the full loaded lookback; survivorship/constituent bias may apply.",
                )
            )
            warnings.append(f"SURVIVORSHIP_OR_SYMBOL_CONTINUITY:{sym}")
        prev = None
        for bar in seq:
            if prev is not None and prev.close > 0:
                ret = (bar.close / prev.close) - 1.0
                if isfinite(ret) and abs(ret) > _SPLIT_LIKE_RETURN:
                    code = "SPLIT_LIKE_JUMP_OR_UNADJUSTED_SERIES"
                    disc.append(
                        PriceDiscontinuityCheck(
                            symbol=sym,
                            timestamp_utc=bar.timestamp_utc,
                            previous_close=prev.close,
                            close=bar.close,
                            absolute_return=abs(ret),
                            warning_code=code,
                        )
                    )
                    corp.append(
                        CorporateActionWarning(
                            symbol=sym,
                            timestamp_utc=bar.timestamp_utc,
                            warning_code=code,
                            detail="Large close-to-close jump detected; verify split/dividend adjustment status before promotion.",
                        )
                    )
            prev = bar

    if corp:
        warnings.append(f"CORPORATE_ACTION_OR_PRICE_DISCONTINUITY:{len(corp)}")
    if adjusted_status == "UNKNOWN":
        warnings.append("ADJUSTED_STATUS_UNKNOWN")
    if snapshot is not None and snapshot.provider_id == "local_file":
        warnings.append("LOCAL_FILE_LICENSE_AND_SURVIVORSHIP_SCOPE_UNVERIFIED")

    if any(c.status == MarketDataIntegrityGateStatus.BLOCKED for c in cont):
        blockers.append("SYMBOL_CONTINUITY_BLOCKED")
    elif any(c.status == MarketDataIntegrityGateStatus.WARNING for c in cont):
        warnings.append("SYMBOL_CONTINUITY_WARNING")

    gate = MarketDataIntegrityGateStatus.PROVEN
    if blockers:
        gate = MarketDataIntegrityGateStatus.BLOCKED
    elif warnings:
        gate = MarketDataIntegrityGateStatus.WARNING

    return _finalize(
        MarketDataIntegrityResult(
            strategy_id=strategy_id,
            batch_id=batch_id,
            run_id=run_id,
            provider_id=provider_id,
            license_scope=license_scope,
            trust_level=trust_level,
            adjusted_status=adjusted_status if adjusted_status in {"ADJUSTED", "UNADJUSTED", "UNKNOWN"} else "UNKNOWN",  # type: ignore[arg-type]
            as_of_utc=as_of,
            row_count=len(bars),
            symbol_count=len(by_symbol),
            stale_last_bar_hours=last_hours,
            trading_calendar_coverage=coverage,
            corporate_action_warnings=corp,
            survivorship_warnings=surv,
            symbol_continuity_checks=cont,
            price_discontinuity_checks=disc,
            duplicate_vendor_record_count=duplicate_count,
            timezone_session_warnings=sorted(set(tz_warnings)),
            benchmark_calendar_mismatch=False,
            gate_status=gate,
            warnings=sorted(set(warnings)),
            blockers=sorted(set(blockers)),
        )
    )


def public_market_data_integrity_payload(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    import json
    from pathlib import Path

    p = Path(path)
    if not p.is_file():
        return None
    raw = json.loads(p.read_text(encoding="utf-8"))
    return {
        "gate_status": raw.get("gate_status"),
        "provider_id": raw.get("provider_id"),
        "license_scope": raw.get("license_scope"),
        "trust_level": raw.get("trust_level"),
        "adjusted_status": raw.get("adjusted_status"),
        "row_count": raw.get("row_count"),
        "symbol_count": raw.get("symbol_count"),
        "stale_last_bar_hours": raw.get("stale_last_bar_hours"),
        "warnings": raw.get("warnings"),
        "blockers": raw.get("blockers"),
        "evidence_sha256": raw.get("evidence_sha256"),
    }


__all__ = ["evaluate_market_data_integrity", "public_market_data_integrity_payload"]
