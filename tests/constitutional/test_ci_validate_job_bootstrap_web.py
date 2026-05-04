"""CI validate job should install Strategist web deps when package-lock exists (parity with strategist-web job)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_JOB_HEADER = re.compile(r"^  [a-z0-9-]+:$")


def _github_workflow_job_block(workflow_text: str, job_name: str) -> str:
    lines = workflow_text.splitlines()
    marker = f"  {job_name}:"
    start = next(i for i, line in enumerate(lines) if line == marker)
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if _JOB_HEADER.match(lines[i]) and lines[i] != marker:
            end = i
            break
    return "\n".join(lines[start:end])


def test_validate_job_bootstraps_strategist_web_when_lockfile_present() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    block = _github_workflow_job_block(workflow, "validate")
    assert "actions/setup-node@v4" in block
    assert "Install Strategist web dependencies (validate)" in block
    assert "working-directory: ui/strategist-web" in block
    assert "run: npm ci" in block
    assert "hashFiles('ui/strategist-web/package-lock.json') != ''" in block
