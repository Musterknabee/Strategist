from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_retrieval import write_paper_execution_evidence_bundle_retention_custody_retrieval_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_retrieval_verification import write_paper_execution_evidence_bundle_retention_custody_retrieval_verification_artifact
from strategy_validator.cli.paper_broker import main
from tests.application.test_paper_execution_evidence_bundle_retention_custody_retrieval import _setup_archive_verification


def test_cli_retention_custody_return_round_trip(tmp_path: Path, capsys) -> None:
    output_root, archive_verification_path = _setup_archive_verification(tmp_path)
    retrieval_path, _, retrieval = write_paper_execution_evidence_bundle_retention_custody_retrieval_artifact(
        retention_custody_archive_verification_artifact_path=archive_verification_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 10, tzinfo=timezone.utc),
    )
    assert retrieval.retrieval_status == "RETRIEVED"
    retrieval_verification_path, _, retrieval_verification = write_paper_execution_evidence_bundle_retention_custody_retrieval_verification_artifact(
        retention_custody_retrieval_artifact_path=retrieval_path,
        output_root=output_root,
    )
    assert retrieval_verification.verification_status == "PASS"

    rc = main([
        "return-evidence-bundle-retention-custody-retrieval",
        "--retention-custody-retrieval-verification-artifact",
        str(retrieval_verification_path),
        "--output-root",
        str(output_root),
        "--returned-by",
        "operator-a",
        "--return-reason",
        "review complete",
    ])
    assert rc == 0
    return_payload = json.loads(capsys.readouterr().out)
    assert return_payload["return_status"] == "RETURNED"

    rc = main([
        "verify-evidence-bundle-retention-custody-return",
        "--retention-custody-return-artifact",
        return_payload["artifact"],
        "--output-root",
        str(output_root),
    ])
    assert rc == 0
    verification_payload = json.loads(capsys.readouterr().out)
    assert verification_payload["verification_status"] == "PASS"
    assert verification_payload["custody_return_statement_hash_valid"] is True


def test_cli_retention_custody_return_help_contains_commands(capsys) -> None:
    try:
        main(["--help"])
    except SystemExit:
        pass
    help_text = capsys.readouterr().out
    assert "return-evidence-bundle-retention-custody-retrieval" in help_text
    assert "verify-evidence-bundle-retention-custody-return" in help_text
