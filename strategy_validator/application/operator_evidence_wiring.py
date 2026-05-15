"""Wire optional Research OS / Oracle satellite modules into the artifact spine (paper-only)."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from strategy_validator.application.oracle_evidence_bridge import discover_latest_batch_summary
from strategy_validator.application.research_os_paths import artifact_root_directory
from strategy_validator.application.shadow_book_ops import create_shadow_book, mark_to_market, simulate_daily_fills
from strategy_validator.application.strategy_memory_ops import (
    build_strategy_memory_index,
    ingest_batch_run,
    strategy_memory_root_directory,
)
from strategy_validator.contracts.portfolio_allocation import AllocationMethod, PortfolioAllocationRequest
from strategy_validator.contracts.shadow_book import ShadowBookAllocation
from strategy_validator.contracts.strategy_batch import StrategyBatchRunSummary, StrategyRunStatus
from strategy_validator.research.portfolio_allocation import simulate_portfolio_allocation


def _read_summary(path: Path) -> StrategyBatchRunSummary:
    return StrategyBatchRunSummary.model_validate(json.loads(path.read_text(encoding="utf-8")))


def wire_strategy_memory(*, batch_run_dir: Path, repo_root: Path | None = None) -> dict[str, Any]:
    records = ingest_batch_run(batch_run_dir.resolve())
    index = build_strategy_memory_index(repo_root=repo_root)
    root = strategy_memory_root_directory(repo_root)
    return {
        "ok": True,
        "ingested": len(records),
        "index_path": str(root / "latest" / "memory_index.json"),
        "active_count": index.active_count,
    }


def wire_shadow_book_from_batch(
    *,
    summary: StrategyBatchRunSummary,
    book_id: str = "operator-shadow-book",
    starting_capital: float = 100_000.0,
    overwrite: bool = True,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    passed = [s for s in summary.strategies if s.status in (StrategyRunStatus.PASSED, StrategyRunStatus.PAPER_ONLY)]
    if not passed:
        return {"ok": False, "error": "NO_PASSED_STRATEGIES_FOR_SHADOW_BOOK"}
    weight = 1.0 / len(passed)
    allocations = [
        ShadowBookAllocation(
            strategy_id=s.strategy_id,
            target_weight=round(weight, 6),
            notional=round(starting_capital * weight, 2),
        )
        for s in passed
    ]
    book = create_shadow_book(
        book_id=book_id,
        starting_capital=starting_capital,
        allocations=allocations,
        overwrite=overwrite,
        repo_root=repo_root,
    )
    as_of = date(2026, 5, 1)
    simulate_daily_fills(book_id, as_of_date=as_of, repo_root=repo_root)
    snap = mark_to_market(book_id, as_of_date=as_of, repo_root=repo_root)
    return {
        "ok": True,
        "book_id": book_id,
        "allocation_count": len(allocations),
        "snapshot_status": snap.status.value,
    }


def wire_portfolio_allocation_if_missing(*, batch_run_dir: Path) -> dict[str, Any]:
    out = batch_run_dir / "portfolio_allocation_result.json"
    if out.is_file():
        return {"ok": True, "skipped": True, "path": str(out)}
    run_dir, summary = batch_run_dir, _read_summary(batch_run_dir / "batch_summary.json")
    req = PortfolioAllocationRequest(
        batch_run_id=summary.run_id,
        capital=100_000.0,
        method=AllocationMethod.equal_weight,
    )
    result = simulate_portfolio_allocation(summary, run_dir=run_dir, request=req)
    out.write_text(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"ok": True, "skipped": False, "path": str(out)}


def wire_research_os_satellite_reports(
    *,
    artifact_root: Path,
    repo_root: Path,
    run_id: str = "full-operator",
    overwrite: bool = True,
) -> dict[str, Any]:
    from strategy_validator.application.research_os_evidence_catalog_ops import build_and_write_research_os_evidence_catalog
    from strategy_validator.application.research_os_drift_ops import build_and_write_research_os_evidence_drift_report
    from strategy_validator.application.research_os_handoff_ops import build_and_write_research_os_handoff_pack
    from strategy_validator.application.research_os_policy_gate_ops import build_and_write_research_os_policy_gate_report
    from strategy_validator.application.research_os_release_readiness_ops import build_and_write_research_os_release_readiness_report
    from strategy_validator.application.research_os_review_journal_ops import build_and_write_research_os_review_journal

    art = artifact_root.resolve()
    repo = repo_root.resolve()
    out: dict[str, Any] = {}

    cat, cat_path = build_and_write_research_os_evidence_catalog(
        catalog_id="research-os-evidence-catalog",
        repo_root=repo,
        artifact_root=art,
        overwrite=overwrite,
    )
    out["evidence_catalog"] = {"path": str(cat_path), "entry_count": len(cat.entries)}

    drift, drift_path = build_and_write_research_os_evidence_drift_report(
        drift_id="research-os-evidence-drift",
        repo_root=repo,
        artifact_root=art,
        overwrite=overwrite,
    )
    out["evidence_drift"] = {"path": str(drift_path), "status": drift.status.value}

    gate, gate_path = build_and_write_research_os_policy_gate_report(
        gate_id="research-os-policy-gate",
        repo_root=repo,
        artifact_root=art,
        overwrite=overwrite,
    )
    out["policy_gate"] = {"path": str(gate_path), "decision": gate.decision.value}

    rr, rr_path = build_and_write_research_os_release_readiness_report(
        report_id="research-os-release-readiness",
        artifact_root=art,
        repo_root=repo,
        overwrite=overwrite,
    )
    out["release_readiness"] = {"path": str(rr_path), "status": rr.status.value}

    handoff, handoff_path = build_and_write_research_os_handoff_pack(
        handoff_id="research-os-handoff",
        artifact_root=art,
        repo_root=repo,
        overwrite=overwrite,
    )
    out["handoff"] = {"path": str(handoff_path), "status": handoff.status.value}

    journal, journal_path = build_and_write_research_os_review_journal(
        journal_id="research-os-review-journal",
        artifact_root=art,
        repo_root=repo,
        overwrite=overwrite,
    )
    out["review_journal"] = {"path": str(journal_path), "status": journal.status.value}

    out["ok"] = True
    return out


def wire_paper_replay_verify(*, artifact_root: Path, repo_root: Path) -> dict[str, Any]:
    from strategy_validator.application.paper_research_replay import discover_replay_manifest_path, verify_replay_manifest

    manifest = discover_replay_manifest_path(repo_root=repo_root, artifact_root=artifact_root)
    if manifest is None:
        return {"ok": True, "skipped": True, "reason": "NO_REPLAY_MANIFEST"}
    summary = verify_replay_manifest(
        manifest,
        repo_root=repo_root,
        artifact_root=artifact_root,
        allow_absolute_paths=True,
    )
    return {"ok": summary.ok, "skipped": False, "replay_ok": summary.ok, "blockers": list(summary.blockers)}


def wire_all_operator_evidence_modules(
    *,
    artifact_root: Path | None = None,
    repo_root: Path | None = None,
    run_id: str = "full-operator",
    overwrite: bool = True,
) -> dict[str, Any]:
    """Populate closure/operator/briefing dependencies not covered by batch+provider+runtime alone."""
    art = (artifact_root or artifact_root_directory(repo_root)).resolve()
    repo = (repo_root or Path.cwd()).resolve()
    report: dict[str, Any] = {"artifact_root": str(art), "steps": {}, "warnings": []}

    try:
        summary_path = discover_latest_batch_summary(art)
        batch_run_dir = summary_path.parent
        summary = _read_summary(summary_path)
    except FileNotFoundError as exc:
        report["ok"] = False
        report["error"] = str(exc)
        return report

    for name, fn in (
        ("strategy_memory", lambda: wire_strategy_memory(batch_run_dir=batch_run_dir, repo_root=repo)),
        ("shadow_book", lambda: wire_shadow_book_from_batch(summary=summary, repo_root=repo, overwrite=overwrite)),
        ("portfolio_allocation", lambda: wire_portfolio_allocation_if_missing(batch_run_dir=batch_run_dir)),
    ):
        try:
            report["steps"][name] = fn()
        except Exception as exc:
            report["warnings"].append(f"{name}:{type(exc).__name__}:{exc}")
            report["steps"][name] = {"ok": False, "error": str(exc)}

    try:
        report["steps"]["research_os_satellites"] = wire_research_os_satellite_reports(
            artifact_root=art,
            repo_root=repo,
            run_id=run_id,
            overwrite=overwrite,
        )
    except Exception as exc:
        report["warnings"].append(f"research_os_satellites:{type(exc).__name__}:{exc}")
        report["steps"]["research_os_satellites"] = {"ok": False, "error": str(exc)}

    try:
        report["steps"]["paper_replay_verify"] = wire_paper_replay_verify(artifact_root=art, repo_root=repo)
    except Exception as exc:
        report["warnings"].append(f"paper_replay_verify:{type(exc).__name__}:{exc}")
        report["steps"]["paper_replay_verify"] = {"ok": False, "error": str(exc)}

    manifest_path = art / "operator_wiring" / "latest" / "operator_evidence_wiring_report.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    report["ok"] = not report.get("error")
    manifest_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report["manifest_path"] = str(manifest_path)
    return report
