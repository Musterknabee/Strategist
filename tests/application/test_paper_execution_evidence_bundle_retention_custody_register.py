from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_register import (
    read_paper_execution_evidence_bundle_retention_custody_register_views,
    write_paper_execution_evidence_bundle_retention_custody_register_artifact,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff_acceptance import write_paper_execution_evidence_bundle_retention_handoff_acceptance_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff_acceptance_verification import write_paper_execution_evidence_bundle_retention_handoff_acceptance_verification_artifact
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from tests.application.test_paper_execution_evidence_bundle_retention_handoff_acceptance import _setup_handoff_verification


def _setup_acceptance_verification(tmp_path: Path) -> tuple[Path, Path]:
    output_root, latest_handoff_verification_path = _setup_handoff_verification(tmp_path)
    latest_acceptance_path, _, _ = write_paper_execution_evidence_bundle_retention_handoff_acceptance_artifact(
        retention_handoff_verification_artifact_path=latest_handoff_verification_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 25, tzinfo=timezone.utc),
    )
    latest_acceptance_verification_path, _, _ = write_paper_execution_evidence_bundle_retention_handoff_acceptance_verification_artifact(
        retention_handoff_acceptance_artifact_path=latest_acceptance_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 26, tzinfo=timezone.utc),
    )
    return output_root, latest_acceptance_verification_path


def test_retention_custody_register_passes_and_surfaces(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    output_root, latest_acceptance_verification_path = _setup_acceptance_verification(tmp_path)

    latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_register_artifact(
        retention_handoff_acceptance_verification_artifact_path=latest_acceptance_verification_path,
        output_root=output_root,
        registered_by="operator-jp",
        custody_location="vault-a",
        generated_at_utc=datetime(2026, 5, 3, 12, 27, tzinfo=timezone.utc),
    )

    assert latest_path.exists()
    assert history_path.exists()
    assert artifact.register_status == "REGISTERED"
    assert artifact.trust_banner == "TRUSTED"
    assert artifact.retention_handoff_acceptance_verification_artifact_hash_valid is True
    assert artifact.retention_handoff_acceptance_artifact_hash_valid is True
    assert artifact.acceptance_statement_hash_valid is True
    assert artifact.recomputed_retention_entry_count == 7
    assert artifact.custody_register_id and artifact.custody_register_id.startswith("retention-custody:")
    assert artifact.execution_authority == "NONE"

    views = read_paper_execution_evidence_bundle_retention_custody_register_views(output_root=output_root)
    assert views and views[0].register_status == "REGISTERED"

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["latest_evidence_bundle_retention_custody_register_status"] == "REGISTERED"
    assert cockpit["latest_evidence_bundle_retention_custody_register"]["custody_location"] == "vault-a"

    daily = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    assert daily["summary"]["paper_execution_latest_bundle_retention_custody_registered_count"] == 1


def test_retention_custody_register_blocks_when_acceptance_verification_failed(tmp_path: Path) -> None:
    output_root, latest_acceptance_verification_path = _setup_acceptance_verification(tmp_path)
    raw = json.loads(latest_acceptance_verification_path.read_text(encoding="utf-8"))
    raw["verification_status"] = "FAIL"
    raw["blockers"] = ["SYNTHETIC_ACCEPTANCE_VERIFICATION_FAILURE"]
    raw["artifact_sha256"] = canonical_json_sha256({k: v for k, v in raw.items() if k != "artifact_sha256"})
    latest_acceptance_verification_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _, _, artifact = write_paper_execution_evidence_bundle_retention_custody_register_artifact(
        retention_handoff_acceptance_verification_artifact_path=latest_acceptance_verification_path,
        output_root=output_root,
    )

    assert artifact.register_status == "BLOCKED"
    assert artifact.trust_banner == "UNTRUSTED"
    assert "RETENTION_HANDOFF_ACCEPTANCE_VERIFICATION_NOT_PASS" in artifact.blockers
