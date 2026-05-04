from __future__ import annotations

from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload


def test_daily_operator_run_is_read_plane_and_composite(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_INTAKE_ROOT", str(tmp_path / "intake"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT", str(tmp_path / "batches"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_MEMORY_ROOT", str(tmp_path / "memory"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    payload = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    assert payload["schema_version"] == "ui_daily_operator_run/v1"
    assert payload["read_plane_only"] is True
    assert payload["mutation_authority"] == "NONE"
    assert payload["promotion_authority"] == "NONE"
    assert payload["execution_authority"] == "NONE"
    assert payload["summary"]["component_count"] == 7
    assert {c["component_id"] for c in payload["components"]} == {
        "provider_setup",
        "strategy_intake",
        "backtest_forensics",
        "strategy_graveyard",
        "evidence_chain",
        "paper_execution",
        "research_os_operator_run",
    }
    assert "/ui/provider-setup" in payload["source_routes"]
    assert "/ui/paper-execution/latest" in payload["source_routes"]
    assert payload["recommended_actions"]
