"""Thesis to Oracle mutation proposals to next batch spec (artifacts only; research/paper)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from strategy_validator.contracts.oracle_mutation_proposal import OracleMutationProposalArtifact
from strategy_validator.contracts.strategy_batch import (
    StrategyBatchRunManifest,
    StrategyBatchRunSummary,
    StrategyBatchSpec,
    StrategyCandidateSpec,
    StrategyRunResult,
    StrategyRunStatus,
)
from strategy_validator.research.oracle_mutation_proposal import build_mutation_proposals
from strategy_validator.research.strategy_thesis_generator import build_strategy_thesis_from_result


def _strategies_from_run_dir(run_dir: Path) -> list[StrategyCandidateSpec]:
    out: list[StrategyCandidateSpec] = []
    root = run_dir / "strategies"
    if not root.is_dir():
        return out
    for child in sorted(root.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        inp = child / "input_manifest.json"
        if not inp.is_file():
            continue
        raw = json.loads(inp.read_text(encoding="utf-8"))
        out.append(StrategyCandidateSpec.model_validate(raw["spec"]))
    return out


def run_thesis_mutation_batch_cycle(
    *,
    batch_summary_path: Path,
    next_batch_spec_output: Path,
    loop_report_output: Path | None = None,
) -> dict[str, Any]:
    """Pick first PASSED/PAPER_ONLY strategy, emit thesis + proposals + proposed next batch JSON."""
    summary = StrategyBatchRunSummary.model_validate(json.loads(batch_summary_path.read_text(encoding="utf-8")))
    run_dir = Path(summary.output_dir)
    chosen: StrategyRunResult | None = next(
        (
            s
            for s in summary.strategies
            if s.status in (StrategyRunStatus.PASSED, StrategyRunStatus.PAPER_ONLY)
        ),
        None,
    )
    if chosen is None:
        return {"ok": False, "error": "NO_SUITABLE_STRATEGY_RESULT", "batch_id": summary.batch_id}

    thesis = build_strategy_thesis_from_result(result=chosen, batch_summary=summary)
    proposals: OracleMutationProposalArtifact = build_mutation_proposals(
        thesis=thesis,
        batch_run_id=summary.run_id,
        strategy_type=chosen.strategy_type,
    )

    manifest = StrategyBatchRunManifest.model_validate(json.loads((run_dir / "batch_manifest.json").read_text(encoding="utf-8")))
    strategies = _strategies_from_run_dir(run_dir)
    if not strategies:
        return {"ok": False, "error": "NO_STRATEGY_INPUT_MANIFESTS", "batch_id": summary.batch_id}

    next_batch_id = f"{summary.batch_id}_mutation_next"
    out_root = run_dir.parent / f"{next_batch_id}_runs"
    next_spec = StrategyBatchSpec(
        batch_id=next_batch_id,
        as_of_utc=manifest.as_of_utc,
        mode=manifest.mode,
        strategies=strategies,
        output_root=str(out_root),
        max_workers=manifest.max_workers,
        worker_model=manifest.compute_worker_model,
    )
    next_batch_spec_output.parent.mkdir(parents=True, exist_ok=True)
    next_batch_spec_output.write_text(
        json.dumps(next_spec.model_dump(mode="json"), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    report: dict[str, Any] = {
        "ok": True,
        "schema_version": "thesis_mutation_batch_loop/v1",
        "batch_id": summary.batch_id,
        "run_id": summary.run_id,
        "chosen_strategy_id": chosen.strategy_id,
        "thesis_id": thesis.thesis_id,
        "proposals": proposals.model_dump(mode="json"),
        "next_batch_spec_output": str(next_batch_spec_output.resolve()),
    }
    if loop_report_output is not None:
        loop_report_output.parent.mkdir(parents=True, exist_ok=True)
        loop_report_output.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return report
