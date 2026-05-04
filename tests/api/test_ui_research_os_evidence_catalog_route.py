from __future__ import annotations

from pathlib import Path

from strategy_validator.application.research_os_evidence_catalog_ops import build_ui_research_os_evidence_catalog_latest_payload


def test_ui_research_os_evidence_catalog_empty_degraded(tmp_path: Path) -> None:
    payload = build_ui_research_os_evidence_catalog_latest_payload(artifact_root=tmp_path / "artifacts")

    assert payload["schema_version"] == "ui_research_os_evidence_catalog/v1"
    assert payload["read_plane_only"] is True
    assert payload["no_live_trading"] is True
    assert payload["no_broker_orders"] is True
    assert payload["status"] == "NOT_PRESENT"
