from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.research_os_evidence_catalog_ops import (
    build_and_write_research_os_evidence_catalog,
    build_research_os_evidence_catalog,
    build_ui_research_os_evidence_catalog_latest_payload,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def test_catalog_indexes_operator_run_and_latest(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    _write_json(
        root / "research_os_operator_runs" / "latest" / "research_os_operator_run_manifest.json",
        {
            "schema_version": "research_os_operator_run_manifest/v1",
            "run_id": "r1",
            "status": "RESTRICTED",
            "trust_banner": "TRUST_RESTRICTED",
            "warnings": ["demo"],
            "blockers": [],
            "ok": True,
        },
    )

    catalog = build_research_os_evidence_catalog(catalog_id="c1", artifact_root=root)

    assert catalog.entry_count == 1
    assert catalog.latest_entry_count == 1
    assert catalog.category_counts["OPERATOR_RUN"] == 1
    assert catalog.entries[0].file_sha256
    assert catalog.entries[0].status_hint == "RESTRICTED"
    assert catalog.status.value == "RESTRICTED"
    assert catalog.manifest_sha256


def test_catalog_blocks_secret_marker(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    _write_json(
        root / "research_os_closure" / "latest" / "research_os_closure_manifest.json",
        {"schema_version": "research_os_closure_manifest/v1", "closure_id": "c", "status": "COMPLETE", "note": "PRIVATE_KEY"},
    )

    catalog = build_research_os_evidence_catalog(catalog_id="c2", artifact_root=root)

    assert catalog.status.value == "BLOCKED"
    assert any("SECRET_MARKER_PRESENT" in b for b in catalog.blockers)


def test_catalog_latest_payload_degrades_when_missing(tmp_path: Path) -> None:
    payload = build_ui_research_os_evidence_catalog_latest_payload(artifact_root=tmp_path / "artifacts")

    assert payload["status"] == "NOT_PRESENT"
    assert "NO_RESEARCH_OS_EVIDENCE_CATALOG" in payload["degraded"]


def test_catalog_write_and_latest_payload(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    _write_json(
        root / "research_os_briefings" / "latest" / "research_os_briefing_pack.json",
        {"schema_version": "research_os_briefing_pack/v1", "briefing_id": "b", "status": "READY", "warnings": [], "blockers": []},
    )

    catalog, path = build_and_write_research_os_evidence_catalog(catalog_id="c3", artifact_root=root, overwrite=True)
    payload = build_ui_research_os_evidence_catalog_latest_payload(artifact_root=root)

    assert path.is_file()
    assert payload["status"] == "PRESENT"
    assert payload["latest"]["catalog_id"] == catalog.catalog_id
    assert payload["latest"]["entry_count"] == 1
