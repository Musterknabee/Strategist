from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.cli.paper_broker import main
from tests.application.test_paper_execution_evidence_bundle_retention_custody_review import _setup_custody_continuity_verification


def test_cli_review_evidence_bundle_retention_custody_writes_artifact(capsys, tmp_path: Path) -> None:
    output_root, latest_continuity_verification_path = _setup_custody_continuity_verification(tmp_path)

    rc = main([
        "review-evidence-bundle-retention-custody",
        "--retention-custody-continuity-verification-artifact",
        str(latest_continuity_verification_path),
        "--reviewed-by",
        "operator-jp",
        "--custody-location",
        "vault-a",
        "--output-root",
        str(output_root),
    ])

    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["ok"] is True
    assert payload["review_status"] == "REVIEWED"
    assert payload["reviewed_by"] == "operator-jp"
    assert Path(payload["artifact"]).exists()


def test_cli_review_evidence_bundle_retention_custody_returns_blocked_for_missing(capsys, tmp_path: Path) -> None:
    rc = main([
        "review-evidence-bundle-retention-custody",
        "--retention-custody-continuity-verification-artifact",
        str(tmp_path / "missing.json"),
        "--output-root",
        str(tmp_path / "paper_broker"),
    ])

    payload = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert payload["ok"] is False
    assert payload["review_status"] == "BLOCKED"
    assert "RETENTION_CUSTODY_CONTINUITY_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE" in payload["blockers"]
