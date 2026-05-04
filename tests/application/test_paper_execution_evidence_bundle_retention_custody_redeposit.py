from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_redeposit import write_paper_execution_evidence_bundle_retention_custody_redeposit_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_redeposit_verification import write_paper_execution_evidence_bundle_retention_custody_redeposit_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_return import write_paper_execution_evidence_bundle_retention_custody_return_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_return_verification import write_paper_execution_evidence_bundle_retention_custody_return_verification_artifact
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from tests.application.test_paper_execution_evidence_bundle_retention_custody_return import _setup_retrieval_verification


def _setup_return_verification(tmp_path: Path) -> tuple[Path, Path]:
    output_root, retrieval_verification_path = _setup_retrieval_verification(tmp_path)
    return_path, _, returned = write_paper_execution_evidence_bundle_retention_custody_return_artifact(
        retention_custody_retrieval_verification_artifact_path=retrieval_verification_path,
        output_root=output_root,
        returned_by="operator-a",
        generated_at_utc=datetime(2026, 5, 10, 12, 12, tzinfo=timezone.utc),
    )
    assert returned.return_status == "RETURNED"
    return_verification_path, _, return_verification = write_paper_execution_evidence_bundle_retention_custody_return_verification_artifact(
        retention_custody_return_artifact_path=return_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 13, tzinfo=timezone.utc),
    )
    assert return_verification.verification_status == "PASS"
    return output_root, return_verification_path


def test_retention_custody_redeposit_passes_and_surfaces(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    output_root, return_verification_path = _setup_return_verification(tmp_path)

    redeposit_path, _, redeposit = write_paper_execution_evidence_bundle_retention_custody_redeposit_artifact(
        retention_custody_return_verification_artifact_path=return_verification_path,
        output_root=output_root,
        redeposited_by="operator-a",
        redeposit_reason="return verification accepted",
        custody_location="retention-vault-a",
        redeposit_note="back in vault slot A",
        generated_at_utc=datetime(2026, 5, 10, 12, 14, tzinfo=timezone.utc),
    )
    assert redeposit.redeposit_status == "REDEPOSITED"
    assert redeposit.trust_banner == "TRUSTED"
    assert redeposit.redeposited_by == "operator-a"

    _, _, verification = write_paper_execution_evidence_bundle_retention_custody_redeposit_verification_artifact(
        retention_custody_redeposit_artifact_path=redeposit_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 15, tzinfo=timezone.utc),
    )
    assert verification.verification_status == "PASS"
    assert verification.custody_redeposit_statement_hash_valid is True

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["latest_evidence_bundle_retention_custody_redeposit_status"] == "REDEPOSITED"
    assert cockpit["latest_evidence_bundle_retention_custody_redeposit_verification"]["verification_status"] == "PASS"

    daily = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    assert daily["summary"]["paper_execution_latest_bundle_retention_custody_redeposit_verified_count"] == 1


def test_retention_custody_redeposit_blocks_without_return_verification(tmp_path: Path) -> None:
    output_root = tmp_path / "artifacts" / "paper_broker"
    _, _, redeposit = write_paper_execution_evidence_bundle_retention_custody_redeposit_artifact(output_root=output_root)
    assert redeposit.redeposit_status == "BLOCKED"
    assert "RETENTION_CUSTODY_RETURN_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE" in redeposit.blockers


def test_retention_custody_redeposit_verification_blocks_when_statement_tampered(tmp_path: Path) -> None:
    output_root, return_verification_path = _setup_return_verification(tmp_path)
    redeposit_path, _, _ = write_paper_execution_evidence_bundle_retention_custody_redeposit_artifact(
        retention_custody_return_verification_artifact_path=return_verification_path,
        output_root=output_root,
    )
    raw = json.loads(redeposit_path.read_text(encoding="utf-8"))
    raw["custody_redeposit_statement_sha256"] = "0" * 64
    raw["artifact_sha256"] = canonical_json_sha256({k: v for k, v in raw.items() if k != "artifact_sha256"})
    redeposit_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _, _, verification = write_paper_execution_evidence_bundle_retention_custody_redeposit_verification_artifact(
        retention_custody_redeposit_artifact_path=redeposit_path,
        output_root=output_root,
    )
    assert verification.verification_status == "FAIL"
    assert verification.custody_redeposit_statement_hash_valid is False
