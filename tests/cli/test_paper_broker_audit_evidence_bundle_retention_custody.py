from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_audit import write_paper_execution_evidence_bundle_retention_custody_audit_artifact
from strategy_validator.cli.paper_broker import main
from tests.application.test_paper_execution_evidence_bundle_retention_custody_audit import _setup_custody_seal_verification


def test_cli_audit_evidence_bundle_retention_custody_writes_artifact(capsys, tmp_path: Path) -> None:
    output_root, latest_seal_verification_path = _setup_custody_seal_verification(tmp_path)

    rc = main([
        "audit-evidence-bundle-retention-custody",
        "--retention-custody-seal-verification-artifact",
        str(latest_seal_verification_path),
        "--audited-by",
        "operator-jp",
        "--custody-location",
        "vault-a",
        "--output-root",
        str(output_root),
    ])

    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["ok"] is True
    assert payload["audit_status"] == "AUDITED"
    assert payload["audited_by"] == "operator-jp"
    assert Path(payload["artifact"]).exists()


def test_cli_audit_evidence_bundle_retention_custody_returns_blocked_for_missing(capsys, tmp_path: Path) -> None:
    rc = main([
        "audit-evidence-bundle-retention-custody",
        "--retention-custody-seal-verification-artifact",
        str(tmp_path / "missing.json"),
        "--output-root",
        str(tmp_path / "paper_broker"),
    ])

    payload = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert payload["ok"] is False
    assert payload["audit_status"] == "BLOCKED"
    assert "RETENTION_CUSTODY_SEAL_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE" in payload["blockers"]
