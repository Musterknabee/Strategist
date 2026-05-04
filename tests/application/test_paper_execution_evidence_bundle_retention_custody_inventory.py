from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_inventory import write_paper_execution_evidence_bundle_retention_custody_inventory_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_inventory_verification import write_paper_execution_evidence_bundle_retention_custody_inventory_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_redeposit import write_paper_execution_evidence_bundle_retention_custody_redeposit_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_redeposit_verification import write_paper_execution_evidence_bundle_retention_custody_redeposit_verification_artifact
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from tests.application.test_paper_execution_evidence_bundle_retention_custody_redeposit import _setup_return_verification


def _setup_redeposit_verification(tmp_path: Path) -> tuple[Path, Path]:
    output_root, return_verification_path = _setup_return_verification(tmp_path)
    redeposit_path, _, redeposit = write_paper_execution_evidence_bundle_retention_custody_redeposit_artifact(
        retention_custody_return_verification_artifact_path=return_verification_path,
        output_root=output_root,
        redeposited_by="operator-a",
        generated_at_utc=datetime(2026, 5, 10, 12, 14, tzinfo=timezone.utc),
    )
    assert redeposit.redeposit_status == "REDEPOSITED"
    redeposit_verification_path, _, redeposit_verification = write_paper_execution_evidence_bundle_retention_custody_redeposit_verification_artifact(
        retention_custody_redeposit_artifact_path=redeposit_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 15, tzinfo=timezone.utc),
    )
    assert redeposit_verification.verification_status == "PASS"
    return output_root, redeposit_verification_path


def test_retention_custody_inventory_passes_and_surfaces(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    output_root, redeposit_verification_path = _setup_redeposit_verification(tmp_path)

    inventory_path, _, inventory = write_paper_execution_evidence_bundle_retention_custody_inventory_artifact(
        retention_custody_redeposit_verification_artifact_path=redeposit_verification_path,
        output_root=output_root,
        inventoried_by="operator-a",
        inventory_reason="redeposit verification accepted",
        custody_location="retention-vault-a",
        inventory_note="inventory slot A confirmed",
        generated_at_utc=datetime(2026, 5, 10, 12, 16, tzinfo=timezone.utc),
    )
    assert inventory.inventory_status == "INVENTORIED"
    assert inventory.trust_banner == "TRUSTED"
    assert inventory.inventoried_by == "operator-a"

    _, _, verification = write_paper_execution_evidence_bundle_retention_custody_inventory_verification_artifact(
        retention_custody_inventory_artifact_path=inventory_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 17, tzinfo=timezone.utc),
    )
    assert verification.verification_status == "PASS"
    assert verification.custody_inventory_statement_hash_valid is True

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["latest_evidence_bundle_retention_custody_inventory_status"] == "INVENTORIED"
    assert cockpit["latest_evidence_bundle_retention_custody_inventory_verification"]["verification_status"] == "PASS"

    daily = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    assert daily["summary"]["paper_execution_latest_bundle_retention_custody_inventory_verified_count"] == 1


def test_retention_custody_inventory_blocks_without_redeposit_verification(tmp_path: Path) -> None:
    output_root = tmp_path / "artifacts" / "paper_broker"
    _, _, inventory = write_paper_execution_evidence_bundle_retention_custody_inventory_artifact(output_root=output_root)
    assert inventory.inventory_status == "BLOCKED"
    assert "RETENTION_CUSTODY_REDEPOSIT_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE" in inventory.blockers


def test_retention_custody_inventory_verification_blocks_when_statement_tampered(tmp_path: Path) -> None:
    output_root, redeposit_verification_path = _setup_redeposit_verification(tmp_path)
    inventory_path, _, _ = write_paper_execution_evidence_bundle_retention_custody_inventory_artifact(
        retention_custody_redeposit_verification_artifact_path=redeposit_verification_path,
        output_root=output_root,
    )
    raw = json.loads(inventory_path.read_text(encoding="utf-8"))
    raw["custody_inventory_statement_sha256"] = "0" * 64
    raw["artifact_sha256"] = canonical_json_sha256({k: v for k, v in raw.items() if k != "artifact_sha256"})
    inventory_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _, _, verification = write_paper_execution_evidence_bundle_retention_custody_inventory_verification_artifact(
        retention_custody_inventory_artifact_path=inventory_path,
        output_root=output_root,
    )
    assert verification.verification_status == "FAIL"
    assert verification.custody_inventory_statement_hash_valid is False
