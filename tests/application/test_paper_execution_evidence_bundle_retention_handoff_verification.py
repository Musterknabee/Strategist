from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff import write_paper_execution_evidence_bundle_retention_handoff_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff_verification import (
    read_paper_execution_evidence_bundle_retention_handoff_verification_views,
    write_paper_execution_evidence_bundle_retention_handoff_verification_artifact,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from tests.application.test_paper_execution_evidence_bundle_retention_handoff import _setup_signoff_verification


def test_retention_handoff_verification_passes_and_surfaces(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    output_root, latest_signoff_verification_path = _setup_signoff_verification(tmp_path)
    latest_handoff_path, _, _ = write_paper_execution_evidence_bundle_retention_handoff_artifact(
        retention_signoff_verification_artifact_path=latest_signoff_verification_path,
        output_root=output_root,
        custodian_id="archive-vault",
        generated_at_utc=datetime(2026, 5, 3, 12, 23, tzinfo=timezone.utc),
    )

    latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_handoff_verification_artifact(
        retention_handoff_artifact_path=latest_handoff_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 24, tzinfo=timezone.utc),
    )

    assert latest_path.exists()
    assert history_path.exists()
    assert artifact.verification_status == "PASS"
    assert artifact.trust_banner == "TRUSTED"
    assert artifact.retention_handoff_artifact_hash_valid is True
    assert artifact.handoff_statement_hash_valid is True
    assert artifact.retention_signoff_verification_artifact_hash_valid is True
    assert artifact.recomputed_retention_entry_count == 7
    assert artifact.execution_authority == "NONE"

    views = read_paper_execution_evidence_bundle_retention_handoff_verification_views(output_root=output_root)
    assert views and views[0].verification_status == "PASS"

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["latest_evidence_bundle_retention_handoff_verification_status"] == "PASS"
    assert cockpit["latest_evidence_bundle_retention_handoff_verification"]["handoff_statement_hash_valid"] is True

    daily = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    paper = next(component for component in daily["components"] if component["component_id"] == "paper_execution")
    assert paper["summary"]["latest_evidence_bundle_retention_handoff_verification_status"] == "PASS"
    assert daily["summary"]["paper_execution_latest_bundle_retention_handoff_verified_count"] == 1


def test_retention_handoff_verification_blocks_when_statement_tampered(tmp_path: Path) -> None:
    output_root, latest_signoff_verification_path = _setup_signoff_verification(tmp_path)
    latest_handoff_path, _, _ = write_paper_execution_evidence_bundle_retention_handoff_artifact(
        retention_signoff_verification_artifact_path=latest_signoff_verification_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 23, tzinfo=timezone.utc),
    )
    raw = json.loads(latest_handoff_path.read_text(encoding="utf-8"))
    raw["handoff_statement_sha256"] = "0" * 64
    raw["artifact_sha256"] = canonical_json_sha256({k: v for k, v in raw.items() if k != "artifact_sha256"})
    latest_handoff_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _, _, artifact = write_paper_execution_evidence_bundle_retention_handoff_verification_artifact(
        retention_handoff_artifact_path=latest_handoff_path,
        output_root=output_root,
    )

    assert artifact.verification_status == "FAIL"
    assert artifact.trust_banner == "UNTRUSTED"
    assert artifact.handoff_statement_hash_valid is False
    assert "RETENTION_HANDOFF_STATEMENT_SHA256_MISMATCH" in artifact.blockers
