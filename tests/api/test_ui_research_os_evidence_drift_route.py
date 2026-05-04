from __future__ import annotations

from strategy_validator.application.research_os_drift_ops import build_ui_research_os_evidence_drift_latest_payload


def test_ui_research_os_evidence_drift_empty_root_degrades(tmp_path):
    payload = build_ui_research_os_evidence_drift_latest_payload(artifact_root=tmp_path)
    assert payload["status"] == "NOT_PRESENT"
    assert payload["read_plane_only"] is True
    assert payload["no_live_trading"] is True
    assert "NO_RESEARCH_OS_EVIDENCE_DRIFT_REPORT" in payload["degraded"]
