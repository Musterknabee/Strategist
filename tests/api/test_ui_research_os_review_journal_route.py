from __future__ import annotations

from strategy_validator.application.research_os_review_journal_ops import build_ui_research_os_review_journal_latest_payload


def test_ui_review_journal_empty_root_degraded(tmp_path):
    payload = build_ui_research_os_review_journal_latest_payload(artifact_root=tmp_path)
    assert payload["status"] == "NOT_PRESENT"
    assert payload["read_plane_only"] is True
    assert payload["no_live_trading"] is True
