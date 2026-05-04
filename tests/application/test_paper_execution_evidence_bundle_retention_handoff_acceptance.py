from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff import write_paper_execution_evidence_bundle_retention_handoff_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff_acceptance import (
    read_paper_execution_evidence_bundle_retention_handoff_acceptance_views,
    write_paper_execution_evidence_bundle_retention_handoff_acceptance_artifact,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff_verification import write_paper_execution_evidence_bundle_retention_handoff_verification_artifact
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from tests.application.test_paper_execution_evidence_bundle_retention_handoff import _setup_signoff_verification


def _setup_handoff_verification(tmp_path: Path) -> tuple[Path, Path]:
    output_root, latest_signoff_verification_path = _setup_signoff_verification(tmp_path)
    latest_handoff_path, _, _ = write_paper_execution_evidence_bundle_retention_handoff_artifact(
        retention_signoff_verification_artifact_path=latest_signoff_verification_path,
        output_root=output_root,
        custodian_id="archive-vault",
        generated_at_utc=datetime(2026, 5, 3, 12, 23, tzinfo=timezone.utc),
    )
    latest_handoff_verification_path, _, _ = write_paper_execution_evidence_bundle_retention_handoff_verification_artifact(
        retention_handoff_artifact_path=latest_handoff_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 24, tzinfo=timezone.utc),
    )
    return output_root, latest_handoff_verification_path


def test_retention_handoff_acceptance_passes_and_surfaces(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    output_root, latest_handoff_verification_path = _setup_handoff_verification(tmp_path)

    latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_handoff_acceptance_artifact(
        retention_handoff_verification_artifact_path=latest_handoff_verification_path,
        output_root=output_root,
        accepting_custodian_id="archive-desk",
        custody_location="vault-a",
        generated_at_utc=datetime(2026, 5, 3, 12, 25, tzinfo=timezone.utc),
    )

    assert latest_path.exists()
    assert history_path.exists()
    assert artifact.acceptance_status == "ACCEPTED_FOR_CUSTODY"
    assert artifact.trust_banner == "TRUSTED"
    assert artifact.retention_handoff_verification_artifact_hash_valid is True
    assert artifact.retention_handoff_artifact_hash_valid is True
    assert artifact.handoff_statement_hash_valid is True
    assert artifact.recomputed_retention_entry_count == 7
    assert artifact.execution_authority == "NONE"
    assert artifact.no_files_copied is True

    views = read_paper_execution_evidence_bundle_retention_handoff_acceptance_views(output_root=output_root)
    assert views and views[0].acceptance_status == "ACCEPTED_FOR_CUSTODY"

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["latest_evidence_bundle_retention_handoff_acceptance_status"] == "ACCEPTED_FOR_CUSTODY"
    assert cockpit["latest_evidence_bundle_retention_handoff_acceptance"]["custody_location"] == "vault-a"

    daily = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    assert daily["summary"]["paper_execution_latest_bundle_retention_handoff_accepted_count"] == 1


def test_retention_handoff_acceptance_blocks_when_verification_failed(tmp_path: Path) -> None:
    output_root, latest_handoff_verification_path = _setup_handoff_verification(tmp_path)
    raw = json.loads(latest_handoff_verification_path.read_text(encoding="utf-8"))
    raw["verification_status"] = "FAIL"
    raw["blockers"] = ["SYNTHETIC_HANDOFF_VERIFICATION_FAILURE"]
    raw["artifact_sha256"] = canonical_json_sha256({k: v for k, v in raw.items() if k != "artifact_sha256"})
    latest_handoff_verification_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _, _, artifact = write_paper_execution_evidence_bundle_retention_handoff_acceptance_artifact(
        retention_handoff_verification_artifact_path=latest_handoff_verification_path,
        output_root=output_root,
    )

    assert artifact.acceptance_status == "BLOCKED"
    assert artifact.trust_banner == "UNTRUSTED"
    assert "RETENTION_HANDOFF_VERIFICATION_NOT_PASS" in artifact.blockers
