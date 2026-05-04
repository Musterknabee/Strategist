from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_inventory import write_paper_execution_evidence_bundle_retention_custody_inventory_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_inventory_verification import write_paper_execution_evidence_bundle_retention_custody_inventory_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_reconciliation import write_paper_execution_evidence_bundle_retention_custody_reconciliation_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_reconciliation_verification import write_paper_execution_evidence_bundle_retention_custody_reconciliation_verification_artifact
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from tests.application.test_paper_execution_evidence_bundle_retention_custody_inventory import _setup_redeposit_verification


def _setup_inventory_verification(tmp_path: Path) -> tuple[Path, Path]:
    output_root, redeposit_verification_path = _setup_redeposit_verification(tmp_path)
    inventory_path, _, inventory = write_paper_execution_evidence_bundle_retention_custody_inventory_artifact(
        retention_custody_redeposit_verification_artifact_path=redeposit_verification_path,
        output_root=output_root,
        inventoried_by="operator-a",
        generated_at_utc=datetime(2026, 5, 10, 12, 16, tzinfo=timezone.utc),
    )
    assert inventory.inventory_status == "INVENTORIED"
    inventory_verification_path, _, inventory_verification = write_paper_execution_evidence_bundle_retention_custody_inventory_verification_artifact(
        retention_custody_inventory_artifact_path=inventory_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 17, tzinfo=timezone.utc),
    )
    assert inventory_verification.verification_status == "PASS"
    return output_root, inventory_verification_path


def test_retention_custody_reconciliation_passes_and_surfaces(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    output_root, inventory_verification_path = _setup_inventory_verification(tmp_path)

    reconciliation_path, _, reconciliation = write_paper_execution_evidence_bundle_retention_custody_reconciliation_artifact(
        retention_custody_inventory_verification_artifact_path=inventory_verification_path,
        output_root=output_root,
        reconciled_by="operator-a",
        reconciliation_reason="inventory verification accepted",
        custody_location="retention-vault-a",
        reconciliation_note="inventory row count and retention index matched",
        generated_at_utc=datetime(2026, 5, 10, 12, 18, tzinfo=timezone.utc),
    )
    assert reconciliation.reconciliation_status == "RECONCILED"
    assert reconciliation.trust_banner == "TRUSTED"
    assert reconciliation.reconciled_by == "operator-a"

    _, _, verification = write_paper_execution_evidence_bundle_retention_custody_reconciliation_verification_artifact(
        retention_custody_reconciliation_artifact_path=reconciliation_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 19, tzinfo=timezone.utc),
    )
    assert verification.verification_status == "PASS"
    assert verification.custody_reconciliation_statement_hash_valid is True

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["latest_evidence_bundle_retention_custody_reconciliation_status"] == "RECONCILED"
    assert cockpit["latest_evidence_bundle_retention_custody_reconciliation_verification"]["verification_status"] == "PASS"


def test_retention_custody_reconciliation_blocks_without_inventory_verification(tmp_path: Path) -> None:
    output_root = tmp_path / "artifacts" / "paper_broker"
    _, _, reconciliation = write_paper_execution_evidence_bundle_retention_custody_reconciliation_artifact(output_root=output_root)
    assert reconciliation.reconciliation_status == "BLOCKED"
    assert "RETENTION_CUSTODY_INVENTORY_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE" in reconciliation.blockers


def test_retention_custody_reconciliation_verification_blocks_when_statement_tampered(tmp_path: Path) -> None:
    output_root, inventory_verification_path = _setup_inventory_verification(tmp_path)
    reconciliation_path, _, _ = write_paper_execution_evidence_bundle_retention_custody_reconciliation_artifact(
        retention_custody_inventory_verification_artifact_path=inventory_verification_path,
        output_root=output_root,
    )
    raw = json.loads(reconciliation_path.read_text(encoding="utf-8"))
    raw["custody_reconciliation_statement_sha256"] = "0" * 64
    raw["artifact_sha256"] = canonical_json_sha256({k: v for k, v in raw.items() if k != "artifact_sha256"})
    reconciliation_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _, _, verification = write_paper_execution_evidence_bundle_retention_custody_reconciliation_verification_artifact(
        retention_custody_reconciliation_artifact_path=reconciliation_path,
        output_root=output_root,
    )
    assert verification.verification_status == "FAIL"
    assert verification.custody_reconciliation_statement_hash_valid is False
