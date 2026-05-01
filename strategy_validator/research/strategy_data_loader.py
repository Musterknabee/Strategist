"""Load governed local bar snapshots for strategy research (no network)."""
from __future__ import annotations

import csv
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from strategy_validator.contracts.strategy_data_snapshot import (
    LocalBarsDataSourceConfig,
    StrategyBar,
    StrategyDataSnapshot,
    StrategyDataSourceClassification,
    StrategyPitSnapshotStatus,
    snapshot_data_gates_promotion,
)
from strategy_validator.contracts.strategy_batch import StrategyBatchSpec, StrategyCandidateSpec
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

_ALLOWED_REL_PREFIXES = (
    "data/strategy_snapshots",
    "artifacts/strategy_data",
    "tests/fixtures",
)


class StrategyDataLoadError(Exception):
    def __init__(self, blockers: list[str]) -> None:
        super().__init__(", ".join(blockers))
        self.blockers = blockers


def _parse_ts(raw: str) -> datetime:
    s = raw.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _float_cell(key: str, raw: str, *, row_no: int) -> float:
    try:
        v = float(raw.strip())
        if not math.isfinite(v):
            raise ValueError
        return v
    except (TypeError, ValueError) as exc:
        raise StrategyDataLoadError([f"MALFORMED_NUMERIC:{key}:row{row_no}"]) from exc


def _resolve_bars_file(path_str: str, *, repo_root: Path) -> Path:
    p = Path(path_str)
    if not p.is_absolute():
        p = (repo_root / p).resolve()
    else:
        p = p.resolve()
    root = repo_root.resolve()
    try:
        p.relative_to(root)
    except ValueError as exc:
        raise StrategyDataLoadError(["BARS_PATH_OUTSIDE_REPO"]) from exc
    rel_posix = p.relative_to(root).as_posix()
    if not any(rel_posix == pref or rel_posix.startswith(pref + "/") for pref in _ALLOWED_REL_PREFIXES):
        raise StrategyDataLoadError(["BARS_PATH_NOT_IN_ALLOWED_PREFIX"])
    if not p.is_file():
        raise StrategyDataLoadError(["BARS_FILE_NOT_FOUND"])
    return p


def _rows_from_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    warnings: list[str] = []
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise StrategyDataLoadError(["CSV_NO_HEADER"])
        fields = {f.strip().lower(): f for f in reader.fieldnames if f}
        required = {"symbol", "timestamp_utc", "open", "high", "low", "close", "volume"}
        if not required.issubset(fields.keys()):
            raise StrategyDataLoadError(["CSV_MISSING_REQUIRED_COLUMNS"])
        for i, rec in enumerate(reader, start=2):
            if not rec or all((v or "").strip() == "" for v in rec.values()):
                continue
            norm: dict[str, str] = {}
            for k in required:
                orig_key = fields[k]
                norm[k] = (rec.get(orig_key) or "").strip()
            if "published_at_utc" in fields:
                norm["published_at_utc"] = (rec.get(fields["published_at_utc"]) or "").strip()
            rows.append(norm)
    return rows, warnings


def _rows_from_json(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise StrategyDataLoadError(["JSON_BARS_MUST_BE_ARRAY"])
    rows: list[dict[str, str]] = []
    for i, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise StrategyDataLoadError([f"JSON_BAR_NOT_OBJECT:{i}"])
        try:
            rows.append(
                {
                    "symbol": str(item["symbol"]).strip(),
                    "timestamp_utc": str(item["timestamp_utc"]).strip(),
                    "open": str(item["open"]).strip(),
                    "high": str(item["high"]).strip(),
                    "low": str(item["low"]).strip(),
                    "close": str(item["close"]).strip(),
                    "volume": str(item.get("volume", "0")).strip(),
                    "published_at_utc": str(item.get("published_at_utc", "")).strip(),
                }
            )
        except KeyError as exc:
            raise StrategyDataLoadError([f"JSON_BAR_MISSING_FIELD:{i}:{exc.args[0]}"]) from exc
    return rows, []


def _dict_rows_to_bars(rows: list[dict[str, str]]) -> list[StrategyBar]:
    bars: list[StrategyBar] = []
    seen: set[tuple[str, str]] = set()
    for i, r in enumerate(rows, start=1):
        sym = r["symbol"]
        if not sym:
            raise StrategyDataLoadError([f"EMPTY_SYMBOL:row{i}"])
        ts = _parse_ts(r["timestamp_utc"])
        key = (sym, ts.isoformat())
        if key in seen:
            raise StrategyDataLoadError([f"DUPLICATE_BAR:{sym}:{ts.isoformat()}"])
        seen.add(key)
        o = _float_cell("open", r["open"], row_no=i)
        h = _float_cell("high", r["high"], row_no=i)
        l = _float_cell("low", r["low"], row_no=i)
        c = _float_cell("close", r["close"], row_no=i)
        vol_raw = r.get("volume", "0") or "0"
        v = _float_cell("volume", vol_raw, row_no=i)
        bar = StrategyBar(symbol=sym, timestamp_utc=ts, open=o, high=h, low=l, close=c, volume=v)
        bars.append(bar)
    return bars


def bars_digest(bars: Iterable[StrategyBar]) -> str:
    """Stable SHA-256 over sorted normalized bar records."""

    items = []
    for b in sorted(bars, key=lambda x: (x.symbol, x.timestamp_utc.isoformat())):
        items.append(
            {
                "close": b.close,
                "high": b.high,
                "low": b.low,
                "open": b.open,
                "symbol": b.symbol,
                "timestamp_utc": b.timestamp_utc.isoformat(),
                "volume": b.volume,
            }
        )
    return canonical_json_sha256(items)


def _universe_symbols(universe: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"[,\s]+", universe.strip()) if p.strip()]
    return parts or [universe.strip()]


