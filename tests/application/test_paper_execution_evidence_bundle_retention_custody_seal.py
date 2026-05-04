from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_register import write_paper_execution_evidence_bundle_retention_custody_register_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_register_verification import write_paper_execution_evidence_bundle_retention_custody_register_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_seal import (
    read_paper_execution_evidence_bundle_retention_custody_seal_views,
    write_paper_execution_evidence_bundle_retention_custody_seal_artifact,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from tests.application.test_paper_execution_evidence_bundle_retention_custody_register import _setup_acceptance_verification


def _setup_custody_register_verification(tmp_path: Path) -> tuple[Path, Path]:
    output_root, latest_acceptance_verification_path = _setup_acceptance_verification(tmp_path)
    latest_register_path, _, _ = write_paper_execution_evidence_bundle_retention_custody_register_artifact(
        retention_handoff_acceptance_verification_artifact_path=latest_acceptance_verification_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 27, tzinfo=timezone.utc),
    )
    latest_register_verification_path, _, _ = write_paper_execution_evidence_bundle_retention_custody_register_verification_artifact(
        retention_custody_register_artifact_path=latest_register_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 28, tzinfo=timezone.utc),
    )
    return output_root, latest_register_verification_path


def test_retention_custody_seal_passes_and_surfaces(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    output_root, latest_register_verification_path = _setup_custody_register_verification(tmp_path)

    latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_seal_artifact(
        retention_custody_register_verification_artifact_path=latest_register_verification_path,
        output_root=output_root,
        sealed_by="operator-jp",
        custody_location="vault-a",
        generated_at_utc=datetime(2026, 5, 3, 12, 29, tzinfo=timezone.utc),
    )

    assert latest_path.exists()
    assert history_path.exists()
    assert artifact.seal_status == "SEALED"
    assert artifact.trust_banner == "TRUSTED"
    assert artifact.retention_custody_register_verification_artifact_hash_valid is True
    assert artifact.retention_custody_register_artifact_hash_valid is True
    assert artifact.custody_register_statement_hash_valid is True
    assert artifact.recomputed_retention_entry_count == 7
    assert artifact.custody_seal_id and artifact.custody_seal_id.startswith("retention-custody-seal:")
    assert artifact.execution_authority == "NONE"

    views = read_paper_execution_evidence_bundle_retention_custody_seal_views(output_root=output_root)
    assert views and views[0].seal_status == "SEALED"

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["latest_evidence_bundle_retention_custody_seal_status"] == "SEALED"
    assert cockpit["latest_evidence_bundle_retention_custody_seal"]["custody_location"] == "vault-a"

    daily = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    assert daily["summary"]["paper_execution_latest_bundle_retention_custody_sealed_count"] == 1


def test_retention_custody_seal_blocks_when_register_verification_failed(tmp_path: Path) -> None:
    output_root, latest_register_verification_path = _setup_custody_register_verification(tmp_path)
    raw = json.loads(latest_register_verification_path.read_text(encoding="utf-8"))
    raw["verification_status"] = "FAIL"
    raw["blockers"] = ["SYNTHETIC_CUSTODY_REGISTER_VERIFICATION_FAILURE"]
    raw["artifact_sha256"] = canonical_json_sha256({k: v for k, v in raw.items() if k != "artifact_sha256"})
    latest_register_verification_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _, _, artifact = write_paper_execution_evidence_bundle_retention_custody_seal_artifact(
        retention_custody_register_verification_artifact_path=latest_register_verification_path,
        output_root=output_root,
    )

    assert artifact.seal_status == "BLOCKED"
    assert artifact.trust_banner == "UNTRUSTED"
    assert "RETENTION_CUSTODY_REGISTER_VERIFICATION_NOT_PASS" in artifact.blockers
