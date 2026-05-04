from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff import (
    read_paper_execution_evidence_bundle_retention_handoff_views,
    write_paper_execution_evidence_bundle_retention_handoff_artifact,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_signoff import write_paper_execution_evidence_bundle_retention_signoff_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_signoff_verification import write_paper_execution_evidence_bundle_retention_signoff_verification_artifact
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from tests.application.test_paper_execution_evidence_bundle_retention_signoff_verification import _setup_retention_verification


def _setup_signoff_verification(tmp_path: Path) -> tuple[Path, Path]:
    output_root, latest_retention_verification_path = _setup_retention_verification(tmp_path)
    latest_signoff_path, _, _ = write_paper_execution_evidence_bundle_retention_signoff_artifact(
        retention_verification_artifact_path=latest_retention_verification_path,
        output_root=output_root,
        operator_id="jp",
        decision_note="external retention approved",
        generated_at_utc=datetime(2026, 5, 3, 12, 21, tzinfo=timezone.utc),
    )
    latest_signoff_verification_path, _, _ = write_paper_execution_evidence_bundle_retention_signoff_verification_artifact(
        retention_signoff_artifact_path=latest_signoff_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 22, tzinfo=timezone.utc),
    )
    return output_root, latest_signoff_verification_path


def test_retention_handoff_passes_and_surfaces(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    output_root, latest_signoff_verification_path = _setup_signoff_verification(tmp_path)

    latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_handoff_artifact(
        retention_signoff_verification_artifact_path=latest_signoff_verification_path,
        output_root=output_root,
        custodian_id="archive-vault",
        handoff_note="custody transfer approved",
        generated_at_utc=datetime(2026, 5, 3, 12, 23, tzinfo=timezone.utc),
    )

    assert latest_path.exists()
    assert history_path.exists()
    assert artifact.handoff_status == "READY_FOR_HANDOFF"
    assert artifact.trust_banner == "TRUSTED"
    assert artifact.retention_signoff_verification_artifact_hash_valid is True
    assert artifact.retention_signoff_artifact_hash_valid is True
    assert artifact.signoff_statement_hash_valid is True
    assert artifact.retention_verification_artifact_hash_valid is True
    assert artifact.recomputed_retention_entry_count == 7
    assert artifact.recomputed_retention_ready_entry_count == 7
    assert artifact.no_files_copied is True
    assert artifact.execution_authority == "NONE"

    views = read_paper_execution_evidence_bundle_retention_handoff_views(output_root=output_root)
    assert views and views[0].handoff_status == "READY_FOR_HANDOFF"
    assert views[0].custodian_id == "archive-vault"

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["latest_evidence_bundle_retention_handoff_status"] == "READY_FOR_HANDOFF"
    assert cockpit["latest_evidence_bundle_retention_handoff"]["custodian_id"] == "archive-vault"

    daily = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    paper = next(component for component in daily["components"] if component["component_id"] == "paper_execution")
    assert paper["summary"]["latest_evidence_bundle_retention_handoff_status"] == "READY_FOR_HANDOFF"
    assert daily["summary"]["paper_execution_latest_bundle_retention_handoff_ready_count"] == 1


def test_retention_handoff_blocks_when_signoff_verification_failed(tmp_path: Path) -> None:
    output_root, latest_signoff_verification_path = _setup_signoff_verification(tmp_path)
    raw = json.loads(latest_signoff_verification_path.read_text(encoding="utf-8"))
    raw["verification_status"] = "FAIL"
    raw["blockers"] = ["SYNTHETIC_SIGNOFF_VERIFICATION_FAILURE"]
    raw["artifact_sha256"] = canonical_json_sha256({k: v for k, v in raw.items() if k != "artifact_sha256"})
    latest_signoff_verification_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _, _, artifact = write_paper_execution_evidence_bundle_retention_handoff_artifact(
        retention_signoff_verification_artifact_path=latest_signoff_verification_path,
        output_root=output_root,
    )

    assert artifact.handoff_status == "BLOCKED"
    assert artifact.trust_banner == "UNTRUSTED"
    assert "RETENTION_SIGNOFF_VERIFICATION_NOT_PASS" in artifact.blockers
    assert any(item.endswith("SYNTHETIC_SIGNOFF_VERIFICATION_FAILURE") for item in artifact.blockers)
