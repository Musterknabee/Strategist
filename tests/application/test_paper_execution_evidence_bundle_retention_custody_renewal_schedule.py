from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_review_verification import write_paper_execution_evidence_bundle_retention_custody_review_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_renewal import write_paper_execution_evidence_bundle_retention_custody_renewal_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_renewal_verification import write_paper_execution_evidence_bundle_retention_custody_renewal_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_schedule import write_paper_execution_evidence_bundle_retention_custody_schedule_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_schedule_verification import write_paper_execution_evidence_bundle_retention_custody_schedule_verification_artifact
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from tests.application.test_paper_execution_evidence_bundle_retention_custody_review_verification import _setup_custody_review


def _setup_review_verification(tmp_path: Path) -> tuple[Path, Path]:
    output_root, review_path = _setup_custody_review(tmp_path)
    review_verification_path, _, artifact = write_paper_execution_evidence_bundle_retention_custody_review_verification_artifact(
        retention_custody_review_artifact_path=review_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 36, tzinfo=timezone.utc),
    )
    assert artifact.verification_status == "PASS"
    return output_root, review_verification_path


def _setup_renewal_verification(tmp_path: Path) -> tuple[Path, Path]:
    output_root, review_verification_path = _setup_review_verification(tmp_path)
    renewal_path, _, renewal = write_paper_execution_evidence_bundle_retention_custody_renewal_artifact(
        retention_custody_review_verification_artifact_path=review_verification_path,
        output_root=output_root,
        renewal_interval_days=45,
        generated_at_utc=datetime(2026, 5, 3, 12, 37, tzinfo=timezone.utc),
    )
    assert renewal.renewal_status == "RENEWED"
    renewal_verification_path, _, verification = write_paper_execution_evidence_bundle_retention_custody_renewal_verification_artifact(
        retention_custody_renewal_artifact_path=renewal_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 38, tzinfo=timezone.utc),
    )
    assert verification.verification_status == "PASS"
    return output_root, renewal_verification_path


def test_retention_custody_renewal_schedule_passes_and_surfaces(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    output_root, renewal_verification_path = _setup_renewal_verification(tmp_path)

    schedule_path, _, schedule = write_paper_execution_evidence_bundle_retention_custody_schedule_artifact(
        retention_custody_renewal_verification_artifact_path=renewal_verification_path,
        output_root=output_root,
        reminder_days_before_due=5,
        generated_at_utc=datetime(2026, 5, 3, 12, 39, tzinfo=timezone.utc),
    )
    assert schedule.schedule_status == "SCHEDULED"
    assert schedule.trust_banner == "TRUSTED"
    assert schedule.next_renewal_due_at_utc.startswith("2026-06-17")

    _, _, verification = write_paper_execution_evidence_bundle_retention_custody_schedule_verification_artifact(
        retention_custody_schedule_artifact_path=schedule_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 40, tzinfo=timezone.utc),
    )
    assert verification.verification_status == "PASS"
    assert verification.custody_schedule_statement_hash_valid is True

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["latest_evidence_bundle_retention_custody_schedule_status"] == "SCHEDULED"
    assert cockpit["latest_evidence_bundle_retention_custody_schedule_verification"]["verification_status"] == "PASS"

    daily = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    assert daily["summary"]["paper_execution_latest_bundle_retention_custody_schedule_verified_count"] == 1


def test_retention_custody_schedule_verification_blocks_when_statement_tampered(tmp_path: Path) -> None:
    output_root, renewal_verification_path = _setup_renewal_verification(tmp_path)
    schedule_path, _, _ = write_paper_execution_evidence_bundle_retention_custody_schedule_artifact(
        retention_custody_renewal_verification_artifact_path=renewal_verification_path,
        output_root=output_root,
    )
    raw = json.loads(schedule_path.read_text(encoding="utf-8"))
    raw["custody_schedule_statement_sha256"] = "0" * 64
    raw["artifact_sha256"] = canonical_json_sha256({k: v for k, v in raw.items() if k != "artifact_sha256"})
    schedule_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _, _, verification = write_paper_execution_evidence_bundle_retention_custody_schedule_verification_artifact(
        retention_custody_schedule_artifact_path=schedule_path,
        output_root=output_root,
    )
    assert verification.verification_status == "FAIL"
    assert verification.custody_schedule_statement_hash_valid is False
