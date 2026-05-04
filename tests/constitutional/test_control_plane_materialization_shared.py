from __future__ import annotations

import json

from strategy_validator.control_plane.materialization import write_json_markdown_artifacts


def test_shared_control_plane_materializer_writes_json_and_markdown_pair(tmp_path) -> None:
    summary_path = tmp_path / "summary.json"
    markdown_path = tmp_path / "summary.md"

    result = write_json_markdown_artifacts(
        summary_output_path=summary_path,
        markdown_output_path=markdown_path,
        payload={"schema_version": "test/v1", "ok": True},
        markdown=["## Test", "- ok: `True`", ""],
    )

    assert json.loads(summary_path.read_text(encoding="utf-8"))["ok"] is True
    assert markdown_path.read_text(encoding="utf-8").endswith("\n")
    assert result.summary_size_bytes == summary_path.stat().st_size
    assert result.markdown_size_bytes == markdown_path.stat().st_size
