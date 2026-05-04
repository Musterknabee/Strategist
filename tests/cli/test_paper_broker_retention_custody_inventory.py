from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_redeposit import write_paper_execution_evidence_bundle_retention_custody_redeposit_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_redeposit_verification import write_paper_execution_evidence_bundle_retention_custody_redeposit_verification_artifact
from strategy_validator.cli.paper_broker import main
from tests.application.test_paper_execution_evidence_bundle_retention_custody_redeposit import _setup_return_verification


def test_cli_retention_custody_inventory_round_trip(tmp_path: Path, capsys) -> None:
    output_root, return_verification_path = _setup_return_verification(tmp_path)
    redeposit_path, _, redeposit = write_paper_execution_evidence_bundle_retention_custody_redeposit_artifact(
        retention_custody_return_verification_artifact_path=return_verification_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 14, tzinfo=timezone.utc),
    )
    assert redeposit.redeposit_status == "REDEPOSITED"
    redeposit_verification_path, _, redeposit_verification = write_paper_execution_evidence_bundle_retention_custody_redeposit_verification_artifact(
        retention_custody_redeposit_artifact_path=redeposit_path,
        output_root=output_root,
    )
    assert redeposit_verification.verification_status == "PASS"

    rc = main([
        "inventory-evidence-bundle-retention-custody-redeposit",
        "--retention-custody-redeposit-verification-artifact",
        str(redeposit_verification_path),
        "--output-root",
        str(output_root),
        "--inventoried-by",
        "operator-a",
        "--inventory-reason",
        "redeposit verified",
    ])
    assert rc == 0
    inventory_payload = json.loads(capsys.readouterr().out)
    assert inventory_payload["inventory_status"] == "INVENTORIED"

    rc = main([
        "verify-evidence-bundle-retention-custody-inventory",
        "--retention-custody-inventory-artifact",
        inventory_payload["artifact"],
        "--output-root",
        str(output_root),
    ])
    assert rc == 0
    verification_payload = json.loads(capsys.readouterr().out)
    assert verification_payload["verification_status"] == "PASS"
    assert verification_payload["custody_inventory_statement_hash_valid"] is True


def test_cli_retention_custody_inventory_help_contains_commands(capsys) -> None:
    try:
        main(["--help"])
    except SystemExit:
        pass
    help_text = capsys.readouterr().out
    assert "inventory-evidence-bundle-retention-custody-redeposit" in help_text
    assert "verify-evidence-bundle-retention-custody-inventory" in help_text
