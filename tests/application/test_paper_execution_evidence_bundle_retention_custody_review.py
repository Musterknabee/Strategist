from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_continuity_verification import write_paper_execution_evidence_bundle_retention_custody_continuity_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_review import (
    read_paper_execution_evidence_bundle_retention_custody_review_views,
    write_paper_execution_evidence_bundle_retention_custody_review_artifact,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from tests.application.test_paper_execution_evidence_bundle_retention_custody_continuity_verification import _setup_custody_continuity


def _setup_custody_continuity_verification(tmp_path: Path) -> tuple[Path, Path]:
    output_root, latest_continuity_path = _setup_custody_continuity(tmp_path)
    latest_continuity_verification_path, _, _ = write_paper_execution_evidence_bundle_retention_custody_continuity_verification_artifact(
        retention_custody_continuity_artifact_path=latest_continuity_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 34, tzinfo=timezone.utc),
    )
    return output_root, latest_continuity_verification_path


def test_retention_custody_review_passes_and_surfaces(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    output_root, latest_continuity_verification_path = _setup_custody_continuity_verification(tmp_path)

    latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_review_artifact(
        retention_custody_continuity_verification_artifact_path=latest_continuity_verification_path,
        output_root=output_root,
        reviewed_by="operator-jp",
        custody_location="vault-a",
        review_note="custody continuity reviewed",
        generated_at_utc=datetime(2026, 5, 3, 12, 35, tzinfo=timezone.utc),
    )

    assert latest_path.exists()
    assert history_path.exists()
    assert artifact.review_status == "REVIEWED"
    assert artifact.trust_banner == "TRUSTED"
    assert artifact.retention_custody_continuity_verification_artifact_hash_valid is True
    assert artifact.recomputed_retention_entry_count == 7
    assert artifact.custody_review_id and artifact.custody_review_id.startswith("retention-custody-review:")
    assert artifact.execution_authority == "NONE"

    views = read_paper_execution_evidence_bundle_retention_custody_review_views(output_root=output_root)
    assert views and views[0].review_status == "REVIEWED"

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["latest_evidence_bundle_retention_custody_review_status"] == "REVIEWED"
    assert cockpit["latest_evidence_bundle_retention_custody_review"]["reviewed_by"] == "operator-jp"

    daily = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    assert daily["summary"]["paper_execution_latest_bundle_retention_custody_reviewed_count"] == 1


def test_retention_custody_review_blocks_when_continuity_verification_failed(tmp_path: Path) -> None:
    output_root, latest_continuity_verification_path = _setup_custody_continuity_verification(tmp_path)
    raw = json.loads(latest_continuity_verification_path.read_text(encoding="utf-8"))
    raw["verification_status"] = "FAIL"
    raw["blockers"] = ["SYNTHETIC_CUSTODY_CONTINUITY_VERIFICATION_FAILURE"]
    raw["artifact_sha256"] = canonical_json_sha256({k: v for k, v in raw.items() if k != "artifact_sha256"})
    latest_continuity_verification_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _, _, artifact = write_paper_execution_evidence_bundle_retention_custody_review_artifact(
        retention_custody_continuity_verification_artifact_path=latest_continuity_verification_path,
        output_root=output_root,
    )

    assert artifact.review_status == "BLOCKED"
    assert artifact.trust_banner == "UNTRUSTED"
    assert "RETENTION_CUSTODY_CONTINUITY_VERIFICATION_NOT_PASS" in artifact.blockers
