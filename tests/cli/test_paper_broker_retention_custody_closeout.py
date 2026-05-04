from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_completion import write_paper_execution_evidence_bundle_retention_custody_completion_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_completion_verification import write_paper_execution_evidence_bundle_retention_custody_completion_verification_artifact
from strategy_validator.cli.paper_broker import main
from tests.application.test_paper_execution_evidence_bundle_retention_custody_completion import _setup_acknowledgment_verification


def test_cli_retention_custody_closeout_round_trip(tmp_path: Path, capsys) -> None:
    output_root, ack_verification_path = _setup_acknowledgment_verification(tmp_path)
    completion_path, _, completion = write_paper_execution_evidence_bundle_retention_custody_completion_artifact(
        retention_custody_acknowledgment_verification_artifact_path=ack_verification_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 4, tzinfo=timezone.utc),
    )
    assert completion.completion_status == "COMPLETED"
    completion_verification_path, _, completion_verification = write_paper_execution_evidence_bundle_retention_custody_completion_verification_artifact(
        retention_custody_completion_artifact_path=completion_path,
        output_root=output_root,
    )
    assert completion_verification.verification_status == "PASS"

    rc = main(["closeout-evidence-bundle-retention-custody-renewal", "--retention-custody-completion-verification-artifact", str(completion_verification_path), "--output-root", str(output_root), "--closed-out-by", "operator-a"])
    assert rc == 0
    closeout_payload = json.loads(capsys.readouterr().out)
    assert closeout_payload["closeout_status"] == "CLOSED"

    rc = main(["verify-evidence-bundle-retention-custody-closeout", "--retention-custody-closeout-artifact", closeout_payload["artifact"], "--output-root", str(output_root)])
    assert rc == 0
    verification_payload = json.loads(capsys.readouterr().out)
    assert verification_payload["verification_status"] == "PASS"
    assert verification_payload["custody_closeout_statement_hash_valid"] is True


def test_cli_retention_custody_closeout_help_contains_commands(capsys) -> None:
    try:
        main(["--help"])
    except SystemExit:
        pass
    help_text = capsys.readouterr().out
    assert "closeout-evidence-bundle-retention-custody-renewal" in help_text
    assert "verify-evidence-bundle-retention-custody-closeout" in help_text
