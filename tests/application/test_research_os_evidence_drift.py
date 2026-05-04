from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.research_os_drift_ops import build_and_write_research_os_evidence_drift_report
from strategy_validator.contracts.research_os_drift import ResearchOsEvidenceDriftChangeType


def _catalog(root: Path, catalog_id: str, digest: str, status: str = "READY") -> Path:
    path = root / "research_os_evidence_catalog" / "catalogs" / catalog_id / "research_os_evidence_catalog.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "research_os_evidence_catalog/v1",
        "catalog_id": catalog_id,
        "generated_at_utc": "2026-05-01T00:00:00+00:00",
        "artifact_root": str(root),
        "status": status,
        "trust_banner": "TRUSTED" if status == "READY" else "TRUST_RESTRICTED",
        "read_plane_only": True,
        "no_live_trading": True,
        "no_broker_orders": True,
        "no_order_controls": True,
        "no_profitability_claim": True,
        "deployment_approval_unchanged": True,
        "entry_count": 1,
        "latest_entry_count": 1,
        "category_counts": {"CLOSURE": 1},
        "latest_by_category": {"CLOSURE": "research_os_closure/latest/research_os_closure_manifest.json"},
        "entries": [
            {
                "schema_version": "research_os_evidence_catalog_entry/v1",
                "label": "closure",
                "category": "CLOSURE",
                "artifact_path": str(root / "research_os_closure/latest/research_os_closure_manifest.json"),
                "relative_path": "research_os_closure/latest/research_os_closure_manifest.json",
                "file_sha256": digest,
                "size_bytes": 12,
                "schema_version_observed": "research_os_closure_manifest/v1",
                "generated_at_utc": "2026-05-01T00:00:00+00:00",
                "status_hint": status,
                "trust_banner_hint": "TRUSTED" if status == "READY" else "TRUST_RESTRICTED",
                "ok_hint": True,
                "run_id_hint": "run",
                "required": True,
                "latest_alias": True,
                "warnings": [],
                "blockers": [],
                "metadata": {},
            }
        ],
        "warnings": [],
        "blockers": [],
        "catalog_spine_sha256": "spine",
        "manifest_sha256": "manifest",
        "disclaimer": "test",
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_evidence_drift_detects_changed_digest(tmp_path: Path) -> None:
    base = _catalog(tmp_path, "base", "a" * 64)
    cand = _catalog(tmp_path, "cand", "b" * 64)
    report, path = build_and_write_research_os_evidence_drift_report(
        drift_id="drift-test",
        artifact_root=tmp_path,
        baseline_catalog_path=base,
        candidate_catalog_path=cand,
        overwrite=True,
    )
    assert path.is_file()
    assert report.changed_count == 1
    assert report.entries[0].change_type == ResearchOsEvidenceDriftChangeType.CHANGED
    assert "file_sha256" in report.entries[0].changed_fields
    assert report.no_live_trading is True
    assert report.no_broker_orders is True


def test_evidence_drift_self_baseline_is_restricted_not_blocked(tmp_path: Path) -> None:
    _catalog(tmp_path, "only", "a" * 64)
    report, _ = build_and_write_research_os_evidence_drift_report(
        drift_id="self-baseline",
        artifact_root=tmp_path,
        overwrite=True,
    )
    assert report.status.value == "RESTRICTED"
    assert report.unchanged_count == 1
    assert any("SELF_BASELINE_USED" in w for w in report.warnings)
