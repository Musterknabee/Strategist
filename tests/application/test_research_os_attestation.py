from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.research_os_attestation_ops import (
    build_operator_attestation,
    build_ui_research_os_attestation_latest_payload,
    verify_research_os_closure_manifest,
    write_operator_attestation,
    write_research_os_closure_verification,
)
from strategy_validator.application.research_os_closure_ops import (
    build_research_os_closure_manifest,
    write_research_os_closure_manifest,
)


def test_research_os_closure_verification_detects_digest_match(monkeypatch, tmp_path: Path) -> None:
    art = tmp_path / "artifacts"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(art))
    p = art / "provider_paper_loop" / "latest" / "provider_paper_loop_manifest.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"schema_version": "provider_paper_loop_manifest/v1", "ok": True}, sort_keys=True), encoding="utf-8")
    closure = build_research_os_closure_manifest(closure_id="verify-demo", artifact_root=art)
    cpath = write_research_os_closure_manifest(closure, artifact_root=art, overwrite=True)

    result = verify_research_os_closure_manifest(verification_id="verify-demo", manifest_path=cpath, artifact_root=art)

    assert result.status.value == "VERIFIED"
    assert result.closure_id == "verify-demo"
    assert result.manifest_sha256_expected == result.manifest_sha256_observed
    assert not result.digest_mismatches
    assert result.no_live_trading is True
    assert "STRATEGY_VALIDATOR_API_TOKEN" not in result.model_dump_json()


def test_research_os_closure_verification_detects_artifact_tamper(monkeypatch, tmp_path: Path) -> None:
    art = tmp_path / "artifacts"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(art))
    p = art / "provider_paper_loop" / "latest" / "provider_paper_loop_manifest.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"schema_version": "provider_paper_loop_manifest/v1", "ok": True}, sort_keys=True), encoding="utf-8")
    closure = build_research_os_closure_manifest(closure_id="tamper-demo", artifact_root=art)
    cpath = write_research_os_closure_manifest(closure, artifact_root=art, overwrite=True)
    p.write_text(json.dumps({"schema_version": "provider_paper_loop_manifest/v1", "ok": False}, sort_keys=True), encoding="utf-8")

    result = verify_research_os_closure_manifest(verification_id="tamper-demo", manifest_path=cpath, artifact_root=art)

    assert result.status.value == "TAMPERED"
    assert "provider_paper_loop_manifest" in result.digest_mismatches
    assert any("DIGEST_MISMATCH" in b for b in result.blockers)


def test_operator_attestation_writes_latest_payload(monkeypatch, tmp_path: Path) -> None:
    art = tmp_path / "artifacts"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(art))
    p = art / "provider_paper_loop" / "latest" / "provider_paper_loop_manifest.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"schema_version": "provider_paper_loop_manifest/v1", "ok": True}, sort_keys=True), encoding="utf-8")
    closure = build_research_os_closure_manifest(closure_id="attest-demo", artifact_root=art)
    cpath = write_research_os_closure_manifest(closure, artifact_root=art, overwrite=True)
    verification = verify_research_os_closure_manifest(verification_id="attest-verify", manifest_path=cpath, artifact_root=art)
    vpath = write_research_os_closure_verification(verification, artifact_root=art, overwrite=True)

    attestation = build_operator_attestation(
        attestation_id="operator-attest-demo",
        operator_id="local-operator",
        decision="ACCEPTED_WITH_RESTRICTIONS",
        rationale="paper-only evidence acknowledged",
        verification=verification,
        artifact_root=art,
    )
    apath = write_operator_attestation(attestation, artifact_root=art, overwrite=True)
    payload = build_ui_research_os_attestation_latest_payload(repo_root=tmp_path)

    assert vpath.is_file()
    assert apath.is_file()
    assert payload["schema_version"] == "ui_research_os_attestation/v1"
    assert payload["status"] == "PRESENT"
    assert payload["no_order_controls"] is True
    assert payload["latest_attestation"]["decision"] == "ACCEPTED_WITH_RESTRICTIONS"
    assert "STRATEGY_VALIDATOR_API_TOKEN" not in str(payload)
