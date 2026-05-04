from __future__ import annotations

from strategy_validator.application.research_os_policy_gate_ops import build_ui_research_os_policy_gate_latest_payload


def test_policy_gate_empty_payload_degrades(tmp_path):
    payload = build_ui_research_os_policy_gate_latest_payload(artifact_root=tmp_path)
    assert payload["status"] == "NOT_PRESENT"
    assert "NO_RESEARCH_OS_POLICY_GATE_REPORT" in payload["degraded"]
