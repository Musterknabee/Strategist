from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_seal import write_paper_execution_evidence_bundle_retention_custody_seal_artifact
from strategy_validator.cli.paper_broker import main
from tests.application.test_paper_execution_evidence_bundle_retention_custody_seal import _setup_custody_register_verification


def test_cli_verify_evidence_bundle_retention_custody_seal_writes_artifact(capsys, tmp_path: Path) -> None:
    output_root, latest_register_verification_path = _setup_custody_register_verification(tmp_path)
    latest_seal_path, _, _ = write_paper_execution_evidence_bundle_retention_custody_seal_artifact(
        retention_custody_register_verification_artifact_path=latest_register_verification_path,
        output_root=output_root,
    )

    rc = main([
        "verify-evidence-bundle-retention-custody-seal",
        "--retention-custody-seal-artifact",
        str(latest_seal_path),
        "--output-root",
        str(output_root),
    ])

    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["ok"] is True
    assert out["verification_status"] == "PASS"
    assert out["custody_seal_statement_hash_valid"] is True
    assert Path(out["artifact"]).exists()


def test_cli_verify_evidence_bundle_retention_custody_seal_returns_fail_for_missing(capsys, tmp_path: Path) -> None:
    rc = main(["verify-evidence-bundle-retention-custody-seal", "--output-root", str(tmp_path / "paper_broker")])

    out = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert out["ok"] is False
    assert out["verification_status"] == "FAIL"
    assert out["blockers"]
