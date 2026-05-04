from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_reconciliation import write_paper_execution_evidence_bundle_retention_custody_reconciliation_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_reconciliation_verification import write_paper_execution_evidence_bundle_retention_custody_reconciliation_verification_artifact
from strategy_validator.cli.paper_broker import main
from tests.application.test_paper_execution_evidence_bundle_retention_custody_reconciliation import _setup_inventory_verification


def test_cli_retention_custody_certification_round_trip(tmp_path: Path, capsys) -> None:
    output_root, inventory_verification_path = _setup_inventory_verification(tmp_path)
    reconciliation_path, _, reconciliation = write_paper_execution_evidence_bundle_retention_custody_reconciliation_artifact(
        retention_custody_inventory_verification_artifact_path=inventory_verification_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 18, tzinfo=timezone.utc),
    )
    assert reconciliation.reconciliation_status == "RECONCILED"
    reconciliation_verification_path, _, reconciliation_verification = write_paper_execution_evidence_bundle_retention_custody_reconciliation_verification_artifact(
        retention_custody_reconciliation_artifact_path=reconciliation_path,
        output_root=output_root,
    )
    assert reconciliation_verification.verification_status == "PASS"

    rc = main([
        "certify-evidence-bundle-retention-custody-reconciliation",
        "--retention-custody-reconciliation-verification-artifact",
        str(reconciliation_verification_path),
        "--output-root",
        str(output_root),
        "--certified-by",
        "operator-a",
        "--certification-reason",
        "reconciliation accepted",
    ])
    assert rc == 0
    certification_payload = json.loads(capsys.readouterr().out)
    assert certification_payload["certification_status"] == "CERTIFIED"

    rc = main([
        "verify-evidence-bundle-retention-custody-certification",
        "--retention-custody-certification-artifact",
        certification_payload["artifact"],
        "--output-root",
        str(output_root),
    ])
    assert rc == 0
    verification_payload = json.loads(capsys.readouterr().out)
    assert verification_payload["verification_status"] == "PASS"
    assert verification_payload["custody_certification_statement_hash_valid"] is True


def test_cli_retention_custody_certification_help_contains_commands(capsys) -> None:
    try:
        main(["--help"])
    except SystemExit:
        pass
    help_text = capsys.readouterr().out
    assert "certify-evidence-bundle-retention-custody-reconciliation" in help_text
    assert "verify-evidence-bundle-retention-custody-certification" in help_text
