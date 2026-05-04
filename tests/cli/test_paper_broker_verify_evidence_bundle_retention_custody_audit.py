from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_audit import write_paper_execution_evidence_bundle_retention_custody_audit_artifact
from strategy_validator.cli.paper_broker import main
from tests.application.test_paper_execution_evidence_bundle_retention_custody_audit import _setup_custody_seal_verification


def test_cli_verify_evidence_bundle_retention_custody_audit_writes_artifact(capsys, tmp_path: Path) -> None:
    output_root, latest_seal_verification_path = _setup_custody_seal_verification(tmp_path)
    latest_audit_path, _, _ = write_paper_execution_evidence_bundle_retention_custody_audit_artifact(
        retention_custody_seal_verification_artifact_path=latest_seal_verification_path,
        output_root=output_root,
    )

    rc = main([
        "verify-evidence-bundle-retention-custody-audit",
        "--retention-custody-audit-artifact",
        str(latest_audit_path),
        "--output-root",
        str(output_root),
    ])

    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["ok"] is True
    assert payload["verification_status"] == "PASS"
    assert payload["custody_audit_statement_hash_valid"] is True
    assert Path(payload["artifact"]).exists()


def test_cli_verify_evidence_bundle_retention_custody_audit_returns_fail_for_missing(capsys, tmp_path: Path) -> None:
    rc = main([
        "verify-evidence-bundle-retention-custody-audit",
        "--retention-custody-audit-artifact",
        str(tmp_path / "missing.json"),
        "--output-root",
        str(tmp_path / "paper_broker"),
    ])

    payload = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert payload["ok"] is False
    assert payload["verification_status"] == "FAIL"
    assert "RETENTION_CUSTODY_AUDIT_ARTIFACT_MISSING_OR_UNREADABLE" in payload["blockers"]
