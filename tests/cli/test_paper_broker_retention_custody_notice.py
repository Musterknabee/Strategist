from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.cli.paper_broker import main
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_review_verification import write_paper_execution_evidence_bundle_retention_custody_review_verification_artifact
from tests.application.test_paper_execution_evidence_bundle_retention_custody_review_verification import _setup_custody_review


def test_cli_retention_custody_notice_round_trip(tmp_path: Path, capsys) -> None:
    output_root, review_path = _setup_custody_review(tmp_path)
    review_verification_path, _, review_verification = write_paper_execution_evidence_bundle_retention_custody_review_verification_artifact(
        retention_custody_review_artifact_path=review_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 36, tzinfo=timezone.utc),
    )
    assert review_verification.verification_status == "PASS"

    rc = main(["renew-evidence-bundle-retention-custody", "--retention-custody-review-verification-artifact", str(review_verification_path), "--output-root", str(output_root), "--renewal-interval-days", "45"])
    assert rc == 0
    renewal_payload = json.loads(capsys.readouterr().out)

    rc = main(["verify-evidence-bundle-retention-custody-renewal", "--retention-custody-renewal-artifact", renewal_payload["artifact"], "--output-root", str(output_root)])
    assert rc == 0
    renewal_verification_payload = json.loads(capsys.readouterr().out)

    rc = main(["schedule-evidence-bundle-retention-custody-renewal", "--retention-custody-renewal-verification-artifact", renewal_verification_payload["artifact"], "--output-root", str(output_root), "--reminder-days-before-due", "5"])
    assert rc == 0
    schedule_payload = json.loads(capsys.readouterr().out)

    rc = main(["verify-evidence-bundle-retention-custody-schedule", "--retention-custody-schedule-artifact", schedule_payload["artifact"], "--output-root", str(output_root)])
    assert rc == 0
    schedule_verification_payload = json.loads(capsys.readouterr().out)

    rc = main(["notice-evidence-bundle-retention-custody-renewal", "--retention-custody-schedule-verification-artifact", schedule_verification_payload["artifact"], "--output-root", str(output_root)])
    assert rc == 0
    notice_payload = json.loads(capsys.readouterr().out)
    assert notice_payload["notice_status"] in {"NOTICE_DUE", "NOTICE_PENDING"}

    rc = main(["verify-evidence-bundle-retention-custody-notice", "--retention-custody-notice-artifact", notice_payload["artifact"], "--output-root", str(output_root)])
    assert rc == 0
    notice_verification_payload = json.loads(capsys.readouterr().out)
    assert notice_verification_payload["verification_status"] == "PASS"
