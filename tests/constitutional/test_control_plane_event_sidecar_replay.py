from __future__ import annotations

import json
from datetime import UTC, datetime

from strategy_validator.control_plane.materialization import write_event_backed_json_markdown_artifacts
from strategy_validator.projections.control_plane_event_sidecars import (
    build_control_plane_event_sidecar_replay_report,
    write_control_plane_event_sidecar_replay_report,
)


def test_control_plane_event_sidecar_replay_projection(tmp_path) -> None:
    write_event_backed_json_markdown_artifacts(
        summary_output_path=tmp_path / "artifact.json",
        markdown_output_path=tmp_path / "artifact.md",
        event_output_path=tmp_path / "artifact.event.json",
        event_type="oracle.test.materialized",
        producer="tests",
        payload={"schema_version": "test/v1", "value": 7},
        actor_id="operator",
        target={"work_item_key": "item-1"},
        idempotency_key="sidecar-replay-key",
        markdown=["# Test"],
    )

    report = build_control_plane_event_sidecar_replay_report(tmp_path)
    assert report.ok is True
    assert report.event_count == 1
    assert report.verified_count == 1
    assert report.records[0].event_type == "oracle.test.materialized"

    output = tmp_path / "projection.json"
    written = write_control_plane_event_sidecar_replay_report(event_root=tmp_path, output_path=output)
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert written.ok is True
    assert payload["schema_version"] == "control_plane_event_sidecar_replay/v1"
    assert payload["records"][0]["verified"] is True