@dataclass(frozen=True)
class LocalBarsLoadResult:
    bars: list[StrategyBar]
    snapshot: StrategyDataSnapshot
    warnings: list[str]


def load_local_bars_snapshot(
    *,
    repo_root: Path,
    candidate: StrategyCandidateSpec,
    batch: StrategyBatchSpec,
    data_source: LocalBarsDataSourceConfig,
    retrieved_at_utc: datetime,
) -> LocalBarsLoadResult:
    """Load bars from CSV/JSON; filter by universe, lookback, and as-of (PIT)."""

    path = _resolve_bars_file(data_source.path, repo_root=repo_root)
    if path.suffix.lower() == ".csv":
        dict_rows, w0 = _rows_from_csv(path)
    elif path.suffix.lower() == ".json":
        dict_rows, w0 = _rows_from_json(path)
    else:
        raise StrategyDataLoadError(["UNSUPPORTED_BARS_FORMAT"])

    warnings = list(w0)
    bars = _dict_rows_to_bars(dict_rows)

    as_of = candidate.as_of_utc.astimezone(timezone.utc)
    lookback_start = as_of - timedelta(days=int(candidate.lookback_days))

    syms = set(_universe_symbols(candidate.universe))
    filtered: list[StrategyBar] = []
    leakage = 0
    for b in bars:
        if b.symbol not in syms:
            continue
        if b.timestamp_utc > as_of:
            leakage += 1
            continue
        if b.timestamp_utc < lookback_start:
            continue
        filtered.append(b)

    if leakage:
        warnings.append(f"EXCLUDED_FUTURE_ROWS:{leakage}")

    filtered.sort(key=lambda x: (x.symbol, x.timestamp_utc))

    if not filtered:
        raise StrategyDataLoadError(["NO_BARS_AFTER_FILTER"])

    row_count = len(filtered)
    symbol_count = len({b.symbol for b in filtered})
    bars_sha = bars_digest(filtered)

    pub_times: list[datetime] = []
    for r in dict_rows:
        if r["symbol"] not in syms:
            continue
        ts = _parse_ts(r["timestamp_utc"])
        if ts > as_of or ts < lookback_start:
            continue
        pub_raw = r.get("published_at_utc", "").strip()
        if pub_raw:
            pub_times.append(_parse_ts(pub_raw))
    published_at = min(pub_times) if pub_times else None

    claim = data_source.pit_status
    eff_pit = claim
    if claim == StrategyPitSnapshotStatus.PIT_VERIFIED and published_at is None:
        eff_pit = StrategyPitSnapshotStatus.MISSING_RELEASE_TIMESTAMPS
        warnings.append("LOCAL_SNAPSHOT_NO_PUBLISHED_AT_METADATA")

    snap = StrategyDataSnapshot(
        strategy_id=candidate.strategy_id,
        batch_id=batch.batch_id,
        universe=candidate.universe,
        timeframe=candidate.timeframe,
        as_of_utc=as_of,
        lookback_start_utc=lookback_start,
        lookback_end_utc=as_of,
        provider_id="local_file",
        source_classification=StrategyDataSourceClassification.LOCAL_GOVERNED_BARS,
        pit_status=eff_pit,
        retrieved_at_utc=retrieved_at_utc,
        published_at_utc=published_at,
        bars_path=str(path),
        bars_sha256=bars_sha,
        row_count=row_count,
        symbol_count=symbol_count,
        warnings=list(warnings),
        blockers=[],
        may_gate_live_promotion=False,
    )
    snap = snap.model_copy(update={"may_gate_live_promotion": snapshot_data_gates_promotion(snap)})
    return LocalBarsLoadResult(bars=filtered, snapshot=snap, warnings=list(warnings))


__all__ = [
    "LocalBarsLoadResult",
    "StrategyDataLoadError",
    "bars_digest",
    "load_local_bars_snapshot",
]
