from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_retrieve_provider_samples_manifest_includes_generated_timestamp(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    output_dir = tmp_path / "provider_samples"
    script_path = repo_root / "scripts" / "retrieve_provider_samples.py"

    proc = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--public-only",
            "--no-network",
            "--max-samples",
            "2",
            "--manifest-json",
            "--output-dir",
            str(output_dir),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout

    manifest_path = output_dir / "manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "provider_samples_manifest/v1"
    assert isinstance(payload.get("generated_at_utc"), str)
    assert payload["generated_at_utc"]
    assert payload["paper_only"] is True
    assert payload["live_trading_blocked"] is True
    assert payload["replayable_offline"] is True
    assert payload["command"] == "python scripts/retrieve_provider_samples.py"
