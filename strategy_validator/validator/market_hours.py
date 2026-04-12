"""
US equities regular-hours helpers for freshness law (NYSE schedule, America/New_York).

This is an **exchange-calendar simplification** (Mon–Fri, 09:30–16:00 local), not a full
holiday calendar. Operators requiring exchange holidays should use SNAPSHOT mode or a
calendar-aware feed upstream.
"""
from __future__ import annotations

from datetime import datetime, time as time_cls
from zoneinfo import ZoneInfo

_NY = ZoneInfo("America/New_York")
_RTH_OPEN = time_cls(9, 30, 0)
_RTH_CLOSE = time_cls(16, 0, 0)


def us_equities_regular_session_open(at_utc: datetime) -> bool:
    """True when ``at_utc`` falls on NYSE regular trading hours (weekday 09:30–16:00 NY)."""
    if at_utc.tzinfo is None:
        at_utc = at_utc.replace(tzinfo=ZoneInfo("UTC"))
    local = at_utc.astimezone(_NY)
    if local.weekday() >= 5:
        return False
    t = local.time()
    return _RTH_OPEN <= t < _RTH_CLOSE
