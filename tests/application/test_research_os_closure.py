from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.research_os_closure_ops import (
    build_research_os_closure_manifest,
    build_ui_research_os_closure_latest_payload,
    write_research_os_closure_manifest,
)


def test_research_os_closure_empty_root_degrades(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    manifest = build_research_os_closure_manifest(closure_id="empty", artifact_root=tmp_path / "artifacts")
    assert manifest.status.value == "EMPTY"
    assert manifest.trust_banner.value == "UNTRUSTED"
    assert manifest.no_live_trading is True
    assert manifest.no_broker_orders is True
    path = write_research_os_closure_manifest(manifest, artifact_root=tmp_path / "artifacts", overwrite=True)
    assert path.is_file()
    payload = build_ui_research_os_closure_latest_payload(repo_root=tmp_path)
    assert payload["schema_version"] == "ui_research_os_closure/v1"
    assert payload["status"] == "PRESENT"
    assert payload["no_order_controls"] is True
    assert "STRATEGY_VALIDATOR_API_TOKEN" not in str(payload)


def test_research_os_closure_digest_links_present_artifacts(monkeypatch, tmp_path: Path) -> None:
    art = tmp_path / "artifacts"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(art))
    p = art / "provider_paper_loop" / "latest" / "provider_paper_loop_manifest.json"
    p.parent.mkdir(parents=True)
    p.write_text(
        json.dumps(
            {
                "schema_version": "provider_paper_loop_manifest/v1",
                "ok": True,
                "run_id": "demo",
                "warnings": ["PAPER_ONLY"],
                "blockers": [],
                "digests": {"demo": "abc"},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    b = art / "paper_broker" / "latest" / "paper_broker_status.json"
    b.parent.mkdir(parents=True)
    b.write_text(
        json.dumps(
            {
                "schema_version": "paper_broker_status/v1",
                "policy_status": "PENDING_KEY",
                "key_configured": False,
                "warnings": ["NO_BROKER_KEYS"],
                "blockers": [],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    manifest = build_research_os_closure_manifest(closure_id="demo", artifact_root=art)
    assert manifest.present_artifact_count >= 2
    assert manifest.digests["provider_paper_loop_manifest"]
    assert manifest.digests["paper_broker_status"]
    assert manifest.manifest_sha256
    assert manifest.status.value in {"DEGRADED", "COMPLETE"}
    assert any("PENDING_KEY" in w for w in manifest.warnings)
