from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_notice import write_paper_execution_evidence_bundle_retention_custody_notice_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_notice_verification import write_paper_execution_evidence_bundle_retention_custody_notice_verification_artifact
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from tests.application.test_paper_execution_evidence_bundle_retention_custody_renewal_schedule import _setup_renewal_verification
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_schedule import write_paper_execution_evidence_bundle_retention_custody_schedule_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_schedule_verification import write_paper_execution_evidence_bundle_retention_custody_schedule_verification_artifact


def _setup_schedule_verification(tmp_path: Path) -> tuple[Path, Path]:
    output_root, renewal_verification_path = _setup_renewal_verification(tmp_path)
    schedule_path, _, schedule = write_paper_execution_evidence_bundle_retention_custody_schedule_artifact(
        retention_custody_renewal_verification_artifact_path=renewal_verification_path,
        output_root=output_root,
        reminder_days_before_due=5,
        generated_at_utc=datetime(2026, 5, 3, 12, 39, tzinfo=timezone.utc),
    )
    assert schedule.schedule_status == "SCHEDULED"
    schedule_verification_path, _, verification = write_paper_execution_evidence_bundle_retention_custody_schedule_verification_artifact(
        retention_custody_schedule_artifact_path=schedule_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 40, tzinfo=timezone.utc),
    )
    assert verification.verification_status == "PASS"
    return output_root, schedule_verification_path


def test_retention_custody_notice_pending_passes_and_surfaces(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    output_root, schedule_verification_path = _setup_schedule_verification(tmp_path)

    notice_path, _, notice = write_paper_execution_evidence_bundle_retention_custody_notice_artifact(
        retention_custody_schedule_verification_artifact_path=schedule_verification_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc),
    )
    assert notice.notice_status == "NOTICE_PENDING"
    assert notice.trust_banner == "TRUSTED"
    assert notice.days_until_due > 30

    _, _, verification = write_paper_execution_evidence_bundle_retention_custody_notice_verification_artifact(
        retention_custody_notice_artifact_path=notice_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 1, tzinfo=timezone.utc),
    )
    assert verification.verification_status == "PASS"
    assert verification.custody_notice_statement_hash_valid is True

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["latest_evidence_bundle_retention_custody_notice_status"] == "NOTICE_PENDING"
    assert cockpit["latest_evidence_bundle_retention_custody_notice_verification"]["verification_status"] == "PASS"

    daily = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    assert daily["summary"]["paper_execution_latest_bundle_retention_custody_notice_verified_count"] == 1


def test_retention_custody_notice_due_inside_reminder_window(tmp_path: Path) -> None:
    output_root, schedule_verification_path = _setup_schedule_verification(tmp_path)
    _, _, notice = write_paper_execution_evidence_bundle_retention_custody_notice_artifact(
        retention_custody_schedule_verification_artifact_path=schedule_verification_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc),
    )
    assert notice.notice_status == "NOTICE_DUE"
    assert 0 <= notice.days_until_due <= 5


def test_retention_custody_notice_verification_blocks_when_statement_tampered(tmp_path: Path) -> None:
    output_root, schedule_verification_path = _setup_schedule_verification(tmp_path)
    notice_path, _, _ = write_paper_execution_evidence_bundle_retention_custody_notice_artifact(
        retention_custody_schedule_verification_artifact_path=schedule_verification_path,
        output_root=output_root,
    )
    raw = json.loads(notice_path.read_text(encoding="utf-8"))
    raw["custody_notice_statement_sha256"] = "0" * 64
    raw["artifact_sha256"] = canonical_json_sha256({k: v for k, v in raw.items() if k != "artifact_sha256"})
    notice_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _, _, verification = write_paper_execution_evidence_bundle_retention_custody_notice_verification_artifact(
        retention_custody_notice_artifact_path=notice_path,
        output_root=output_root,
    )
    assert verification.verification_status == "FAIL"
    assert verification.custody_notice_statement_hash_valid is False
