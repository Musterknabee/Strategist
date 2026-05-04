from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from strategy_validator.cli.paper_broker import main
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_review_verification import write_paper_execution_evidence_bundle_retention_custody_review_verification_artifact
from tests.application.test_paper_execution_evidence_bundle_retention_custody_review_verification import _setup_custody_review


def test_cli_retention_custody_renewal_schedule_round_trip(tmp_path: Path, capsys) -> None:
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
    assert renewal_payload["renewal_status"] == "RENEWED"

    rc = main(["verify-evidence-bundle-retention-custody-renewal", "--retention-custody-renewal-artifact", renewal_payload["artifact"], "--output-root", str(output_root)])
    assert rc == 0
    renewal_verification_payload = json.loads(capsys.readouterr().out)
    assert renewal_verification_payload["verification_status"] == "PASS"

    rc = main(["schedule-evidence-bundle-retention-custody-renewal", "--retention-custody-renewal-verification-artifact", renewal_verification_payload["artifact"], "--output-root", str(output_root), "--reminder-days-before-due", "5"])
    assert rc == 0
    schedule_payload = json.loads(capsys.readouterr().out)
    assert schedule_payload["schedule_status"] == "SCHEDULED"
    start_s = str(schedule_payload.get("schedule_start_at_utc") or "").strip()
    due_s = str(schedule_payload.get("next_renewal_due_at_utc") or "").strip()
    assert start_s and due_s
    d0 = datetime.fromisoformat(start_s.replace("Z", "+00:00"))
    d1 = datetime.fromisoformat(due_s.replace("Z", "+00:00"))
    assert d1 - d0 == timedelta(days=int(schedule_payload["renewal_interval_days"]))

    rc = main(["verify-evidence-bundle-retention-custody-schedule", "--retention-custody-schedule-artifact", schedule_payload["artifact"], "--output-root", str(output_root)])
    assert rc == 0
    schedule_verification_payload = json.loads(capsys.readouterr().out)
    assert schedule_verification_payload["verification_status"] == "PASS"
