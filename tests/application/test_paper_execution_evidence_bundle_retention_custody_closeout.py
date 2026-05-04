from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_closeout import write_paper_execution_evidence_bundle_retention_custody_closeout_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_closeout_verification import write_paper_execution_evidence_bundle_retention_custody_closeout_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_completion import write_paper_execution_evidence_bundle_retention_custody_completion_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_completion_verification import write_paper_execution_evidence_bundle_retention_custody_completion_verification_artifact
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from tests.application.test_paper_execution_evidence_bundle_retention_custody_completion import _setup_acknowledgment_verification


def _setup_completion_verification(tmp_path: Path) -> tuple[Path, Path]:
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
        generated_at_utc=datetime(2026, 5, 10, 12, 5, tzinfo=timezone.utc),
    )
    assert completion_verification.verification_status == "PASS"
    return output_root, completion_verification_path


def test_retention_custody_closeout_passes_and_surfaces(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    output_root, completion_verification_path = _setup_completion_verification(tmp_path)

    closeout_path, _, closeout = write_paper_execution_evidence_bundle_retention_custody_closeout_artifact(
        retention_custody_completion_verification_artifact_path=completion_verification_path,
        output_root=output_root,
        closed_out_by="operator-a",
        generated_at_utc=datetime(2026, 5, 10, 12, 6, tzinfo=timezone.utc),
    )
    assert closeout.closeout_status == "CLOSED"
    assert closeout.trust_banner == "TRUSTED"
    assert closeout.closed_out_by == "operator-a"

    _, _, verification = write_paper_execution_evidence_bundle_retention_custody_closeout_verification_artifact(
        retention_custody_closeout_artifact_path=closeout_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 7, tzinfo=timezone.utc),
    )
    assert verification.verification_status == "PASS"
    assert verification.custody_closeout_statement_hash_valid is True

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["latest_evidence_bundle_retention_custody_closeout_status"] == "CLOSED"
    assert cockpit["latest_evidence_bundle_retention_custody_closeout_verification"]["verification_status"] == "PASS"

    daily = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    assert daily["summary"]["paper_execution_latest_bundle_retention_custody_closeout_verified_count"] == 1


def test_retention_custody_closeout_blocks_without_completion_verification(tmp_path: Path) -> None:
    output_root = tmp_path / "artifacts" / "paper_broker"
    _, _, closeout = write_paper_execution_evidence_bundle_retention_custody_closeout_artifact(output_root=output_root)
    assert closeout.closeout_status == "BLOCKED"
    assert "RETENTION_CUSTODY_COMPLETION_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE" in closeout.blockers


def test_retention_custody_closeout_verification_blocks_when_statement_tampered(tmp_path: Path) -> None:
    output_root, completion_verification_path = _setup_completion_verification(tmp_path)
    closeout_path, _, _ = write_paper_execution_evidence_bundle_retention_custody_closeout_artifact(
        retention_custody_completion_verification_artifact_path=completion_verification_path,
        output_root=output_root,
    )
    raw = json.loads(closeout_path.read_text(encoding="utf-8"))
    raw["custody_closeout_statement_sha256"] = "0" * 64
    raw["artifact_sha256"] = canonical_json_sha256({k: v for k, v in raw.items() if k != "artifact_sha256"})
    closeout_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _, _, verification = write_paper_execution_evidence_bundle_retention_custody_closeout_verification_artifact(
        retention_custody_closeout_artifact_path=closeout_path,
        output_root=output_root,
    )
    assert verification.verification_status == "FAIL"
    assert verification.custody_closeout_statement_hash_valid is False
