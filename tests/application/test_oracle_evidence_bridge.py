from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.oracle_evidence_bridge import discover_latest_batch_summary


def test_discover_latest_batch_summary_prefers_oracle_next_batch(tmp_path: Path) -> None:
    runs = tmp_path / "strategy_runs" / "batch-a"
    for run_id in ("older-run", "full-runtime", "oracle-next-batch"):
        d = runs / run_id
        d.mkdir(parents=True)
        (d / "batch_summary.json").write_text(
            json.dumps({"batch_id": "batch-a", "run_id": run_id, "strategies": [], "output_dir": str(d)}),
            encoding="utf-8",
        )
    picked = discover_latest_batch_summary(tmp_path)
    assert picked.parent.name == "oracle-next-batch"
