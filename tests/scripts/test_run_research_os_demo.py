from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_run_research_os_demo_writes_manifest(tmp_path: Path) -> None:
    out_root = tmp_path / "research_os_demo"
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_research_os_demo.py"),
        "--output-root",
        str(out_root),
        "--run-id",
        "pytest-research-os-demo",
        "--overwrite",
        "--skip-benchmark",
        "--skip-portfolio",
        "--json",
    ]
    completed = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=600)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    assert payload.get("ok") is True
    mpath = Path(payload["manifest_path"])
    assert mpath.is_file()
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    assert manifest.get("schema_version") == "research_os_demo_manifest/v1"
    steps = manifest.get("steps")
    assert isinstance(steps, list) and steps
    names = {s.get("name") for s in steps if isinstance(s, dict)}
    assert "gauntlet_batch" in names
    assert "paper_daily" in names
