from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.data_spine.normalize import normalize_one_sample
from strategy_validator.evidence.provider_bundle import build_provider_evidence_manifest_payload
from strategy_validator.oracle.provider_ingestion import build_advisory_summary_from_evidence
from strategy_validator.providers.health import (
    build_provider_health_snapshot,
    provider_health_snapshot_public_payload,
)
from strategy_validator.contracts.evidence_manifest import ProviderEvidenceManifest


def test_provider_health_snapshot_shape_and_no_secrets_in_json() -> None:
    snap = build_provider_health_snapshot(env={}, repo_root=None, samples_manifest_path=None)
    raw = json.dumps(snap.model_dump(mode="json"))
    assert "sk-" not in raw and "apikey=" not in raw.lower()
    assert snap.schema_version == "provider_health_snapshot/v1"
    assert len(snap.entries) >= 1
    for ent in snap.entries:
        assert "http_status" in ent.model_dump(mode="json")


def test_public_payload_omits_null_execution_posture_on_non_alpaca() -> None:
    snap = build_provider_health_snapshot(env={}, repo_root=None, samples_manifest_path=None)
    payload = provider_health_snapshot_public_payload(snap)
    for ent in payload["entries"]:
        assert isinstance(ent, dict)
        pid = ent.get("provider_id")
        if pid == "alpaca":
            assert ent.get("execution_posture") is not None
        else:
            assert "execution_posture" not in ent


def test_alpaca_execution_posture_reflects_env_without_secrets() -> None:
    env = {
        "ALPACA_TRADING_MODE": "paper",
        "PERSONAL_LIVE_APPROVED": "false",
    }
    snap = build_provider_health_snapshot(env=env, repo_root=None, samples_manifest_path=None)
    alpaca = next(e for e in snap.entries if e.provider_id == "alpaca")
    assert alpaca.execution_posture is not None
    assert alpaca.execution_posture.get("trading_mode") == "paper"
    assert alpaca.execution_posture.get("personal_live_approved") is False
    assert alpaca.execution_posture.get("execution_authority") == "NOT_BLOCKED_BY_POLICY"
    dumped = json.dumps(snap.model_dump(mode="json"))
    assert "sk-" not in dumped


def test_provider_health_http_status_from_manifest(tmp_path: Path) -> None:
    row = {
        "provider_id": "fred",
        "classified_status": "OK",
        "http_status": 200,
        "sha256": "a" * 64,
        "retrieved_at_utc": "2024-01-01T00:00:00+00:00",
    }
    man = tmp_path / "manifest.json"
    man.write_text(json.dumps({"entries": [row]}), encoding="utf-8")
    snap = build_provider_health_snapshot(env={}, repo_root=tmp_path, samples_manifest_path=man)
    fred = next(e for e in snap.entries if e.provider_id == "fred")
    assert fred.http_status == 200


def test_normalize_fred_deterministic_digest(tmp_path: Path) -> None:
    body = {
        "observations": [{"date": "2020-01-01", "value": "1.0"}],
    }
    raw_path = tmp_path / "fred.json"
    raw_path.write_text(json.dumps(body), encoding="utf-8")
    row = {
        "provider_id": "fred",
        "classified_status": "OK",
        "http_status": 200,
        "retrieved_at_utc": "2024-01-01T00:00:00+00:00",
        "endpoint": "https://api.stlouisfed.org/fred/series/observations",
        "query_params": {"series_id": "GDP"},
        "sample_path": "fred.json",
    }
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"entries": [row]}), encoding="utf-8")
    rec = normalize_one_sample(
        provider_id="fred",
        manifest_row=row,
        raw_bytes=raw_path.read_bytes(),
        samples_dir=tmp_path,
    )
    assert rec is not None
    d1 = rec.normalized_digest
    rec2 = normalize_one_sample(
        provider_id="fred",
        manifest_row=row,
        raw_bytes=raw_path.read_bytes(),
        samples_dir=tmp_path,
    )
    assert rec2 is not None
    assert rec2.normalized_digest == d1


def test_evidence_manifest_deterministic_with_fixed_ids(tmp_path: Path) -> None:
    man = tmp_path / "manifest.json"
    man.write_text(json.dumps({"entries": []}), encoding="utf-8")
    health = build_provider_health_snapshot(env={}, repo_root=None, samples_manifest_path=man)
    m1 = build_provider_evidence_manifest_payload(
        samples_manifest_path=man,
        normalized_records_path=None,
        health_snapshot=health,
        generated_at_utc="2099-01-01T00:00:00+00:00",
        source_run_id="fixed-run",
    )
    m2 = build_provider_evidence_manifest_payload(
        samples_manifest_path=man,
        normalized_records_path=None,
        health_snapshot=health,
        generated_at_utc="2099-01-01T00:00:00+00:00",
        source_run_id="fixed-run",
    )
    assert m1.model_dump(mode="json") == m2.model_dump(mode="json")


def test_oracle_advisory_from_manifest_no_ledger_import() -> None:
    m = ProviderEvidenceManifest(
        generated_at_utc="t",
        source_run_id="r",
        provider_sample_manifest_digest="a",
        normalized_records_digest="b",
        provider_health_digest="c",
    )
    adv = build_advisory_summary_from_evidence(manifest=m, normalized_records=None)
    assert adv.advisory_only is True
    assert adv.ledger_mutation_disclaimed is True


def test_oracle_provider_ingestion_module_avoids_authority_imports() -> None:
    import strategy_validator.oracle.provider_ingestion as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "strategy_validator.validator" not in src
    assert "ledger.writer" not in src
    assert "promotion" not in src.lower()
