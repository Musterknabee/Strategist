from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_retrieve_provider_samples_explicit_keyed_missing_key_blocks(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    output_dir = tmp_path / "provider_samples"
    script_path = repo_root / "scripts" / "retrieve_provider_samples.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--providers",
            "fred",
            "--output-dir",
            str(output_dir),
            "--manifest-json",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 3, proc.stderr or proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["status"] == "BLOCKED"
    assert "PROVIDER_KEY_PENDING:fred" in payload["blockers"]
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert "PROVIDER_KEY_PENDING:fred" in manifest["blockers"]
    assert manifest["status_summary"]["canonical_status_counts"]["PENDING_KEY"] >= 1
