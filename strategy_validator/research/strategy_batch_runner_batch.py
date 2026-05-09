"""Batch-level orchestration for strategy batch runs."""
from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.contracts.strategy_batch import (
    StrategyBatchRunManifest,
    StrategyBatchRunSummary,
    StrategyBatchSpec,
    StrategyCandidateSpec,
    StrategyRunResult,
    StrategyRunStatus,
)
from strategy_validator.research.strategy_batch_analytics import apply_batch_ranking
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from strategy_validator.research.strategy_batch_runner_common import (
    _prepare_run_directory,
    _resolve_output_base,
    _run_id_for_batch,
    _write_json,
)
from strategy_validator.research.strategy_batch_runner_single import run_single_strategy_impl
from strategy_validator.research.strategy_portfolio_summary import build_batch_portfolio_summary

def _process_pool_run_single(
    payload: tuple[dict[str, Any], dict[str, Any], str, str, bool],
) -> StrategyRunResult:
    cand_dict, spec_dict, run_id, run_dir_str, allow_synthetic = payload
    cand = StrategyCandidateSpec.model_validate(cand_dict)
    spec = StrategyBatchSpec.model_validate(spec_dict)
    return run_single_strategy_impl(
        candidate=cand,
        batch=spec,
        run_id=run_id,
        run_dir=Path(run_dir_str),
        allow_synthetic=allow_synthetic,
        adjudication_hook=None,
    )




