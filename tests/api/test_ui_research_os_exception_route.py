from __future__ import annotations

from strategy_validator.application.research_os_exception_ops import build_ui_research_os_exception_latest_payload


def test_exception_empty_payload_degrades(tmp_path):
    payload = build_ui_research_os_exception_latest_payload(artifact_root=tmp_path)
    assert payload["status"] == "NOT_PRESENT"
    assert "NO_RESEARCH_OS_EXCEPTION_RECORD" in payload["degraded"]
