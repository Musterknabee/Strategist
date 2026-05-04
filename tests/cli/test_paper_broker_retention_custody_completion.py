from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_acknowledgment import write_paper_execution_evidence_bundle_retention_custody_acknowledgment_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_acknowledgment_verification import write_paper_execution_evidence_bundle_retention_custody_acknowledgment_verification_artifact
from strategy_validator.cli.paper_broker import main
from tests.application.test_paper_execution_evidence_bundle_retention_custody_acknowledgment import _setup_notice_verification


def test_cli_retention_custody_completion_round_trip(tmp_path: Path, capsys) -> None:
    output_root, notice_verification_path = _setup_notice_verification(tmp_path)
    ack_path, _, ack = write_paper_execution_evidence_bundle_retention_custody_acknowledgment_artifact(
        retention_custody_notice_verification_artifact_path=notice_verification_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 2, tzinfo=timezone.utc),
    )
    assert ack.acknowledgment_status == "ACKNOWLEDGED"
    ack_verification_path, _, ack_verification = write_paper_execution_evidence_bundle_retention_custody_acknowledgment_verification_artifact(
        retention_custody_acknowledgment_artifact_path=ack_path,
        output_root=output_root,
    )
    assert ack_verification.verification_status == "PASS"

    rc = main(["complete-evidence-bundle-retention-custody-renewal", "--retention-custody-acknowledgment-verification-artifact", str(ack_verification_path), "--output-root", str(output_root), "--completed-by", "operator-a"])
    assert rc == 0
    completion_payload = json.loads(capsys.readouterr().out)
    assert completion_payload["completion_status"] == "COMPLETED"

    rc = main(["verify-evidence-bundle-retention-custody-completion", "--retention-custody-completion-artifact", completion_payload["artifact"], "--output-root", str(output_root)])
    assert rc == 0
    verification_payload = json.loads(capsys.readouterr().out)
    assert verification_payload["verification_status"] == "PASS"
    assert verification_payload["custody_completion_statement_hash_valid"] is True


def test_cli_retention_custody_completion_help_contains_commands(capsys) -> None:
    try:
        main(["--help"])
    except SystemExit:
        pass
    help_text = capsys.readouterr().out
    assert "complete-evidence-bundle-retention-custody-renewal" in help_text
    assert "verify-evidence-bundle-retention-custody-completion" in help_text
