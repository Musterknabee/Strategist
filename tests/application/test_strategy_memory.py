from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.strategy_memory_ops import (
    build_memory_record_from_batch_result,
    build_strategy_memory_index,
    build_ui_strategy_memory_latest_payload,
    detect_duplicate_variant,
    strategy_memory_root_directory,
    write_memory_record,
)
from strategy_validator.contracts.strategy_batch import StrategyGateSummary, StrategyRunResult, StrategyRunStatus
from strategy_validator.contracts.strategy_memory import StrategyMemoryStatus


def _result(strategy_id: str, *, status: StrategyRunStatus = StrategyRunStatus.BLOCKED) -> StrategyRunResult:
    return StrategyRunResult(
        strategy_id=strategy_id,
        status=status,
        completed_at_utc=datetime.now(timezone.utc),
        data_plane="PROVIDER_SNAPSHOT",
        blockers=["ROBUSTNESS_BLOCKED"],
        gate_summary=StrategyGateSummary(robustness_gate="BLOCKED", promotion_eligible=False),
    )


def test_blocked_strategy_creates_graveyard_entry(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    record = build_memory_record_from_batch_result(
        _result("bad-momentum"),
        batch_id="b1",
        run_id="r1",
        strategy_type="momentum",
        universe="SPY",
        params={"lookback": 20},
    )
    assert record.status == StrategyMemoryStatus.REJECTED
    write_memory_record(record, repo_root=tmp_path)
    root = strategy_memory_root_directory(tmp_path)
    assert (root / "variants" / "bad-momentum.json").is_file()
    assert (root / "graveyard" / "bad-momentum.json").is_file()


def test_duplicate_variant_warning_is_deterministic(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    one = build_memory_record_from_batch_result(
        _result("dup-1", status=StrategyRunStatus.PASSED),
        batch_id="b1",
        run_id="r1",
        strategy_type="momentum",
        universe="SPY",
        params={"lookback": 20},
    )
    two = build_memory_record_from_batch_result(
        _result("dup-2", status=StrategyRunStatus.PASSED),
        batch_id="b1",
        run_id="r2",
        strategy_type="momentum",
        universe="SPY",
        params={"lookback": 20},
    )
    warnings = detect_duplicate_variant(two, [one])
    assert len(warnings) == 1
    assert warnings[0].similar_strategy_id == "dup-1"
    assert "same normalized variant fingerprint" in warnings[0].similarity_basis


def test_memory_index_empty_degraded_200(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    payload = build_ui_strategy_memory_latest_payload(repo_root=tmp_path)
    assert payload["schema_version"] == "ui_strategy_memory/v1"
    assert "NO_STRATEGY_MEMORY_INDEX" in payload["degraded"]
    assert "STRATEGY_VALIDATOR_API_TOKEN" not in str(payload)


def test_memory_index_builds_from_records(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    rec = build_memory_record_from_batch_result(
        _result("bad-robust"),
        batch_id="b1",
        run_id="r1",
        strategy_type="momentum",
        universe="SPY",
        params={"lookback": 20},
    )
    write_memory_record(rec, repo_root=tmp_path)
    index = build_strategy_memory_index(repo_root=tmp_path)
    assert index.rejected_count == 1
    assert index.family_count == 1
    assert index.top_failure_reasons["ROBUSTNESS"] == 1
    assert index.index_sha256
