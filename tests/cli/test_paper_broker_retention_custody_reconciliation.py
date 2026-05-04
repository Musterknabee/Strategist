from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_inventory import write_paper_execution_evidence_bundle_retention_custody_inventory_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_inventory_verification import write_paper_execution_evidence_bundle_retention_custody_inventory_verification_artifact
from strategy_validator.cli.paper_broker import main
from tests.application.test_paper_execution_evidence_bundle_retention_custody_inventory import _setup_redeposit_verification


def test_cli_retention_custody_reconciliation_round_trip(tmp_path: Path, capsys) -> None:
    output_root, redeposit_verification_path = _setup_redeposit_verification(tmp_path)
    inventory_path, _, inventory = write_paper_execution_evidence_bundle_retention_custody_inventory_artifact(
        retention_custody_redeposit_verification_artifact_path=redeposit_verification_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 16, tzinfo=timezone.utc),
    )
    assert inventory.inventory_status == "INVENTORIED"
    inventory_verification_path, _, inventory_verification = write_paper_execution_evidence_bundle_retention_custody_inventory_verification_artifact(
        retention_custody_inventory_artifact_path=inventory_path,
        output_root=output_root,
    )
    assert inventory_verification.verification_status == "PASS"

    rc = main([
        "reconcile-evidence-bundle-retention-custody-inventory",
        "--retention-custody-inventory-verification-artifact",
        str(inventory_verification_path),
        "--output-root",
        str(output_root),
        "--reconciled-by",
        "operator-a",
        "--reconciliation-reason",
        "inventory verified",
    ])
    assert rc == 0
    reconciliation_payload = json.loads(capsys.readouterr().out)
    assert reconciliation_payload["reconciliation_status"] == "RECONCILED"

    rc = main([
        "verify-evidence-bundle-retention-custody-reconciliation",
        "--retention-custody-reconciliation-artifact",
        reconciliation_payload["artifact"],
        "--output-root",
        str(output_root),
    ])
    assert rc == 0
    verification_payload = json.loads(capsys.readouterr().out)
    assert verification_payload["verification_status"] == "PASS"
    assert verification_payload["custody_reconciliation_statement_hash_valid"] is True


def test_cli_retention_custody_reconciliation_help_contains_commands(capsys) -> None:
    try:
        main(["--help"])
    except SystemExit:
        pass
    help_text = capsys.readouterr().out
    assert "reconcile-evidence-bundle-retention-custody-inventory" in help_text
    assert "verify-evidence-bundle-retention-custody-reconciliation" in help_text
