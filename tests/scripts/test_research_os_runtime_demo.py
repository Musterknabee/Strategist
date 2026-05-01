from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.application.ui_research_os import build_ui_research_os_status_payload
from strategy_validator.cli.research_os_runtime_demo import main as runtime_main
from strategy_validator.contracts.portfolio_allocation import (
    AllocationGateStatus,
    PortfolioAllocationRequest,
    PortfolioAllocationResult,
)
from strategy_validator.contracts.strategy_batch import StrategyBatchRunSummary

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_runtime_demo_writes_manifest_and_ui_sees_it(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    art = tmp_path / "art"
    monkeypatch.chdir(REPO_ROOT)
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(art))
    rc = runtime_main(
        [
            "--artifact-root",
            str(art),
            "--run-id",
            "pytest-runtime-os",
            "--overwrite",
            "--allow-synthetic-demo",
            "--skip-benchmark",
            "--skip-portfolio",
            "--json",
        ]
    )
    assert rc == 0
    man_path = art / "research_os_runtime" / "latest" / "runtime_demo_manifest.json"
    assert man_path.is_file()
    raw = json.loads(man_path.read_text(encoding="utf-8"))
    assert raw.get("schema_version") == "research_os_runtime_demo_manifest/v1"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(art))
    p = build_ui_research_os_status_payload(repo_root=REPO_ROOT)
    assert p["runtime_demo_manifest"]["status"] == "PRESENT"
    assert "STRATEGY_VALIDATOR_API_TOKEN" not in str(p)


def test_ui_research_os_portfolio_present_blocked_not_portfolio_degraded(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """BLOCKED allocation artifact counts as present — not NO_PORTFOLIO_ALLOCATION_ARTIFACT."""
    sr = tmp_path / "strategy_runs" / "b" / "r"
    sr.mkdir(parents=True)
    summ = StrategyBatchRunSummary(
        ok=True,
        batch_id="b",
        run_id="r",
        output_dir=str(sr.resolve()),
        strategy_count=1,
    )
    (sr / "batch_summary.json").write_text(summ.model_dump_json(indent=2), encoding="utf-8")
    req = PortfolioAllocationRequest(batch_run_id="r", capital=100_000.0)
    alloc = PortfolioAllocationResult(request=req, allocation_gate_status=AllocationGateStatus.BLOCKED, blockers=["CORRELATION"])
    (sr / "portfolio_allocation_result.json").write_text(alloc.model_dump_json(indent=2), encoding="utf-8")
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT", str(tmp_path / "strategy_runs"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT", str(tmp_path / "paper_tracking"))
    man = tmp_path / "artifacts" / "research_os_runtime" / "latest" / "runtime_demo_manifest.json"
    man.parent.mkdir(parents=True, exist_ok=True)
    man.write_text(
        json.dumps({"schema_version": "research_os_runtime_demo_manifest/v1", "ok": True, "run_id": "x"}),
        encoding="utf-8",
    )
    sd = tmp_path / "artifacts" / "strategy_data"
    sd.mkdir(parents=True, exist_ok=True)
    (sd / "p_manifest.json").write_text(
        json.dumps({"provider_status": "PENDING_KEY", "pit_status": "BLOCKED_PROVIDER_UNAVAILABLE"}),
        encoding="utf-8",
    )
    p = build_ui_research_os_status_payload(repo_root=tmp_path)
    assert "NO_PORTFOLIO_ALLOCATION_ARTIFACT" not in p["degraded"]
    assert any("PORTFOLIO_ALLOCATION_GATE_BLOCKED" in w for w in p["warnings"])
    assert p["portfolio_allocation_latest"]["allocation_gate_status"] == "BLOCKED"
