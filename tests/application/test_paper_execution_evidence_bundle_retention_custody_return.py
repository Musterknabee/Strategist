from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_return import write_paper_execution_evidence_bundle_retention_custody_return_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_return_verification import write_paper_execution_evidence_bundle_retention_custody_return_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_retrieval import write_paper_execution_evidence_bundle_retention_custody_retrieval_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_retrieval_verification import write_paper_execution_evidence_bundle_retention_custody_retrieval_verification_artifact
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from tests.application.test_paper_execution_evidence_bundle_retention_custody_retrieval import _setup_archive_verification


def _setup_retrieval_verification(tmp_path: Path) -> tuple[Path, Path]:
    output_root, archive_verification_path = _setup_archive_verification(tmp_path)
    retrieval_path, _, retrieval = write_paper_execution_evidence_bundle_retention_custody_retrieval_artifact(
        retention_custody_archive_verification_artifact_path=archive_verification_path,
        output_root=output_root,
        retrieved_by="operator-a",
        generated_at_utc=datetime(2026, 5, 10, 12, 10, tzinfo=timezone.utc),
    )
    assert retrieval.retrieval_status == "RETRIEVED"
    retrieval_verification_path, _, retrieval_verification = write_paper_execution_evidence_bundle_retention_custody_retrieval_verification_artifact(
        retention_custody_retrieval_artifact_path=retrieval_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 11, tzinfo=timezone.utc),
    )
    assert retrieval_verification.verification_status == "PASS"
    return output_root, retrieval_verification_path


def test_retention_custody_return_passes_and_surfaces(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    output_root, retrieval_verification_path = _setup_retrieval_verification(tmp_path)

    return_path, _, returned = write_paper_execution_evidence_bundle_retention_custody_return_artifact(
        retention_custody_retrieval_verification_artifact_path=retrieval_verification_path,
        output_root=output_root,
        returned_by="operator-a",
        return_reason="review complete",
        custody_location="retention-vault-a",
        return_note="sealed back into custody",
        generated_at_utc=datetime(2026, 5, 10, 12, 12, tzinfo=timezone.utc),
    )
    assert returned.return_status == "RETURNED"
    assert returned.trust_banner == "TRUSTED"
    assert returned.returned_by == "operator-a"

    _, _, verification = write_paper_execution_evidence_bundle_retention_custody_return_verification_artifact(
        retention_custody_return_artifact_path=return_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 13, tzinfo=timezone.utc),
    )
    assert verification.verification_status == "PASS"
    assert verification.custody_return_statement_hash_valid is True

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["latest_evidence_bundle_retention_custody_return_status"] == "RETURNED"
    assert cockpit["latest_evidence_bundle_retention_custody_return_verification"]["verification_status"] == "PASS"

    daily = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    assert daily["summary"]["paper_execution_latest_bundle_retention_custody_return_verified_count"] == 1


def test_retention_custody_return_blocks_without_retrieval_verification(tmp_path: Path) -> None:
    output_root = tmp_path / "artifacts" / "paper_broker"
    _, _, returned = write_paper_execution_evidence_bundle_retention_custody_return_artifact(output_root=output_root)
    assert returned.return_status == "BLOCKED"
    assert "RETENTION_CUSTODY_RETRIEVAL_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE" in returned.blockers


def test_retention_custody_return_verification_blocks_when_statement_tampered(tmp_path: Path) -> None:
    output_root, retrieval_verification_path = _setup_retrieval_verification(tmp_path)
    return_path, _, _ = write_paper_execution_evidence_bundle_retention_custody_return_artifact(
        retention_custody_retrieval_verification_artifact_path=retrieval_verification_path,
        output_root=output_root,
    )
    raw = json.loads(return_path.read_text(encoding="utf-8"))
    raw["custody_return_statement_sha256"] = "0" * 64
    raw["artifact_sha256"] = canonical_json_sha256({k: v for k, v in raw.items() if k != "artifact_sha256"})
    return_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _, _, verification = write_paper_execution_evidence_bundle_retention_custody_return_verification_artifact(
        retention_custody_return_artifact_path=return_path,
        output_root=output_root,
    )
    assert verification.verification_status == "FAIL"
    assert verification.custody_return_statement_hash_valid is False
