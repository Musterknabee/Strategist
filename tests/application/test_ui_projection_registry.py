from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.ui_projection_registry import build_ui_projection_registry_payload


def _write_index(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "ORACLE_PROJECTION_ARTIFACT_INDEX.json").write_text(
        json.dumps(
            {
                "schema_version": "oracle_projection_artifact_index/v1",
                "entry_count": 2,
                "entries": [
                    {
                        "registry_path": "registry.projection.registry.json",
                        "projection_label": "oracle_derived_view",
                        "projection_family": "canonical_event_projection",
                        "projection_version": "v1",
                        "generated_at_utc": "2026-01-01T00:00:00+00:00",
                        "projection_digest_sha256": "a" * 64,
                        "source_artifact_count": 1,
                        "output_artifact_count": 1,
                        "source_artifact_labels": ["source:event_log"],
                        "output_artifact_labels": ["output:derived-view.json"],
                        "output_artifact_paths": ["derived-view.json"],
                    },
                    {
                        "registry_path": "orphan.registry.json",
                        "projection_label": "orphan_label",
                        "projection_family": "orphan_family",
                        "projection_version": "v1",
                        "generated_at_utc": "2026-01-02T00:00:00+00:00",
                        "projection_digest_sha256": "b" * 64,
                        "source_artifact_count": 0,
                        "output_artifact_count": 1,
                        "source_artifact_labels": [],
                        "output_artifact_labels": ["orphan"],
                        "output_artifact_paths": ["orphan.json"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def test_projection_registry_payload_indexes_registered_and_orphan_artifacts(tmp_path: Path) -> None:
    _write_index(tmp_path)
    payload = build_ui_projection_registry_payload(search_root=tmp_path)

    assert payload["schema_version"] == "ui_projection_registry/v1"
    assert payload["read_plane_only"] is True
    assert payload["summary"]["registered_projection_count"] >= 3
    assert payload["summary"]["observed_artifact_entry_count"] == 2
    assert payload["summary"]["orphan_artifact_entry_count"] == 1
    assert "UNREGISTERED_PROJECTION_ARTIFACTS_PRESENT" in payload["degraded"]
    assert any(entry["projection_family"] == "canonical_event_projection" and entry["observed_artifact_count"] == 1 for entry in payload["entries"])


def test_projection_registry_payload_filters_checkpoint_capable_entries(tmp_path: Path) -> None:
    _write_index(tmp_path)
    payload = build_ui_projection_registry_payload(
        search_root=tmp_path,
        supports_checkpoints=True,
        output_label_contains="derived",
        handler_contains="projection_backfill",
    )

    assert payload["filters"]["supports_checkpoints"] is True
    assert payload["summary"]["filtered_projection_count"] >= 1
    assert all(entry["supports_checkpoints"] is True for entry in payload["entries"])
    assert any("derived" in " ".join(entry["output_artifact_labels"]) for entry in payload["entries"])
