from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def summarize_burnin_artifact(artifact_path: Path) -> dict[str, Any]:
    lines = [line.strip() for line in artifact_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    parsed: list[dict[str, Any]] = []
    for line in lines:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            parsed.append(value)
    statuses = [str(item.get('status')) for item in parsed if item.get('status') is not None]
    fallback_count = sum(1 for item in parsed if item.get('fallback_applied') is True)
    stale_count = sum(1 for item in parsed if str(item.get('freshness_status', '')).upper() == 'STALE')
    symbols = sorted({str(item.get('symbol')) for item in parsed if item.get('symbol')})
    return {
        'artifact_path': str(artifact_path),
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'round_count': len(parsed),
        'statuses': statuses,
        'symbols': symbols,
        'fallback_count': fallback_count,
        'stale_count': stale_count,
    }


def summarize_burnin_set(*artifact_paths: Path) -> dict[str, Any]:
    summaries = [summarize_burnin_artifact(path) for path in artifact_paths]
    return {
        'artifact_count': len(summaries),
        'artifacts': summaries,
        'total_round_count': sum(int(item['round_count']) for item in summaries),
        'total_fallback_count': sum(int(item['fallback_count']) for item in summaries),
        'total_stale_count': sum(int(item['stale_count']) for item in summaries),
    }
