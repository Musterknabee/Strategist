from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from strategy_validator.api.app import create_app


def test_ui_evidence_bundle_index_route_is_read_only_discovery(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts"
    release_root = artifact_root / "release_verification" / "latest"
    release_root.mkdir(parents=True)
    (release_root / "main-release-verification-pack.json").write_text(
        json.dumps({"generated_at_utc": "2026-05-05T00:00:00Z", "status": "PASS"}),
        encoding="utf-8",
    )

    client = TestClient(create_app())
    response = client.get(
        "/ui/evidence-bundles",
        params={
            "repo_root": str(tmp_path),
            "artifact_root": str(artifact_root),
            "include_digests": "true",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "evidence_bundle_index/v1"
    assert payload["blockers"] == []
    assert "Not live trading authorization." in payload["disclaimers"]
    release_entry = next(entry for entry in payload["entries"] if entry["kind"] == "release_verification_pack")
    assert release_entry["exists"] is True
    assert release_entry["status"] == "PASS"
    assert isinstance(release_entry["sha256"], str)


def test_ui_facade_declares_evidence_bundle_index_route() -> None:
    client = TestClient(create_app())
    payload = client.get("/ui/facade").json()
    routes = {(route["method"], route["path"]): route for route in payload["routes"]}
    route = routes[("GET", "/ui/evidence-bundles")]
    assert route["kind"] == "read"
    assert route["auth_required"] is False
    assert route["payload_schema"] == "evidence_bundle_index/v1"
