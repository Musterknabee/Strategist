from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_register import write_paper_execution_evidence_bundle_retention_custody_register_artifact
from strategy_validator.cli.paper_broker import main
from tests.application.test_paper_execution_evidence_bundle_retention_custody_register import _setup_acceptance_verification


def test_cli_verify_evidence_bundle_retention_custody_register_writes_artifact(capsys, tmp_path: Path) -> None:
    output_root, latest_acceptance_verification_path = _setup_acceptance_verification(tmp_path)
    latest_register_path, _, _ = write_paper_execution_evidence_bundle_retention_custody_register_artifact(
        retention_handoff_acceptance_verification_artifact_path=latest_acceptance_verification_path,
        output_root=output_root,
    )

    rc = main([
        "verify-evidence-bundle-retention-custody-register",
        "--retention-custody-register-artifact",
        str(latest_register_path),
        "--output-root",
        str(output_root),
    ])

    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["ok"] is True
    assert out["verification_status"] == "PASS"
    assert out["custody_register_statement_hash_valid"] is True
    assert Path(out["artifact"]).exists()


def test_cli_verify_evidence_bundle_retention_custody_register_returns_fail_for_missing(capsys, tmp_path: Path) -> None:
    rc = main(["verify-evidence-bundle-retention-custody-register", "--output-root", str(tmp_path / "paper_broker")])

    out = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert out["ok"] is False
    assert out["verification_status"] == "FAIL"
    assert out["blockers"]
