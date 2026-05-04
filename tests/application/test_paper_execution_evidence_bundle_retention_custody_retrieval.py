from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_archive import write_paper_execution_evidence_bundle_retention_custody_archive_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_archive_verification import write_paper_execution_evidence_bundle_retention_custody_archive_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_retrieval import write_paper_execution_evidence_bundle_retention_custody_retrieval_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_retrieval_verification import write_paper_execution_evidence_bundle_retention_custody_retrieval_verification_artifact
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from tests.application.test_paper_execution_evidence_bundle_retention_custody_archive import _setup_closeout_verification


def _setup_archive_verification(tmp_path: Path) -> tuple[Path, Path]:
    output_root, closeout_verification_path = _setup_closeout_verification(tmp_path)
    archive_path, _, archive = write_paper_execution_evidence_bundle_retention_custody_archive_artifact(
        retention_custody_closeout_verification_artifact_path=closeout_verification_path,
        output_root=output_root,
        archived_by="operator-a",
        generated_at_utc=datetime(2026, 5, 10, 12, 8, tzinfo=timezone.utc),
    )
    assert archive.archive_status == "ARCHIVED"
    archive_verification_path, _, archive_verification = write_paper_execution_evidence_bundle_retention_custody_archive_verification_artifact(
        retention_custody_archive_artifact_path=archive_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 9, tzinfo=timezone.utc),
    )
    assert archive_verification.verification_status == "PASS"
    return output_root, archive_verification_path


def test_retention_custody_retrieval_passes_and_surfaces(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    output_root, archive_verification_path = _setup_archive_verification(tmp_path)

    retrieval_path, _, retrieval = write_paper_execution_evidence_bundle_retention_custody_retrieval_artifact(
        retention_custody_archive_verification_artifact_path=archive_verification_path,
        output_root=output_root,
        retrieved_by="operator-a",
        retrieval_purpose="quarterly evidence review",
        custody_location="retention-vault-a",
        retrieval_note="read-only retrieval",
        generated_at_utc=datetime(2026, 5, 10, 12, 10, tzinfo=timezone.utc),
    )
    assert retrieval.retrieval_status == "RETRIEVED"
    assert retrieval.trust_banner == "TRUSTED"
    assert retrieval.retrieved_by == "operator-a"

    _, _, verification = write_paper_execution_evidence_bundle_retention_custody_retrieval_verification_artifact(
        retention_custody_retrieval_artifact_path=retrieval_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 11, tzinfo=timezone.utc),
    )
    assert verification.verification_status == "PASS"
    assert verification.custody_retrieval_statement_hash_valid is True

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["latest_evidence_bundle_retention_custody_retrieval_status"] == "RETRIEVED"
    assert cockpit["latest_evidence_bundle_retention_custody_retrieval_verification"]["verification_status"] == "PASS"

    daily = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    assert daily["summary"]["paper_execution_latest_bundle_retention_custody_retrieval_verified_count"] == 1


def test_retention_custody_retrieval_blocks_without_archive_verification(tmp_path: Path) -> None:
    output_root = tmp_path / "artifacts" / "paper_broker"
    _, _, retrieval = write_paper_execution_evidence_bundle_retention_custody_retrieval_artifact(output_root=output_root)
    assert retrieval.retrieval_status == "BLOCKED"
    assert "RETENTION_CUSTODY_ARCHIVE_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE" in retrieval.blockers


def test_retention_custody_retrieval_verification_blocks_when_statement_tampered(tmp_path: Path) -> None:
    output_root, archive_verification_path = _setup_archive_verification(tmp_path)
    retrieval_path, _, _ = write_paper_execution_evidence_bundle_retention_custody_retrieval_artifact(
        retention_custody_archive_verification_artifact_path=archive_verification_path,
        output_root=output_root,
    )
    raw = json.loads(retrieval_path.read_text(encoding="utf-8"))
    raw["custody_retrieval_statement_sha256"] = "0" * 64
    raw["artifact_sha256"] = canonical_json_sha256({k: v for k, v in raw.items() if k != "artifact_sha256"})
    retrieval_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _, _, verification = write_paper_execution_evidence_bundle_retention_custody_retrieval_verification_artifact(
        retention_custody_retrieval_artifact_path=retrieval_path,
        output_root=output_root,
    )
    assert verification.verification_status == "FAIL"
    assert verification.custody_retrieval_statement_hash_valid is False
