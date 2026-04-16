from __future__ import annotations

from pathlib import Path


def test_ci_workflow_uploads_release_candidate_handoff_artifacts() -> None:
    workflow = Path('.github/workflows/ci.yml').read_text(encoding='utf-8')

    assert 'actions/upload-artifact@v4' in workflow
    assert 'Upload CI handoff artifacts' in workflow
    assert 'artifacts/release_candidate/**' in workflow


def test_ci_workflow_validates_strategist_web_shell() -> None:
    workflow = Path('.github/workflows/ci.yml').read_text(encoding='utf-8')

    assert 'actions/setup-node@v4' in workflow
    assert 'ui/strategist-web/package-lock.json' in workflow
    assert 'Install Strategist web dependencies' in workflow
    assert 'working-directory: ui/strategist-web' in workflow
    assert 'npm ci' in workflow
    assert 'Strategist web check' in workflow
    assert 'npm run check' in workflow
