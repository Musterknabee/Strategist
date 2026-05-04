from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_archive import write_paper_execution_evidence_bundle_retention_custody_archive_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_archive_verification import write_paper_execution_evidence_bundle_retention_custody_archive_verification_artifact
from strategy_validator.cli.paper_broker import main
from tests.application.test_paper_execution_evidence_bundle_retention_custody_archive import _setup_closeout_verification


def test_cli_retention_custody_retrieval_round_trip(tmp_path: Path, capsys) -> None:
    output_root, closeout_verification_path = _setup_closeout_verification(tmp_path)
    archive_path, _, archive = write_paper_execution_evidence_bundle_retention_custody_archive_artifact(
        retention_custody_closeout_verification_artifact_path=closeout_verification_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 8, tzinfo=timezone.utc),
    )
    assert archive.archive_status == "ARCHIVED"
    archive_verification_path, _, archive_verification = write_paper_execution_evidence_bundle_retention_custody_archive_verification_artifact(
        retention_custody_archive_artifact_path=archive_path,
        output_root=output_root,
    )
    assert archive_verification.verification_status == "PASS"

    rc = main([
        "retrieve-evidence-bundle-retention-custody-archive",
        "--retention-custody-archive-verification-artifact",
        str(archive_verification_path),
        "--output-root",
        str(output_root),
        "--retrieved-by",
        "operator-a",
        "--retrieval-purpose",
        "quarterly evidence review",
    ])
    assert rc == 0
    retrieval_payload = json.loads(capsys.readouterr().out)
    assert retrieval_payload["retrieval_status"] == "RETRIEVED"

    rc = main([
        "verify-evidence-bundle-retention-custody-retrieval",
        "--retention-custody-retrieval-artifact",
        retrieval_payload["artifact"],
        "--output-root",
        str(output_root),
    ])
    assert rc == 0
    verification_payload = json.loads(capsys.readouterr().out)
    assert verification_payload["verification_status"] == "PASS"
    assert verification_payload["custody_retrieval_statement_hash_valid"] is True


def test_cli_retention_custody_retrieval_help_contains_commands(capsys) -> None:
    try:
        main(["--help"])
    except SystemExit:
        pass
    help_text = capsys.readouterr().out
    assert "retrieve-evidence-bundle-retention-custody-archive" in help_text
    assert "verify-evidence-bundle-retention-custody-retrieval" in help_text
