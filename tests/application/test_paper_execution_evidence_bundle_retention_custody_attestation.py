from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_attestation import write_paper_execution_evidence_bundle_retention_custody_attestation_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_attestation_verification import write_paper_execution_evidence_bundle_retention_custody_attestation_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_certification import write_paper_execution_evidence_bundle_retention_custody_certification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_certification_verification import write_paper_execution_evidence_bundle_retention_custody_certification_verification_artifact
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from tests.application.test_paper_execution_evidence_bundle_retention_custody_certification import _setup_reconciliation_verification


def _setup_certification_verification(tmp_path: Path) -> tuple[Path, Path]:
    output_root, reconciliation_verification_path = _setup_reconciliation_verification(tmp_path)
    certification_path, _, certification = write_paper_execution_evidence_bundle_retention_custody_certification_artifact(
        retention_custody_reconciliation_verification_artifact_path=reconciliation_verification_path,
        output_root=output_root,
        certified_by="operator-a",
        certification_reason="closed-loop reconciliation accepted",
        custody_location="retention-vault-a",
        generated_at_utc=datetime(2026, 5, 10, 12, 20, tzinfo=timezone.utc),
    )
    assert certification.certification_status == "CERTIFIED"
    certification_verification_path, _, certification_verification = write_paper_execution_evidence_bundle_retention_custody_certification_verification_artifact(
        retention_custody_certification_artifact_path=certification_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 21, tzinfo=timezone.utc),
    )
    assert certification_verification.verification_status == "PASS"
    return output_root, certification_verification_path


def test_retention_custody_attestation_passes_and_surfaces(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    output_root, certification_verification_path = _setup_certification_verification(tmp_path)

    attestation_path, _, attestation = write_paper_execution_evidence_bundle_retention_custody_attestation_artifact(
        retention_custody_certification_verification_artifact_path=certification_verification_path,
        output_root=output_root,
        attested_by="operator-a",
        attestation_reason="certification verification accepted",
        attestation_scope="paper-execution-retention-custody",
        attestation_note="certified custody chain attested",
        generated_at_utc=datetime(2026, 5, 10, 12, 22, tzinfo=timezone.utc),
    )
    assert attestation.attestation_status == "ATTESTED"
    assert attestation.trust_banner == "TRUSTED"
    assert attestation.attested_by == "operator-a"

    _, _, verification = write_paper_execution_evidence_bundle_retention_custody_attestation_verification_artifact(
        retention_custody_attestation_artifact_path=attestation_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 10, 12, 23, tzinfo=timezone.utc),
    )
    assert verification.verification_status == "PASS"
    assert verification.custody_attestation_statement_hash_valid is True

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["latest_evidence_bundle_retention_custody_attestation_status"] == "ATTESTED"
    assert cockpit["latest_evidence_bundle_retention_custody_attestation_verification"]["verification_status"] == "PASS"


def test_retention_custody_attestation_blocks_without_certification_verification(tmp_path: Path) -> None:
    output_root = tmp_path / "artifacts" / "paper_broker"
    _, _, attestation = write_paper_execution_evidence_bundle_retention_custody_attestation_artifact(output_root=output_root)
    assert attestation.attestation_status == "BLOCKED"
    assert "RETENTION_CUSTODY_CERTIFICATION_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE" in attestation.blockers


def test_retention_custody_attestation_verification_blocks_when_statement_tampered(tmp_path: Path) -> None:
    output_root, certification_verification_path = _setup_certification_verification(tmp_path)
    attestation_path, _, _ = write_paper_execution_evidence_bundle_retention_custody_attestation_artifact(
        retention_custody_certification_verification_artifact_path=certification_verification_path,
        output_root=output_root,
    )
    raw = json.loads(attestation_path.read_text(encoding="utf-8"))
    raw["custody_attestation_statement_sha256"] = "0" * 64
    raw["artifact_sha256"] = canonical_json_sha256({k: v for k, v in raw.items() if k != "artifact_sha256"})
    attestation_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _, _, verification = write_paper_execution_evidence_bundle_retention_custody_attestation_verification_artifact(
        retention_custody_attestation_artifact_path=attestation_path,
        output_root=output_root,
    )
    assert verification.verification_status == "FAIL"
    assert verification.custody_attestation_statement_hash_valid is False
