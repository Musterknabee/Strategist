from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_notice import write_paper_execution_evidence_bundle_retention_custody_notice_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_notice_verification import write_paper_execution_evidence_bundle_retention_custody_notice_verification_artifact
from strategy_validator.cli.paper_broker import main
from tests.application.test_paper_execution_evidence_bundle_retention_custody_notice import _setup_schedule_verification


def test_cli_retention_custody_acknowledgment_round_trip(tmp_path: Path, capsys) -> None:
    output_root, schedule_verification_path = _setup_schedule_verification(tmp_path)
    notice_path, _, notice = write_paper_execution_evidence_bundle_retention_custody_notice_artifact(
        retention_custody_schedule_verification_artifact_path=schedule_verification_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc),
    )
    assert notice.notice_status == "NOTICE_PENDING"
    notice_verification_path, _, notice_verification = write_paper_execution_evidence_bundle_retention_custody_notice_verification_artifact(
        retention_custody_notice_artifact_path=notice_path,
        output_root=output_root,
    )
    assert notice_verification.verification_status == "PASS"

    rc = main(["acknowledge-evidence-bundle-retention-custody-notice", "--retention-custody-notice-verification-artifact", str(notice_verification_path), "--output-root", str(output_root), "--acknowledged-by", "operator-a"])
    assert rc == 0
    ack_payload = json.loads(capsys.readouterr().out)
    assert ack_payload["acknowledgment_status"] == "ACKNOWLEDGED"

    rc = main(["verify-evidence-bundle-retention-custody-acknowledgment", "--retention-custody-acknowledgment-artifact", ack_payload["artifact"], "--output-root", str(output_root)])
    assert rc == 0
    verification_payload = json.loads(capsys.readouterr().out)
    assert verification_payload["verification_status"] == "PASS"
    assert verification_payload["custody_acknowledgment_statement_hash_valid"] is True


def test_cli_retention_custody_acknowledgment_help_contains_commands(capsys) -> None:
    try:
        main(["--help"])
    except SystemExit:
        pass
    help_text = capsys.readouterr().out
    assert "acknowledge-evidence-bundle-retention-custody-notice" in help_text
    assert "verify-evidence-bundle-retention-custody-acknowledgment" in help_text
