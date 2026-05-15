"""Parse pytest slowest-duration transcripts for certification sharding hints."""
from __future__ import annotations

import re
from dataclasses import dataclass


_DURATION_LINE = re.compile(
    r"^\s*([0-9.]+)s\s+(call|setup|teardown)\s+(.+)$",
)


@dataclass(frozen=True)
class SlowDurationEntry:
    nodeid: str
    duration_seconds: float
    phase: str

    @property
    def recommended_marker(self) -> str:
        if self.nodeid.startswith("tests/constitutional/"):
            return "slow_constitutional"
        return "slow"

    @property
    def recommended_shard_category(self) -> str:
        if self.nodeid.startswith("tests/constitutional/"):
            return "constitutional_shards"
        return "pytest_execution_shards"


def parse_pytest_durations(transcript: str) -> list[SlowDurationEntry]:
    entries: list[SlowDurationEntry] = []
    in_section = False
    for line in transcript.splitlines():
        if "slowest" in line and "durations" in line:
            in_section = True
            continue
        if not in_section:
            continue
        if line.strip().startswith("="):
            break
        m = _DURATION_LINE.match(line)
        if not m:
            continue
        duration_seconds = float(m.group(1))
        phase = m.group(2)
        nodeid = m.group(3).strip()
        entries.append(SlowDurationEntry(nodeid=nodeid, duration_seconds=duration_seconds, phase=phase))
    entries.sort(key=lambda item: item.duration_seconds, reverse=True)
    return entries


def summarize_by_file(entries: list[SlowDurationEntry]) -> list[dict[str, object]]:
    totals: dict[str, float] = {}
    for entry in entries:
        file_key = entry.nodeid.split("::", 1)[0]
        totals[file_key] = totals.get(file_key, 0.0) + entry.duration_seconds
    rows = [{"file": path, "total_duration_seconds": round(total, 2)} for path, total in totals.items()]
    rows.sort(key=lambda row: float(row["total_duration_seconds"]), reverse=True)
    return rows