def run_strategy_batch_impl(
    spec: StrategyBatchSpec,
    *,
    allow_synthetic: bool = True,
    fail_fast: bool = False,
    adjudication_hook: Any | None = None,
    run_id: str | None = None,
    overwrite: bool = False,
    run_single_strategy_fn: Any | None = None,
) -> StrategyBatchRunSummary:
    """Run all strategies in *spec* concurrently; write manifests under output_root."""

    single_strategy = run_single_strategy_fn or run_single_strategy_impl

    base = _resolve_output_base(spec)
    run_id_final = run_id.strip() if run_id and run_id.strip() else _run_id_for_batch(spec)
    run_dir = _prepare_run_directory(
        output_base=base, batch_id=spec.batch_id, run_id=run_id_final, overwrite=overwrite
    )

    spec_sha = canonical_json_sha256(spec.model_dump(mode="json"))
    manifest = StrategyBatchRunManifest(
        batch_id=spec.batch_id,
        run_id=run_id_final,
        spec_sha256=spec_sha,
        mode=spec.mode,
        as_of_utc=spec.as_of_utc,
        created_at_utc=datetime.now(timezone.utc),
        output_dir=str(run_dir),
        strategy_count=len(spec.strategies),
        max_workers=spec.max_workers,
        fail_fast=fail_fast,
        allow_synthetic=allow_synthetic,
        adjudication_enabled=adjudication_hook is not None,
        compute_backend="cpu",
        compute_worker_model=spec.worker_model,
        cuda_available=False,
    )
    _write_json(run_dir / "batch_manifest.json", manifest.model_dump(mode="json"))

    results: list[StrategyRunResult] = []
    if fail_fast:
        for cand in sorted(spec.strategies, key=lambda s: s.strategy_id):
            r = single_strategy(
                candidate=cand,
                batch=spec,
                run_id=run_id_final,
                run_dir=run_dir,
                allow_synthetic=allow_synthetic,
                adjudication_hook=adjudication_hook,
            )
            results.append(r)
            if r.status in (StrategyRunStatus.FAILED, StrategyRunStatus.BLOCKED):
                break
    else:
        max_workers = min(spec.max_workers, len(spec.strategies))
        if spec.worker_model == "process_pool":
            if adjudication_hook is not None:
                raise ValueError("WORKER_MODEL_PROCESS_POOL_REQUIRES_ADJUDICATION_DISABLED")
            from concurrent.futures import ProcessPoolExecutor

            spec_dump = spec.model_dump(mode="json")
            tasks = [
                (
                    c.model_dump(mode="json"),
                    spec_dump,
                    run_id_final,
                    str(run_dir),
                    allow_synthetic,
                )
                for c in sorted(spec.strategies, key=lambda s: s.strategy_id)
            ]
            with ProcessPoolExecutor(max_workers=max_workers) as ex:
                futs = [ex.submit(_process_pool_run_single, t) for t in tasks]
                results = [fu.result() for fu in futs]
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futs = {
                    ex.submit(
                        single_strategy,
                        candidate=c,
                        batch=spec,
                        run_id=run_id_final,
                        run_dir=run_dir,
                        allow_synthetic=allow_synthetic,
                        adjudication_hook=adjudication_hook,
                    ): c.strategy_id
                    for c in spec.strategies
                }
                for fut in as_completed(futs):
                    results.append(fut.result())

    results.sort(key=lambda r: r.strategy_id)

    results, batch_ranking = apply_batch_ranking(results)

    portfolio = build_batch_portfolio_summary(
        batch_id=spec.batch_id, run_id=run_id_final, strategies=results
    )
    port_plain = portfolio.model_dump(mode="json")
    _write_json(
        run_dir / "portfolio_correlation_summary.json",
        {
            **port_plain,
            "portfolio_summary_evidence_sha256": portfolio.portfolio_summary_evidence_sha256,
        },
    )

    top_candidate: dict[str, Any] | None = None
    for row in batch_ranking:
        if row.get("blocked_tier"):
            continue
        sid = str(row["strategy_id"])
        match = next((s for s in results if s.strategy_id == sid), None)
        if match is not None and match.gate_summary.promotion_eligible:
            top_candidate = {
                "strategy_id": sid,
                "rank": row["rank"],
                "score": row.get("score"),
            }
            break

    promo_counts: dict[str, int] = {}
    ctr: Counter[str] = Counter()
    for r in results:
        for reason in r.gate_summary.promotion_blocked_reasons:
            key = reason.split(":", 1)[0] if ":" in reason else reason
            ctr[key] += 1
    promo_counts = dict(ctr)

    provider_rows: list[dict[str, str | None]] = []
    for r in results:
        if r.provider_snapshot_source_manifest_path:
            provider_rows.append(
                {
                    "strategy_id": r.strategy_id,
                    "provider_snapshot_source_manifest_path": r.provider_snapshot_source_manifest_path,
                    "provider_snapshot_manifest_sha256": r.provider_snapshot_manifest_sha256,
                }
            )
    if provider_rows:
        _write_json(
            run_dir / "batch_provider_historical_evidence.json",
            {
                "schema_version": "batch_provider_historical_evidence/v1",
                "batch_id": spec.batch_id,
                "run_id": run_id_final,
                "strategies": provider_rows,
            },
        )

    passed = sum(1 for r in results if r.status == StrategyRunStatus.PASSED)
    blocked = sum(1 for r in results if r.status == StrategyRunStatus.BLOCKED)
    paper = sum(1 for r in results if r.status == StrategyRunStatus.PAPER_ONLY)
    failed = sum(1 for r in results if r.status == StrategyRunStatus.FAILED)
    pending = len(spec.strategies) - len(results)

    summary = StrategyBatchRunSummary(
        ok=failed == 0 and pending == 0,
        batch_id=spec.batch_id,
        run_id=run_id_final,
        output_dir=str(run_dir),
        strategy_count=len(spec.strategies),
        passed_count=passed,
        blocked_count=blocked,
        paper_only_count=paper,
        failed_count=failed,
        pending_count=pending,
        strategies=results,
        batch_ranking=batch_ranking,
        portfolio_correlation_summary=port_plain,
        top_candidate=top_candidate,
        promotion_blocked_counts=promo_counts,
        manifest=manifest,
    )
    if any(r.status == StrategyRunStatus.FAILED for r in results):
        summary.ok = False
        summary.blockers.append("ONE_OR_MORE_STRATEGIES_FAILED")
    _write_json(run_dir / "batch_summary.json", summary.model_dump(mode="json"))
    return summary



__all__ = ["run_strategy_batch_impl"]
