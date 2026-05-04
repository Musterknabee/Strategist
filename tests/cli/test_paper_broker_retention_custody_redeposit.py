from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_return import write_paper_execution_evidence_bundle_retention_custody_return_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_return_verification import write_paper_execution_evidence_bundle_retention_custody_return_verification_artifact
from strategy_validator.cli.paper_broker import main
from tests.application.test_paper_execution_evidence_bundle_retention_custody_return import _setup_retrieval_verification


def test_cli_retention_custody_redeposit_round_trip(tmp_path: Path, capsys) -> None:
    output_root, retrieval_verification_path = _setup_retrieval_verification(tmp_path)
    return_path, _, returned = write_paper_execution_evidence_bundle_retention_custody_return_artifact(
        retention_custody_retrieval_verification_artifact_path=retrieval_verification_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 12, tzinfo=timezone.utc),
    )
    assert returned.return_status == "RETURNED"
    return_verification_path, _, return_verification = write_paper_execution_evidence_bundle_retention_custody_return_verification_artifact(
        retention_custody_return_artifact_path=return_path,
        output_root=output_root,
    )
    assert return_verification.verification_status == "PASS"

    rc = main([
        "redeposit-evidence-bundle-retention-custody-return",
        "--retention-custody-return-verification-artifact",
        str(return_verification_path),
        "--output-root",
        str(output_root),
        "--redeposited-by",
        "operator-a",
        "--redeposit-reason",
        "return verified",
    ])
    assert rc == 0
    redeposit_payload = json.loads(capsys.readouterr().out)
    assert redeposit_payload["redeposit_status"] == "REDEPOSITED"

    rc = main([
        "verify-evidence-bundle-retention-custody-redeposit",
        "--retention-custody-redeposit-artifact",
        redeposit_payload["artifact"],
        "--output-root",
        str(output_root),
    ])
    assert rc == 0
    verification_payload = json.loads(capsys.readouterr().out)
    assert verification_payload["verification_status"] == "PASS"
    assert verification_payload["custody_redeposit_statement_hash_valid"] is True


def test_cli_retention_custody_redeposit_help_contains_commands(capsys) -> None:
    try:
        main(["--help"])
    except SystemExit:
        pass
    help_text = capsys.readouterr().out
    assert "redeposit-evidence-bundle-retention-custody-return" in help_text
    assert "verify-evidence-bundle-retention-custody-redeposit" in help_text
