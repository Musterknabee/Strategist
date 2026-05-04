from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_certification import write_paper_execution_evidence_bundle_retention_custody_certification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_certification_verification import write_paper_execution_evidence_bundle_retention_custody_certification_verification_artifact
from strategy_validator.cli.paper_broker import main
from tests.application.test_paper_execution_evidence_bundle_retention_custody_certification import _setup_reconciliation_verification


def test_cli_retention_custody_attestation_round_trip(tmp_path: Path, capsys) -> None:
    output_root, reconciliation_verification_path = _setup_reconciliation_verification(tmp_path)
    certification_path, _, certification = write_paper_execution_evidence_bundle_retention_custody_certification_artifact(
        retention_custody_reconciliation_verification_artifact_path=reconciliation_verification_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 20, tzinfo=timezone.utc),
    )
    assert certification.certification_status == "CERTIFIED"
    certification_verification_path, _, certification_verification = write_paper_execution_evidence_bundle_retention_custody_certification_verification_artifact(
        retention_custody_certification_artifact_path=certification_path,
        output_root=output_root,
    )
    assert certification_verification.verification_status == "PASS"

    rc = main([
        "attest-evidence-bundle-retention-custody-certification",
        "--retention-custody-certification-verification-artifact",
        str(certification_verification_path),
        "--output-root",
        str(output_root),
        "--attested-by",
        "operator-a",
        "--attestation-reason",
        "certification accepted",
    ])
    assert rc == 0
    attestation_payload = json.loads(capsys.readouterr().out)
    assert attestation_payload["attestation_status"] == "ATTESTED"

    rc = main([
        "verify-evidence-bundle-retention-custody-attestation",
        "--retention-custody-attestation-artifact",
        attestation_payload["artifact"],
        "--output-root",
        str(output_root),
    ])
    assert rc == 0
    verification_payload = json.loads(capsys.readouterr().out)
    assert verification_payload["verification_status"] == "PASS"
    assert verification_payload["custody_attestation_statement_hash_valid"] is True


def test_cli_retention_custody_attestation_help_contains_commands(capsys) -> None:
    try:
        main(["--help"])
    except SystemExit:
        pass
    help_text = capsys.readouterr().out
    assert "attest-evidence-bundle-retention-custody-certification" in help_text
    assert "verify-evidence-bundle-retention-custody-attestation" in help_text
