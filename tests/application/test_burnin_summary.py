from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.burnin import summarize_burnin_artifact, summarize_burnin_set


def test_summarize_burnin_artifact_counts_rounds_and_flags(tmp_path: Path) -> None:
    artifact = tmp_path / 'pilot.jsonl'
    artifact.write_text(
        '\n'.join([
            json.dumps({'round': 1, 'status': 'SUCCESS', 'symbol': 'SPY', 'fallback_applied': False, 'freshness_status': 'FRESH'}),
            json.dumps({'round': 2, 'status': 'SUCCESS', 'symbol': 'QQQ', 'fallback_applied': True, 'freshness_status': 'STALE'}),
        ]) + '\n',
        encoding='utf-8',
    )
    summary = summarize_burnin_artifact(artifact)
    assert summary['round_count'] == 2
    assert summary['fallback_count'] == 1
    assert summary['stale_count'] == 1
    assert summary['symbols'] == ['QQQ', 'SPY']


def test_summarize_burnin_set_aggregates_artifacts(tmp_path: Path) -> None:
    a = tmp_path / 'a.jsonl'
    b = tmp_path / 'b.jsonl'
    a.write_text(json.dumps({'round': 1, 'status': 'SUCCESS', 'symbol': 'SPY'}) + '\n', encoding='utf-8')
    b.write_text(json.dumps({'round': 1, 'status': 'SUCCESS', 'symbol': 'QQQ', 'fallback_applied': True}) + '\n', encoding='utf-8')
    summary = summarize_burnin_set(a, b)
    assert summary['artifact_count'] == 2
    assert summary['total_round_count'] == 2
    assert summary['total_fallback_count'] == 1
