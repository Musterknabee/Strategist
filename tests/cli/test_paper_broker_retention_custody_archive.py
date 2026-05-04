from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_closeout import write_paper_execution_evidence_bundle_retention_custody_closeout_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_closeout_verification import write_paper_execution_evidence_bundle_retention_custody_closeout_verification_artifact
from strategy_validator.cli.paper_broker import main
from tests.application.test_paper_execution_evidence_bundle_retention_custody_closeout import _setup_completion_verification


def test_cli_retention_custody_archive_round_trip(tmp_path: Path, capsys) -> None:
    output_root, completion_verification_path = _setup_completion_verification(tmp_path)
    closeout_path, _, closeout = write_paper_execution_evidence_bundle_retention_custody_closeout_artifact(
        retention_custody_completion_verification_artifact_path=completion_verification_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 6, tzinfo=timezone.utc),
    )
    assert closeout.closeout_status == "CLOSED"
    closeout_verification_path, _, closeout_verification = write_paper_execution_evidence_bundle_retention_custody_closeout_verification_artifact(
        retention_custody_closeout_artifact_path=closeout_path,
        output_root=output_root,
    )
    assert closeout_verification.verification_status == "PASS"

    rc = main([
        "archive-evidence-bundle-retention-custody-closeout",
        "--retention-custody-closeout-verification-artifact",
        str(closeout_verification_path),
        "--output-root",
        str(output_root),
        "--archived-by",
        "operator-a",
        "--custody-location",
        "retention-vault-a",
    ])
    assert rc == 0
    archive_payload = json.loads(capsys.readouterr().out)
    assert archive_payload["archive_status"] == "ARCHIVED"

    rc = main([
        "verify-evidence-bundle-retention-custody-archive",
        "--retention-custody-archive-artifact",
        archive_payload["artifact"],
        "--output-root",
        str(output_root),
    ])
    assert rc == 0
    verification_payload = json.loads(capsys.readouterr().out)
    assert verification_payload["verification_status"] == "PASS"
    assert verification_payload["custody_archive_statement_hash_valid"] is True


def test_cli_retention_custody_archive_help_contains_commands(capsys) -> None:
    try:
        main(["--help"])
    except SystemExit:
        pass
    help_text = capsys.readouterr().out
    assert "archive-evidence-bundle-retention-custody-closeout" in help_text
    assert "verify-evidence-bundle-retention-custody-archive" in help_text
