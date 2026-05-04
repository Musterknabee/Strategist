"""Aggregate pilot probe NDJSON and suggest policy env lines from counts only."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


def load_pilot_records(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def summarize_records(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    recs = list(records)
    n = len(recs)
    if n == 0:
        return {"rounds": 0}

    domains = Counter((r.get("failure_domain") or "NONE") for r in recs)
    codes = Counter((r.get("failure_code") or "NONE") for r in recs)
    statuses = Counter((r.get("provider_status") or "NONE") for r in recs)
    ages = [float(r["snapshot_age_s"]) for r in recs if r.get("snapshot_age_s") is not None]
    latencies = [float(r["latency_ms"]) for r in recs if r.get("latency_ms") is not None]
    primary_lat = [float(r["primary_latency_ms"]) for r in recs if r.get("primary_latency_ms") is not None]
    fallback_lat = [float(r["fallback_latency_ms"]) for r in recs if r.get("fallback_latency_ms") is not None]

    ev_domains: Counter[str] = Counter()
    ev_codes: Counter[str] = Counter()
    for r in recs:
        for ev in r.get("vendor_failure_events") or []:
            if isinstance(ev, dict):
                ev_domains[str(ev.get("domain") or "NONE")] += 1
                ev_codes[str(ev.get("code") or "NONE")] += 1

    eff_fresh = Counter(
        (r.get("effective_freshness_status") or _infer_effective_freshness(r) or "UNKNOWN") for r in recs
    )
    pri_fresh = Counter((r.get("primary_freshness_status") or "UNKNOWN") for r in recs)

    staleish = sum(
        1
        for r in recs
        if (r.get("provider_status") == "STALE")
        or (r.get("effective_freshness_status") == "STALE")
        or (r.get("snapshot_age_s") is not None and float(r["snapshot_age_s"]) > 120)
    )
    rate_limited = (
        domains.get("RATE_LIMIT", 0)
        + ev_domains.get("RATE_LIMIT", 0)
        + sum(1 for r in recs if "429" in str(r.get("error_summary") or ""))
    )
    auth = domains.get("AUTH", 0) + ev_domains.get("AUTH", 0)
    timeouts = statuses.get("TIMEOUT", 0) + sum(1 for r in recs if "timeout" in str(r.get("error_summary") or "").lower())
    fallback_hits = sum(1 for r in recs if r.get("fallback_applied") is True)

    return {
        "rounds": n,
        "pilot_schema_counts": dict(Counter(str(r.get("pilot_schema") or "1") for r in recs)),
        "failure_domain_counts": dict(domains),
        "failure_code_counts": dict(codes),
        "vendor_failure_event_domain_counts": dict(ev_domains),
        "vendor_failure_event_code_counts": dict(ev_codes),
        "provider_status_counts": dict(statuses),
        "timeout_signal_rounds": timeouts,
        "snapshot_age_s_max": max(ages) if ages else None,
        "snapshot_age_s_p95": _p95(ages) if ages else None,
        "latency_ms_distribution": _latency_distribution(latencies),
        "primary_latency_ms_distribution": _latency_distribution(primary_lat),
        "fallback_latency_ms_distribution": _latency_distribution(fallback_lat),
        "latency_ms_p95": _p95(latencies) if latencies else None,
        "effective_freshness_counts": dict(eff_fresh),
        "primary_freshness_counts": dict(pri_fresh),
        "fallback_applied_rounds": fallback_hits,
        "stale_or_old_snapshot_rounds": staleish,
        "rate_limit_proxy_rounds": rate_limited,
        "auth_domain_rounds": auth,
    }


def _p95(vals: list[float]) -> float | None:
    if not vals:
        return None
    s = sorted(vals)
    idx = min(len(s) - 1, int(0.95 * (len(s) - 1)))
    return round(s[idx], 4)


def _p_quantile(vals: list[float], q: float) -> float | None:
    if not vals:
        return None
    s = sorted(vals)
    if len(s) == 1:
        return round(s[0], 4)
    idx = min(len(s) - 1, int(q * (len(s) - 1)))
    return round(s[idx], 4)


def _latency_distribution(latencies: list[float]) -> dict[str, Any]:
    if not latencies:
        return {"n": 0}
    s = sorted(latencies)
    return {
        "n": len(s),
        "min_ms": round(s[0], 4),
        "p50_ms": _p_quantile(latencies, 0.50),
        "p90_ms": _p_quantile(latencies, 0.90),
        "p95_ms": _p_quantile(latencies, 0.95),
        "p99_ms": _p_quantile(latencies, 0.99),
        "max_ms": round(s[-1], 4),
    }


def _infer_effective_freshness(r: dict[str, Any]) -> str | None:
    """Schema-1 rows lack explicit freshness; approximate from status + age."""
    st = r.get("provider_status")
    if st in ("ERROR", "TIMEOUT", "MISSING", "CIRCUIT_OPEN"):
        return None
    if st == "STALE":
        return "STALE"
    if st == "SUCCESS" and r.get("snapshot_present") is True:
        return "FRESH"
    return None


def suggest_env_from_summary(summary: dict[str, Any]) -> list[str]:
    """
    Emit suggested env assignments **only** from observed aggregates (no vendor guessing).

    Lines are comments + optional export hints for operators to paste after review.
    """
    lines: list[str] = []
    n = int(summary.get("rounds") or 0)
    if n == 0:
        lines.append("# No pilot rows - run: python -m strategy_validator.cli.pilot probe --output pilot.jsonl")
        return lines

    lines.append(f"# Pilot summary ({n} rounds) - review before applying")

    rl = int(summary.get("rate_limit_proxy_rounds") or 0)
    if rl >= max(2, n // 4):
        lines.append("# Observed frequent rate-limit signals -> consider more client backoff / fewer parallel pilots.")
        lines.append("# STRATEGY_VALIDATOR_MARKET_DATA_PROVIDER_MAX_RETRIES=<current+1>  # only if failures were transient")
        lines.append("# STRATEGY_VALIDATOR_TELEMETRY_HTTP_BACKOFF_START_MS=200  # telemetry only; does not fix MD")

    stale = int(summary.get("stale_or_old_snapshot_rounds") or 0)
    if stale >= max(2, n // 4):
        lines.append("# Observed many STALE or large snapshot ages -> widen LIVE window or use US RTH off-hours law.")
        lines.append("# STRATEGY_VALIDATOR_LIVE_MARKET_DATA_FRESHNESS_THRESHOLD_SECONDS=<raise_from_observed_p95_age>")
        lines.append("# STRATEGY_VALIDATOR_LIVE_FRESHNESS_MARKET_HOURS_PROFILE=US_EQUITIES_RTH")
        lines.append("# STRATEGY_VALIDATOR_LIVE_FRESHNESS_OFF_HOURS_THRESHOLD_SECONDS=<match_off_hours_p95>")

    auth = int(summary.get("auth_domain_rounds") or 0)
    if auth > 0:
        lines.append("# Observed AUTH-class failures -> fix credentials / key rotation (not threshold tuning).")

    dom = summary.get("failure_domain_counts") or {}
    if int(dom.get("VENDOR_5XX", 0)) >= max(2, n // 4):
        lines.append("# Observed vendor 5xx bursts -> optional softer circuit policy during pilot burn-in.")
        lines.append("# STRATEGY_VALIDATOR_MARKET_DATA_VENDOR_OUTAGE_CIRCUIT_POLICY=LENIENT_TRANSIENT_5XX")

    lat_p95 = summary.get("latency_ms_p95")
    if lat_p95 is not None and float(lat_p95) > 2000:
        lines.append("# High p95 latency - increase HTTP/Alpaca timeouts only if errors were timeouts, not 4xx.")
        lines.append("# STRATEGY_VALIDATOR_ALPACA_TIMEOUT_SECONDS=<from_p95_s_plus_buffer>")
        lines.append("# STRATEGY_VALIDATOR_HTTP_MARKET_DATA_TIMEOUT_SECONDS=<from_p95_s_plus_buffer>")

    if len(lines) == 1:
        lines.append("# No strong aggregate signals - keep policy; extend pilot sample size.")

    return lines
